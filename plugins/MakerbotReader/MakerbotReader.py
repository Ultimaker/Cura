# Copyright (c) 2024 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING, List, Optional, cast

from UM.Mesh.MeshReader import MeshReader
from UM.MimeTypeDatabase import MimeType, MimeTypeDatabase
from UM.PluginRegistry import PluginRegistry
from UM.Application import Application
from UM.Logger import Logger
from UM.i18n import i18nCatalog
from UM.Message import Message
from Charon.VirtualFile import VirtualFile # For Zip file handling
from UM.Scene.SceneNode import SceneNode # Import SceneNode

if TYPE_CHECKING:
    from cura.Scene.CuraSceneNode import CuraSceneNode

catalog = i18nCatalog("cura")

class MakerbotReader(MeshReader):
    def __init__(self) -> None:
        super().__init__()
        MimeTypeDatabase.addMimeType(
            MimeType(
                name = "application/x-makerbot",
                comment = "Makerbot Toolpath Package",
                suffixes = ["makerbot"]
            )
        )
        self._supported_extensions = [".makerbot"]
        Logger.info("MakerbotReader plugin initialized.")

    def _read(self, file_name: str) -> Optional[List["CuraSceneNode"]]:
        Logger.info(f"Attempting to read Makerbot file: {file_name}")
        nodes: List[SceneNode] = []
        try:
            archive = VirtualFile()
            if not archive.open(file_name, "r"):
                Logger.error(f"Could not open Makerbot archive: {file_name}")
                Message(catalog.i18nc("@error:file", "Could not open Makerbot archive: {0}", file_name),
                        title = catalog.i18nc("@error:title", "File Error")).show()
                return None

            # Check for gcode file first
            gcode_file_path_in_archive = "print.gcode" # Common name in MakerBot files
            if archive.exists(gcode_file_path_in_archive):
                gcode_data_map = archive.getData(gcode_file_path_in_archive)
                gcode_bytes = gcode_data_map.get(gcode_file_path_in_archive)

                if not gcode_bytes:
                    Logger.error(f"Could not read '{gcode_file_path_in_archive}' from Makerbot archive: {file_name}")
                    Message(catalog.i18nc("@error:file", "Could not read '{0}' from Makerbot archive: {1}", gcode_file_path_in_archive, file_name),
                            title = catalog.i18nc("@error:title", "File Error")).show()
                    archive.close()
                    return None

                gcode_stream = gcode_bytes.decode("utf-8", errors = "replace")

                gcode_reader = PluginRegistry.getInstance().getPluginObject("GCodeReader")
                if not gcode_reader:
                    Logger.error("GCodeReader plugin not found.")
                    Message(catalog.i18nc("@error:plugin", "GCodeReader plugin not found. Cannot process .makerbot file."),
                            title = catalog.i18nc("@error:title", "Plugin Error")).show()
                    archive.close()
                    return None

                # The GCodeReader's read method expects a file name, but we have a stream.
                # We need to ensure preReadFromStream and readFromStream are correctly used.
                # GCodeReader's typical usage might involve filenames for context, so we pass the original .makerbot filename.
                cast(MeshReader, gcode_reader).preReadFromStream(gcode_stream)
                gcode_nodes = cast(MeshReader, gcode_reader).readFromStream(gcode_stream, file_name) # Pass original filename for context
                if gcode_nodes:
                    nodes.extend(gcode_nodes)
                else:
                    Logger.warning(f"GCodeReader did not return any nodes for {file_name}")

            # Check for jsontoolpath if gcode wasn't found or didn't produce nodes
            elif archive.exists("print.jsontoolpath"):
                Logger.warning("Makerbot file contains a 'print.jsontoolpath' file. This format is not yet supported by the MakerbotReader.")
                Message(catalog.i18nc("@warning:unsupported_format",
                                       "The Makerbot file '{0}' contains a '.jsontoolpath' file, which is not currently supported. Only '.gcode' inside .makerbot is supported.",
                                       file_name),
                        title = catalog.i18nc("@warning:title", "Unsupported Format"),
                        message_type = Message.MessageType.WARNING).show()
                archive.close()
                return None # Explicitly return None as jsontoolpath is not supported

            else:
                Logger.error(f"No 'print.gcode' or 'print.jsontoolpath' found in Makerbot archive: {file_name}")
                Message(catalog.i18nc("@error:file", "No 'print.gcode' or 'print.jsontoolpath' found in Makerbot archive: {0}", file_name),
                        title = catalog.i18nc("@error:title", "File Error")).show()
                archive.close()
                return None

            archive.close()

            if not nodes: # If after all checks, nodes list is empty
                Logger.info(f"No processable content found or GCodeReader returned no nodes for {file_name}.")
                # Optionally, show a message if no content led to nodes
                # Message(catalog.i18nc("@info:file", "No displayable content found in {0}.", file_name),
                #         title=catalog.i18nc("@info:title", "Empty File")).show()
                return None


        except Exception as e:
            Logger.error(f"Failed to read Makerbot file {file_name}: {e}")
            Message(catalog.i18nc("@error:file", "An unexpected error occurred while reading {0}: {1}", file_name, str(e)),
                    title = catalog.i18nc("@error:title", "File Error")).show()
            return None

        # Ensure CuraSceneNode type for all nodes if needed, though GCodeReader should provide them.
        # This step might be redundant if GCodeReader already returns List[CuraSceneNode]
        # but good for ensuring type safety if GCodeReader's return type is List[SceneNode].
        cura_nodes: List["CuraSceneNode"] = []
        for node in nodes:
            if hasattr(node, "setSelectable"): # A crude check if it's likely a CuraSceneNode or compatible
                cura_nodes.append(cast("CuraSceneNode", node))
            else:
                # This case should ideally not happen if GCodeReader works as expected.
                # If it does, a proper conversion or wrapping might be needed.
                Logger.warning(f"Node {node.getName()} from GCodeReader is not a CuraSceneNode. Conversion might be needed.")

        return cura_nodes if cura_nodes else None
