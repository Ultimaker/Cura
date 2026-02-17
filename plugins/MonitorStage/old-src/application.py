from core import Controller
from ui import Ui # Renamed Ui to PrinterGUI as per previous refactoring
import tkinter as tk # Tkinter root will be managed here
from logger import Logger

class PrinterApplication:
    """
    Orchestrates the 3D Printer Controller and its Graphical User Interface.
    Manages the setup, communication, and lifecycle of the application.
    """
    def __init__(self):
        self.controller = Controller(Logger("Controller"))
        self.ui = Ui(Logger("Ui"), update=self.update) # Pass the root to the UI

        self._update_job_id = None
        self.gcode_pointer = 0 # Manage gcode pointer state within the application

    def update(self):
        """TODO"""
        for event in self.controller.update():
            self.ui.handle(event)

        for event in self.ui.update():
            self.controller.handle(event)
        
    def run(self):
        """Initializes and runs the application."""
        print("Initializing application...")
        self.controller.connect() # Establish connection to hardware/simulator
        self.ui.initialize()     # Build the UI widgets

        self.ui.run()