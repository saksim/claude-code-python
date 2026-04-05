#!/usr/bin/env python3
"""
Claude Code Python - Entry Point
Quick launcher script.
"""

import sys
import os

# Add the package to path if running from source
if os.path.exists(os.path.join(os.path.dirname(__file__), "claude_code")):
    sys.path.insert(0, os.path.dirname(__file__))

from claude_code.main import main

if __name__ == "__main__":
    main()
