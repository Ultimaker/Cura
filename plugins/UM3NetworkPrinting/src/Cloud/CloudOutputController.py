# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from cura.PrinterOutput.PrinterOutputController import PrinterOutputController


class CloudOutputController(PrinterOutputController):
    def __init__(self, output_device):
        super().__init__(output_device)
        
        # The cloud connection only supports fetching the printer and queue status and adding a job to the queue.
        # To let the UI know this we mark all features below as False.
        self.can_pause = False
        self.can_abort = False
        self.can_pre_heat_bed = False
        self.can_pre_heat_hotends = False
        self.can_send_raw_gcode = False
        self.can_control_manually = False
        self.can_update_firmware = False
