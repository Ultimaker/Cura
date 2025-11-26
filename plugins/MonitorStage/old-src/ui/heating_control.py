import tkinter as tk
from tkinter import ttk

class HeatingControl:
    """Manages heating sliders for multiple tools independently."""
    def __init__(self, parent_frame: ttk.Frame, on_update=None):
        self._on_update = on_update

        # Initial slider values
        self.slider_values = {"T0": 20, "T1": 20}

        # --- T0 Slider ---
        ttk.Label(parent_frame, text="T0 Temperature", style='DarkLabel.TLabel').pack(anchor=tk.NW, pady=(5, 0))
        self.slider_t0 = tk.Scale(
            parent_frame,
            from_=20,
            to=50,
            orient=tk.HORIZONTAL,
            command=lambda v: self._on_slider_change("T0", v),
            tickinterval=5,
            showvalue=0,
            relief=tk.RIDGE,
            bd=2
        )
        self.slider_t0.set(self.slider_values["T0"])
        self.slider_t0.pack(fill=tk.X, pady=(0, 10))

        self.label_t0 = ttk.Label(parent_frame, text=f"T0 Heating Level: {self.slider_values['T0']}°C", style='DarkLabel.TLabel')
        self.label_t0.pack(anchor=tk.NW, pady=(0, 10))

        # --- T1 Slider ---
        ttk.Label(parent_frame, text="T1 Temperature", style='DarkLabel.TLabel').pack(anchor=tk.NW, pady=(5, 0))
        self.slider_t1 = tk.Scale(
            parent_frame,
            from_=20,
            to=50,
            orient=tk.HORIZONTAL,
            command=lambda v: self._on_slider_change("T1", v),
            tickinterval=5,
            showvalue=0,
            relief=tk.RIDGE,
            bd=2
        )
        self.slider_t1.set(self.slider_values["T1"])
        self.slider_t1.pack(fill=tk.X, pady=(0, 10))

        self.label_t1 = ttk.Label(parent_frame, text=f"T1 Heating Level: {self.slider_values['T1']}°C", style='DarkLabel.TLabel')
        self.label_t1.pack(anchor=tk.NW, pady=(0, 10))

    def _on_slider_change(self, tool, value):
        """Callback when a slider value changes."""
        level = int(float(value))
        self.slider_values[tool] = level

        # Update label
        if tool == "T0":
            self.label_t0.config(text=f"T0 Heating Level: {level}°C")
        elif tool == "T1":
            self.label_t1.config(text=f"T1 Heating Level: {level}°C")

        # Call update callback if provided
        if self._on_update:
            self._on_update(tool=tool, level=level)
