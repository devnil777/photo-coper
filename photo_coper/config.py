import os
import yaml
from pathlib import Path

DEFAULT_CONFIG_NAME = ".photo-coper.yaml"

DEFAULT_CONFIG = {
    "extensions": ["*.cr2", "*.cr3", "*.raf", "*.jpg"],
    "destination_directories": [],
    "lr_template_path": "",
    "lightroom_exe": "lightroom.exe",  # Default shell command
}

def get_config_path():
    return Path.home() / DEFAULT_CONFIG_NAME

def load_config():
    config_path = get_config_path()
    if not config_path.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
            # Merge with defaults
            config = DEFAULT_CONFIG.copy()
            config.update(user_config)
            return config
    except Exception as e:
        print(f"Ошибка при загрузке конфига: {e}")
        return DEFAULT_CONFIG

def save_config(config):
    config_path = get_config_path()
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config, f, allow_unicode=True)
    except Exception as e:
        print(f"Ошибка при сохранении конфига: {e}")
