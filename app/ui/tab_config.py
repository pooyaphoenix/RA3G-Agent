import streamlit as st
import yaml
import requests
import os

def render_config_tab():
    st.subheader("⚙️ Configuration Settings")

    CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config.yml"))

    if not os.path.exists(CONFIG_PATH):
        st.error(f"Configuration file not found: {CONFIG_PATH}")
        return

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    editable_config = {}

    def fetch_ollama_models(ollama_url):
        try:
            url = ollama_url.replace("/api/generate", "/api/tags")
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return [m["name"] for m in response.json().get("models", [])]
        except:
            return []

    ollama_url = config_data.get("OLLAMA_URL", "http://localhost:11434/api/generate")
    available_models = fetch_ollama_models(ollama_url)

    for key, value in config_data.items():
        if key == "OLLAMA_MODEL":
            editable_config[key] = st.selectbox(key, available_models, index=available_models.index(value) if value in available_models else 0) if available_models else st.text_input(key, value)
        elif key == "THRESHOLDS" and isinstance(value, dict):
            editable_config[key] = {k: st.number_input(f"{key} → {k}", value=float(v), min_value=0.0, max_value=1.0, step=0.01) for k, v in value.items()}
        elif isinstance(value, bool):
            editable_config[key] = st.checkbox(key, value=value)
        elif isinstance(value, (int, float)):
            editable_config[key] = st.number_input(key, value=value)
        elif isinstance(value, list):
            editable_config[key] = st.text_area(key, value=", ".join(map(str, value)))
        else:
            editable_config[key] = st.text_input(key, value=str(value))

    if st.button("💾 Save Changes", key="save_config_btn"):
        for k, v in editable_config.items():
            if isinstance(config_data.get(k), list):
                editable_config[k] = [x.strip() for x in v.split(",") if x.strip()]
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(editable_config, f, sort_keys=False, allow_unicode=True)
        st.success("Config saved. Restart the service.")
