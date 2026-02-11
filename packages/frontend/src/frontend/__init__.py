import os
import sys

from streamlit.web import cli as stcli


def main():
    """Entry point for the frontend application."""
    app_path = os.path.join(os.path.dirname(__file__), "main.py")
    # Streamlit CLI expects the script path as an argument to 'run'
    sys.argv = ["streamlit", "run", app_path]
    sys.exit(stcli.main())
