# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshReader import MeshReader
from UM.Mesh.MeshData import MeshData
from UM.Logger import Logger
from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector

import os
import struct
import math
from os import listdir
import untangle
import zipfile

class ThreeMFReader(MeshReader):
    def __init__(self):
        super(ThreeMFReader, self).__init__()
        self._supported_extension = ".3mf"
        
    def read(self, file_name):
        extension = os.path.splitext(file_name)[1]
        if extension.lower() == self._supported_extension:
            mesh = MeshData()
            archive = zipfile.ZipFile(file_name, 'r')
            #print(archive.read("3D/3dmodel.model"))
            try:
                object = untangle.parse(archive.read("3D/3dmodel.model").decode("utf-8"))
                for object in object.model.resources.object:
                    vertex_list = []
                    for vertex in object.mesh.vertices.vertex:
                        vertex_list.append([vertex['x'],vertex['y'],vertex['z']])
                    
                    mesh.reserveFaceCount(len(object.mesh.triangles.triangle))
                    for triangle in object.mesh.triangles.triangle:
                        v1 = int(triangle["v1"])
                        v2 = int(triangle["v2"])
                        v3 = int(triangle["v3"])
                        mesh.addFace(vertex_list[v1][0],vertex_list[v1][1],vertex_list[v1][2],vertex_list[v2][0],vertex_list[v2][1],vertex_list[v2][2],vertex_list[v3][0],vertex_list[v3][1],vertex_list[v3][2])
                    #if not mesh.hasNormals():
                    mesh.calculateNormals()
                    
                    return mesh
                    #object.mesh.vertices
                    #object.mesh.triangles
                    
            except Exception as e:
                print(e)
