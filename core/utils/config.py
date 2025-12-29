"""
Config utility for loading/saving templates and schedule configurations
"""
import json
import os
from pathlib import Path

CONFIG_DIR = "config"
TEMPLATES_CONFIG = os.path.join(CONFIG_DIR, "templates.json")
SCHEDULE_CONFIG = os.path.join(CONFIG_DIR, "schedule.json")

def ensure_config_dir():
    """Create config directory if it doesn't exist"""
    Path(CONFIG_DIR).mkdir(parents=True, exist_ok=True)

def load_template_config():
    """Load template configuration from JSON file"""
    ensure_config_dir()
    if os.path.exists(TEMPLATES_CONFIG):
        with open(TEMPLATES_CONFIG, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_template_config(config):
    """Save template configuration to JSON file"""
    ensure_config_dir()
    with open(TEMPLATES_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def load_schedule_config():
    """Load schedule configuration from JSON file"""
    ensure_config_dir()
    if os.path.exists(SCHEDULE_CONFIG):
        with open(SCHEDULE_CONFIG, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "daily_limit": 30,
        "business_hours_only": False,
        "start_hour": 9,
        "end_hour": 17,
        "delay_seconds": 30,
        "smtp_email": "rikinshah787@gmail.com"
    }

def save_schedule_config(config):
    """Save schedule configuration to JSON file"""
    ensure_config_dir()
    with open(SCHEDULE_CONFIG, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
