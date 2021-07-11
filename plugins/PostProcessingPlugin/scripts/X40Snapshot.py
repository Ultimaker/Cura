from UM.Logger import Logger
from cura.Snapshot import Snapshot
from PyQt5.QtCore import QBuffer

from ..Script import Script


class X40Snapshot(Script):
    def __init__(self):
        super().__init__()

    def _createSnapshot(self, width, height):
        Logger.log("d", "Creating thumbnail image...")
        try:
            return Snapshot.snapshot(width, height)
        except Exception:
            Logger.logException("w", "Failed to create snapshot image")

    def _convertSnapshotToGcode(self, snapshot):
        Logger.log("d", "Encoding thumbnail image...")
        try:
            thumbnail_buffer = QBuffer()
            thumbnail_buffer.open(QBuffer.ReadWrite)
            thumbnail_image = snapshot
            thumbnail_image.save(thumbnail_buffer, "JPG")

            thumbnail_buffer.seek(0)
            gcode = []
            newline = "W221"
            byte = thumbnail_buffer.read(1)
            counter = 0
            while byte != b"":
                if counter == 0:
                    gcode.append(newline)
                    newline = "W220 "
                    counter = 40
                newline += byte.hex()
                counter -= 1

                byte = thumbnail_buffer.read(1)
            gcode.append(newline)
            gcode.append("W222")

            thumbnail_buffer.close()
            return gcode
        except Exception:
            Logger.logException("w", "Failed to encode snapshot image")

    def getSettingDataString(self):
        return """{
            "name": "Create Thumbnail for Weedo X40",
            "key": "X40Snapshot",
            "metadata": {},
            "version": 2,
            "settings":
            {}
        }"""

    def execute(self, data):
        width = 180
        height = 180

        snapshot = self._createSnapshot(width, height)
        if snapshot:
            snapshot_gcode = self._convertSnapshotToGcode(snapshot)

            for layer in data:
                layer_index = data.index(layer)
                lines = data[layer_index].split("\n")
                for line in lines:
                    if line.startswith(";Generated with Cura"):
                        line_index = lines.index(line)
                        insert_index = line_index + 1
                        lines[insert_index:insert_index] = snapshot_gcode
                        break

                final_lines = "\n".join(lines)
                data[layer_index] = final_lines

        return data
