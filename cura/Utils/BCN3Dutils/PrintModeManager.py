from UM.Application import Application

from UM.Signal import Signal
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.RemoveSceneNodeOperation import RemoveSceneNodeOperation
from UM.Math.Vector import Vector
from UM.Message import Message
import cura.CuraApplication
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Utils.BCN3Dutils.Scene.DuplicatedNode import DuplicatedNode
from cura.Settings.ExtruderManager import ExtruderManager
from UM.Scene.Selection import Selection
from UM.Logger import Logger


class PrintModeManager:

    def __init__(self):
        super().__init__()
        if PrintModeManager._instance is not None:
            raise ValueError("Duplicate singleton creation")

        PrintModeManager._instance = self
        self._duplicated_nodes = []
        self._scene = Application.getInstance().getController().getScene()
        application = cura.CuraApplication.CuraApplication.getInstance()
        self._global_stack = application.getGlobalContainerStack()
        self._last_mode : str = "singleT0"
        self._print_mode_to_load :str = "singleT0"
        self.openedFromMFReader : bool = False
        self.savedMode : str = "singleT0"
        self._loading_message : Message = None

        if self._global_stack is not None:
            self._global_stack.setProperty("print_mode", "value", "singleT0")
            for node in Selection.getAllSelectedObjects():
                node.setSetting("print_mode", "singleT0")
            self._last_mode = self._global_stack.getProperty("print_mode", "value")

        Application.getInstance().globalContainerStackChanged.connect(self._onGlobalStackChanged)
        self._onGlobalStackChanged()
        self.printModeChanged.connect(self._onPrintModeChanged)
        self._onPrintModeChanged()

    def getPrintModeToLoad(self)-> str:
        return self._print_mode_to_load 
    
    def setPrintModeToLoad(self, value : str) -> None:
        self._print_mode_to_load = value
    
    def reset3MFPrintMode(self) -> None:
        self._print_mode_to_load = "singleT0"

    # Bugfix when a stl is imported into a dupli/mirror buildplate as a shadow
    def checkSTLScene(self, filename : str, loading_message : Message) -> None:
        is_project = filename.lower().endswith('3mf') or filename.lower().endswith('amf')
        app = Application.getInstance()
        target_print_mode = self._print_mode_to_load
        self.savedMode =  target_print_mode
        self._loading_message = loading_message
        #STL imported into a dupli/mirror scene
        if not is_project and (target_print_mode == 'mirror' or target_print_mode =='duplication'):
            self._loading_message.setProgress(70)
            
            # Apply new print mode when render finishes
            app.getMainWindow().renderCompleted.connect(self.applyIDEX)
            
            # Reset Print mode
            self.reset3MFPrintMode()
            bcn3dplugin = app.getPluginRegistry().getPluginObject("BCN3D")
            bcn3dplugin.print_modes.getPrintModeManager().setPrintMode(self._print_mode_to_load)
        else:
            self._loading_message.hide()

    def applyIDEX(self, *args):
        self._loading_message.setProgress(90)
        self._loading_message.setText("Finishing View")

        app = Application.getInstance()
        app.getMainWindow().renderCompleted.disconnect(self.applyIDEX)
        # Apply Dupli/mirror mode
        bcn3dplugin = app.getPluginRegistry().getPluginObject("BCN3D")
        bcn3dplugin.print_modes.getPrintModeManager().setPrintMode(self.savedMode)

        self._loading_message.hide()

    def applyPrintMode(self):
        app = Application.getInstance()
        bcn3d_api = app.getPluginRegistry().getPluginObject("BCN3D")
        bcn3d_api.getPrintersManager().setPrintMode(self.getPrintModeToLoad())

    def addDuplicatedNode(self, node) -> None:
        node.callDecoration("setBuildPlateNumber", 0)
        if node not in self._duplicated_nodes:
            self._duplicated_nodes.append(node)
        for child in node.getChildren():
            if isinstance(child, CuraSceneNode):
                self.addDuplicatedNode(child)

    def deleteDuplicatedNodes(self) -> None:
        del self._duplicated_nodes[:]

    def deleteDuplicatedNode(self, node, delete_children = True) -> None:
        if node in self._duplicated_nodes:
            self._duplicated_nodes.remove(node)
        if delete_children:
            for child in node.getChildren():
                if isinstance(child, CuraSceneNode):
                    self.deleteDuplicatedNode(child)

    def getDuplicatedNode(self, node):
        for node_dup in self._duplicated_nodes:
            if node_dup.node == node:
                return node_dup

    def getDuplicatedNodes(self):
        return self._duplicated_nodes

    def renderDuplicatedNode(self, node) -> None:
        node.callDecoration("setBuildPlateNumber", 0)
        if node.node.getParent() != self._scene.getRoot():
            parent = self.getDuplicatedNode(node.node.getParent())
        else:
            parent = self._scene.getRoot()
        op = AddSceneNodeOperation(node, parent)
        op.redo()
        node.update()

    def renderDuplicatedNodes(self) -> None:
        for node in self._duplicated_nodes:
            self.renderDuplicatedNode(node)

    def removeDuplicatedNodes(self) -> None:
        for node in self._duplicated_nodes:
            op = RemoveSceneNodeOperation(node)
            op.redo()

    def _onGlobalStackChanged(self, *args) -> None:
        if self._global_stack:
            self._global_stack.propertyChanged.disconnect(self._onPropertyChanged)

        self._global_stack = Application.getInstance().getGlobalContainerStack()

        if self._global_stack:
            self._global_stack.propertyChanged.connect(self._onPropertyChanged)
            if not self._global_stack.getProperty("print_mode", "enabled"):
                self.removeDuplicatedNodes()
                self.deleteDuplicatedNodes()
            else:
                if len(self._duplicated_nodes) == 0:
                    for node in self._scene.getRoot().getChildren():
                        if type(node) == CuraSceneNode:
                            self.addDuplicatedNode(DuplicatedNode(node, node.getParent()))
                self._onPrintModeChanged()

    printModeChanged = Signal()
    printModeApplied = Signal()

    def _onPropertyChanged(self, key, property_name) -> None:
        if key == "print_mode" and property_name == "value":
            self.printModeChanged.emit()

    # Add/remove duplicated node
    def _onPrintModeChanged(self) -> None:
        if self._global_stack:
            print_mode = self._global_stack.getProperty("print_mode", "value")
            Logger.info("Print mode has changed from %s to %s" % (self._last_mode, print_mode)) 
            nodes = self._scene.getRoot().getChildren()
            # ::::: TO SINGLE/DUAL :::::
            if print_mode in ["singleT0", "singleT1", "dual"] and self._last_mode in ["mirror", "duplication"]:
                if self._mesh_on_buildplate(nodes):
                    #remove duplicate nodes
                    self.removeDuplicatedNodes()
                    Logger.info("Moving nodes to the right")  
                    self._moveNodes(nodes, 1)
            
            # ::::: TO IDEX :::::
            if print_mode in ["mirror", "duplication"]:
                #Set active extruder for diasable bed area
                for node in nodes:
                    self._setActiveExtruder(node)
                    if self._last_mode in ["singleT0", "singleT1", "dual"] and type(node) == CuraSceneNode:
                        self.addDuplicatedNode(DuplicatedNode(node, node.getParent()))
                if self._last_mode in ["singleT0", "singleT1", "dual"]:
                    Logger.info("Moving nodes to the left")
                    self._moveNodes(nodes, -1)

            # Set last print mode
            self._last_mode = print_mode

    def _moveNodes(self, nodes, direcction) -> None:
        #If a file is opened from MFReader, the nodes are already moved
        if self.openedFromMFReader:
            Logger.info("File opened from MFReader, not need to move nodes")
            self.openedFromMFReader = False
        else:
            nodesMoved = 0
            machine_width = self._global_stack.getProperty("machine_width", "value")
            offset = machine_width/4 * direcction
            for node in nodes:
                if self._is_node_a_mesh(node):
                    position = node.getPosition()
                    node.setPosition(Vector(position.x + offset, position.y, position.z))
                    nodesMoved += 1
                    for child in node.getChildren():
                        self._moveNodes([child], offset, direcction)
            Logger.info("Nodes moved: %s" % nodesMoved)
        

    # Check if there is a mesh (3D object) in the buildplate
    def _mesh_on_buildplate(self, nodes) -> bool:
        mesh = False
        for n in nodes:
            if (n.callDecoration("isSliceable") or n.callDecoration("isGroup")) and not isinstance(n, DuplicatedNode):
                mesh = True
                break
        return mesh

    # Check if node is a mesh (3D object)
    def _is_node_a_mesh(self, node) -> bool:
           return (node.callDecoration("isSliceable") or node.callDecoration("isGroup")) and not isinstance(node, DuplicatedNode)
          
    def _setActiveExtruder(self, node) -> None:
        if type(node) == CuraSceneNode:
            node.callDecoration("setActiveExtruder", ExtruderManager.getInstance().getExtruderStack(0).getId())
            for child in node.getChildren():
                self._setActiveExtruder(child)

    @classmethod
    def getInstance(cls) -> "PrintModeManager":
        # Note: Explicit use of class name to prevent issues with inheritance.
        if not PrintModeManager._instance:
            PrintModeManager._instance = cls()

        return PrintModeManager._instance

    _instance = None