from abc import ABC, abstractmethod


class GcodeHandler:
    def __init__(self, filename=None):
        self.filename = filename
        
        self.playing = False
        self.execution_line = -1 # the line that is estimated to be executing
        self.com_line = 0 # the last line that was sent to the COM
        self.aprox_buffer = 0 # an estimate of the current planner buffer size in the arduino
        # this is a theoretical maximum

        with open(filename, 'r') as f:
            self.gcode_lines = f.read().split('\n')

    def get_line(self, line: int):
        return self.gcode_lines[line]

    def get_size(self):
        return len(self.gcode_lines)
    
    def play(self):
        if not self.playing:
            self.playing = True
        
    def pause(self):
        if self.playing:
            self.playing = False


class EmptyGcodeHandler:
    def __init__(self, filename=None):
        self.playing = False
        self.aprox_buffer = 0
    
    def get_line(self, line: int):
        return ""

    def get_size(self):
        return 1
    
    def play(self):
        ...

    def pause(self):
        ...