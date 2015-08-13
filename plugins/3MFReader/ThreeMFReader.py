# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Mesh.MeshReader import MeshReader
from UM.Mesh.MeshData import MeshData
from UM.Logger import Logger
from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector
from UM.Scene.SceneNode import SceneNode
from UM.Scene.GroupDecorator import GroupDecorator
from UM.Math.Quaternion import Quaternion


import os
import struct
import math
from os import listdir
import untangle
import zipfile


##    Base implementation for reading 3MF files. Has no support for textures. Only loads meshes!
class ThreeMFReader(MeshReader):
    def __init__(self):
        super(ThreeMFReader, self).__init__()
        self._supported_extension = ".3mf"
        
    def read(self, file_name):
        result = None
        extension = os.path.splitext(file_name)[1]
        if extension.lower() == self._supported_extension:
            result = SceneNode()
            # The base object of 3mf is a zipped archive.
            archive = zipfile.ZipFile(file_name, 'r')
            try:
                # The model is always stored in this place.
                root = untangle.parse(archive.read("3D/3dmodel.model").decode("utf-8"))
                for object in root.model.resources.object: # There can be multiple objects, try to load all of them.
                    mesh = MeshData()
                    node = SceneNode()
                    vertex_list = []
                    for vertex in object.mesh.vertices.vertex:
                        vertex_list.append([vertex['x'],vertex['y'],vertex['z']])
                    
                    mesh.reserveFaceCount(len(object.mesh.triangles.triangle))
                    
                    for triangle in object.mesh.triangles.triangle:
                        v1 = int(triangle["v1"])
                        v2 = int(triangle["v2"])
                        v3 = int(triangle["v3"])
                        mesh.addFace(vertex_list[v1][0],vertex_list[v1][1],vertex_list[v1][2],vertex_list[v2][0],vertex_list[v2][1],vertex_list[v2][2],vertex_list[v3][0],vertex_list[v3][1],vertex_list[v3][2])
                    #TODO: We currently do not check for normals and simply recalculate them. 
                    mesh.calculateNormals()
                    node.setMeshData(mesh)
                    node.setSelectable(True)
                    
                    # Magical python comprehension; looks for the matching transformation
                    transformation = next((x for x in root.model.build.item if x["objectid"] == object["id"]), None)
                    
                    if transformation["transform"]:
                        splitted_transformation = transformation["transform"].split() 
                        ## Transformation is saved as:
                        ## M00 M01 M02 0.0
                        ## M10 M11 M12 0.0
                        ## M20 M21 M22 0.0
                        ## M30 M31 M32 1.0
                        ## We switch the row & cols as that is how everyone else uses matrices!
                        temp_mat = Matrix()
                        # Rotation & Scale
                        temp_mat._data[0,0] = splitted_transformation[0]
                        temp_mat._data[1,0] = splitted_transformation[1]
                        temp_mat._data[2,0] = splitted_transformation[2]
                        temp_mat._data[0,1] = splitted_transformation[3]
                        temp_mat._data[1,1] = splitted_transformation[4]
                        temp_mat._data[2,1] = splitted_transformation[5]
                        temp_mat._data[0,2] = splitted_transformation[6]
                        temp_mat._data[1,2] = splitted_transformation[7]
                        temp_mat._data[2,2] = splitted_transformation[8]
                        
                        # Translation
                        temp_mat._data[0,3] = splitted_transformation[9]
                        temp_mat._data[1,3] = splitted_transformation[10]
                        temp_mat._data[2,3] = splitted_transformation[11]
                        
                        node.setPosition(Vector(temp_mat.at(0,3), temp_mat.at(1,3), temp_mat.at(2,3)))
                        
                        temp_quaternion = Quaternion()
                        temp_quaternion.setByMatrix(temp_mat)
                        node.setOrientation(temp_quaternion)
                        
                        # Magical scale extraction
                        S2 = temp_mat.getTransposed().multiply(temp_mat)
                        scale_x = math.sqrt(S2.at(0,0))
                        scale_y = math.sqrt(S2.at(1,1))
                        scale_z = math.sqrt(S2.at(2,2))
                        node.setScale(Vector(scale_x,scale_y,scale_z))
                        
                        # We use a different coordinate frame, so rotate.
                        rotation = Quaternion.fromAngleAxis(-0.5 * math.pi, Vector(1,0,0))
                        node.rotate(rotation)
                    result.addChild(node)
                
                # If there is more then one object, group them.
                try:
                    if len(root.model.resources.object) > 1:  
                        group_decorator = GroupDecorator()
                        result.addDecorator(group_decorator)
                except:
                    pass
            except Exception as e:
                Logger.log("e" ,"exception occured in 3mf reader: %s" , e)      
        return result  
