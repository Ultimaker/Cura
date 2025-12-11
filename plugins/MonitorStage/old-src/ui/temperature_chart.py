import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from tkinter import ttk
from collections import deque

class TemperatureChart:
    """Manages the Matplotlib temperature chart for multiple tools."""
    COLORS = {"T0": "#e74c3c", "T1": "#3498db"}  # T0=red, T1=blue

    def __init__(self, parent_frame: ttk.Frame, max_chart_points: int = 60):
        self.max_chart_points = max_chart_points
        self.temperature_data = {tool: deque(maxlen=max_chart_points) for tool in TemperatureChart.COLORS}
        self.time_data = deque(maxlen=max_chart_points)
        self.target_temperatures = {tool: None for tool in TemperatureChart.COLORS}
        self.lines = {}
        self.target_lines = {}

        # Figure setup
        self.fig, self.ax = plt.subplots(figsize=(5, 3), dpi=100)
        self._configure_chart_style()

        # Create one line per tool
        for tool, color in TemperatureChart.COLORS.items():
            line, = self.ax.plot([], [], color=color, linewidth=2, label=f"{tool} Current")
            self.lines[tool] = line

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

        # Labels per tool
        self.temp_labels = {}
        for tool in TemperatureChart.COLORS:
            label = ttk.Label(parent_frame, text=f"{tool}: --.--°C", style='DarkLabel.TLabel')
            label.pack(anchor="s", pady=(5, 0))
            self.temp_labels[tool] = label

        self.ax.legend(loc='upper left', facecolor='#2c313a', edgecolor='#cccccc', labelcolor='white', framealpha=0.8)

    def _configure_chart_style(self):
        self.ax.set_facecolor('#1e2127')
        self.fig.patch.set_facecolor('#1e2127')
        self.ax.tick_params(axis='x', colors='#cccccc')
        self.ax.tick_params(axis='y', colors='#cccccc')
        self.ax.spines['bottom'].set_color('#cccccc')
        self.ax.spines['left'].set_color('#cccccc')
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)

        self.ax.set_xlabel("Time", color='#cccccc')
        self.ax.set_ylabel("Temperature (°C)", color='#cccccc')
        self.ax.set_title("Temperature Readings", color='#ffffff')
        self.ax.set_ylim(0, 50)

    def add_temperatures(self, temps: dict):
        """
        Add temperatures for all tools at the current time step.
        temps: dict mapping tool -> temperature
        """
        now = datetime.now()
        self.time_data.append(now)

        for tool in self.temperature_data:
            if tool in temps:
                self.temperature_data[tool].append(temps[tool])
            else:
                # Repeat last value if no new reading
                last = self.temperature_data[tool][-1] if self.temperature_data[tool] else 0.0
                self.temperature_data[tool].append(last)

            # Update label if tool was provided
            if tool in temps:
                self.temp_labels[tool].config(text=f"{tool}: {temps[tool]:.1f}°C")

        # Update all lines
        for tool, line in self.lines.items():
            line.set_data(list(self.time_data), list(self.temperature_data[tool]))

        # Update x-axis
        if self.time_data:
            self.ax.set_xlim(self.time_data[0], self.time_data[-1])
            num_ticks = 5
            tick_indices = [int(i*(len(self.time_data)-1)/(num_ticks-1)) for i in range(num_ticks)] if len(self.time_data) > 1 else [0]
            self.ax.set_xticks([self.time_data[i] for i in tick_indices])
            self.ax.set_xticklabels([self.time_data[i].strftime("%H:%M:%S") for i in tick_indices], rotation=45, ha='right')
            self.ax.figure.autofmt_xdate()

        self.canvas.draw_idle()



    def set_target_temperature(self, tool: str, target_temp: float):
        """Set target temperature for a specific tool."""
        self.target_temperatures[tool] = target_temp

        if tool in self.target_lines and self.target_lines[tool]:
            self.target_lines[tool].remove()

        self.target_lines[tool] = self.ax.axhline(
            y=target_temp,
            color=TemperatureChart.COLORS[tool],
            linestyle='--',
            linewidth=1.5,
            label=f"{tool} Target: {target_temp:.1f}°C"
        )
 
        self.ax.legend(loc='upper left', facecolor='#2c313a', edgecolor='#cccccc', labelcolor='white', framealpha=0.8)
        self.canvas.draw_idle()

    def close(self):
        plt.close(self.fig)
