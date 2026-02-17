import tkinter as tk
from tkinter import ttk
from .gcode_viewer import GcodeViewer


        
class GcodeFrame:
    """Manages the G-code text area, highlighting, and scrolling."""
    def __init__(self, parent_frame: ttk.Frame):

        title = ttk.Label(parent_frame, text="G-code Execution", style='Heading.TLabel')
        title.pack(anchor=tk.NW, pady=(0, 10))

        self.filename_label = tk.Label(parent_frame, text="No file selected")
        self.filename_label.pack(anchor=tk.NW, pady=(0, 10))

        self.gcode_viewer = GcodeViewer(parent_frame)

    
    def set_fileHandler(self, filehandler: object):
        self.filename_label.configure(text=filehandler.filename)
        self.gcode_viewer.set_fileHandler(filehandler)
    
    def set_gcode_pointer(self, pointer: int):
        self.gcode_viewer.set_gcode_pointer(pointer)