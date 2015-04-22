from UM.Backend.Backend import Backend
from UM.Application import Application
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Preferences import Preferences
from UM.Math.Vector import Vector
from UM.Signal import Signal

from . import Cura_pb2
from . import ProcessSlicedObjectListJob
from . import ProcessGCodeJob

import os
import sys
import numpy

from PyQt5.QtCore import QTimer

class CuraEngineBackend(Backend):
    def __init__(self):
        super().__init__()

        # Find out where the engine is located, and how it is called. This depends on how Cura is packaged and which OS we are running on.
        default_engine_location = '../PinkUnicornEngine/CuraEngine'
        if hasattr(sys, 'frozen'):
            default_engine_location = os.path.join(os.path.dirname(os.path.abspath(sys.executable)), 'CuraEngine')
        if sys.platform == 'win32':
            default_engine_location += '.exe'
        default_engine_location = os.path.abspath(default_engine_location)
        Preferences.getInstance().addPreference('backend/location', default_engine_location)

        self._scene = Application.getInstance().getController().getScene()
        self._scene.sceneChanged.connect(self._onSceneChanged)

        self._settings = None
        Application.getInstance().activeMachineChanged.connect(self._onActiveMachineChanged)
        self._onActiveMachineChanged()

        self._change_timer = QTimer()
        self._change_timer.setInterval(500)
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self.slice)

        self._message_handlers[Cura_pb2.SlicedObjectList] = self._onSlicedObjectListMessage
        self._message_handlers[Cura_pb2.Progress] = self._onProgressMessage
        self._message_handlers[Cura_pb2.GCodeLayer] = self._onGCodeLayerMessage
        self._message_handlers[Cura_pb2.GCodePrefix] = self._onGCodePrefixMessage
        self._message_handlers[Cura_pb2.ObjectPrintTime] = self._onObjectPrintTimeMessage

        self._center = None

        self._slicing = False
        self._restart = False

        self._save_gcode = True
        self._save_polygons = True
        self._report_progress = True

        self.backendConnected.connect(self._onBackendConnected)

    def getEngineCommand(self):
        return [Preferences.getInstance().getValue("backend/location"), '-vv', '--connect', "127.0.0.1:{0}".format(self._port)]

    ##  Emitted when we get a message containing print duration and material amount. This also implies the slicing has finished.
    #   \param time The amount of time the print will take.
    #   \param material_amount The amount of material the print will use.
    printDurationMessage = Signal()

    ##  Emitted when the slicing process starts.
    slicingStarted = Signal()

    ##  Emitted whne the slicing process is aborted forcefully.
    slicingCancelled = Signal()

    ##  Perform a slice of the scene with the given set of settings.
    #
    #   \param kwargs Keyword arguments.
    #                 Valid values are:
    #                 - settings: The settings to use for the slice. The default is the active machine.
    #                 - save_gcode: True if the generated gcode should be saved, False if not. True by default.
    #                 - save_polygons: True if the generated polygon data should be saved, False if not. True by default.
    #                 - force_restart: True if the slicing process should be forcefully restarted if it is already slicing.
    #                                  If False, this method will do nothing when already slicing. True by default.
    #                 - report_progress: True if the slicing progress should be reported, False if not. Default is True.
    def slice(self, **kwargs):
        if self._slicing:
            if not kwargs.get('force_restart', True):
                return

            self._slicing = False
            self._restart = True
            if self._process is not None:
                try:
                    self._process.terminate()
                except: # terminating a process that is already terminating causes an exception, silently ignore this.
                    pass
            self.slicingCancelled.emit()
            return

        objects = []
        for node in DepthFirstIterator(self._scene.getRoot()):
            if type(node) is SceneNode and node.getMeshData() and node.getMeshData().getVertices() is not None:
                if not getattr(node, '_outside_buildarea', False):
                    objects.append(node)

        if not objects:
            return #No point in slicing an empty build plate

        self._slicing = True
        self.slicingStarted.emit()

        self._report_progress = kwargs.get('report_progress', True)
        if self._report_progress:
            self.processingProgress.emit(0.0)

        self._sendSettings(kwargs.get('settings', self._settings))

        self._scene.acquireLock()

        # Set the gcode as an empty list. This will be filled with strings by GCodeLayer messages.
        # This is done so the gcode can be fragmented in memory and does not need a continues memory space.
        # (AKA. This prevents MemoryErrors)
        self._save_gcode = kwargs.get('save_gcode', True)
        if self._save_gcode:
            setattr(self._scene, 'gcode_list', [])

        self._save_polygons = kwargs.get('save_polygons', True)

        msg = Cura_pb2.ObjectList()

        #TODO: All at once/one at a time mode
        center = Vector()
        for object in objects:
            center += object.getPosition()

            mesh_data = object.getMeshData().getTransformed(object.getWorldTransformation())

            obj = msg.objects.add()
            obj.id = id(object)
            
            verts = numpy.array(mesh_data.getVertices(), copy=True)
            verts[:,[1,2]] = verts[:,[2,1]]
            verts[:,[2]] *= -1
            obj.vertices = verts.tostring()

            #if meshData.hasNormals():
                #obj.normals = meshData.getNormalsAsByteArray()

            #if meshData.hasIndices():
                #obj.indices = meshData.getIndicesAsByteArray()

        self._scene.releaseLock()

        self._socket.sendMessage(msg)

    def _onSceneChanged(self, source):
        if (type(source) is not SceneNode) or (source is self._scene.getRoot()) or (source.getMeshData() is None):
            return

        if(source.getMeshData().getVertices() is None):
            return

        self._onChanged()

    def _onActiveMachineChanged(self):
        if self._settings:
            self._settings.settingChanged.disconnect(self._onSettingChanged)

        self._settings = Application.getInstance().getActiveMachine()
        if self._settings:
            self._settings.settingChanged.connect(self._onSettingChanged)
            self._onChanged()

    def _onSettingChanged(self, setting):
        self._onChanged()

    def _onSlicedObjectListMessage(self, message):
        if self._save_polygons:
            job = ProcessSlicedObjectListJob.ProcessSlicedObjectListJob(message, self._center)
            job.start()

    def _onProgressMessage(self, message):
        if message.amount >= 0.99:
            self._slicing = False

        if self._report_progress:
            self.processingProgress.emit(message.amount)

    def _onGCodeLayerMessage(self, message):
        if self._save_gcode:
            job = ProcessGCodeJob.ProcessGCodeLayerJob(message)
            job.start()

    def _onGCodePrefixMessage(self, message):
        if self._save_gcode:
            self._scene.gcode_list.insert(0, message.data.decode('utf-8', 'replace'))

    def _onObjectPrintTimeMessage(self, message):
        self.printDurationMessage.emit(message.time, message.material_amount)

    def _createSocket(self):
        super()._createSocket()
        
        self._socket.registerMessageType(1, Cura_pb2.ObjectList)
        self._socket.registerMessageType(2, Cura_pb2.SlicedObjectList)
        self._socket.registerMessageType(3, Cura_pb2.Progress)
        self._socket.registerMessageType(4, Cura_pb2.GCodeLayer)
        self._socket.registerMessageType(5, Cura_pb2.ObjectPrintTime)
        self._socket.registerMessageType(6, Cura_pb2.SettingList)
        self._socket.registerMessageType(7, Cura_pb2.GCodePrefix)

    def _onChanged(self):
        if not self._settings:
            return

        self._change_timer.start()

    ## TODO: Neith settings need to be moved to their own backend.
    def _sendSettings(self, settings):
        if settings.getSettingValueByKey('wireframe'):
            self._sendSettings_neith(settings)
        else:
            self._sendSettings_normal(settings)

    def _sendSettings_neith(self, settings):
        extruder = 0
        
        # AKA The Dictionary of Doom (tm)
        engine_settings = {
            'neith': 1,
            'extruderNr': extruder,
            'printTemperature': int(settings.getSettingValueByKey('material_print_temperature')),
            'bedTemperature': int(settings.getSettingValueByKey('material_bed_temperature')),
            'filamentDiameter': int(settings.getSettingValueByKey('material_diameter') * 1000),
            'retractionAmount': int(settings.getSettingValueByKey('retraction_amount') * 1000),
            'retractionAmountPrime': int(0 * 1000),
            # 'retractionAmountExtruderSwitch': int(fbk('') * 1000),
            'retractionSpeed': int(settings.getSettingValueByKey('retraction_speed')),
            'retractionPrimeSpeed': int(settings.getSettingValueByKey('retraction_speed')),
            'retractionMinimalDistance': int(settings.getSettingValueByKey('retraction_min_travel') * 1000),
            'retractionZHop': int(settings.getSettingValueByKey('retraction_hop') * 1000),

            'moveSpeed': int(settings.getSettingValueByKey('speed_travel')),

            'fanSpeedMin': settings.getSettingValueByKey('cool_fan_speed_min'),
            'fanSpeedMax': settings.getSettingValueByKey('cool_fan_speed_max'),

            # ================================
            #    wireframe printing options
            # ================================
            'wireframeConnectionHeight': int(settings.getSettingValueByKey('wireframe_height')*1000),
            'wireframeNozzleClearance': int(settings.getSettingValueByKey('wireframe_nozzle_clearance')*1000),

            'machineNozzleTipOuterDiameter': int(settings.getSettingValueByKey('machine_nozzle_tip_outer_diameter')*1000),
            'machineNozzleHeadDistance': int(settings.getSettingValueByKey('machine_nozzle_head_distance')*1000),
            'machineNozzleExpansionAngle': int(settings.getSettingValueByKey('machine_nozzle_expansion_angle')),

            'wireframePrintspeedBottom': settings.getSettingValueByKey('wireframe_printspeed_bottom'),
            'wireframePrintspeedUp': settings.getSettingValueByKey('wireframe_printspeed_up'),
            'wireframePrintspeedDown': settings.getSettingValueByKey('wireframe_printspeed_down'),
            'wireframePrintspeedFlat': settings.getSettingValueByKey('wireframe_printspeed_flat'),

            'wireframeFlowConnection': int(settings.getSettingValueByKey('wireframe_flow_connection')),
            'wireframeFlowFlat': int(settings.getSettingValueByKey('wireframe_flow_flat')),

            'wireframeTopDelay': int(settings.getSettingValueByKey('wireframe_top_delay')*100),
            'wireframeBottomDelay': int(settings.getSettingValueByKey('wireframe_bottom_delay')*100),
            'wireframeFlatDelay': int(settings.getSettingValueByKey('wireframe_flat_delay')*100),

            'wireframeUpDistHalfSpeed': int(settings.getSettingValueByKey('wireframe_up_half_speed')*1000),
            'wireframeTopJump': int(settings.getSettingValueByKey('wireframe_top_jump')*1000),

            'wireframeFallDown': int(settings.getSettingValueByKey('wireframe_fall_down')*1000),
            'wireframeDragAlong': int(settings.getSettingValueByKey('wireframe_drag_along')*1000),

            'wireframeStraightBeforeDown': int(settings.getSettingValueByKey('wireframe_straight_before_down')),


            'wireframeRoofFallDown': int(settings.getSettingValueByKey('wireframe_roof_fall_down')*1000),
            'wireframeRoofDragAlong': int(settings.getSettingValueByKey('wireframe_roof_drag_along')*1000),
            'wireframeRoofOuterDelay': int(settings.getSettingValueByKey('wireframe_roof_outer_delay')*100),
            'wireframeRoofInset': int(settings.getSettingValueByKey('wireframe_roof_inset')*1000),
        }

        wireFrameStrategy = settings.getSettingValueByKey('wireframe_strategy')
        if wireFrameStrategy == 'Compensate':
            engine_settings['wireframeStrategy'] = 0
        if wireFrameStrategy == 'Knot':
            engine_settings['wireframeStrategy'] = 1
        if wireFrameStrategy == 'Retract':
            engine_settings['wireframeStrategy'] = 2

        gcodeFlavor = settings.getSettingValueByKey('machine_gcode_flavor')
        if gcodeFlavor == 'UltiGCode':
            engine_settings['gcodeFlavor'] = "GCODE_FLAVOR_ULTIGCODE"
        elif gcodeFlavor == 'Makerbot':
            engine_settings['gcodeFlavor'] = "GCODE_FLAVOR_MAKERBOT"
        elif gcodeFlavor == 'BFB':
            engine_settings['gcodeFlavor'] = "GCODE_FLAVOR_BFB"
        elif gcodeFlavor == 'Mach3':
            engine_settings['gcodeFlavor'] = "GCODE_FLAVOR_MACH3"
        elif gcodeFlavor == 'Volumetric':
            engine_settings['gcodeFlavor'] = "GCODE_FLAVOR_REPRAP_VOLUMATRIC"
        else:
            engine_settings['gcodeFlavor'] = "GCODE_FLAVOR_REPRAP"

        engine_settings['startCode'] = settings.getSettingValueByKey('machine_start_gcode')
        engine_settings['endCode'] = settings.getSettingValueByKey('machine_end_gcode')

        #for n in range(1, self._machine.getMaxNozzles()):
        n = 1
        engine_settings['extruderOffset1.X'] = int(settings.getSettingValueByKey('machine_nozzle_offset_x_1') * 1000)
        engine_settings['extruderOffset1.Y'] = int(settings.getSettingValueByKey('machine_nozzle_offset_y_1') * 1000)

        if not settings.getSettingValueByKey('machine_center_is_zero'):
            engine_settings['position.X'] = int((settings.getSettingValueByKey('machine_width') / 2.0) * 1000)
            engine_settings['position.Y'] = int((settings.getSettingValueByKey('machine_depth') / 2.0) * 1000)
            self._center = Vector(settings.getSettingValueByKey('machine_width') / 2.0, 0.0, settings.getSettingValueByKey('machine_depth') / 2.0)
        else:
            engine_settings['position.X'] = 0
            engine_settings['position.Y'] = 0
            self._center = Vector(0.0, 0.0, 0.0)
        engine_settings['position.Z'] = 0

        msg = Cura_pb2.SettingList()
        for key, value in engine_settings.items():
            s = msg.settings.add()
            s.name = key
            s.value = str(value).encode('utf-8')

        self._socket.sendMessage(msg)

    def _sendSettings_normal(self, settings):
        extruder = 0

        # AKA The Dictionary of Doom (tm)
        engine_settings = {
            'extruderNr': extruder,
            'layerThickness': int(settings.getSettingValueByKey('layer_height') * 1000),
            'initialLayerThickness': int(settings.getSettingValueByKey('layer_height_0') * 1000),
            'printTemperature': int(settings.getSettingValueByKey('material_print_temperature')),
            'bedTemperature': int(settings.getSettingValueByKey('material_bed_temperature')),
            'filamentDiameter': int(settings.getSettingValueByKey('material_diameter') * 1000),
            'filamentFlow': int(settings.getSettingValueByKey('material_flow')),
            'layer0extrusionWidth': int(settings.getSettingValueByKey('wall_line_width_0') * 1000),
            'extrusionWidth': int(settings.getSettingValueByKey('wall_line_width_x') * 1000),
            'insetCount': int(settings.getSettingValueByKey('wall_line_count')),
            'downSkinCount': int(settings.getSettingValueByKey('bottom_layers')),
            'upSkinCount': int(settings.getSettingValueByKey('top_layers')),
            'skirtDistance': int(settings.getSettingValueByKey('skirt_gap') * 1000),
            'skirtLineCount': int(settings.getSettingValueByKey('skirt_line_count')),
            'skirtMinLength': int(settings.getSettingValueByKey('skirt_minimal_length') * 1000),

            'retractionAmount': int(settings.getSettingValueByKey('retraction_amount') * 1000),
            'retractionAmountPrime': int(0 * 1000),
            # 'retractionAmountExtruderSwitch': int(fbk('') * 1000),
            'retractionSpeed': int(settings.getSettingValueByKey('retraction_speed')),
            'retractionPrimeSpeed': int(settings.getSettingValueByKey('retraction_speed')),
            'retractionMinimalDistance': int(settings.getSettingValueByKey('retraction_min_travel') * 1000),
            'minimalExtrusionBeforeRetraction': int(settings.getSettingValueByKey('retraction_minimal_extrusion') * 1000),
            'retractionZHop': int(settings.getSettingValueByKey('retraction_hop') * 1000),

            'enableCombing': 1 if settings.getSettingValueByKey('retraction_combing') else 0,
            # 'enableOozeShield': int(fbk('') * 1000),
            # 'wipeTowerSize': int(fbk('') * 1000),
            # 'multiVolumeOverlap': int(fbk('') * 1000),

            'initialSpeedupLayers': int(settings.getSettingValueByKey('speed_slowdown_layers')),
            'initialLayerSpeed': int(settings.getSettingValueByKey('speed_layer_0')),
            'skirtSpeed': int(settings.getSettingValueByKey('skirt_speed')),
            'inset0Speed': int(settings.getSettingValueByKey('speed_wall_0')),
            'insetXSpeed': int(settings.getSettingValueByKey('speed_wall_x')),
            'supportSpeed': int(settings.getSettingValueByKey('speed_support')),
            'moveSpeed': int(settings.getSettingValueByKey('speed_travel')),
            'skinSpeed': int(settings.getSettingValueByKey('speed_topbottom')),

            'infillOverlap': int(settings.getSettingValueByKey('fill_overlap')),
            'infillSpeed': int(settings.getSettingValueByKey('speed_infill')),

            'minimalLayerTime': int(settings.getSettingValueByKey('cool_min_layer_time')),
            'minimalFeedrate': int(settings.getSettingValueByKey('cool_min_speed')),
            'coolHeadLift': 1 if settings.getSettingValueByKey('cool_lift_head') else 0,
            'fanSpeedMin': settings.getSettingValueByKey('cool_fan_speed_min'),
            'fanSpeedMax': settings.getSettingValueByKey('cool_fan_speed_max'),
            'fanFullOnLayerNr': settings.getSettingValueByKey('cool_fan_full_layer'),

            'spiralizeMode': 1 if settings.getSettingValueByKey('magic_spiralize') == 'True' else 0,

        }

        if settings.getSettingValueByKey('top_bottom_pattern') == 'Lines':
            engine_settings['skinPattern'] = 'SKIN_LINES'
        elif settings.getSettingValueByKey('top_bottom_pattern') == 'Concentric':
            engine_settings['skinPattern'] = 'SKIN_CONCENTRIC'

        if settings.getSettingValueByKey('fill_pattern') == 'Grid':
            engine_settings['infillPattern'] = 'INFILL_GRID'
        elif settings.getSettingValueByKey('fill_pattern') == 'Triangles': # TODO add option to fdmPrinter.json once it has been translated(?)
            engine_settings['infillPattern'] = 'INFILL_TRIANGLES'
        elif settings.getSettingValueByKey('fill_pattern') == 'Lines':
            engine_settings['infillPattern'] = 'INFILL_LINES'
        elif settings.getSettingValueByKey('fill_pattern') == 'Concentric':
            engine_settings['infillPattern'] = 'INFILL_CONCENTRIC'
        elif settings.getSettingValueByKey('fill_pattern') == 'ZigZag':
            engine_settings['infillPattern'] = 'INFILL_ZIGZAG'

        adhesion_type = settings.getSettingValueByKey('adhesion_type')
        if adhesion_type == 'Raft':
            engine_settings['raftMargin'] = int(settings.getSettingValueByKey('raft_margin') * 1000)
            engine_settings['raftLineSpacing'] = int(settings.getSettingValueByKey('raft_line_spacing') * 1000)
            engine_settings['raftBaseThickness'] = int(settings.getSettingValueByKey('raft_base_thickness') * 1000)
            engine_settings['raftBaseLinewidth'] = int(settings.getSettingValueByKey('raft_base_linewidth') * 1000)
            engine_settings['raftBaseSpeed'] = int(settings.getSettingValueByKey('raft_base_speed') * 1000)
            engine_settings['raftInterfaceThickness'] = int(settings.getSettingValueByKey('raft_interface_thickness') * 1000)
            engine_settings['raftInterfaceLinewidth'] = int(settings.getSettingValueByKey('raft_interface_linewidth') * 1000)
            engine_settings['raftInterfaceLineSpacing'] = int(settings.getSettingValueByKey('raft_line_spacing') * 1000)
            engine_settings['raftFanSpeed'] = 0
            engine_settings['raftSurfaceThickness'] = int(settings.getSettingValueByKey('layer_height_0') * 1000)
            engine_settings['raftSurfaceLinewidth'] = int(settings.getSettingValueByKey('wall_line_width_x') * 1000)
            engine_settings['raftSurfaceLineSpacing'] = int(settings.getSettingValueByKey('wall_line_width_x') * 1000)
            engine_settings['raftSurfaceLayers'] = int(settings.getSettingValueByKey('raft_surface_layers'))
            engine_settings['raftSurfaceSpeed'] = int(settings.getSettingValueByKey('speed_layer_0') * 1000)
            engine_settings['raftAirGap'] = int(settings.getSettingValueByKey('raft_airgap') * 1000)
            engine_settings['skirtLineCount'] = 0
            pass
        elif adhesion_type == 'Brim':
            engine_settings['skirtDistance'] = 0
            engine_settings['skirtLineCount'] = settings.getSettingValueByKey('brim_line_count')

        if settings.getSettingValueByKey('support_type') == 'None':
            engine_settings['supportType'] = ''
            engine_settings['supportAngle'] = -1
        else:
            engine_settings['supportAngle'] = settings.getSettingValueByKey('support_angle')
            engine_settings['supportOnBuildplateOnly'] = 1 if settings.getSettingValueByKey('support_type') == 'Touching Buildplate' else 0
            engine_settings['supportLineDistance'] = int(100 * settings.getSettingValueByKey('wall_line_width_x') * 1000 / settings.getSettingValueByKey('support_fill_rate'))
            engine_settings['supportXYDistance'] = int(settings.getSettingValueByKey('support_xy_distance') * 1000)
            engine_settings['supportZDistance'] = int(settings.getSettingValueByKey('support_z_distance') * 1000)
            engine_settings['supportZDistanceBottom'] = int(settings.getSettingValueByKey('support_top_distance') * 1000)
            engine_settings['supportZDistanceTop'] = int(settings.getSettingValueByKey('support_bottom_distance') * 1000)
            engine_settings['supportJoinDistance'] = int(settings.getSettingValueByKey('support_join_distance') * 1000)
            engine_settings['supportAreaSmoothing'] = int(settings.getSettingValueByKey('support_area_smoothing') * 1000)
            engine_settings['supportMinimalAreaSqrt'] = int(settings.getSettingValueByKey('support_minimal_diameter') * 1000) if settings.getSettingValueByKey('support_use_towers') else 0
            engine_settings['supportTowerDiameter'] = int(settings.getSettingValueByKey('support_tower_diameter') * 1000)
            engine_settings['supportTowerRoofAngle'] = int(settings.getSettingValueByKey('support_tower_roof_angle'))
            engine_settings['supportConnectZigZags'] = 1 if settings.getSettingValueByKey('support_connect_zigzags') else 0
            engine_settings['supportExtruder'] = -1 #Not yet implemented
            if settings.getSettingValueByKey('support_pattern') == 'Grid':
                engine_settings['supportType'] = 'GRID'
            elif settings.getSettingValueByKey('support_pattern') == 'Lines':
                engine_settings['supportType'] = 'LINES'
            elif settings.getSettingValueByKey('support_pattern') == 'ZigZag':
                engine_settings['supportType'] = 'ZIGZAG'

        engine_settings['sparseInfillLineDistance'] = -1
        if settings.getSettingValueByKey('fill_sparse_density') >= 100:
            engine_settings['sparseInfillLineDistance'] = settings.getSettingValueByKey('wall_line_width_x')
            engine_settings['downSkinCount'] = 10000
            engine_settings['upSkinCount'] = 10000
        elif settings.getSettingValueByKey('fill_sparse_density') > 0:
            engine_settings['sparseInfillLineDistance'] = int(100 * settings.getSettingValueByKey('wall_line_width_x') * 1000 / settings.getSettingValueByKey('fill_sparse_density'))
        engine_settings['sparseInfillCombineCount'] = int(round(settings.getSettingValueByKey('fill_sparse_combine')))

        gcodeFlavor = settings.getSettingValueByKey('machine_gcode_flavor')
        if gcodeFlavor == 'UltiGCode':
            engine_settings['gcodeFlavor'] = "GCODE_FLAVOR_ULTIGCODE"
        elif gcodeFlavor == 'Makerbot':
            engine_settings['gcodeFlavor'] = "GCODE_FLAVOR_MAKERBOT"
        elif gcodeFlavor == 'BFB':
            engine_settings['gcodeFlavor'] = "GCODE_FLAVOR_BFB"
        elif gcodeFlavor == 'Mach3':
            engine_settings['gcodeFlavor'] = "GCODE_FLAVOR_MACH3"
        elif gcodeFlavor == 'Volumetric':
            engine_settings['gcodeFlavor'] = "GCODE_FLAVOR_REPRAP_VOLUMATRIC"
        else:
            engine_settings['gcodeFlavor'] = "GCODE_FLAVOR_REPRAP"

        engine_settings['startCode'] = settings.getSettingValueByKey('machine_start_gcode')
        engine_settings['endCode'] = settings.getSettingValueByKey('machine_end_gcode')

        #for n in range(1, self._machine.getMaxNozzles()):
        n = 1
        engine_settings['extruderOffset1.X'] = int(settings.getSettingValueByKey('machine_nozzle_offset_x_1') * 1000)
        engine_settings['extruderOffset1.Y'] = int(settings.getSettingValueByKey('machine_nozzle_offset_y_1') * 1000)

        if not settings.getSettingValueByKey('machine_center_is_zero'):
            engine_settings['position.X'] = int((settings.getSettingValueByKey('machine_width') / 2.0) * 1000)
            engine_settings['position.Y'] = int((settings.getSettingValueByKey('machine_depth') / 2.0) * 1000)
            self._center = Vector(settings.getSettingValueByKey('machine_width') / 2.0, 0.0, settings.getSettingValueByKey('machine_depth') / 2.0)
        else:
            engine_settings['position.X'] = 0
            engine_settings['position.Y'] = 0
            self._center = Vector(0.0, 0.0, 0.0)
        engine_settings['position.Z'] = 0

        msg = Cura_pb2.SettingList()
        for key, value in engine_settings.items():
            s = msg.settings.add()
            s.name = key
            s.value = str(value).encode('utf-8')

        self._socket.sendMessage(msg)

    def _onBackendConnected(self):
        if self._restart:
            self._onChanged()
            self._restart = False
