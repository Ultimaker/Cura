# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshReader import MeshReader
from UM.Application import Application
from UM.Scene.SceneNode import SceneNode
from UM.Mesh.MeshData import MeshData

from cura.LayerData import LayerData
from cura.LayerDataDecorator import LayerDataDecorator

import os
import numpy

class GCodeReader(MeshReader):
    def __init__(self):
        super().__init__()
        self._supported_extension = ".gcode"
        self._scene = Application.getInstance().getController().getScene()

    def read(self, file_name):
        extension = os.path.splitext(file_name)[1]
        if extension.lower() == self._supported_extension:
            layer_data = LayerData()
            with open (file_name,"rt") as f:
                layer = ""
                current_path_type = ""

                current_layer_nr = 0
                poly_list = []
                old_position = [0,0,0]
                current_z = 0
                for line in f:
                    if line.startswith(';TYPE:'):
                        current_path_type = line[6:].strip()
                        #layer_data.addPolygon(current_layer_nr,3 ,None ,5 )
                    elif line.startswith(';LAYER:'):
                        current_layer_nr = int(line[7:].strip())
                        layer_data.addLayer(int(line[7:].strip()))
                    elif line.startswith(';'):
                        pass # Ignore comments
                    else:
                        command_type = self.getCodeInt(line, 'G')
                        if command_type == 0 or command_type == 1: #Move command
                            x = self.getCodeFloat(line, 'X')
                            y = self.getCodeFloat(line, 'Y')
                            z = self.getCodeFloat(line, 'Z')
                            if z:
                                current_z = z
                            if x and y:
                                polygon_data = numpy.zeros((4,3)) #Square :)
                                polygon_data[0,:] = old_position
                                polygon_data[1,:] = old_position
                                polygon_data[2,:] = [x,current_z,y]
                                polygon_data[3,:] = [x,current_z,y]
                                old_position = [x,current_z,y]
                                if current_path_type == "SKIRT":
                                    layer_data.addPolygon(current_layer_nr,5 ,polygon_data ,5 )
                                elif current_path_type == "WALL-INNER":
                                    layer_data.addPolygon(current_layer_nr,3 ,polygon_data ,5 )
                                elif current_path_type == "WALL-OUTER":
                                    layer_data.addPolygon(current_layer_nr,1 ,polygon_data ,5 )
                                else:
                                    layer_data.addPolygon(current_layer_nr,2 ,polygon_data ,5 )
                            #e = self.getCodeFloat(line, 'E')
                            #print(x , " ", y , " ", z, " " , e)
                        pass
            layer_data.build()
            decorator = LayerDataDecorator()
            decorator.setLayerData(layer_data)
            new_node = SceneNode()
            new_node.setMeshData(MeshData())
            new_node.addDecorator(decorator)
            new_node.setParent(self._scene.getRoot())


    ##  Gets the value after the 'code' as int
    #   example: line = "G50" and code is "G" this function will return 50
    #   \param line string containing g-code.
    #   \param code string Letter to look for.
    #   \sa getCodeFloat
    #   \returns int
    def getCodeInt(self, line, code):
        n = line.find(code) + 1
        if n < 1:
            return None
        m = line.find(' ', n)
        try:
            if m < 0:
                return int(line[n:])
            return int(line[n:m])
        except:
            return None
    ##  Gets the value after the 'code' as float
    #   example: line = "G50" and code is "G" this function will return 50
    #   \param line string containing g-code.
    #   \param code string Letter to look for.
    #   \sa getCodeInt
    #   \returns float
    def getCodeFloat(self, line, code):
        n = line.find(code) + 1
        if n < 1:
            return None
        m = line.find(' ', n)
        try:
            if m < 0:
                return float(line[n:])
            return float(line[n:m])
        except:
            return None