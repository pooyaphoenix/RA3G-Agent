import os
import yaml


class Config:
    _config_data = None
    _config_path = "config.yml"

    @classmethod
    def load_config(cls, path: str = None):
        """Load YAML configuration file. If path is None, reloads from last known path."""
        if path:
            cls._config_path = path
        if not os.path.exists(cls._config_path):
            raise FileNotFoundError(f"Configuration file not found: {cls._config_path}")
        with open(cls._config_path, "r", encoding="utf-8") as file:
            cls._config_data = yaml.safe_load(file)
        # Update class attributes dynamically
        for key, value in cls._config_data.items():
            setattr(cls, key, value)

    @classmethod
    def reload_config(cls):
        """Reload configuration from the current config file."""
        cls.load_config()

    @classmethod
    def get(cls, key: str, default=None):
        """Retrieve a configuration value by key."""
        if cls._config_data is None:
            cls.load_config()
        return cls._config_data.get(key, default)

# Load configuration on import
Config.load_config()

# Assign class attributes dynamically (so Config.<var> works)
for key, value in Config._config_data.items():
    setattr(Config, key, value)

# Provide sensible defaults if not supplied in config.yml
if not hasattr(Config, "THRESHOLDS"):
    setattr(
        Config,
        "THRESHOLDS",
        {
            "retriever": 0.6,
            "reasoner": 0.7,
        },
    )
