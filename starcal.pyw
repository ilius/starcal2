#!/usr/bin/env python3
from os.path import dirname, join
with open(join(dirname(__file__), "scal3", "ui_gtk", "starcal.py"), encoding="utf-8") as codeFile:
	exec(codeFile.read())
