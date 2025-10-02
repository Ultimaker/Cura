from tkinter import ttk


class DarkTheme:
    """Manages the application's dark theme styles for Tkinter widgets."""
    def __init__(self, root):
        self.style = ttk.Style()
        self._configure_styles()
        root.tk_setPalette(background='#2c313a', foreground='#ffffff')

    def _configure_styles(self):
        """Applies the dark theme configurations to ttk widgets."""
        FONT_SIZE = 16
        self.style.theme_use('clam')
        self.style.configure('DarkFrame.TFrame', background='#2c313a', relief='flat')
        self.style.configure('DarkLabel.TLabel', background='#2c313a', foreground='#ffffff', font=('Inter', 16))
        self.style.configure('Heading.TLabel', background='#2c313a', foreground='#ffffff', font=('Inter', FONT_SIZE, 'bold'))
        self.style.configure('DarkText.TText', background='#1e2127', foreground='#ffffff', insertbackground='#ffffff', font=('monospace', 10))
        self.style.configure('DarkButton.TButton', background='#4a90e2', foreground='#ffffff',
                             font=('Inter', FONT_SIZE, 'bold'), borderwidth=0, focusthickness=3, focuscolor='none')
        self.style.map('DarkButton.TButton',
                        background=[('active', '#357abd')],
                        foreground=[('active', '#ffffff')])
        
        # ----- Scale -----
        self.style.layout('DarkScale.Horizontal.TScale',
                          [('Horizontal.Scale.trough',
                            {'children': [('Horizontal.Scale.slider',
                                           {'side': 'left', 'sticky': 'ns'})],
                             'sticky': 'nswe'})])
        
        self.style.configure('DarkScale.Horizontal.TScale',
                              background='#2c313a', troughcolor='#1e2127',
                              slidercolor='#4a90e2',
                              foreground='#ffffff', highlightbackground='#2c313a',
                              borderwidth=0)
        self.style.map('DarkScale.Horizontal.TScale',
                        slidercolor=[('active', '#357abd')])

        # ----- Progressbar -----
        self.style.layout('Dark.Horizontal.TProgressbar',
                          [('Horizontal.Progressbar.trough',
                            {'children': [('Horizontal.Progressbar.pbar',
                                           {'side': 'left', 'sticky': 'ns'})],
                             'sticky': 'nswe'})])

        self.style.configure('Dark.Horizontal.TProgressbar',
                              troughcolor='#1e2127',
                              background='#4a90e2',
                              bordercolor='#2c313a',
                              lightcolor='#4a90e2',
                              darkcolor='#4a90e2',
                              thickness=20)

        self.style.map('Dark.Horizontal.TProgressbar',
                        background=[('active', '#357abd')])
