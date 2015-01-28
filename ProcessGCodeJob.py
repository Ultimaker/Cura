from UM.Job import Job
from UM.Application import Application

import os

class ProcessGCodeJob(Job):
    def __init__(self, message):
        super().__init__()

        self._message = message

    def run(self):
        with open(self._message.filename) as f:
            data = f.read(None)
            Application.getInstance().getController().getScene().gcode = data

        os.remove(self._message.filename)
