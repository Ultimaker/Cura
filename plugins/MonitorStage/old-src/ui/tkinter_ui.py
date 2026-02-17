from .abstract_ui import AbstractUI
from .dark_theme import DarkTheme
from .heating_control import HeatingControl
from .temperature_chart import TemperatureChart
from .gcode import GcodeFrame
import events
from .actions_control import ActionsControl

import tkinter as tk
from tkinter import ttk

class TkinterUi(AbstractUI):
    MIN_WIDTH = 1000
    MIN_HEIGHT = 800

    def __init__(self, logger, update:callable):
        self.logger = logger
        self.registered_events = []

        self.root = tk.Tk()
        self.root.title("3D Printer Control Panel")
        self.root.geometry(f"{TkinterUi.MIN_WIDTH}x{TkinterUi.MIN_HEIGHT}")
        self.root.minsize(TkinterUi.MIN_WIDTH, TkinterUi.MIN_HEIGHT)
        self.root.configure(bg="#282c36")

        self.status_label = tk.Label(self.root, text="Disconnected", fg="red", bg="#282c36", font=("Arial", 10))

        self._update_job_id = None
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._running = True
        self._on_update = update

    def initialize(self):
        """Creates and lays out all the GUI elements using specialized components."""
        
        # Apply dark theme using the global ttk.Style instance
        self.theme = DarkTheme(self.root) # Call without arguments now

        # Main Layout Frames
        top_frame = ttk.Frame(self.root, padding="10 10 10 10", style='DarkFrame.TFrame')
        top_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        bottom_frame = ttk.Frame(self.root, padding="10 10 10 10", style='DarkFrame.TFrame')
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Temperature Chart Section
        temp_chart_frame = ttk.Frame(top_frame, padding="15", style='DarkFrame.TFrame')
        temp_chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        ttk.Label(temp_chart_frame, text="🔴 Current Temperature (Live Chart)", style='Heading.TLabel', foreground='#e74c3c').pack(anchor=tk.NW, pady=(0, 10))
        self.temperature_chart = TemperatureChart(temp_chart_frame)

        actions_frame = ttk.Frame(top_frame, padding="0 15 0 0", style='DarkFrame.TFrame') # Add some top padding
        actions_frame.pack(fill=tk.X, pady=(10,0)) # Fill horizontally within settings_frame
        # Initialize ActionsControl, passing initial callbacks (which might be None at this point)
        self.actions_control = ActionsControl(
            actions_frame,
            play_callback=lambda: self.register_event(events.PlayGcode),
            home_callback=lambda: self.register_event(events.Home),
            pause_callback=lambda: self.register_event(events.PauseGcode),
            jog_callback=lambda movement: self.register_event(events.Jog(movement)),
            open_file_callback=lambda filename: self.register_event(events.NewGcodeFile(filename)),
        )

        # Printer Settings Section
        settings_frame = ttk.Frame(top_frame, padding="15", style='DarkFrame.TFrame')
        settings_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        # ttk.Label(settings_frame, text="Printer Settings", style='Heading.TLabel').pack(anchor=tk.NW, pady=(0, 10))
        
        # Pass the slider_callback to HeatingControl
        def update_heating_temp(tool, level):
            # update horizontal line in graph
            self.temperature_chart.set_target_temperature(tool, level)
            # register event for controller
            self.register_event(events.UpdateTargetTemperature(tool, level))
        self.heating_control = HeatingControl(settings_frame, on_update=update_heating_temp)

        # G-code Execution Section
        self.gcode_frame = ttk.Frame(bottom_frame, padding="15", style='DarkFrame.TFrame')
        self.gcode_viewer = GcodeFrame(self.gcode_frame)
        self.gcode_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def run(self):
        """TODO"""
        self._periodic_update()
        self.root.mainloop()
    
    def handle(self, event: events.Event):
        match event:
            case events.UpdateNozzleTemperature(tool=tool, temperature=temp):
                self.temperature_chart.add_temperatures({tool: temp})
            case events.NewGcodeFileHandler(handler=handler):
                self.gcode_viewer.set_fileHandler(handler)
            case events.SetGcodeLine(line=line):
                self.gcode_viewer.set_gcode_pointer(line)
            case events.ArduinoConnected():
                self.status_label.config(text="Connected", fg="green")
            case events.ArduinoDisconnected():
                self.status_label.config(text="Disconnected", fg="red")
            case _:
                raise NotImplementedError("Event not caught: " + str(event))

        
    def register_event(self, event: events.Event):
        self.registered_events.append(event)

    def update(self):
        """
        Updates the GUI. This is typically handled by the Tkinter event loop,
        but can be called explicitly for immediate redraws if necessary.
        """
        self.root.update_idletasks()

        # return all registered events and clear
        cpy = self.registered_events
        self.registered_events = []
        return cpy

    def _periodic_update(self):
        """
        Performs periodic updates for the controller and UI.
        This simulates continuous data flow and G-code progression.
        """
        if self._running:
            self._on_update()

            # Schedule the next update
            if self._running:
                self._update_job_id = self.root.after(500, self._periodic_update)
            else:
                print("UI is not running, stopping periodic updates.")
    
    def _on_closing(self):
        self._running = False
        self.temperature_chart.close() # Close Matplotlib figure
        self.root.destroy()
        if self._update_job_id:
            self.root.after_cancel(self._update_job_id)