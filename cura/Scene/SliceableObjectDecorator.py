# Copyright (c) 2026 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import copy
import json
import numpy

from typing import Optional, Dict, List, Set

from PyQt6.QtCore import QBuffer, QTimer
from PyQt6.QtGui import QImage, QImageWriter

from UM.Decorators import deprecated
from UM.Scene.SceneNodeDecorator import SceneNodeDecorator
from UM.View.GL.OpenGL import OpenGL
from UM.View.GL.Texture import Texture
from UM.Signal import Signal


class SliceableObjectDecorator(SceneNodeDecorator):
    def __init__(self) -> None:
        super().__init__()
        self._paint_texture = None
        self._texture_data_mapping: Dict[str, tuple[int, int]] = {}

        self._is_assigned_to_disabled_extruder: bool = False

        from cura.CuraApplication import CuraApplication
        application = CuraApplication.getInstance()
        if application is not None:
            application.getMachineManager().extruderChanged.connect(self._updateIsAssignedToDisabledExtruder)
        self._painted_extruders: Optional[List[int]] = None
        self._painted_support_texels: bool = False

        self.paintTextureChanged = Signal()

        self._texture_change_timer: Optional[QTimer] = None
        self._texture_bitflags_maybe_dirty: int = 0b0

    def setNode(self, node: "SceneNode") -> None:
        if self._node is not None:
            signal = self._node.callDecoration("getActiveExtruderChangedSignal")
            if signal is not None:
                signal.disconnect(self._updateIsAssignedToDisabledExtruder)

        super().setNode(node)

        if self._node is not None:
            # Make sure all the decorators have been assigned to the node before connecting to the signal
            QTimer.singleShot(0, self._connectToExtruderChangedSignal)

    def isSliceable(self) -> bool:
        return True

    def getPaintTexture(self) -> Optional[Texture]:
        return self._paint_texture

    def getPaintTextureChangedSignal(self) -> Signal:
        return self.paintTextureChanged

    @deprecated("Replaced by 'setPaintedCountsDirty', since that now also counts the painted 'support' texels.", since="5.14.0")
    def setPaintedExtrudersCountDirty(self) -> None:
        if "extruder" in self._texture_data_mapping:
            self.setPaintedCountsDirty(self._texture_data_mapping["extruder"])

    def setPaintedCountsDirty(self, bitrange: tuple[int, int]) -> None:
        if self._texture_change_timer is None:
            # Lazy initialize the timer because constructor can be called from non-Qt thread
            self._texture_change_timer = QTimer()
            self._texture_change_timer.setInterval(500)  # Long interval to avoid triggering during painting
            self._texture_change_timer.setSingleShot(True)
            self._texture_change_timer.timeout.connect(self._onTextureChangeTimerFinished)

        for i in range(bitrange[0], bitrange[1] + 1):
           self._texture_bitflags_maybe_dirty |= 0b1 << i

        self._texture_change_timer.start()

    def _onTextureChangeTimerFinished(self) -> None:
        self._painted_extruders = None
        self._painted_support_texels = False

        if self._paint_texture is None or self._paint_texture.getImage() is None:
            return

        image = self._paint_texture.getImage()
        image_bits = image.constBits()
        image_bits.setsize(image.sizeInBytes())
        image_array = numpy.frombuffer(image_bits, dtype=numpy.uint32)

        def bitrange_dirty(name: str) -> bool:
            named_range = self._texture_data_mapping.get(name, None)
            if named_range is None:
                return False
            named_bitflags = 0b0
            for i in range(named_range[0], named_range[1] + 1):
                named_bitflags |= 0b1 << i
            return (named_bitflags & self._texture_bitflags_maybe_dirty) != 0b0

        if "extruder" in self._texture_data_mapping and bitrange_dirty("extruder"):
            self._updatePaintedExtruders(image_array)
        if "support" in self._texture_data_mapping and bitrange_dirty("support"):
            self._updatePaintedSupport(image_array)

        self._texture_bitflags_maybe_dirty = 0b0

        from cura.CuraApplication import CuraApplication
        CuraApplication.getInstance().globalContainerStackChanged.emit()

    def _updatePaintedExtruders(self, image_array) -> None:
        bit_range_start, bit_range_end = self._texture_data_mapping["extruder"]
        full_int32 = 0xffffffff
        bit_mask = (((full_int32 << (32 - 1 - (bit_range_end - bit_range_start))) & full_int32) >> (
                32 - 1 - bit_range_end))

        texel_counts = numpy.bincount((image_array & bit_mask) >> bit_range_start)
        self._painted_extruders = [extruder_nr for extruder_nr, count in enumerate(texel_counts) if count > 0]

    def _updatePaintedSupport(self, image_array) -> None:
        bit_range_start, bit_range_end = self._texture_data_mapping["support"]
        # We only need the 'allow' bit; 'dissallow' or 'no value' don't change wether or not support will be generated.
        bit_mask = 0b1 << bit_range_start
        self._painted_support_texels = numpy.any(image_array & bit_mask)

    def setPaintTexture(self, texture: Texture) -> None:
        self._paint_texture = texture
        self.paintTextureChanged.emit()

    def getTextureDataMapping(self) -> Dict[str, tuple[int, int]]:
        return self._texture_data_mapping

    def setTextureDataMapping(self, mapping: Dict[str, tuple[int, int]]) -> None:
        self._texture_data_mapping = mapping

    def prepareTexture(self, width: int, height: int) -> None:
        if self._paint_texture is None:
            self._paint_texture = OpenGL.getInstance().createTexture(width, height)
            image = QImage(width, height, QImage.Format.Format_RGB32)
            image.fill(0)
            self._paint_texture.setImage(image)
            self.paintTextureChanged.emit()

    def packTexture(self) -> Optional[bytearray]:
        if self._paint_texture is None:
            return None

        texture_image = self._paint_texture.getImage()
        if texture_image is None:
            return None

        texture_buffer = QBuffer()
        texture_buffer.open(QBuffer.OpenModeFlag.ReadWrite)
        image_writer = QImageWriter(texture_buffer, b"png")
        image_writer.setText("Description", json.dumps(self._texture_data_mapping))
        image_writer.write(texture_image)

        return texture_buffer.data()

    def isAssignedToDisabledExtruder(self) -> bool:
        return self._is_assigned_to_disabled_extruder

    def _updateIsAssignedToDisabledExtruder(self) -> None:
        new_is_assigned_to_disabled_extruder = False
        try:
            extruder_stack = self.getNode().getPrintingExtruder()
            new_is_assigned_to_disabled_extruder = ((extruder_stack is None or not extruder_stack.isEnabled) and
                                              not self.getNode().callDecoration("isGroup"))
        except IndexError:  # Happens when the extruder list is too short. We're not done building the printer in memory yet.
            pass
        except TypeError:  # Happens when extruder_position is None. This object has no extruder decoration.
            pass

        self._is_assigned_to_disabled_extruder = new_is_assigned_to_disabled_extruder

    def getPaintedExtruders(self) -> Optional[List[int]]:
        return self._painted_extruders

    def getPaintedSupportTexels(self) -> bool:
        return self._painted_support_texels

    def _connectToExtruderChangedSignal(self):
        if self._node is not None:
            signal = self._node.callDecoration("getActiveExtruderChangedSignal")
            if signal is not None:
                signal.connect(self._updateIsAssignedToDisabledExtruder)

    def __deepcopy__(self, memo) -> "SliceableObjectDecorator":
        copied_decorator = SliceableObjectDecorator()
        copied_decorator.setPaintTexture(copy.deepcopy(self.getPaintTexture()))
        copied_decorator.setTextureDataMapping(copy.deepcopy(self.getTextureDataMapping()))
        return copied_decorator
