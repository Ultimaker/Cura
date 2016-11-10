from UM.Workspace.WorkspaceReader import WorkspaceReader
from UM.Application import Application

from UM.Logger import Logger
from UM.Settings.ContainerStack import ContainerStack

import zipfile

##    Base implementation for reading 3MF workspace files.
class ThreeMFWorkspaceReader(WorkspaceReader):
    def __init__(self):
        super().__init__()
        self._supported_extensions = [".3mf"]

        self._3mf_mesh_reader = None

    def preRead(self, file_name):
        self._3mf_mesh_reader = Application.getInstance().getMeshFileHandler().getReaderForFile(file_name)
        if self._3mf_mesh_reader and self._3mf_mesh_reader.preRead(file_name) == WorkspaceReader.PreReadResult.accepted:
            pass
        else:
            Logger.log("w", "Could not find reader that was able to read the scene data for 3MF workspace")
            return WorkspaceReader.PreReadResult.failed
        # TODO: Ask user if it's  okay for the scene to be cleared
        return WorkspaceReader.PreReadResult.accepted

    def read(self, file_name):
        # Load all the nodes / meshdata of the workspace
        nodes = self._3mf_mesh_reader.read(file_name)
        if nodes is None:
            nodes = []


        archive = zipfile.ZipFile(file_name, "r")

        cura_file_names = [name for name in archive.namelist() if name.startswith("Cura/")]

        # Get the stack(s) saved in the workspace.
        container_stack_files = [name for name in cura_file_names if name.endswith(".stack.cfg")]
        global_stack = None
        extruder_stacks = []
        for container_stack_file in container_stack_files:
            container_id = container_stack_file.replace("Cura/", "")
            container_id = container_id.replace(".stack.cfg", "")
            stack = ContainerStack(container_id)

            # Serialize stack by converting read data from bytes to string
            stack.deserialize(archive.open(container_stack_file).read().decode("utf-8"))

            if stack.getMetaDataEntry("type") == "extruder_train":
                extruder_stacks.append(stack)
            else:
                global_stack = stack

        # Check if the right machine type is active now
        #Application.getInstance().getGlobalContainerStack().getBottom().getId() ==


        return nodes
