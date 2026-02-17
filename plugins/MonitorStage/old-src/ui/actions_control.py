import tkinter as tk
from tkinter import ttk

class ActionsControl:
    """Manages the Play, Pause, Stop, and Jog buttons."""
    def __init__(
            self,
            parent_frame: ttk.Frame,
            play_callback: callable = None,
            home_callback: callable = None,
            pause_callback: callable = None,
            stop_callback: callable = None,
            jog_callback: callable = None,
            open_file_callback: callable = None,
        ):
        self.parent_frame = parent_frame

        self.play_callback = play_callback
        self.home_callback = home_callback
        self.pause_callback = pause_callback
        self.stop_callback = stop_callback
        self.jog_callback = jog_callback  # Accept a general jog callback
        self.open_file_callback = open_file_callback

        self.playing = False

        ttk.Label(parent_frame, text="Actions", style='Heading.TLabel').pack(anchor=tk.NW, pady=(0, 10))

        button_frame = ttk.Frame(parent_frame, style='DarkFrame.TFrame')
        button_frame.pack(fill=tk.X, pady=(5, 0))

        self.play_button = ttk.Button(
            button_frame,
            text="▶ Play",
            command=self._on_play,
            style='DarkButton.TButton'
        )
        self.play_button.pack(side=tk.LEFT, expand=True, padx=5, pady=5)

        self.open_file_button = ttk.Button(
            button_frame,
            text="📄 Open",
            command=self._on_open_file,
            style='DarkButton.TButton'
        )
        self.open_file_button.pack(side=tk.LEFT, expand=True, padx=5, pady=5)

        # Jog buttons section
        jog_frame = ttk.Frame(parent_frame, style='DarkFrame.TFrame')
        jog_frame.pack(pady=(10, 0))

        directions = [
            ("X-", [-1, 0, 0, 0], 0, 0), ("X+", [1, 0, 0, 0], 0, 1),
            ("Y-", [0, -1, 0, 0], 1, 0), ("Y+", [0, 1, 0, 0], 1, 1),
            ("Z-", [0, 0, -1, 0], 2, 0), ("Z+", [0, 0, 1, 0], 2, 1),
            ("E-", [0, 0, 0, -1], 3, 0), ("E+", [0, 0, 0, 1], 3, 1),
        ]

        for label, movement, row, col in directions:
            btn = ttk.Button(
                jog_frame,
                text=label,
                command=lambda movement=movement: self._on_jog(movement),
                style='DarkButton.TButton'
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        # Optional: make buttons stretch to fill the frame
        for i in range(3):
            jog_frame.rowconfigure(i, weight=1)
        for i in range(2):
            jog_frame.columnconfigure(i, weight=1)


        self.home_button = ttk.Button(
            button_frame,
            text="🏠 Home",
            command=self._on_home,
            style='DarkButton.TButton'
        )
        self.home_button.pack(side=tk.LEFT, expand=True, padx=5, pady=5)

    def _on_play(self):
        if self.playing:
            # pause
            if self.pause_callback:
                self.pause_callback()
                self.play_button.configure(text="▶ Play")
                self.playing = False
        else:
            # play
            if self.play_callback:
                self.play_callback()
                self.play_button.configure(text="⏸ Pause")
                self.playing = True
                

    def _on_home(self):
        if self.home_callback:
            self.home_callback()

    def _on_jog(self, axis):
        if self.jog_callback:
            self.jog_callback(axis)
        
    def _on_open_file(self):
        file = tk.filedialog.askopenfilename(
            parent=self.parent_frame,
            # mode='r',
            title="Select a file",
            initialdir="C:\\Users\\Simon\\Documents\\projecten\\Chocolate-Printer\\3d files\\",
            filetypes=(("Gcode Slice", "*.gcode"),),
            defaultextension="gcode",
            multiple=False
        )
        if file is None:
            # user canceled selection
            return 

        if self.open_file_callback is None:
            raise ValueError()
        
        self.open_file_callback(file)