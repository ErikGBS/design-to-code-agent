from __future__ import annotations
import os

ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]

# Model used for every agent/tool call
MODEL = "claude-opus-4-7"

# Max parallel workers for screen fetching and file generation
MAX_PARALLEL_SCREENS = 4
MAX_PARALLEL_FILES = 6
