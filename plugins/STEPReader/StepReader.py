# Copyright (c) 2018 Ultimaker B.V.
# Uranium is released under the terms of the LGPLv3 or higher.

from UM.Mesh.MeshReader import MeshReader
from UM.Mesh.MeshBuilder import MeshBuilder
from UM.Logger import Logger
from UM.Scene.SceneNode import SceneNode
from UM.Job import Job


from os.path import abspath, join, dirname

import OCC.GProp
import OCC.BRepGProp


import OCC.BRep
import OCC.IFSelect
import OCC.Interface
import OCC.STEPControl
import OCC.TopoDS

import OCC.BRepBuilderAPI
import OCC.gp
import OCC.TopoDS

from OCC.gp import gp_Pnt

from .stl import StlExporter

from aocutils.analyze.bounds import BoundingBox


class STEPReader(MeshReader):
    def __init__(self):
        super(STEPReader, self).__init__()
        self._supported_extensions = [".step"]

    def read(self, file_name):

        mesh_builder = MeshBuilder()
        mesh_builder.setFileName(file_name)
        scene_node = SceneNode()

        self._shapes = list()

        stepcontrol_reader = OCC.STEPControl.STEPControl_Reader()
        status = stepcontrol_reader.ReadFile(file_name)

        if status == OCC.IFSelect.IFSelect_RetDone:
            stepcontrol_reader.PrintCheckLoad(False, OCC.IFSelect.IFSelect_ItemsByEntity)
            nb_roots = stepcontrol_reader.NbRootsForTransfer()

            if nb_roots == 0:
                return None

            stepcontrol_reader.PrintCheckTransfer(False, OCC.IFSelect.IFSelect_ItemsByEntity)

            self._number_of_shapes = stepcontrol_reader.NbShapes()

            for n in range(1, nb_roots + 1):
                ok = stepcontrol_reader.TransferRoot(n)
                if ok:
                    a_shape = stepcontrol_reader.Shape(n)
                    if a_shape.IsNull():
                        return None
                    else:
                        self._shapes.append(a_shape)

                        step_ = abspath(join(dirname(__file__), "./test_model.stl"))

                        self.shape_to_stl(a_shape, step_,  scale=1., ascii_mode_=True, factor_=4000., use_min_dim_=False)

            return scene_node

    def shape_to_stl(self, shape_, stl_file_, scale, ascii_mode_, factor_, use_min_dim_):

        exporter = StlExporter(filename=stl_file_, ascii_mode=ascii_mode_)
        shape_ = self.scale_uniform(shape_, gp_Pnt(0, 0, 0), scale, False)

        self.createMesh(shape_, factor=factor_, use_min_dim=use_min_dim_)

        exporter.set_shape(shape_)
        exporter.write_file()


    def initSceneNode(self, m_shape):
        print()


    def createMesh(self,shape, factor=4000., use_min_dim=False):
        bb = BoundingBox(shape)
        if use_min_dim:
            linear_deflection = bb.min_dimension / factor

            OCC.BRepMesh.BRepMesh_IncrementalMesh(shape, linear_deflection)
        else:
            linear_deflection = bb.max_dimension / factor

            OCC.BRepMesh.BRepMesh_IncrementalMesh(shape, linear_deflection)

    def scale_uniform(self, brep, pnt, factor, copy=False):

        trns = OCC.gp.gp_Trsf()
        trns.SetScale(pnt, factor)
        brep_trns = OCC.BRepBuilderAPI.BRepBuilderAPI_Transform(brep, trns, copy)
        brep_trns.Build()

        return brep_trns.Shape()