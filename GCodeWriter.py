from UM.Mesh.MeshWriter import MeshWriter
from UM.Logger import Logger

class GCodeWriter(MeshWriter):
    def __init__(self):
        super().__init__()
        self._gcode = None

    def write(self, file_name, storage_device, mesh_data):
        if 'gcode' in file_name:
            gcode = getattr(mesh_data, 'gcode', False)
            if gcode:
                f = storage_device.openFile(file_name, 'wt')
                Logger.log('d', "Writing GCode to file %s", file_name)
                f.write(gcode)
                storage_device.closeFile(f)
                return True

        return False
