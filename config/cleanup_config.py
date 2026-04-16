import os
import re
import sys
import yaml
from loguru import logger
from core.constants import ConfigFields

DEFAULT_CONFIG_PATH = "rules/cleanup_rules_default.yaml"

def load_cleanup_config():
    clean_config_path = os.getenv("CLEAN_CONFIG_PATH", DEFAULT_CONFIG_PATH)
    if not os.path.exists(clean_config_path):
        logger.critical(f"Cleanup config file not found: {clean_config_path}")
        sys.exit(1)

    with open(clean_config_path, "r", encoding="utf-8") as f:
        try:
            raw = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.exception(f"Error parsing cleanup config: {e}")
            sys.exit(1)

    rules = raw.get("cleanup_rules", {})
    if not isinstance(rules, dict):
        logger.critical("cleanup_rules must be a dictionary")
        sys.exit(1)

    for rule_name, rule in rules.items():
        if not isinstance(rule, dict):
            logger.critical(f"Rule '{rule_name}' must be a dictionary")
            sys.exit(1)

        regexp = rule.get(ConfigFields.REGEXP.value).strip()
        if not isinstance(regexp, str):
            logger.critical(f"Rule '{rule_name}' is not a string")
            sys.exit(1)
        
        # Rexexp check
        try:
            re.compile(regexp)
        except re.error as e:
            logger.critical(f"Rule '{rule_name}' has invalid regexp '{regexp}': {e}")
            sys.exit(1)

    logger.success(f"Cleanup config from {clean_config_path} loaded")
    return rules
