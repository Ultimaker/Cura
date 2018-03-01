#!/usr/bin/env bash
Xvfb :1 -screen 0 1280x800x16 &
python3 cura_app.py --headless