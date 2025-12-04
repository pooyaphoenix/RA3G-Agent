import streamlit as st
import yaml
import requests
import os


def render_config_tab():
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

        st.success("Config saved. Restart the service.")

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
