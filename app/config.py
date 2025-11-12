import os
import yaml


class Config:
    _config_data = None

    @classmethod
    def load_config(cls, path: str = "config.yml"):
        """Load YAML configuration file once."""
        if cls._config_data is None:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Configuration file not found: {path}")
            with open(path, "r", encoding="utf-8") as file:
                cls._config_data = yaml.safe_load(file)

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
