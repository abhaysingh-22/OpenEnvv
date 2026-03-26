"""Configuration settings for OpenEnv."""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
TESTS_DIR = PROJECT_ROOT / 'tests'

# Environment settings
MAX_STEPS = 100
TIMEOUT_SECONDS = 300
SEED = 42

# Agent settings
DEFAULT_AGENT_TYPE = 'dummy'
AGENT_CONFIG = {
    'dummy': {},
    'hf': {
        'model_name': 'gpt2',
        'device': 'cpu'
    }
}

# Task settings
TASK_DIFFICULTIES = ['easy', 'medium', 'hard']
DEFAULT_DIFFICULTY = 'medium'

# Grading settings
MAX_REWARD = 1.0
MIN_REWARD = 0.0
STEP_PENALTY = 0.01

# Logging settings
LOG_LEVEL = 'INFO'
LOG_FILE = PROJECT_ROOT / 'logs' / 'openenv.log'

# Data files
TICKETS_EASY_PATH = DATA_DIR / 'tickets_easy.json'
TICKETS_MEDIUM_PATH = DATA_DIR / 'tickets_medium.json'
TICKETS_HARD_PATH = DATA_DIR / 'tickets_hard.json'
ANSWER_KEYS_PATH = DATA_DIR / 'answer_keys.json'
POLICY_PATH = DATA_DIR / 'company_policy.json'
FORBIDDEN_PHRASES_PATH = DATA_DIR / 'forbidden_phrases.txt'
