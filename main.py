import os
import configparser
import logging
from media_manager.core.orchestrator import MediaOrchestrator

# Configure logging globally for the application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def load_config(config_path: str = "media_manager/config.ini") -> configparser.ConfigParser:
    """Loads and parses the configuration file."""
    if not os.path.exists(config_path):
        logging.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")
    return config

def main():
    try:
        config = load_config()
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        return

    # Initialize the orchestrator with our config
    orchestrator = MediaOrchestrator(config)

    # Run the workflow
    orchestrator.execute()

if __name__ == "__main__":
    main()