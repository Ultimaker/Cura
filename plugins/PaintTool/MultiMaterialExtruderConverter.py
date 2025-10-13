# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import numpy
from weakref import WeakKeyDictionary
import functools

from typing import Optional

from UM.Scene.SceneNode import SceneNode
from cura.CuraApplication import CuraApplication
from cura.Machines.Models.ExtrudersModel import ExtrudersModel
from UM.Signal import Signal

from .PaintCommand import PaintCommand


class MultiMaterialExtruderConverter:
    """
    This class is a single object living in the background, which only job is to watch when extruders of objects
    are changed and to convert their multi-material painting textures accordingly.
    """

    MAX_EXTRUDER_COUNT = 16

    def __init__(self, extruders_model: ExtrudersModel) -> None:
        application = CuraApplication.getInstance()
        scene = application.getController().getScene()
        scene.getRoot().childrenChanged.connect(self._onChildrenChanged)

        self._extruders_model: extruders_model
        self._watched_nodes: WeakKeyDictionary[SceneNode, tuple[Optional[int], Optional[functools.partial]]] = WeakKeyDictionary()

        self.mainExtruderChanged = Signal()

    def _onChildrenChanged(self, node: SceneNode):
        if node not in self._watched_nodes and node.callDecoration("isSliceable"):
            self._watched_nodes[node] = (None, None)
            node.decoratorsChanged.connect(self._onDecoratorsChanged)
            self._onDecoratorsChanged(node)

        for child in node.getChildren():
            self._onChildrenChanged(child)

    def _onDecoratorsChanged(self, node: SceneNode) -> None:
        if node not in self._watched_nodes:
            return

        current_extruder, extruder_changed_callback = self._watched_nodes[node]
        if extruder_changed_callback is None:
            extruder_changed_signal = node.callDecoration("getActiveExtruderChangedSignal")
            if extruder_changed_signal is not None:
                extruder_changed_callback = functools.partial(self._onExtruderChanged, node)
                extruder_changed_signal.connect(extruder_changed_callback)
                self._watched_nodes[node] = current_extruder, extruder_changed_callback

        self._onExtruderChanged(node)

    def _onExtruderChanged(self, node: SceneNode) -> None:
        self._changeMainObjectExtruder(node)

    @staticmethod
    def getPaintedObjectExtruderNr(node: SceneNode) -> Optional[int]:
        extruder_stack = node.getPrintingExtruder()
        if extruder_stack is None:
            return None

        return extruder_stack.getValue("extruder_nr")

    def _changeMainObjectExtruder(self, node: SceneNode) -> None:
        if node not in self._watched_nodes:
            return

        old_extruder_nr, extruder_changed_callback = self._watched_nodes[node]
        new_extruder_nr = MultiMaterialExtruderConverter.getPaintedObjectExtruderNr(node)
        if new_extruder_nr == old_extruder_nr:
            return

        self._watched_nodes[node] = (new_extruder_nr, extruder_changed_callback)

        if old_extruder_nr is None or new_extruder_nr is None:
            return

        texture = node.callDecoration("getPaintTexture")
        if texture is None:
            return

        paint_data_mapping = node.callDecoration("getTextureDataMapping")
        if paint_data_mapping is None or "extruder" not in paint_data_mapping:
            return

        bits_range = paint_data_mapping["extruder"]

        image = texture.getImage()
        image_ptr = image.bits()
        image_ptr.setsize(image.sizeInBytes())
        image_array = numpy.frombuffer(image_ptr, dtype=numpy.uint32)

        bit_range_start, bit_range_end = bits_range
        bit_mask = numpy.uint32(PaintCommand.getBitRangeMask(bits_range))

        target_bits = (image_array & bit_mask) >> bit_range_start
        target_bits[target_bits == old_extruder_nr] = MultiMaterialExtruderConverter.MAX_EXTRUDER_COUNT
        target_bits[target_bits == new_extruder_nr] = old_extruder_nr
        target_bits[target_bits == MultiMaterialExtruderConverter.MAX_EXTRUDER_COUNT] = new_extruder_nr

        image_array &= ~bit_mask
        image_array |= ((target_bits << bit_range_start) & bit_mask)

        texture.updateImagePart(image.rect())

        node.callDecoration("setPaintedExtrudersCountDirty")

        self.mainExtruderChanged.emit(node)
