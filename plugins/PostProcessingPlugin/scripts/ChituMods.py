# Cura PostProcessingPlugin
# Author:   Spanni
# Date:     November 15, 2019

# Description:  This plugin generates and inserts code including a image of the
#               sliced part.


from ..Script import Script
from cura.Snapshot import Snapshot
from UM.Logger import Logger
import re

def getValue(line, key, default=None):
        if key not in line:
            return default
        else:
            subPart = line[line.find(key) + len(key):]
            m = re.search('^-?[0-9]+\\.?[0-9]*', subPart)
            #if m is None:
            #    pass
            #return default
        try:
            return float(m.group(0))
        except:
            return default

class ChituMods(Script):
    def __init__(self):
        super().__init__()
        self._snapshot = None

    def getSettingDataString(self):
        return """{
            "name": "Insert mods for chitu boards",
            "key": "ChituMods",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "insert_preview_image":
                {
                    "label": "Insert a preview image for printers with chitu boards?",
                    "description": "Selecting this a image will be generated and included into the gcode so the touch displays can show it",
                    "type": "bool",
                    "default_value": false
                },
                "insert_time_info":
                
                {
                    "label": "Insert the needed time and the elapsed time?",
                    "description": "Selecting this the calculated time and the elapsed time will be included in chitu style",
                    "type": "bool",
                    "default_value": false
                }
            }
        }"""

    def execute(self, in_data):
        # we get a list, each list item is the command set for a complete layer
        out_data = in_data
        if self.getSettingValueByKey("insert_preview_image"):
            img_data=[]
            img_data.append('\n'.join(self.generate_image_code(self._createSnapshot()))) # create one long string and add it as item to a list
            img_data[0] += ('\n') # add an additional newline, looks better
            img_data.extend(in_data)
            out_data=img_data      

        if self.getSettingValueByKey("insert_time_info"):
            Logger.log("d", "Modifying time info for chitu ...")
            time_data=self.insert_time_infos(out_data)
            out_data=time_data
        return out_data
    
    

    def insert_time_infos(self, gcode_data):
        return_data=[]
        Logger.log("d", "Modifying time info for chitu ...")
        for gcode in gcode_data:
            lines = gcode.split('\n')
            modified = False
            for index, line in enumerate(lines):
                if line.startswith(';TIME:'):
                    lines[index] = 'M2100 T%d' % int(getValue(line, ';TIME:', 0))
                    modified=True
                elif line.startswith(';TIME_ELAPSED:'):
                    lines[index] = 'M2101 T%d' % int(getValue(line, ';TIME_ELAPSED:', 0)) 
                    modified=True
            if modified:
                return_data.append('\n'.join(lines))
            else:
                return_data.append(gcode)
        return return_data        
        

    def _createSnapshot(self, *args):
        Logger.log("d", "Creating tronxy thumbnail image ...")
        try:
            snapshot = Snapshot.snapshot(width = 300, height = 300)
        except Exception:
            Logger.logException("w", "Failed to create snapshot image")
            snapshot = None  
        return snapshot
   

    def generate_image_code(self, image,startX=0, startY=0, endX=300, endY=300):
        MAX_PIC_WIDTH_HEIGHT = 320
        width = image.width()
        height = image.height()
        if endX > width:
            endX = width
        if endY > height:
            endY = height
        scale = 1.0
        max_edge = endY - startY
        if max_edge < endX - startX:
            max_edge = endX - startX
        if max_edge > MAX_PIC_WIDTH_HEIGHT:
            scale = MAX_PIC_WIDTH_HEIGHT / max_edge
        if scale != 1.0:
            width = int(width * scale)
            height = int(height * scale)
            startX = int(startX * scale)
            startY = int(startY * scale)
            endX = int(endX * scale)
            endY = int(endY * scale)
            image = image.scaled(width, height)
        res_list = []
        print('StartY:', startY, ' endY:', endY)
        for i in range(startY, endY):
            for j in range(startX, endX):
                res_list.append(image.pixel(j, i))

        index_pixel = 0
        pixel_num = 0
        pixel_data = ''
        pixel_list = []
        pixel_list.append('M4010 X%d Y%d' % (endX - startX, endY - startY))
        last_color = -1
        mask = 32
        unmask = ~mask
        same_pixel = 1
        color = 0
        for j in res_list:
            a = j >> 24 & 255
            if not a:
                r = g = b = 255
            else:
                r = j >> 16 & 255
                g = j >> 8 & 255
                b = j & 255
            color = (r >> 3 << 11 | g >> 2 << 5 | b >> 3) & unmask
            if last_color == -1:
                last_color = color
            elif last_color == color and same_pixel < 4095:
                same_pixel += 1
            elif same_pixel >= 2:
                pixel_data += '%04x' % (last_color | mask)
                pixel_data += '%04x' % (12288 | same_pixel)
                pixel_num += same_pixel
                last_color = color
                same_pixel = 1
            else:
                pixel_data += '%04x' % last_color
                last_color = color
                pixel_num += 1
            if len(pixel_data) >= 180:
                pixel_list.append("M4010 I%d T%d '%s'" % (index_pixel, pixel_num, pixel_data))
                pixel_data = ''
                index_pixel += pixel_num
                pixel_num = 0

        if same_pixel >= 2:
            pixel_data += '%04x' % (last_color | mask)
            pixel_data += '%04x' % (12288 | same_pixel)
            pixel_num += same_pixel
            last_color = color
            same_pixel = 1
        else:
            pixel_data += '%04x' % last_color
            last_color = color
            pixel_num += 1
        pixel_list.append("M4010 I%d T%d '%s'" % (index_pixel, pixel_num, pixel_data))
        return pixel_list