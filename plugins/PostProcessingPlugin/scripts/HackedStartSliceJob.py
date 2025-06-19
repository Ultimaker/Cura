try:
    from plugins.CuraEngineBackend.StartSliceJob import *
    from plugins.CuraEngineBackend.CuraEngineBackend import *
except:
    from share.cura.plugins.CuraEngineBackend.StartSliceJob import *
    from share.cura.plugins.CuraEngineBackend.CuraEngineBackend import *


class HackedStartSliceJob(StartSliceJob):
    def run(self) -> None:
        """Runs the job that initiates the slicing."""

        if self._build_plate_number is None:
            self.setResult(StartJobResult.Error)
            return

        stack = CuraApplication.getInstance().getGlobalContainerStack()
        if not stack:
            self.setResult(StartJobResult.Error)
            return

        # Don't slice if there is a setting with an error value.
        if CuraApplication.getInstance().getMachineManager().stacksHaveErrors:
            self.setResult(StartJobResult.SettingError)
            return

        if CuraApplication.getInstance().getBuildVolume().hasErrors():
            self.setResult(StartJobResult.BuildPlateError)
            return

        # Wait for error checker to be done.
        while CuraApplication.getInstance().getMachineErrorChecker().needToWaitForResult:
            time.sleep(0.1)

        if CuraApplication.getInstance().getMachineErrorChecker().hasError:
            self.setResult(StartJobResult.SettingError)
            return

        # Don't slice if the buildplate or the nozzle type is incompatible with the materials
        if not CuraApplication.getInstance().getMachineManager().variantBuildplateCompatible and \
                not CuraApplication.getInstance().getMachineManager().variantBuildplateUsable:
            self.setResult(StartJobResult.MaterialIncompatible)
            return

        for extruder_stack in stack.extruderList:
            material = extruder_stack.findContainer({"type": "material"})
            if not extruder_stack.isEnabled:
                continue
            if material:
                if material.getMetaDataEntry("compatible") == False:
                    self.setResult(StartJobResult.MaterialIncompatible)
                    return

        # Don't slice if there is a per object setting with an error value.
        for node in DepthFirstIterator(self._scene.getRoot()):
            if not isinstance(node, CuraSceneNode) or not node.isSelectable():
                continue

            if self._checkStackForErrors(node.callDecoration("getStack")):
                self.setResult(StartJobResult.ObjectSettingError)
                return

        # Remove old layer data.
        for node in DepthFirstIterator(self._scene.getRoot()):
            if node.callDecoration("getLayerData") and node.callDecoration(
                    "getBuildPlateNumber") == self._build_plate_number:
                # Since we walk through all nodes in the scene, they always have a parent.
                cast(SceneNode, node.getParent()).removeChild(node)
                break

        # Get the objects in their groups to print.
        object_groups = []
        if stack.getProperty("print_sequence", "value") == "one_at_a_time":
            modifier_mesh_nodes = []

            for node in DepthFirstIterator(self._scene.getRoot()):
                build_plate_number = node.callDecoration("getBuildPlateNumber")
                if node.callDecoration("isNonPrintingMesh") and build_plate_number == self._build_plate_number:
                    modifier_mesh_nodes.append(node)

            for node in OneAtATimeIterator(self._scene.getRoot()):
                temp_list = []

                # Filter on current build plate
                build_plate_number = node.callDecoration("getBuildPlateNumber")
                if build_plate_number is not None and build_plate_number != self._build_plate_number:
                    continue

                children = node.getAllChildren()
                children.append(node)
                for child_node in children:
                    mesh_data = child_node.getMeshData()
                    if mesh_data and mesh_data.getVertices() is not None:
                        temp_list.append(child_node)

                if temp_list:
                    object_groups.append(temp_list + modifier_mesh_nodes)
                Job.yieldThread()
            if len(object_groups) == 0:
                Logger.log("w", "No objects suitable for one at a time found, or no correct order found")
        else:
            temp_list = []
            has_printing_mesh = False
            for node in DepthFirstIterator(self._scene.getRoot()):
                mesh_data = node.getMeshData()
                if node.callDecoration("isSliceable") and mesh_data and mesh_data.getVertices() is not None:
                    is_non_printing_mesh = bool(node.callDecoration("isNonPrintingMesh"))

                    # Find a reason not to add the node
                    if node.callDecoration("getBuildPlateNumber") != self._build_plate_number:
                        continue
                    if getattr(node, "_outside_buildarea", False) and not is_non_printing_mesh:
                        continue

                    temp_list.append(node)
                    if not is_non_printing_mesh:
                        has_printing_mesh = True

                Job.yieldThread()

            # If the list doesn't have any model with suitable settings then clean the list
            # otherwise CuraEngine will crash
            if not has_printing_mesh:
                temp_list.clear()

            if temp_list:
                object_groups.append(temp_list)

        if stack.getProperty("print_sequence", "value") == "one_at_a_time":
            idx = 0
            while 'drywise_purge_box' not in object_groups[idx][0].getName():
                idx += 1
                if len(object_groups) <= idx:
                    break
            else:
                object_groups[0], object_groups[idx] = object_groups[idx], object_groups[0]
        else:
            group = object_groups[0]
            idx = 0
            while 'drywise_purge_box' not in group[idx].getName():
                idx += 1
                if len(group) <= idx:
                    break
            else:
                object_groups = [[group.pop(idx)], group]

        global_stack = CuraApplication.getInstance().getGlobalContainerStack()
        if not global_stack:
            return
        extruders_enabled = [stack.isEnabled for stack in global_stack.extruderList]
        filtered_object_groups = []
        has_model_with_disabled_extruders = False
        associated_disabled_extruders = set()
        for group in object_groups:
            stack = global_stack
            skip_group = False
            for node in group:
                # Only check if the printing extruder is enabled for printing meshes
                is_non_printing_mesh = node.callDecoration("evaluateIsNonPrintingMesh")
                extruder_position = int(node.callDecoration("getActiveExtruderPosition"))
                if not is_non_printing_mesh and not extruders_enabled[extruder_position]:
                    skip_group = True
                    has_model_with_disabled_extruders = True
                    associated_disabled_extruders.add(extruder_position)
            if not skip_group:
                filtered_object_groups.append(group)

        if has_model_with_disabled_extruders:
            self.setResult(StartJobResult.ObjectsWithDisabledExtruder)
            associated_disabled_extruders = {p + 1 for p in associated_disabled_extruders}
            self._associated_disabled_extruders = ", ".join(map(str, sorted(associated_disabled_extruders)))
            return

        # There are cases when there is nothing to slice. This can happen due to one at a time slicing not being
        # able to find a possible sequence or because there are no objects on the build plate (or they are outside
        # the build volume)
        if not filtered_object_groups:
            self.setResult(StartJobResult.NothingToSlice)
            return

        self._buildGlobalSettingsMessage(stack)
        self._buildGlobalInheritsStackMessage(stack)

        user_id = uuid.getnode()  # On all of Cura's supported platforms, this returns the MAC address which is pseudonymical information (!= anonymous).
        user_id %= 2 ** 16  # So to make it anonymous, apply a bitmask selecting only the last 16 bits. This prevents it from being traceable to a specific user but still gives somewhat of an idea of whether it's just the same user hitting the same crash over and over again, or if it's widespread.
        self._slice_message.sentry_id = f"{user_id}"
        self._slice_message.cura_version = CuraVersion

        # Add the project name to the message if the user allows for non-anonymous crash data collection.
        account = CuraApplication.getInstance().getCuraAPI().account
        if account and account.isLoggedIn and not CuraApplication.getInstance().getPreferences().getValue(
                "info/anonymous_engine_crash_report"):
            self._slice_message.project_name = CuraApplication.getInstance().getPrintInformation().baseName
            self._slice_message.user_name = account.userName

        # Build messages for extruder stacks
        for extruder_stack in global_stack.extruderList:
            self._buildExtruderMessage(extruder_stack)

        backend_plugins = CuraApplication.getInstance().getBackendPlugins()

        # Sort backend plugins by name. Not a very good strategy, but at least it is repeatable. This will be improved later.
        backend_plugins = sorted(backend_plugins, key=lambda backend_plugin: backend_plugin.getId())

        for plugin in backend_plugins:
            if not plugin.usePlugin():
                continue
            for slot in plugin.getSupportedSlots():
                # Right now we just send the message for every slot that we support. A single plugin can support
                # multiple slots
                # In the future the frontend will need to decide what slots that a plugin actually supports should
                # also be used. For instance, if you have two plugins and each of them support a_generate and b_generate
                # only one of each can actually be used (eg; plugin 1 does both, plugin 1 does a_generate and 2 does
                # b_generate, etc).
                plugin_message = self._slice_message.addRepeatedMessage("engine_plugins")
                plugin_message.id = slot
                plugin_message.address = plugin.getAddress()
                plugin_message.port = plugin.getPort()
                plugin_message.plugin_name = plugin.getPluginId()
                plugin_message.plugin_version = plugin.getVersion()

        for group in filtered_object_groups:
            group_message = self._slice_message.addRepeatedMessage("object_lists")
            parent = group[0].getParent()
            if parent is not None and parent.callDecoration("isGroup"):
                self._handlePerObjectSettings(cast(CuraSceneNode, parent), group_message)

            for object in group:
                mesh_data = object.getMeshData()
                if mesh_data is None:
                    continue
                rot_scale = object.getWorldTransformation().getTransposed().getData()[0:3, 0:3]
                translate = object.getWorldTransformation().getData()[:3, 3]

                # This effectively performs a limited form of MeshData.getTransformed that ignores normals.
                verts = mesh_data.getVertices()
                verts = verts.dot(rot_scale)
                verts += translate

                # Convert from Y up axes to Z up axes. Equals a 90 degree rotation.
                verts[:, [1, 2]] = verts[:, [2, 1]]
                verts[:, 1] *= -1

                obj = group_message.addRepeatedMessage("objects")
                obj.id = id(object)
                obj.name = object.getName()
                indices = mesh_data.getIndices()
                if indices is not None:
                    flat_verts = numpy.take(verts, indices.flatten(), axis=0)
                else:
                    flat_verts = numpy.array(verts)

                obj.vertices = flat_verts

                self._handlePerObjectSettings(cast(CuraSceneNode, object), obj)

                Job.yieldThread()

        self.setResult(StartJobResult.Finished)


def hacked_slice(self: CuraEngineBackend) -> None:
    """Perform a slice of the scene."""

    self._createSnapshot()

    self.startPlugins()

    Logger.log("i", "Starting to slice...")
    self._time_start_process = time()
    if not self._build_plates_to_be_sliced:
        self.processingProgress.emit(1.0)
        Logger.log("w", "Slice unnecessary, nothing has changed that needs reslicing.")
        self.setState(BackendState.Done)
        return

    if self._process_layers_job:
        Logger.log("d", "Process layers job still busy, trying later.")
        return

    if not hasattr(self._scene, "gcode_dict"):
        self._scene.gcode_dict = {}  # type: ignore
        # We need to ignore type because we are creating the missing attribute here.

    # see if we really have to slice
    application = CuraApplication.getInstance()
    active_build_plate = application.getMultiBuildPlateModel().activeBuildPlate
    build_plate_to_be_sliced = self._build_plates_to_be_sliced.pop(0)
    Logger.log("d", "Going to slice build plate [%s]!" % build_plate_to_be_sliced)
    num_objects = self._numObjectsPerBuildPlate()

    self._stored_layer_data = []

    if build_plate_to_be_sliced not in num_objects or num_objects[build_plate_to_be_sliced] == 0:
        self._scene.gcode_dict[build_plate_to_be_sliced] = []   # type: ignore
        # We need to ignore the type because we created this attribute above.
        Logger.log("d", "Build plate %s has no objects to be sliced, skipping", build_plate_to_be_sliced)
        if self._build_plates_to_be_sliced:
            self.slice()
        return
    self._stored_optimized_layer_data[build_plate_to_be_sliced] = []
    if application.getPrintInformation() and build_plate_to_be_sliced == active_build_plate:
        application.getPrintInformation().setToZeroPrintInformation(build_plate_to_be_sliced)

    if self._process is None:  # type: ignore
        self._createSocket()
    self.stopSlicing()
    self._engine_is_fresh = False  # Yes we're going to use the engine

    self.processingProgress.emit(0.0)
    self.backendStateChange.emit(BackendState.NotStarted)

    self._scene.gcode_dict[build_plate_to_be_sliced] = []  # type: ignore #[] indexed by build plate number
    self._slicing = True
    self.slicingStarted.emit()

    self.determineAutoSlicing()  # Switch timer on or off if appropriate

    slice_message = self._socket.createMessage("cura.proto.Slice")
    self._start_slice_job = HackedStartSliceJob(slice_message)
    self._start_slice_job_build_plate = build_plate_to_be_sliced
    self._start_slice_job.setBuildPlate(self._start_slice_job_build_plate)
    self._start_slice_job.start()
    self._start_slice_job.finished.connect(self._onStartSliceCompleted)


def apply_hack():
    from UM.PluginRegistry import PluginRegistry

    registry = PluginRegistry.getInstance()
    backend: CuraEngineBackend = registry.getPluginObject('CuraEngineBackend')
    backend.slice = lambda b=backend: hacked_slice(backend)

# def apply_hack():
#     def decor(func):
#         def wrapper(*args, **kwargs):
#             print('wrapped')
#             func(*args, **kwargs)
#             print('wrapped')
#         return wrapper
#
#     StartSliceJob.run = decor(hacked_run)
#     print('hacked')

