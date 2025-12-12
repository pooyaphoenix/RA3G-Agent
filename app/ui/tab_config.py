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

    editable_config = {}
    
    # Master Toggles Section
    st.markdown("### 🎛️ Master Controls")
    
    # Get current master toggle states
    pii_detection_enabled = config_data.get("PII_DETECTION_ENABLED", True)
    governance_enabled = config_data.get("GOVERNANCE_ENABLED", True)
    
    master_col1, master_col2 = st.columns(2)
    with master_col1:
        pii_master_toggle = st.toggle(
            "🔒 Enable PII Detection",
            value=pii_detection_enabled,
            key="pii_master_toggle",
            help="Master switch to enable/disable all PII detection and redaction"
        )
    with master_col2:
        governance_master_toggle = st.toggle(
            "🛡️ Enable Governance Policies",
            value=governance_enabled,
            key="governance_master_toggle",
            help="Master switch to enable/disable all governance checks (banned phrases, confidence thresholds)"
        )
    
    st.divider()
    
    # PII Filters Section
    st.markdown("### 🔒 PII Detection Filters")
    st.caption("Configure which types of Personally Identifiable Information (PII) should be redacted.")
    
    # Fetch current PII config from backend
    try:
        pii_response = requests.get(f"{fastapi_url}/pii/config", timeout=2)
        if pii_response.status_code == 200:
            current_pii_filters = pii_response.json().get("pii_filters", {})
        else:
            current_pii_filters = config_data.get("PII_FILTERS", {
                "REDACTED_EMAIL": True,
                "REDACTED_PHONE": True,
                "REDACTED_IP": True,
                "REDACTED_DATE": True,
                "REDACTED_ID": True,
                "REDACTED_NAME": True,
            })
    except:
        current_pii_filters = config_data.get("PII_FILTERS", {
            "REDACTED_EMAIL": True,
            "REDACTED_PHONE": True,
            "REDACTED_IP": True,
            "REDACTED_DATE": True,
            "REDACTED_ID": True,
            "REDACTED_NAME": True,
        })
    
    # Display PII filter checkboxes (disabled if master toggle is off)
    pii_filter_labels = {
        "REDACTED_EMAIL": "📧 Email Addresses",
        "REDACTED_PHONE": "📞 Phone Numbers",
        "REDACTED_IP": "🌐 IP Addresses",
        "REDACTED_DATE": "📅 Dates",
        "REDACTED_ID": "🆔 IDs (SSN, Passport, etc.)",
        "REDACTED_NAME": "👤 Names",
    }
    
    updated_pii_filters = {}
    col1, col2 = st.columns(2)
    
    pii_items = list(current_pii_filters.items())
    for i, (key, value) in enumerate(pii_items):
        col = col1 if i % 2 == 0 else col2
        with col:
            label = pii_filter_labels.get(key, key)
            updated_pii_filters[key] = st.checkbox(
                label,
                value=value if pii_master_toggle else False,
                disabled=not pii_master_toggle,
                key=f"pii_filter_{key}",
                help=f"Enable/disable redaction of {key.replace('REDACTED_', '').lower()}" + (" (disabled - PII detection is off)" if not pii_master_toggle else "")
            )
    
    # Save Master Toggles and PII filters button
    if st.button("💾 Save All Settings", key="save_all_settings_btn"):
        try:
            # Update master toggles via API
            toggles_response = requests.put(
                f"{fastapi_url}/config/master-toggles",
                json={
                    "pii_detection_enabled": pii_master_toggle,
                    "governance_enabled": governance_master_toggle
                },
                timeout=5
            )
            
            # Update PII filters via API
            pii_response = requests.put(
                f"{fastapi_url}/pii/config",
                json={"pii_filters": updated_pii_filters},
                timeout=5
            )
            
            if toggles_response.status_code == 200 and pii_response.status_code == 200:
                # Also update local config file
                config_data["PII_DETECTION_ENABLED"] = pii_master_toggle
                config_data["GOVERNANCE_ENABLED"] = governance_master_toggle
                config_data["PII_FILTERS"] = updated_pii_filters
                with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                    yaml.safe_dump(config_data, f, sort_keys=False, allow_unicode=True)
                
                st.success("✅ All settings updated successfully! Changes are active immediately.")
            else:
                error_msg = ""
                if toggles_response.status_code != 200:
                    error_msg += f"Master toggles: {toggles_response.text}. "
                if pii_response.status_code != 200:
                    error_msg += f"PII filters: {pii_response.text}"
                st.error(f"Failed to update settings: {error_msg}")
        except Exception as e:
            st.error(f"Error updating settings: {str(e)}")
    
    st.divider()

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

<<<<<<< HEAD
    # --------------------------------------------------------------
    # 📌 Render editable config.yml form
    # --------------------------------------------------------------
=======
    st.markdown("### ⚙️ General Configuration")
    
>>>>>>> 45bf111 (Add configurable PII detection filters with master toggles)
    for key, value in config_data.items():
        # Skip PII_FILTERS as it's handled separately above
        if key == "PII_FILTERS":
            continue
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

<<<<<<< HEAD
    # --------------------------------------------------------------
    # 📌 Save config.yml
    # --------------------------------------------------------------
    if st.button("💾 Save Changes", key="save_config_btn"):
=======
    if st.button("💾 Save General Config", key="save_config_btn"):
        # Preserve PII_FILTERS if they exist
        if "PII_FILTERS" in config_data:
            editable_config["PII_FILTERS"] = config_data["PII_FILTERS"]
>>>>>>> 45bf111 (Add configurable PII detection filters with master toggles)
        for k, v in editable_config.items():
            if isinstance(config_data.get(k), list):
                editable_config[k] = [
                    x.strip() for x in v.split(",") if x.strip()
                ]

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
<<<<<<< HEAD
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
=======
            yaml.safe_dump(editable_config, f, sort_keys=False, allow_unicode=True)
        st.success("✅ General config saved. Restart the service for full effect.")
>>>>>>> 45bf111 (Add configurable PII detection filters with master toggles)
