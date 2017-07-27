# Copyright (c) 2017 Thomas Karl Pietrowski

# Buildins
import os
import tempfile

# Uranium/Cura
from UM.Application import Application
from UM.i18n import i18nCatalog
i18n_catalog = i18nCatalog("CuraSolidWorksIntegrationPlugin")
from UM.Message import Message
from UM.Logger import Logger
from UM.Mesh.MeshReader import MeshReader
from UM.PluginRegistry import PluginRegistry
from UM.Scene.SceneNode import SceneNode

# PyWin32
from comtypes.client import GetClassObject


class CommonCOMReader(MeshReader):
    def __init__(self, app_name, app_friendly_name):
        super().__init__()
        self._app_name = app_name
        self._app_friendly_name = app_friendly_name

        # Start/stop behaviour

        # Technically neither preloading nor keeping the instance up, is possible, since Cura calls the file reader from different/new threads
        # The error when trying to use it here is:
        # > pywintypes.com_error: (-2147417842, 'The application called an interface that was marshalled for a different thread.', None, None)
        self._app_preload = False
        self._app_keep_running = False

        """
        if self._app_preload and not self._app_keep_running:
            self._app_keep_running = True
        """

        # Preparations
        """
        if self._app_preload:
            Logger.log("d", "Preloading %s..." %(self._app_friendlyName))
            self.startApp()
        """

        Logger.log("d", "Looking for readers...")
        self.__init_builtin_readers__()

    def __init_builtin_readers__(self):
        self._file_formats_first_choice = [] # Ordered list of preferred formats
        self._reader_for_file_format = {}

        # Trying 3MF first because it describes the model much better..
        # However, this is untested since this plugin was only tested with STL support
        if PluginRegistry.getInstance().isActivePlugin("3MFReader"):
            self._reader_for_file_format["3mf"] = PluginRegistry.getInstance().getPluginObject("3MFReader")
            self._file_formats_first_choice.append("3mf")

        if PluginRegistry.getInstance().isActivePlugin("STLReader"):
            self._reader_for_file_format["stl"] = PluginRegistry.getInstance().getPluginObject("STLReader")
            self._file_formats_first_choice.append("stl")

        if not len(self._reader_for_file_format):
            Logger.log("d", "Could not find any reader for (probably) supported file formats!")

    def getSaveTempfileName(self, suffix = ""):
        # Only get a save name for a temp_file here...
        temp_stl_file = tempfile.NamedTemporaryFile()
        temp_stl_file_name = "%s%s" % (temp_stl_file.name, suffix)
        temp_stl_file.close()

        return temp_stl_file_name

    def startApp(self, visible = False):
        Logger.log("d", "Starting %s...", self._app_friendly_name)

        com_class_object = GetClassObject(self._app_name)
        com_instance = com_class_object.CreateInstance()

        return com_instance

    def checkApp(self):
        raise NotImplementedError("Checking app is not implemented!")

    def getAppVisible(self, state):
        raise NotImplementedError("Toggle for visibility not implemented!")

    def setAppVisible(self, state, **options):
        raise NotImplementedError("Toggle for visibility not implemented!")

    def closeApp(self, **options):
        raise NotImplementedError("Procedure how to close your app is not implemented!")

    def openForeignFile(self, **options):
        "This function shall return options again. It optionally contains other data, which is needed by the reader for other tasks later."
        raise NotImplementedError("Opening files is not implemented!")

    def exportFileAs(self, model, **options):
        raise NotImplementedError("Exporting files is not implemented!")

    def closeForeignFile(self, **options):
        raise NotImplementedError("Closing files is not implemented!")

    def nodePostProcessing(self, node):
        return node

    def read(self, file_path):
        options = {"foreignFile": file_path,
                   "foreignFormat": os.path.splitext(file_path)[1],
                   }

        # Starting app, if needed
        try:
            options["app_instance"] = self.startApp()
        except Exception:
            Logger.logException("e", "Failed to start <%s>...", self._app_name)
            error_message = Message(i18n_catalog.i18nc("@info:status", "Error while starting %s!" % self._app_friendly_name))
            error_message.show()
            return None

        # Tell the 3rd party application to open a file...
        Logger.log("d", "Opening file with %s..." % self._app_friendly_name)
        options = self.openForeignFile(**options)

        # Append all formats which are not preferred to the end of the list
        fileFormats = self._file_formats_first_choice
        for file_format in self._reader_for_file_format.keys():
            if file_format not in fileFormats:
                fileFormats.append(file_format)

        # Trying to convert into all formats 1 by 1 and continue with the successful export
        Logger.log("i", "Trying to convert into: %s", fileFormats)
        for file_format in fileFormats:
            Logger.log("d", "Trying to convert <%s> into '%s'", file_path, file_format)

            options["tempType"] = file_format

            options["tempFile"] = self.getSaveTempfileName(".%s" % file_format.upper())
            Logger.log("d", "Using temporary file <%s>", options["tempFile"])

            # In case there is already a file with this name (very unlikely...)
            if os.path.isfile(options["tempFile"]):
                Logger.log("w", "Removing already available file, called: %s", options["tempFile"])
                os.remove(options["tempFile"])

            Logger.log("d", "Saving as: <%s>", options["tempFile"])
            try:
                self.exportFileAs(**options)
            except:
                Logger.logException("e", "Could not export <%s> into '%s'.", file_path, file_format)
                continue

            if os.path.isfile(options["tempFile"]):
                Logger.log("d", "Saved as: <%s>", options["tempFile"])
            else:
                Logger.log("d", "Temporary file not found after export!")
                continue

            # Opening the resulting file in Cura
            try:
                #reader = self._readerForFileformat[fileFormat]
                reader = Application.getInstance().getMeshFileHandler().getReaderForFile(options["tempFile"])
                if not reader:
                    Logger.log("d", "Found no reader for %s. That's strange...")
                    continue
                Logger.log("d", "Using reader: %s", reader.getPluginId())
                temp_scene_node = reader.read(options["tempFile"])
            except:
                Logger.logException("e", "Failed to open exported <%s> file in Cura!", file_format)
                continue

            # Remove the temp_file again
            Logger.log("d", "Removing temporary STL file, called <%s>", options["tempFile"])
            os.remove(options["tempFile"])

            break

        # Closing document in the app
        self.closeForeignFile(**options)

        # Closing the app again..
        self.closeApp(**options)

        scene_node = SceneNode()
        temp_scene_node = self.nodePostProcessing(temp_scene_node)
        mesh = temp_scene_node.getMeshDataTransformed()

        # When using 3MF as the format to convert into we get an list of meshes instead of only one mesh directly.
        # This is a little workaround since reloading of 3MF files doesn't work at the moment.
        if type(mesh) == list:
            error_message = Message(i18n_catalog.i18nc("@info:status", "Please keep in mind, that you have to reopen your SolidWorks file manually! Reloading the model won't work!"))
            error_message.show()
            mesh = mesh.set(file_name = None)
        else:
            mesh = mesh.set(file_name = file_path)
        scene_node.setMeshData(mesh)

        if scene_node:
            return scene_node
