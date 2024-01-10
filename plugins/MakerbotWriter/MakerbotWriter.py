# Copyright (c) 2023 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from io import StringIO, BufferedIOBase
import json
from typing import cast, List, Optional, Dict
from zipfile import BadZipFile, ZipFile, ZIP_DEFLATED
import pyDulcificum as du

from PyQt6.QtCore import QBuffer

from UM.Logger import Logger
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Mesh.MeshWriter import MeshWriter
from UM.MimeTypeDatabase import MimeTypeDatabase, MimeType
from UM.PluginRegistry import PluginRegistry
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.i18n import i18nCatalog

from cura.CuraApplication import CuraApplication
from cura.Snapshot import Snapshot
from cura.Utils.Threading import call_on_qt_thread
from cura.CuraVersion import ConanInstalls

catalog = i18nCatalog("cura")


class MakerbotWriter(MeshWriter):
    """A file writer that writes '.makerbot' files."""

    def __init__(self) -> None:
        super().__init__(add_to_recent_files=False)
        Logger.info(f"Using PyDulcificum: {du.__version__}")
        MimeTypeDatabase.addMimeType(
            MimeType(
                name="application/x-makerbot",
                comment="Makerbot Toolpath Package",
                suffixes=["makerbot"]
            )
        )

    _PNG_FORMATS = [
        {"prefix": "isometric_thumbnail", "width": 120, "height": 120},
        {"prefix": "isometric_thumbnail", "width": 320, "height": 320},
        {"prefix": "isometric_thumbnail", "width": 640, "height": 640},
        {"prefix": "thumbnail", "width": 140, "height": 106},
        {"prefix": "thumbnail", "width": 212, "height": 300},
        {"prefix": "thumbnail", "width": 960, "height": 1460},
        {"prefix": "thumbnail", "width": 90, "height": 90},
    ]
    _META_VERSION = "3.0.0"

    # must be called from the main thread because of OpenGL
    @staticmethod
    @call_on_qt_thread
    def _createThumbnail(width: int, height: int) -> Optional[QBuffer]:
        if not CuraApplication.getInstance().isVisible:
            Logger.warning("Can't create snapshot when renderer not initialized.")
            return
        try:
            snapshot = Snapshot.isometricSnapshot(width, height)

            thumbnail_buffer = QBuffer()
            thumbnail_buffer.open(QBuffer.OpenModeFlag.WriteOnly)

            snapshot.save(thumbnail_buffer, "PNG")

            return thumbnail_buffer

        except:
            Logger.logException("w", "Failed to create snapshot image")

        return None

    def write(self, stream: BufferedIOBase, nodes: List[SceneNode], mode=MeshWriter.OutputMode.BinaryMode) -> bool:
        if mode != MeshWriter.OutputMode.BinaryMode:
            Logger.log("e", "MakerbotWriter does not support text mode.")
            self.setInformation(catalog.i18nc("@error:not supported", "MakerbotWriter does not support text mode."))
            return False

        # The GCodeWriter plugin is always available since it is in the "required" list of plugins.
        gcode_writer = PluginRegistry.getInstance().getPluginObject("GCodeWriter")

        if gcode_writer is None:
            Logger.log("e", "Could not find the GCodeWriter plugin, is it disabled?.")
            self.setInformation(
                catalog.i18nc("@error:load", "Could not load GCodeWriter plugin. Try to re-enable the plugin."))
            return False

        gcode_writer = cast(MeshWriter, gcode_writer)

        gcode_text_io = StringIO()
        success = gcode_writer.write(gcode_text_io, None)

        # Writing the g-code failed. Then I can also not write the gzipped g-code.
        if not success:
            self.setInformation(gcode_writer.getInformation())
            return False

        json_toolpaths = du.gcode_2_miracle_jtp(gcode_text_io.getvalue())
        metadata = self._getMeta(nodes)

        png_files = []
        for png_format in self._PNG_FORMATS:
            width, height, prefix = png_format["width"], png_format["height"], png_format["prefix"]
            thumbnail_buffer = self._createThumbnail(width, height)
            if thumbnail_buffer is None:
                Logger.warning(f"Could not create thumbnail of size {width}x{height}.")
                continue
            png_files.append({
                "file": f"{prefix}_{width}x{height}.png",
                "data": thumbnail_buffer.data(),
            })

        try:
            with ZipFile(stream, "w", compression=ZIP_DEFLATED) as zip_stream:
                zip_stream.writestr("meta.json", json.dumps(metadata, indent=4))
                zip_stream.writestr("print.jsontoolpath", json_toolpaths)
                for png_file in png_files:
                    file, data = png_file["file"], png_file["data"]
                    zip_stream.writestr(file, data)
        except (IOError, OSError, BadZipFile) as ex:
            Logger.log("e", f"Could not write to (.makerbot) file because: '{ex}'.")
            self.setInformation(catalog.i18nc("@error", "MakerbotWriter could not save to the designated path."))
            return False

        return True

    def _getMeta(self, root_nodes: List[SceneNode]) -> Dict[str, any]:
        application = CuraApplication.getInstance()
        machine_manager = application.getMachineManager()
        global_stack = machine_manager.activeMachine
        extruders = global_stack.extruderList

        nodes = []
        for root_node in root_nodes:
            for node in DepthFirstIterator(root_node):
                if not getattr(node, "_outside_buildarea", False):
                    if node.callDecoration(
                            "isSliceable") and node.getMeshData() and node.isVisible() and not node.callDecoration(
                            "isNonThumbnailVisibleMesh"):
                        nodes.append(node)

        meta = dict()

        meta["bot_type"] = global_stack.definition.getMetaDataEntry("reference_machine_id")

        bounds: Optional[AxisAlignedBox] = None
        for node in nodes:
            node_bounds = node.getBoundingBox()
            if node_bounds is None:
                continue
            if bounds is None:
                bounds = node_bounds
            else:
                bounds = bounds + node_bounds

        if bounds is not None:
            meta["bounding_box"] = {
                "x_min": bounds.left,
                "x_max": bounds.right,
                "y_min": bounds.back,
                "y_max": bounds.front,
                "z_min": bounds.bottom,
                "z_max": bounds.top,
            }

        material_bed_temperature = global_stack.getProperty("material_bed_temperature", "value")
        meta["platform_temperature"] = material_bed_temperature

        build_volume_temperature = global_stack.getProperty("build_volume_temperature", "value")
        meta["build_plane_temperature"] = build_volume_temperature

        print_information = application.getPrintInformation()

        meta["commanded_duration_s"] = int(print_information.currentPrintTime)
        meta["duration_s"] = int(print_information.currentPrintTime)

        material_lengths = list(map(meterToMillimeter, print_information.materialLengths))
        meta["extrusion_distance_mm"] = material_lengths[0]
        meta["extrusion_distances_mm"] = material_lengths

        meta["extrusion_mass_g"] = print_information.materialWeights[0]
        meta["extrusion_masses_g"] = print_information.materialWeights

        meta["uuid"] = print_information.slice_uuid

        materials = [extruder.material.getMetaData().get("reference_material_id") for extruder in extruders]

        meta["material"] = materials[0]
        meta["materials"] = materials

        materials_temps = [extruder.getProperty("default_material_print_temperature", "value") for extruder in
                           extruders]
        meta["extruder_temperature"] = materials_temps[0]
        meta["extruder_temperatures"] = materials_temps

        meta["model_counts"] = [{"count": 1, "name": node.getName()} for node in nodes]

        tool_types = [extruder.variant.getMetaDataEntry("reference_extruder_id") for extruder in extruders]
        meta["tool_type"] = tool_types[0]
        meta["tool_types"] = tool_types

        meta["version"] = MakerbotWriter._META_VERSION

        meta["preferences"] = dict()
        for node in nodes:
            bounds = node.getBoundingBox()
            meta["preferences"][str(node.getName())] = {
                "machineBounds": [bounds.right, bounds.back, bounds.left, bounds.front] if bounds is not None else None,
                "printMode": CuraApplication.getInstance().getIntentManager().currentIntentCategory,
            }

        meta["miracle_config"] = {"gaggles": {str(node.getName()): {} for node in nodes}}

        version_info = dict()
        cura_engine_info = ConanInstalls.get("curaengine", {"version": "unknown", "revision": "unknown"})
        version_info["curaengine_version"] = cura_engine_info["version"]
        version_info["curaengine_commit_hash"] = cura_engine_info["revision"]

        dulcificum_info = ConanInstalls.get("dulcificum", {"version": "unknown", "revision": "unknown"})
        version_info["dulcificum_version"] = dulcificum_info["version"]
        version_info["dulcificum_commit_hash"] = dulcificum_info["revision"]

        version_info["makerbot_writer_version"] = self.getVersion()
        version_info["pyDulcificum_version"] = du.__version__

        # Add engine plugin information to the metadata
        for name, package_info in ConanInstalls.items():
            if not name.startswith("curaengine_"):
                continue
            version_info[f"{name}_version"] = package_info["version"]
            version_info[f"{name}_commit_hash"] = package_info["revision"]

        # Add version info to the main metadata, but also to "miracle_config"
        # so that it shows up in analytics
        meta["miracle_config"].update(version_info)
        meta.update(version_info)

        # TODO add the following instructions
        # num_tool_changes
        # num_z_layers
        # num_z_transitions
        # platform_temperature
        # total_commands

        return meta


def meterToMillimeter(value: float) -> float:
    """Converts a value in meters to millimeters."""
    return value * 1000.0
