# Copyright (c) 2024 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.
from io import StringIO, BufferedIOBase
import json
from typing import cast, List, Optional, Dict, Tuple
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
from cura.PrinterOutput.FormatMaps import FormatMaps
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
        MimeTypeDatabase.addMimeType(
            MimeType(
                name="application/x-makerbot-sketch",
                comment="Makerbot Toolpath Package",
                suffixes=["makerbot"]
            )
        )
        MimeTypeDatabase.addMimeType(
            MimeType(
                name="application/x-makerbot-replicator_plus",
                comment="Makerbot Toolpath Package",
                suffixes=["makerbot"]
            )
        )

    _PNG_FORMAT = [
        {"prefix": "isometric_thumbnail", "width": 120, "height": 120},
        {"prefix": "isometric_thumbnail", "width": 320, "height": 320},
        {"prefix": "isometric_thumbnail", "width": 640, "height": 640},
        {"prefix": "thumbnail", "width": 90, "height": 90},
    ]

    _PNG_FORMAT_METHOD = [
        {"prefix": "thumbnail", "width": 140, "height": 106},
        {"prefix": "thumbnail", "width": 212, "height": 300},
        {"prefix": "thumbnail", "width": 960, "height": 1460},
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
        metadata, file_format  = self._getMeta(nodes)
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
        filename, filedata = "", ""
        # Writing the g-code failed. Then I can also not write the gzipped g-code.
        if not success:
            self.setInformation(gcode_writer.getInformation())
            return False
        match file_format:
            case "application/x-makerbot-sketch":
                filename, filedata = "print.gcode", gcode_text_io.getvalue()
            case "application/x-makerbot":
                filename, filedata = "print.jsontoolpath", du.gcode_2_miracle_jtp(gcode_text_io.getvalue())
            case "application/x-makerbot-replicator_plus":
                filename, filedata = "print.jsontoolpath", du.gcode_2_miracle_jtp(gcode_text_io.getvalue(), nb_extruders=1)
            case _:
                raise Exception("Unsupported Mime type")

        png_files = []
        for png_format in (self._PNG_FORMAT + self._PNG_FORMAT_METHOD):
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
                zip_stream.writestr(filename, filedata)
                for png_file in png_files:
                    file, data = png_file["file"], png_file["data"]
                    zip_stream.writestr(file, data)
                api = CuraApplication.getInstance().getCuraAPI()
                metadata_json = api.interface.settings.getSliceMetadata()

                # All the mapping stuff we have to do:
                product_to_id_map = FormatMaps.getProductIdMap()
                printer_name_map = FormatMaps.getInversePrinterNameMap()
                extruder_type_map = FormatMaps.getInverseExtruderTypeMap()
                material_map = FormatMaps.getInverseMaterialMap()
                for key, value in metadata_json.items():
                    if "all_settings" in value:
                        if "machine_name" in value["all_settings"]:
                            machine_name = value["all_settings"]["machine_name"]
                            if machine_name in product_to_id_map:
                                machine_name = product_to_id_map[machine_name][0]
                            value["all_settings"]["machine_name"] = printer_name_map.get(machine_name, machine_name)
                        if "machine_nozzle_id" in value["all_settings"]:
                            extruder_type = value["all_settings"]["machine_nozzle_id"]
                            value["all_settings"]["machine_nozzle_id"] = extruder_type_map.get(extruder_type, extruder_type)
                        if "material_type" in value["all_settings"]:
                            material_type = value["all_settings"]["material_type"]
                            value["all_settings"]["material_type"] = material_map.get(material_type, material_type)

                slice_metadata = json.dumps(metadata_json, separators=(", ", ": "), indent=4)
                zip_stream.writestr("slicemetadata.json", slice_metadata)
        except (IOError, OSError, BadZipFile) as ex:
            Logger.log("e", f"Could not write to (.makerbot) file because: '{ex}'.")
            self.setInformation(catalog.i18nc("@error", "MakerbotWriter could not save to the designated path."))
            return False

        return True

    def _getMeta(self, root_nodes: List[SceneNode]) -> Tuple[Dict[str, any], str]:
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
        # This is a bit of a "hack", the mime type should be passed through with the export writer but
        # since this is not the case we get the mime type from the global stack instead
        file_format = global_stack.definition.getMetaDataEntry("file_formats")
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
        if file_format == "application/x-makerbot-sketch":
            bounds = None
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

        meta["model_counts"] = [{"count": len(nodes), "name": "instance0"}]

        tool_types = [extruder.variant.getMetaDataEntry("reference_extruder_id") for extruder in extruders]
        meta["tool_type"] = tool_types[0]
        meta["tool_types"] = tool_types

        meta["version"] = MakerbotWriter._META_VERSION

        meta["preferences"] = dict()
        bounds = application.getBuildVolume().getBoundingBox()
        intent = CuraApplication.getInstance().getIntentManager().currentIntentCategory
        meta["preferences"]["instance0"] = {
            "machineBounds": [bounds.right, bounds.front, bounds.left, bounds.back] if bounds is not None else None,
            "printMode": intent
        }

        if file_format == "application/x-makerbot":
            accel_overrides = meta["accel_overrides"] = {}
            if intent in ['highspeed', 'highspeedsolid']:
                accel_overrides['do_input_shaping'] = True
                accel_overrides['do_corner_rounding'] = True
            bead_mode_overrides = accel_overrides["bead_mode"] = {}

            accel_enabled = global_stack.getProperty('acceleration_enabled', 'value')

            if accel_enabled:
                global_accel_setting = global_stack.getProperty('acceleration_print', 'value')
                accel_overrides["rate_mm_per_s_sq"] = {
                    "x": global_accel_setting,
                    "y": global_accel_setting
                }

                if global_stack.getProperty('acceleration_travel_enabled', 'value'):
                    travel_accel_setting = global_stack.getProperty('acceleration_travel', 'value')
                    bead_mode_overrides['Travel Move'] = {
                        "rate_mm_per_s_sq": {
                            "x": travel_accel_setting,
                            "y": travel_accel_setting
                        }
                    }

            jerk_enabled = global_stack.getProperty('jerk_enabled', 'value')
            if jerk_enabled:
                global_jerk_setting = global_stack.getProperty('jerk_print', 'value')
                accel_overrides["max_speed_change_mm_per_s"] = {
                    "x": global_jerk_setting,
                    "y": global_jerk_setting
                }

                if global_stack.getProperty('jerk_travel_enabled', 'value'):
                    travel_jerk_setting = global_stack.getProperty('jerk_travel', 'value')
                    if 'Travel Move' not in bead_mode_overrides:
                        bead_mode_overrides['Travel Move' ] = {}
                    bead_mode_overrides['Travel Move'].update({
                        "max_speed_change_mm_per_s": {
                            "x": travel_jerk_setting,
                            "y": travel_jerk_setting
                        }
                    })


            # Get bead mode settings per extruder
            available_bead_modes = {
                "infill": "FILL",
                "prime_tower": "PRIME_TOWER",
                "roofing": "TOP_SURFACE",
                "support_infill": "SUPPORT",
                "support_interface": "SUPPORT_INTERFACE",
                "wall_0": "WALL_OUTER",
                "wall_x": "WALL_INNER",
                "skirt_brim": "SKIRT"
            }
            for idx, extruder in enumerate(extruders):
                for bead_mode_setting, bead_mode_tag in available_bead_modes.items():
                    ext_specific_tag = "%s_%s" % (bead_mode_tag, idx)
                    if accel_enabled or jerk_enabled:
                        bead_mode_overrides[ext_specific_tag] = {}

                    if accel_enabled:
                        accel_val = extruder.getProperty('acceleration_%s' % bead_mode_setting, 'value')
                        bead_mode_overrides[ext_specific_tag]["rate_mm_per_s_sq"] = {
                            "x": accel_val,
                            "y": accel_val
                        }
                    if jerk_enabled:
                        jerk_val = extruder.getProperty('jerk_%s' % bead_mode_setting, 'value')
                        bead_mode_overrides[ext_specific_tag][ "max_speed_change_mm_per_s"] = {
                            "x": jerk_val,
                            "y": jerk_val
                        }

        meta["miracle_config"] = {"gaggles": {"instance0": {}}}

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

        return meta, file_format


def meterToMillimeter(value: float) -> float:
    """Converts a value in meters to millimeters."""
    return value * 1000.0
