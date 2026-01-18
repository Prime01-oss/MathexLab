import sys
# [CRITICAL] Import 'run' from your UI app module
# This function contains the Icon setup, Taskbar ID fix, and App creation logic.
from mathexlab.ui.app import run

if __name__ == "__main__":
    # Do not create QApplication here manually. 
    # Just call run(), which handles everything.
    run()