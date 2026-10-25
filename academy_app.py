"""
Kept so a deployment created with `academy_app.py` as its main file keeps
working: the Academy is now one space of the Sensitor platform.

    streamlit run sensitor_app.py      # the entry point to use
"""

import os
import runpy

runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sensitor_app.py"),
               run_name="__main__")
