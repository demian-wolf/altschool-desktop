import tkinter as tk
import functools

from .base import GUITestCase
from pyalt.gui import icons


class TestGUIIcons(GUITestCase):
    def test__get_iconphoto(self):
        for name in ("app", "updater"):
            iconphoto = icons.get_iconphoto(name + ".png")

            self.assertIsInstance(
                iconphoto,
                tk.PhotoImage,
            )
            self.assertNotIn(
                0,
                (iconphoto.width(), iconphoto.height())
            )

        for filename in ("not_found.png", "foo.bar", "foobar"):
            self.assertRaises(
                tk.TclError,
                functools.partial(icons.get_iconphoto, filename)
            )
