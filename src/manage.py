#!/usr/bin/env python3
import os
import sys

if __name__ == "__main__":
    src_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(src_dir)
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    if repo_root not in sys.path:
        sys.path.append(repo_root)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
