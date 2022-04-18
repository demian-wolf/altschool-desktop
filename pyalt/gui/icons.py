from pathlib import Path
import os.path
import tkinter as tk


def get_iconphoto(filename):
    package_path = Path(__file__).parent.parent
    format_ = os.path.splitext(filename)[1][1:]

    return tk.PhotoImage(
        file=package_path / "icons" / format_ / filename
    )
