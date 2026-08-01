import streamlit as st
import yaml
import requests
import os


def render_config_tab(fastapi_url: str = "http://localhost:8010"):
    st.subheader("⚙️ Configuration Settings")

    # ------------------------------------------------------------------
    # 📌 Load config.yml
    # ------------------------------------------------------------------
    CONFIG_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "config.yml")
    )

    if not os.path.exists(CONFIG_PATH):
        st.error(f"Configuration file not found: {CONFIG_PATH}")
        return

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    if not config_data:
        config_data = {}
    if "PII_FILTERS" not in config_data or not isinstance(config_data["PII_FILTERS"], dict):
        config_data["PII_FILTERS"] = {
            "email": True, "phone": True, "ip": True,
            "date": True, "id": True, "name": True,
        }

    editable_config = {}

    # --------------------------------------------------------------
    # 📌 Helper: Fetch available Ollama models
    # --------------------------------------------------------------
    def fetch_ollama_models(ollama_url):
        try:
            url = ollama_url.replace("/api/generate", "/api/tags")
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return [m["name"] for m in response.json().get("models", [])]
        except Exception:
            return []

    ollama_url = config_data.get(
        "OLLAMA_URL", "http://localhost:11434/api/generate"
    )
    available_models = fetch_ollama_models(ollama_url)

    # --------------------------------------------------------------
    # 📌 Render editable config.yml form
    # --------------------------------------------------------------
    for key, value in config_data.items():
        if key == "OLLAMA_MODEL":
            editable_config[key] = (
                st.selectbox(
                    key,
                    available_models,
                    index=available_models.index(value)
                    if value in available_models
                    else 0,
                )
                if available_models
                else st.text_input(key, value)
            )

        elif key == "THRESHOLDS" and isinstance(value, dict):
            editable_config[key] = {
                k: st.number_input(
                    f"{key} → {k}", value=float(v), min_value=0.0, max_value=1.0, step=0.01
                )
                for k, v in value.items()
            }

        elif key == "PII_FILTERS" and isinstance(value, dict):
            st.markdown("**PII detection filters** — enable/disable redaction per type")
            editable_config[key] = {}
            for pii_key, pii_val in sorted(value.items()):
                editable_config[key][pii_key] = st.checkbox(
                    f"Redact {pii_key} ([REDACTED_{pii_key.upper()}])",
                    value=bool(pii_val),
                    key=f"pii_filter_{pii_key}",
                )

        elif isinstance(value, bool):
            editable_config[key] = st.checkbox(key, value=value)

        elif isinstance(value, (int, float)):
            editable_config[key] = st.number_input(key, value=value)

        elif isinstance(value, list):
            editable_config[key] = st.text_area(
                key, value=", ".join(map(str, value))
            )

        else:
            editable_config[key] = st.text_input(key, value=str(value))

    # --------------------------------------------------------------
    # 📌 Save config.yml
    # --------------------------------------------------------------
    if st.button("💾 Save Changes", key="save_config_btn"):
        for k, v in editable_config.items():
            if isinstance(config_data.get(k), list):
                editable_config[k] = [
                    x.strip() for x in v.split(",") if x.strip()
                ]

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                editable_config, f, sort_keys=False, allow_unicode=True
            )

        # Propagate PII filters to backend so they take effect immediately
        if "PII_FILTERS" in editable_config and isinstance(editable_config["PII_FILTERS"], dict):
            try:
                r = requests.put(
                    f"{fastapi_url}/pii/config",
                    json=editable_config["PII_FILTERS"],
                    timeout=5,
                )
                r.raise_for_status()
            except Exception as e:
                st.warning(f"Config saved to file, but backend sync failed: {e}. Restart the service for PII changes.")

        st.success("Config saved. PII filter changes are active immediately.")

    # ==================================================================
    # ==================================================================
    # 📌 NEW SECTION: Instructions Editor (data/instructions.txt)
    # ==================================================================
    # ==================================================================
    st.markdown("---")
    st.markdown("### 📝 Instructions File Editor")

    INSTRUCTIONS_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "instructions.txt")
    )

    # Ensure file exists
    if not os.path.exists(INSTRUCTIONS_PATH):
        st.warning(
            f"instructions.txt not found. Creating new file at:\n{INSTRUCTIONS_PATH}"
        )
        os.makedirs(os.path.dirname(INSTRUCTIONS_PATH), exist_ok=True)
        with open(INSTRUCTIONS_PATH, "w", encoding="utf-8") as f:
            f.write("")

    # Load instructions
    with open(INSTRUCTIONS_PATH, "r", encoding="utf-8") as f:
        instructions_text = f.read()

    # Editable text area
    edited_instructions = st.text_area(
        "Edit Instructions (data/instructions.txt):",
        instructions_text,
        height=300,
    )

    # Save button
    if st.button("💾 Save Instructions", key="save_instructions_btn"):
        try:
            with open(INSTRUCTIONS_PATH, "w", encoding="utf-8") as f:
                f.write(edited_instructions)
            st.success("Instructions saved successfully!")
        except Exception as e:
            st.error(f"Failed to save instructions: {e}")

    # ==================================================================
    # 📌 NEW SECTION: Per-Corpus Confidence Weights  (Issue #25)
    # ==================================================================
    st.markdown("---")
    st.markdown("### ⚖️ Per-Corpus Reliability Weights")
    st.caption(
        "Assign a reliability factor (0.5 = less trusted, 1.0 = neutral, 2.0 = highly trusted) "
        "to each corpus source. These weights influence confidence scoring for answers "
        "drawn from that corpus."
    )

    # Fetch corpus list from backend
    try:
        doc_res = requests.get(f"{fastapi_url}/documents/list", timeout=3)
        all_docs = doc_res.json().get("documents", []) if doc_res.status_code == 200 else []
        # Only consider .txt files (the extracted corpus) or .pdf base names
        corpus_names = sorted({
            os.path.splitext(d)[0]
            for d in all_docs
            if d.lower().endswith((".pdf", ".txt"))
        })
    except Exception:
        corpus_names = []

    # Load current weights from config
    current_weights: dict = config_data.get("CORPUS_WEIGHTS", {})

    if not corpus_names:
        st.info("No corpus documents found. Upload documents in the **Documents** tab first.")
    else:
        corpus_weights_edited = {}
        for name in corpus_names:
            default_weight = float(current_weights.get(name, 1.0))
            corpus_weights_edited[name] = st.slider(
                f"🗂️ {name}",
                min_value=0.1,
                max_value=2.0,
                value=default_weight,
                step=0.05,
                key=f"corpus_weight_{name}",
                help="0.1 = low trust  |  1.0 = neutral  |  2.0 = high trust",
            )

        if st.button("💾 Save Corpus Weights", key="save_corpus_weights_btn"):
            try:
                # Update config.yml
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    live_config = yaml.safe_load(f) or {}
                live_config["CORPUS_WEIGHTS"] = corpus_weights_edited
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    yaml.safe_dump(live_config, f, sort_keys=False, allow_unicode=True)

                # Propagate to backend
                try:
                    r = requests.put(
                        f"{fastapi_url}/confidence/tuning",
                        json={"weights": corpus_weights_edited},
                        timeout=5,
                    )
                    if r.status_code == 200:
                        st.success("Corpus weights saved and applied to backend.")
                    else:
                        st.success("Corpus weights saved to config file.")
                        st.warning(f"Backend sync returned {r.status_code} — restart service to apply.")
                except Exception:
                    st.success("Corpus weights saved to config file.")
                    st.info("Backend not reachable — weights will apply on next service restart.")
            except Exception as e:
                st.error(f"Failed to save corpus weights: {e}")
