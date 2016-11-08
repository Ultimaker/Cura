from UM.Workspace.WorkspaceReader import WorkspaceReader


##    Base implementation for reading 3MF workspace files.
class ThreeMFWorkspaceReader(WorkspaceReader):
    def __init__(self):
        super().__init__()

    def preRead(self, file_name):
        return WorkspaceReader.PreReadResult.accepted
        # TODO: Find 3MFFileReader so we can load SceneNodes
        # TODO: Ask user if it's  okay for the scene to be cleared
