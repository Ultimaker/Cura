# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.
import copy
import json
import numpy

from typing import Optional, Dict, List

from PyQt6.QtCore import QBuffer, QTimer
from PyQt6.QtGui import QImage, QImageWriter

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
        application.getMachineManager().extruderChanged.connect(self._updateIsAssignedToDisabledExtruder)
        self._painted_extruders: Optional[List[int]] = None

        self.paintTextureChanged = Signal()

        self._texture_change_timer: Optional[QTimer] = None

    def isSliceable(self) -> bool:
        return True

    def getPaintTexture(self) -> Optional[Texture]:
        return self._paint_texture

    def getPaintTextureChangedSignal(self) -> Signal:
        return self.paintTextureChanged

    def setPaintedExtrudersCountDirty(self) -> None:
        if self._texture_change_timer is None:
            # Lazy initialize the timer because constructor can be called from non-Qt thread
            self._texture_change_timer = QTimer()
            self._texture_change_timer.setInterval(500)  # Long interval to avoid triggering during painting
            self._texture_change_timer.setSingleShot(True)
            self._texture_change_timer.timeout.connect(self._onTextureChangeTimerFinished)

        self._texture_change_timer.start()

    def _onTextureChangeTimerFinished(self) -> None:
        self._painted_extruders = None

        if (self._paint_texture is None or self._paint_texture.getImage() is None or
                "extruder" not in self._texture_data_mapping):
            return

        image = self._paint_texture.getImage()
        image_bits = image.constBits()
        image_bits.setsize(image.sizeInBytes())
        image_array = numpy.frombuffer(image_bits, dtype=numpy.uint32)

        bit_range_start, bit_range_end = self._texture_data_mapping["extruder"]
        full_int32 = 0xffffffff
        bit_mask = (((full_int32 << (32 - 1 - (bit_range_end - bit_range_start))) & full_int32) >> (
                32 - 1 - bit_range_end))

        texel_counts = numpy.bincount((image_array & bit_mask) >> bit_range_start)
        self._painted_extruders = [extruder_nr for extruder_nr, count in enumerate(texel_counts) if count > 0]

        from cura.CuraApplication import CuraApplication
        CuraApplication.getInstance().globalContainerStackChanged.emit()

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

    def __deepcopy__(self, memo) -> "SliceableObjectDecorator":
        copied_decorator = SliceableObjectDecorator()
        copied_decorator.setPaintTexture(copy.deepcopy(self.getPaintTexture()))
        copied_decorator.setTextureDataMapping(copy.deepcopy(self.getTextureDataMapping()))
        return copied_decorator
