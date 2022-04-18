import tkinter as tk
import _tkinter
import unittest


class GUITestCase(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.pump_events()

    def tearDown(self):
        self.root.destroy()
        self.pump_events()

    def pump_events(self):
        while self.root.dooneevent(_tkinter.ALL_EVENTS | _tkinter.DONT_WAIT):
            pass
