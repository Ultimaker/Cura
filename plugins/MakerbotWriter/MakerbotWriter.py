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
    _PRINT_NAME_MAP = {
        "Makerbot Method": "fire_e",
        "Makerbot Method X": "lava_f",
        "Makerbot Method XL": "magma_10",
    }
    _EXTRUDER_NAME_MAP = {
        "1XA": "mk14_hot",
        "2XA": "mk14_hot_s",
        "1C": "mk14_c",
        "1A": "mk14",
        "2A": "mk14_s",
    }
    _MATERIAL_MAP = {"2780b345-577b-4a24-a2c5-12e6aad3e690": "abs",
                     "88c8919c-6a09-471a-b7b6-e801263d862d": "abs-wss1",
                     "416eead4-0d8e-4f0b-8bfc-a91a519befa5": "asa",
                     "85bbae0e-938d-46fb-989f-c9b3689dc4f0": "nylon-cf",
                     "283d439a-3490-4481-920c-c51d8cdecf9c": "nylon",
                     "62414577-94d1-490d-b1e4-7ef3ec40db02": "pc",
                     "69386c85-5b6c-421a-bec5-aeb1fb33f060": "petg",
                     "0ff92885-617b-4144-a03c-9989872454bc": "pla",
                     "a4255da2-cb2a-4042-be49-4a83957a2f9a": "pva",
                     "a140ef8f-4f26-4e73-abe0-cfc29d6d1024": "wss1",
                     "77873465-83a9-4283-bc44-4e542b8eb3eb": "sr30",
                     "96fca5d9-0371-4516-9e96-8e8182677f3c": "im-pla",
                     "9f52c514-bb53-46a6-8c0c-d507cd6ee742": "abs",
                     "0f9a2a91-f9d6-4b6b-bd9b-a120a29391be": "abs",
                     "d3e972f2-68c0-4d2f-8cfd-91028dfc3381": "abs",
                     "495a0ce5-9daf-4a16-b7b2-06856d82394d": "abs-cf10",
                     "cb76bd6e-91fd-480c-a191-12301712ec77": "abs-wss1",
                     "a017777e-3f37-4d89-a96c-dc71219aac77": "abs-wss1",
                     "4d96000d-66de-4d54-a580-91827dcfd28f": "abs-wss1",
                     "0ecb0e1a-6a66-49fb-b9ea-61a8924e0cf5": "asa",
                     "efebc2ea-2381-4937-926f-e824524524a5": "asa",
                     "b0199512-5714-4951-af85-be19693430f8": "asa",
                     "b9f55a0a-a2b6-4b8d-8d48-07802c575bd1": "pla",
                     "c439d884-9cdc-4296-a12c-1bacae01003f": "pla",
                     "16a723e3-44df-49f4-82ec-2a1173c1e7d9": "pla",
                     "74d0f5c2-fdfd-4c56-baf1-ff5fa92d177e": "pla",
                     "64dcb783-470d-4400-91b1-7001652f20da": "pla",
                     "3a1b479b-899c-46eb-a2ea-67050d1a4937": "pla",
                     "4708ac49-5dde-4cc2-8c0a-87425a92c2b3": "pla",
                     "4b560eda-1719-407f-b085-1c2c1fc8ffc1": "pla",
                     "e10a287d-0067-4a58-9083-b7054f479991": "im-pla",
                     "01a6b5b0-fab1-420c-a5d9-31713cbeb404": "im-pla",
                     "f65df4ad-a027-4a48-a51d-975cc8b87041": "im-pla",
                     "f48739f8-6d96-4a3d-9a2e-8505a47e2e35": "im-pla",
                     "5c7d7672-e885-4452-9a78-8ba90ec79937": "petg",
                     "91e05a6e-2f5b-4964-b973-d83b5afe6db4": "petg",
                     "bdc7dd03-bf38-48ee-aeca-c3e11cee799e": "petg",
                     "54f66c89-998d-4070-aa60-1cb0fd887518": "nylon",
                     "002c84b3-84ac-4b5a-b57d-fe1f555a6351": "pva",
                     "e4da5fcb-f62d-48a2-aaef-0b645aa6973b": "wss1",
                     "77f06146-6569-437d-8380-9edb0d635a32": "sr30"}

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

        meta["bot_type"] = MakerbotWriter._PRINT_NAME_MAP.get((name := global_stack.definition.name), name)

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

        materials = []
        for extruder in extruders:
            guid = extruder.material.getMetaData().get("GUID")
            material_name = extruder.material.getMetaData().get("material")
            material = self._MATERIAL_MAP.get(guid, material_name)
            materials.append(material)

        meta["material"] = materials[0]
        meta["materials"] = materials

        materials_temps = [extruder.getProperty("default_material_print_temperature", "value") for extruder in
                           extruders]
        meta["extruder_temperature"] = materials_temps[0]
        meta["extruder_temperatures"] = materials_temps

        meta["model_counts"] = [{"count": 1, "name": node.getName()} for node in nodes]

        tool_types = [MakerbotWriter._EXTRUDER_NAME_MAP.get((name := extruder.variant.getName()), name) for extruder in
                      extruders]
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

        cura_engine_info = ConanInstalls.get("curaengine", {"version": "unknown", "revision": "unknown"})
        meta["curaengine_version"] = cura_engine_info["version"]
        meta["curaengine_commit_hash"] = cura_engine_info["revision"]

        dulcificum_info = ConanInstalls.get("dulcificum", {"version": "unknown", "revision": "unknown"})
        meta["dulcificum_version"] = dulcificum_info["version"]
        meta["dulcificum_commit_hash"] = dulcificum_info["revision"]

        meta["makerbot_writer_version"] = self.getVersion()
        meta["pyDulcificum_version"] = du.__version__

        # Add engine plugin information to the metadata
        for name, package_info in ConanInstalls.items():
            if not name.startswith("curaengine_"):
                continue
            meta[f"{name}_version"] = package_info["version"]
            meta[f"{name}_commit_hash"] = package_info["revision"]

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
