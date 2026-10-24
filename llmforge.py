#!/usr/bin/env python3
"""
LLMForge — Terminal Foundry for OpenRouter Free-Tier Models.
Entry point script.
"""

import sys

# Ensure UTF-8 output encoding across Windows and POSIX
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from llmforge.cli import main

if __name__ == "__main__":
    main()
