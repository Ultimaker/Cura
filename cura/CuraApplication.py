# Copyright (c) 2015 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.

from UM.Qt.QtApplication import QtApplication
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Camera import Camera
from UM.Scene.Platform import Platform
from UM.Math.Vector import Vector
from UM.Math.Quaternion import Quaternion
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Resources import Resources
from UM.Scene.ToolHandle import ToolHandle
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Mesh.ReadMeshJob import ReadMeshJob
from UM.Logger import Logger
from UM.Preferences import Preferences
from UM.JobQueue import JobQueue

from UM.Scene.Selection import Selection
from UM.Scene.GroupDecorator import GroupDecorator

from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.SetTransformOperation import SetTransformOperation

from UM.i18n import i18nCatalog

from . import PlatformPhysics
from . import BuildVolume
from . import CameraAnimation
from . import PrintInformation
from . import CuraActions
from . import MultiMaterialDecorator
from . import ZOffsetDecorator
from . import CuraSplashScreen

from PyQt5.QtCore import pyqtSlot, QUrl, pyqtSignal, pyqtProperty, QEvent, Q_ENUMS
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtQml import qmlRegisterUncreatableType

import platform
import sys
import os.path
import numpy
import copy
numpy.seterr(all="ignore")

if platform.system() == "Linux": # Needed for platform.linux_distribution, which is not available on Windows and OSX
    # For Ubuntu: https://bugs.launchpad.net/ubuntu/+source/python-qt4/+bug/941826
    if platform.linux_distribution()[0] in ("Ubuntu", ): # TODO: Needs a "if X11_GFX == 'nvidia'" here. The workaround is only needed on Ubuntu+NVidia drivers. Other drivers are not affected, but fine with this fix.
        import ctypes
        from ctypes.util import find_library
        ctypes.CDLL(find_library('GL'), ctypes.RTLD_GLOBAL)

try:
    from cura.CuraVersion import CuraVersion
except ImportError:
    CuraVersion = "master" # [CodeStyle: Reflecting imported value]

class CuraApplication(QtApplication):
    class ResourceTypes:
        QmlFiles = Resources.UserType + 1
        Firmware = Resources.UserType + 2
    Q_ENUMS(ResourceTypes)

    def __init__(self):
        Resources.addSearchPath(os.path.join(QtApplication.getInstallPrefix(), "share", "cura"))
        if not hasattr(sys, "frozen"):
            Resources.addSearchPath(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))

        self._open_file_queue = [] #Files to open when plug-ins are loaded.

        super().__init__(name = "cura", version = CuraVersion)

        self.setWindowIcon(QIcon(Resources.getPath(Resources.Images, "cura-icon.png")))

        self.setRequiredPlugins([
            "CuraEngineBackend",
            "MeshView",
            "LayerView",
            "STLReader",
            "SelectionTool",
            "CameraTool",
            "GCodeWriter",
            "LocalFileOutputDevice"
        ])
        self._physics = None
        self._volume = None
        self._platform = None
        self._output_devices = {}
        self._print_information = None
        self._i18n_catalog = None
        self._previous_active_tool = None
        self._platform_activity = False
        self._scene_boundingbox = AxisAlignedBox()
        self._job_name = None
        self._center_after_select = False

        self.getMachineManager().activeMachineInstanceChanged.connect(self._onActiveMachineChanged)
        self.getMachineManager().addMachineRequested.connect(self._onAddMachineRequested)
        self.getController().getScene().sceneChanged.connect(self.updatePlatformActivity)
        self.getController().toolOperationStopped.connect(self._onToolOperationStopped)

        Resources.addType(self.ResourceTypes.QmlFiles, "qml")
        Resources.addType(self.ResourceTypes.Firmware, "firmware")

        Preferences.getInstance().addPreference("cura/active_machine", "")
        Preferences.getInstance().addPreference("cura/active_mode", "simple")
        Preferences.getInstance().addPreference("cura/recent_files", "")
        Preferences.getInstance().addPreference("cura/categories_expanded", "")
        Preferences.getInstance().addPreference("view/center_on_select", True)
        Preferences.getInstance().addPreference("mesh/scale_to_fit", True)
        Preferences.getInstance().setDefault("local_file/last_used_type", "text/x-gcode")

        JobQueue.getInstance().jobFinished.connect(self._onJobFinished)

        self._recent_files = []
        files = Preferences.getInstance().getValue("cura/recent_files").split(";")
        for f in files:
            if not os.path.isfile(f):
                continue

            self._recent_files.append(QUrl.fromLocalFile(f))

    @pyqtSlot(result = QUrl)
    def getDefaultPath(self):
        return QUrl.fromLocalFile(os.path.expanduser("~/"))
    
    ##  Handle loading of all plugin types (and the backend explicitly)
    #   \sa PluginRegistery
    def _loadPlugins(self):
        self._plugin_registry.addPluginLocation(os.path.join(QtApplication.getInstallPrefix(), "lib", "cura"))
        if not hasattr(sys, "frozen"):
            self._plugin_registry.addPluginLocation(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "plugins"))
            self._plugin_registry.loadPlugin("ConsoleLogger")
            self._plugin_registry.loadPlugin("CuraEngineBackend")

        self._plugin_registry.loadPlugins()

        if self.getBackend() == None:
            raise RuntimeError("Could not load the backend plugin!")

        self._plugins_loaded = True

    def addCommandLineOptions(self, parser):
        super().addCommandLineOptions(parser)
        parser.add_argument("file", nargs="*", help="Files to load after starting the application.")
        parser.add_argument("--debug", dest="debug-mode", action="store_true", default=False, help="Enable detailed crash reports.")

    def run(self):
        self._i18n_catalog = i18nCatalog("cura");

        i18nCatalog.setTagReplacements({
            "filename": "font color=\"black\"",
            "message": "font color=UM.Theme.colors.message_text;",
        })

        self.showSplashMessage(self._i18n_catalog.i18nc("@info:progress", "Setting up scene..."))

        controller = self.getController()

        controller.setActiveView("SolidView")
        controller.setCameraTool("CameraTool")
        controller.setSelectionTool("SelectionTool")

        t = controller.getTool("TranslateTool")
        if t:
            t.setEnabledAxis([ToolHandle.XAxis, ToolHandle.YAxis,ToolHandle.ZAxis])

        Selection.selectionChanged.connect(self.onSelectionChanged)

        root = controller.getScene().getRoot()
        self._platform = Platform(root)

        self._volume = BuildVolume.BuildVolume(root)

        self.getRenderer().setBackgroundColor(QColor(245, 245, 245))

        self._physics = PlatformPhysics.PlatformPhysics(controller, self._volume)

        camera = Camera("3d", root)
        camera.setPosition(Vector(-80, 250, 700))
        camera.setPerspective(True)
        camera.lookAt(Vector(0, 0, 0))
        controller.getScene().setActiveCamera("3d")

        self.getController().getTool("CameraTool").setOrigin(Vector(0, 100, 0))

        self._camera_animation = CameraAnimation.CameraAnimation()
        self._camera_animation.setCameraTool(self.getController().getTool("CameraTool"))

        self.showSplashMessage(self._i18n_catalog.i18nc("@info:progress", "Loading interface..."))

        self.setMainQml(Resources.getPath(self.ResourceTypes.QmlFiles, "Cura.qml"))
        self.initializeEngine()

        if self._engine.rootObjects:
            self.closeSplash()

            for file in self.getCommandLineOption("file", []):
                self._openFile(file)
            for file_name in self._open_file_queue: #Open all the files that were queued up while plug-ins were loading.
                self._openFile(file_name)

            self.exec_()

    #   Handle Qt events
    def event(self, event):
        if event.type() == QEvent.FileOpen:
            if self._plugins_loaded:
                self._openFile(event.file())
            else:
                self._open_file_queue.append(event.file())

        return super().event(event)

    def getPrintInformation(self):
        return self._print_information

    def registerObjects(self, engine):
        engine.rootContext().setContextProperty("Printer", self)
        self._print_information = PrintInformation.PrintInformation()
        engine.rootContext().setContextProperty("PrintInformation", self._print_information)
        self._cura_actions = CuraActions.CuraActions(self)
        engine.rootContext().setContextProperty("CuraActions", self._cura_actions)

        qmlRegisterUncreatableType(CuraApplication, "Cura", 1, 0, "ResourceTypes", "Just an Enum type")

    def onSelectionChanged(self):
        if Selection.hasSelection():
            if not self.getController().getActiveTool():
                if self._previous_active_tool:
                    self.getController().setActiveTool(self._previous_active_tool)
                    self._previous_active_tool = None
                else:
                    self.getController().setActiveTool("TranslateTool")
            if Preferences.getInstance().getValue("view/center_on_select"):
                self._center_after_select = True
        else:
            if self.getController().getActiveTool():
                self._previous_active_tool = self.getController().getActiveTool().getPluginId()
                self.getController().setActiveTool(None)
            else:
                self._previous_active_tool = None

    def _onToolOperationStopped(self, event):
        if self._center_after_select:
            self._center_after_select = False
            self._camera_animation.setStart(self.getController().getTool("CameraTool").getOrigin())
            self._camera_animation.setTarget(Selection.getSelectedObject(0).getWorldPosition())
            self._camera_animation.start()

    requestAddPrinter = pyqtSignal()
    activityChanged = pyqtSignal()
    sceneBoundingBoxChanged = pyqtSignal()

    @pyqtProperty(bool, notify = activityChanged)
    def getPlatformActivity(self):
        return self._platform_activity

    @pyqtProperty(str, notify = sceneBoundingBoxChanged)
    def getSceneBoundingBoxString(self):
        return self._i18n_catalog.i18nc("@info", "%(width).1f x %(depth).1f x %(height).1f mm") % {'width' : self._scene_boundingbox.width.item(), 'depth': self._scene_boundingbox.depth.item(), 'height' : self._scene_boundingbox.height.item()}

    def updatePlatformActivity(self, node = None):
        count = 0
        scene_boundingbox = None
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode or not node.getMeshData():
                continue

            count += 1
            if not scene_boundingbox:
                scene_boundingbox = copy.deepcopy(node.getBoundingBox())
            else:
                scene_boundingbox += node.getBoundingBox()

        if not scene_boundingbox:
            scene_boundingbox = AxisAlignedBox()

        if repr(self._scene_boundingbox) != repr(scene_boundingbox):
            self._scene_boundingbox = scene_boundingbox
            self.sceneBoundingBoxChanged.emit()

        self._platform_activity = True if count > 0 else False
        self.activityChanged.emit()

    @pyqtSlot(str)
    def setJobName(self, name):
        name = os.path.splitext(name)[0] #when a file is opened using the terminal; the filename comes from _onFileLoaded and still contains its extension. This cuts the extension off if nescessary.
        if self._job_name != name:
            self._job_name = name
            self.jobNameChanged.emit()

    jobNameChanged = pyqtSignal()

    @pyqtProperty(str, notify = jobNameChanged)
    def jobName(self):
        return self._job_name

    # Remove all selected objects from the scene.
    @pyqtSlot()
    def deleteSelection(self):
        if not self.getController().getToolsEnabled():
            return

        op = GroupedOperation()
        nodes = Selection.getAllSelectedObjects()
        for node in nodes:
            op.addOperation(RemoveSceneNodeOperation(node))

        op.push()

        pass

    ##  Remove an object from the scene.
    #   Note that this only removes an object if it is selected.
    @pyqtSlot("quint64")
    def deleteObject(self, object_id):
        if not self.getController().getToolsEnabled():
            return

        node = self.getController().getScene().findObject(object_id)

        if not node and object_id != 0: #Workaround for tool handles overlapping the selected object
            node = Selection.getSelectedObject(0)

        if node:
            if node.getParent():
                group_node = node.getParent()
                if not group_node.callDecoration("isGroup"):
                    op = RemoveSceneNodeOperation(node)
                else:
                    while group_node.getParent().callDecoration("isGroup"):
                        group_node = group_node.getParent()
                    op = RemoveSceneNodeOperation(group_node)
            op.push()

    ##  Create a number of copies of existing object.
    @pyqtSlot("quint64", int)
    def multiplyObject(self, object_id, count):
        node = self.getController().getScene().findObject(object_id)

        if not node and object_id != 0: #Workaround for tool handles overlapping the selected object
            node = Selection.getSelectedObject(0)

        if node:
            op = GroupedOperation()
            for _ in range(count):
                if node.getParent() and node.getParent().callDecoration("isGroup"):
                    new_node = copy.deepcopy(node.getParent()) #Copy the group node.
                    new_node.callDecoration("setConvexHull",None)

                    op.addOperation(AddSceneNodeOperation(new_node,node.getParent().getParent()))
                else:
                    new_node = copy.deepcopy(node)
                    new_node.callDecoration("setConvexHull", None)
                    op.addOperation(AddSceneNodeOperation(new_node, node.getParent()))

            op.push()

    ##  Center object on platform.
    @pyqtSlot("quint64")
    def centerObject(self, object_id):
        node = self.getController().getScene().findObject(object_id)
        if not node and object_id != 0: #Workaround for tool handles overlapping the selected object
            node = Selection.getSelectedObject(0)

        if not node:
            return

        if node.getParent() and node.getParent().callDecoration("isGroup"):
            node = node.getParent()

        if node:
            op = SetTransformOperation(node, Vector())
            op.push()
    
    ##  Delete all mesh data on the scene.
    @pyqtSlot()
    def deleteAll(self):
        if not self.getController().getToolsEnabled():
            return

        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode:
                continue
            if not node.getMeshData() and not node.callDecoration("isGroup"):
                continue #Node that doesnt have a mesh and is not a group.
            if node.getParent() and node.getParent().callDecoration("isGroup"):
                continue #Grouped nodes don't need resetting as their parent (the group) is resetted)
            nodes.append(node)
        if nodes:
            op = GroupedOperation()

            for node in nodes:
                op.addOperation(RemoveSceneNodeOperation(node))

            op.push()

    ## Reset all translation on nodes with mesh data. 
    @pyqtSlot()
    def resetAllTranslation(self):
        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode:
                continue
            if not node.getMeshData() and not node.callDecoration("isGroup"):
                continue #Node that doesnt have a mesh and is not a group.
            if node.getParent() and node.getParent().callDecoration("isGroup"):
                continue #Grouped nodes don't need resetting as their parent (the group) is resetted)

            nodes.append(node)

        if nodes:
            op = GroupedOperation()
            for node in nodes:
                node.removeDecorator(ZOffsetDecorator.ZOffsetDecorator)
                op.addOperation(SetTransformOperation(node, Vector(0,0,0)))

            op.push()
    
    ## Reset all transformations on nodes with mesh data. 
    @pyqtSlot()
    def resetAll(self):
        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode:
                continue
            if not node.getMeshData() and not node.callDecoration("isGroup"):
                continue #Node that doesnt have a mesh and is not a group.
            if node.getParent() and node.getParent().callDecoration("isGroup"):
                continue #Grouped nodes don't need resetting as their parent (the group) is resetted)
            nodes.append(node)

        if nodes:
            op = GroupedOperation()

            for node in nodes:
                # Ensure that the object is above the build platform
                node.removeDecorator(ZOffsetDecorator.ZOffsetDecorator)
                op.addOperation(SetTransformOperation(node, Vector(0,0,0), Quaternion(), Vector(1, 1, 1)))

            op.push()
            
    ##  Reload all mesh data on the screen from file.
    @pyqtSlot()
    def reloadAll(self):
        nodes = []
        for node in DepthFirstIterator(self.getController().getScene().getRoot()):
            if type(node) is not SceneNode or not node.getMeshData():
                continue

            nodes.append(node)

        if not nodes:
            return

        for node in nodes:
            if not node.getMeshData():
                continue

            file_name = node.getMeshData().getFileName()
            if file_name:
                job = ReadMeshJob(file_name)
                job._node = node
                job.finished.connect(self._reloadMeshFinished)
                job.start()
    
    ##  Get logging data of the backend engine
    #   \returns \type{string} Logging data
    @pyqtSlot(result=str)
    def getEngineLog(self):
        log = ""

        for entry in self.getBackend().getLog():
            log += entry.decode()

        return log

    recentFilesChanged = pyqtSignal()

    @pyqtProperty("QVariantList", notify = recentFilesChanged)
    def recentFiles(self):
        return self._recent_files

    @pyqtSlot("QStringList")
    def setExpandedCategories(self, categories):
        categories = list(set(categories))
        categories.sort()
        joined = ";".join(categories)
        if joined != Preferences.getInstance().getValue("cura/categories_expanded"):
            Preferences.getInstance().setValue("cura/categories_expanded", joined)
            self.expandedCategoriesChanged.emit()

    expandedCategoriesChanged = pyqtSignal()

    @pyqtProperty("QStringList", notify = expandedCategoriesChanged)
    def expandedCategories(self):
        return Preferences.getInstance().getValue("cura/categories_expanded").split(";")

    @pyqtSlot(str, result = "QVariant")
    def getSettingValue(self, key):
        if not self.getMachineManager().getWorkingProfile():
            return None
        return self.getMachineManager().getWorkingProfile().getSettingValue(key)
        #return self.getActiveMachine().getSettingValueByKey(key)
    
    ##  Change setting by key value pair
    @pyqtSlot(str, "QVariant")
    def setSettingValue(self, key, value):
        if not self.getMachineManager().getWorkingProfile():
            return

        self.getMachineManager().getWorkingProfile().setSettingValue(key, value)
        
    @pyqtSlot()
    def mergeSelected(self):
        self.groupSelected()
        try:
            group_node = Selection.getAllSelectedObjects()[0]
        except Exception as e:
            Logger.log("d", "mergeSelected: Exception:", e)
            return
        multi_material_decorator = MultiMaterialDecorator.MultiMaterialDecorator()
        group_node.addDecorator(multi_material_decorator)
        # Reset the position of each node
        for node in group_node.getChildren():
            new_position = node.getMeshData().getCenterPosition()
            new_position = new_position.scale(node.getScale())
            node.setPosition(new_position)
        
        # Use the previously found center of the group bounding box as the new location of the group
        group_node.setPosition(group_node.getBoundingBox().center)
    
    @pyqtSlot()
    def groupSelected(self):
        group_node = SceneNode()
        group_decorator = GroupDecorator()
        group_node.addDecorator(group_decorator)
        group_node.setParent(self.getController().getScene().getRoot())
        group_node.setSelectable(True)
        center = Selection.getSelectionCenter()
        group_node.setPosition(center)
        group_node.setCenterPosition(center)

        for node in Selection.getAllSelectedObjects():
            world = node.getWorldPosition()
            node.setParent(group_node)
            node.setPosition(world - center)

        for node in group_node.getChildren():
            Selection.remove(node)

        Selection.add(group_node)

    @pyqtSlot()
    def ungroupSelected(self):
        ungrouped_nodes = []
        selected_objects = Selection.getAllSelectedObjects()[:] #clone the list
        for node in selected_objects:
            if node.callDecoration("isGroup" ):
                children_to_move = []
                for child in node.getChildren():
                    if type(child) is SceneNode:
                        children_to_move.append(child)

                for child in children_to_move:
                    position = child.getWorldPosition()
                    child.setParent(node.getParent())
                    child.setPosition(position - node.getParent().getWorldPosition())
                    child.scale(node.getScale())
                    child.rotate(node.getOrientation())

                    Selection.add(child)
                    child.callDecoration("setConvexHull",None)
                node.setParent(None)
                ungrouped_nodes.append(node)
        for node in ungrouped_nodes:
            Selection.remove(node)

    def _createSplashScreen(self):
        return CuraSplashScreen.CuraSplashScreen()

    def _onActiveMachineChanged(self):
        machine = self.getMachineManager().getActiveMachineInstance()
        if machine:
            pass
            #Preferences.getInstance().setValue("cura/active_machine", machine.getName())

            #self._volume.setWidth(machine.getSettingValueByKey("machine_width"))
            #self._volume.setHeight(machine.getSettingValueByKey("machine_height"))
            #self._volume.setDepth(machine.getSettingValueByKey("machine_depth"))

            #disallowed_areas = machine.getSettingValueByKey("machine_disallowed_areas")
            #areas = []
            #if disallowed_areas:
                #for area in disallowed_areas:
                    #areas.append(Polygon(numpy.array(area, numpy.float32)))

            #self._volume.setDisallowedAreas(areas)

            #self._volume.rebuild()

            #offset = machine.getSettingValueByKey("machine_platform_offset")
            #if offset:
                #self._platform.setPosition(Vector(offset[0], offset[1], offset[2]))
            #else:
                #self._platform.setPosition(Vector(0.0, 0.0, 0.0))

    def _onFileLoaded(self, job):
        node = job.getResult()
        if node != None:
            self.setJobName(os.path.basename(job.getFileName()))
            node.setSelectable(True)
            node.setName(os.path.basename(job.getFileName()))
            op = AddSceneNodeOperation(node, self.getController().getScene().getRoot())
            op.push()

            self.getController().getScene().sceneChanged.emit(node) #Force scene change.

    def _onJobFinished(self, job):
        if type(job) is not ReadMeshJob or not job.getResult():
            return

        f = QUrl.fromLocalFile(job.getFileName())
        if f in self._recent_files:
            self._recent_files.remove(f)

        self._recent_files.insert(0, f)
        if len(self._recent_files) > 10:
            del self._recent_files[10]

        pref = ""
        for path in self._recent_files:
            pref += path.toLocalFile() + ";"

        Preferences.getInstance().setValue("cura/recent_files", pref)
        self.recentFilesChanged.emit()

    def _reloadMeshFinished(self, job):
        # TODO; This needs to be fixed properly. We now make the assumption that we only load a single mesh!
        job._node.setMeshData(job.getResult().getMeshData())
        #job.getResult().setParent(self.getController().getScene().getRoot())
        #job._node.setParent(self.getController().getScene().getRoot())
        #job._node.meshDataChanged.emit(job._node)

    def _openFile(self, file):
        job = ReadMeshJob(os.path.abspath(file))
        job.finished.connect(self._onFileLoaded)
        job.start()

    def _onAddMachineRequested(self):
        self.requestAddPrinter.emit()
