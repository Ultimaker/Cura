# UseDrywiseDryer script - Dry your filaments in realtime with minimal effort
# This script is automates the pre-drying process when using the Drywise inline filament dryer in tandem with an Ultimaker
# It runs with the PostProcessingPlugin which is released under the terms of the LGPLv3 or higher.
# This script is licensed under the Creative Commons - Attribution - Share Alike (CC BY-SA) terms
import dataclasses
import enum
import json
import math
import re
from pathlib import Path
import typing
import numpy as np
# Authors of the Drywise plugin / script:
# Written by Edward Borg, edward@thought3d.com

# Uses -
# M104 S<temp> T<0-#toolheads> - set extruder <T> to target temperature <S>
# M140 S<temp> - set bed target temperature
# M109 S<PWM> - set fan speed to target speed <S>
# G04 S<mm> F<mm/m> - set the retract length <S> or feed rate <F>
# M117 - output the current changes

from UM.Application import Application
from UM.Settings.ContainerStack import ContainerStack
from UM.Settings.ContainerFormatError import ContainerFormatError
from UM.Settings.InstanceContainer import InstanceContainer
from UM.Settings.DefinitionContainer import DefinitionContainer
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.SettingDefinition import SettingDefinition
from UM.Math.Vector import Vector
from UM.Math.Quaternion import Quaternion
from UM.Math.AxisAlignedBox import AxisAlignedBox
from UM.Math.Polygon import Polygon
from UM.Scene.SceneNodeDecorator import SceneNodeDecorator

from UM.Scene.SceneNode import SceneNode

from UM.Logger import Logger
from UM.Message import Message
from UM.i18n import i18nCatalog
from cura.Settings.SettingOverrideDecorator import SettingOverrideDecorator
catalog = i18nCatalog("cura")

from cura.Settings.GlobalStack import GlobalStack
from cura.Settings.ExtruderStack import ExtruderStack
from cura.CuraApplication import CuraApplication
from cura.Scene.CuraSceneNode import CuraSceneNode
from cura.Scene.ConvexHullDecorator import ConvexHullDecorator
from cura.Scene.ConvexHullNode import ConvexHullNode


from PyQt6.QtCore import QUrl

from typing import List, Dict
from ..Script import Script

from ..scripts.PurgeCubeNode import PurgeCubeSceneNode, load_purge_cube

from HackedStartSliceJob import apply_hack

class DrywiseException(Exception):
    pass


@dataclasses.dataclass
class LoadFilamentResult:
    result: List[str]
    loaded_filament: float
    total_time: float
    extra_filament_to_purge: float
    extra_filament_to_print_slower: float


@dataclasses.dataclass
class PurgeFilamentResult:
    result: List[str]
    purged_filament: float
    total_time: float


def error_handling_decorator(on_error=None):
    def decor(func):
        def show_cura_log(msg: Message, action: str):
            from UM.Resources import Resources
            import subprocess

            # File path is based on the implementation of `UM.plugins.FileLogger.FileLogger`
            subprocess.Popen(f'explorer "{Resources.getStoragePath(Resources.Resources)}"')
            msg.hide()

        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except DrywiseException as e:
                Message(
                    text=f'UseDrywiseDryer has detected a problem:\n'
                         f'{str(e)}\n'
                         f'Contact the drywise support at drywise@thought3d.com if you need help.',
                    title=catalog.i18nc("@info:title", f"UseDrywiseDryer script"),
                    dismissable=True, lifetime=0, message_type=Message.MessageType.ERROR,
                ).show()
                Logger.logException("e", "Drywise Exception in UseDrywiseScript. An error to be shown to the user")
                if on_error:
                    return on_error(*args, **kwargs)
            except Exception as e:
                msg = Message(
                    text=f'An unexpected error with the UseDrywiseDryer script has occurred. '
                         f'Please, contact the drywise support at drywise@thought3d.com to help resolve this issue. '
                         f'Please, enclose the log from cura. You can access by clicking the button below. ',
                    title=catalog.i18nc("@info:title", f"UseDrywiseDryer script"),
                    dismissable=True, lifetime=0, message_type=Message.MessageType.ERROR,
                )
                msg.addAction(action_id='show_log', name='Open cura log directory', icon='cura-icon.png',
                              description='my_description')
                msg.pyQtActionTriggered.connect(show_cura_log)
                msg.show()
                Logger.logException("e", "Unexpected Exception in UseDrywiseScript.")
                if on_error:
                    return on_error(*args, **kwargs)

        return wrapper
    return decor




class UseDrywiseDryer(Script):
    _id = 0
    def __init__(self):
        super().__init__()
        self.script_id = UseDrywiseDryer._id
        UseDrywiseDryer._id += 1

        # Dist from dryer T (where the filament is just dry) to dryer output (from where the user normally measures
        # the purging dist). This section of the filament is also wet, therefore also needs to be purged
        # It will be directly added to the purging distance.
        # This is equivalent to the length of the filament that needs to be cut during manual operation of the dryer.
        # Yes, this is hardcoded, but this is fine mostly. It's not like the design of the dryer changes everyday
        # So long as it is well documented, this is fine.
        self.dryer_t_to_dryer_output_dist = 50
        # Distance from the tip of the nozzle to the cold area of the hotend. Usually, this area will be filled with
        # plastic, so it is only necessary to load till this dist
        # TODO: I think that cura defines this setting for printers. Should use that instead of hard-coded value.
        self.nozzle_heating_dist = 15
        # The filament in the dryer has to move at the minimum speed defined below so that it does not go into
        # idle mode. By default, the filament has to move 50mm every 5 mins
        self.punc_speed = 55 / (5 * 60)
        # When the dryer goes into printing mode, the filament does not need to start moving immediately. Instead, it
        # dries for 20 min regardless of whether the filament moves or not. At the end of the 20 mins it can go into
        # idle mode if the filament did not move 50 mm in the past 5 mins
        self.punctuation_move_start = (20.0 - 5.0) * 60

        app = CuraApplication.getInstance()
        # All of these signals fire twice for some reason.
        extruder_manager = app.getExtruderManager()

        # Signals when switching the tab of the extruder at the top (material selection)
        # Signals when switching the tab of th extruder at the settings screen
        # extruder_manager.activeExtruderChanged.connect(self.load_cube)
        # # Signals on adding an object
        # # Signals when selecting an object
        # # Signals when deselecting an object
        # # Signals when selecting which extruder should print the object
        # extruder_manager.selectedObjectExtrudersChanged.connect(
        #     lambda: Message('Selected object extruder changed', title=catalog.i18nc("@info:title", "Post Processing")).show())

        # # signals on enable/disabled extruder
        # extruder_manager.extrudersChanged.connect(self.on_extruders_changed)

        self.purge_cube_node: PurgeCubeSceneNode | None = None


        # # Signals when any node undergoes any change. ANY CHANGE, including selecting, deselecting, rotating camera etc.
        # app.getController().getScene().sceneChanged.connect(self.on_scene_changed)
        # # Signals when the file loading is completed (i.e. node added)
        # app.on_file_completed.connect()

        # Remove self from the script list of PostProcessingPlugin
        from UM.PluginRegistry import PluginRegistry
        if (registry := PluginRegistry.getInstance()) is None:
            return
        from ..PostProcessingPlugin import PostProcessingPlugin
        if 'PostProcessingPlugin' not in registry.getActivePlugins():
            return
        self.ppp = typing.cast(PostProcessingPlugin, registry.getPluginObject('PostProcessingPlugin'))

    # def on_extruders_changed(self):
    #     """ Update the Drywise connected extruder when an extruder is enabled/disabled
    #
    #     The policy is as follows:
    #     1. If there is a single extruder enabled, then switch to that extruder
    #     2. Otherwise, do nothing.
    #
    #     We will show the error later if the selected extruder is not enabled. This is done to be as little disruptive
    #     as possible.
    #     """
    #     extruder_manager = CuraApplication.getInstance().getExtruderManager()
    #
    #     idxs_enabled = [i for i, extruder in enumerate(extruder_manager.getActiveExtruderStacks()) if extruder.isEnabled]
    #     if len(idxs_enabled) != 1:
    #         return
    #
    #     # Change extruder value if
    #     idx_enabled_extruder = idxs_enabled[0]
    #     idx_current_extruder = self.getSettingValueByKey('extruder_used')
    #     if idx_current_extruder == idx_enabled_extruder:
    #         return
    #
    #     self._instance.setProperty('extruder_used', 'value', idx_enabled_extruder)
    #
    #     def revert_change(msg: Message, action: str, old_extruder_value: int):
    #         if action != 'undo_extruder':
    #             return
    #
    #         self._instance.setProperty('extruder_used', 'value', old_extruder_value)
    #
    #         msg.hide()
    #         Message(
    #             text=f'Extruder used is changed back to Extruder {old_extruder_value}',
    #             title=catalog.i18nc("@info:title", f"UseDrywiseDryer script"),
    #             dismissable=True, lifetime=3, message_type=Message.MessageType.POSITIVE,
    #         ).show()
    #
    #     msg = Message(
    #         text=f'Drywise connected extruder was changed to "Extruder {idx_enabled_extruder + 1}", because '
    #              f'it is the only enabled extruder.',
    #         title=catalog.i18nc("@info:title", f"UseDrywiseDryer script"),
    #         dismissable=True, lifetime=10
    #     )
    #     msg.addAction(action_id='undo_extruder', name='Undo change', icon='cura-icon.png', description='my_description')
    #     msg.pyQtActionTriggered.connect(lambda *args, ext=idx_current_extruder: revert_change(*args, ext))
    #     msg.show()

    def set_setting_value(self, key: str, value: typing.Any, property_name: str = 'value'):
        self._instance.setProperty(key, property_name, value)

    def on_extruder_change(self):
        """ Called when the node's extruder is changed and updates the scripts `extruder_used` parameter """
        if (app := CuraApplication.getInstance()) is None:
            return
        if (global_stack := app.getGlobalContainerStack()) is None:
            return

        try:
            printing_extruder_idx = global_stack.extruderList.index(self.purge_cube_node.getPrintingExtruder())
        except ValueError:
            return  # Extruder not defined for some reason... Silently fail.

        if printing_extruder_idx != int(self.getSettingValueByKey('extruder_used')):
            self.set_setting_value('extruder_used', printing_extruder_idx)

    @error_handling_decorator()
    def load_purge_cube_node(self, path: str = 'cube.stl'):
        # For whatever reason, often the script gets initialized before the build volume. As a result, trying to
        # add the node to the non-existent build volume fails silently (See CurApplication._readMeshFinished).
        # So, what we do is we just try again a bit later.
        if (app := CuraApplication.getInstance()) is None or app.getBuildVolume() is None:
            from PyQt6.QtCore import QTimer
            self._timer = QTimer()
            self._timer.setInterval(1000)
            self._timer.setSingleShot(True)
            self._timer.timeout.connect(lambda p=path: self.load_purge_cube_node(p))
            self._timer.start()
            return

        node_name = f'drywise_purge_box_{self.script_id}'
        # No need to iterate deeply, the purge cube node is always at the first level.
        for node in app.getController().getScene().getRoot().getChildren():
            if isinstance(node, PurgeCubeSceneNode) and node.getName() == node_name:
                self.purge_cube_node = node
                break
        else:
            self.purge_cube_node = load_purge_cube(path='cube.stl', node_name=node_name)
            if self.purge_cube_node is None:
                raise FileNotFoundError

        self.purge_cube_node.drywise_script = self

        self.purge_cube_node.getDecorator(SettingOverrideDecorator).activeExtruderChanged.connect(self.on_extruder_change)
        root_node = app.getController().getScene().getRoot()
        #root_node.childrenChanged.connect(self.verify_if_still_exists)

        # Update the cube size and volume
        self.on_script_setting_change(force=True)
        # Set initial position of the cube on the buildplate
        self.purge_cube_node.place_and_resize_at(
            pos=self.getSettingValueByKey('cube_position'),
            bed_offset=float(self.getSettingValueByKey('bed_edge_offset'))
        )

        # Apply object-level slicing settings to the purge cube node
        # All settings that are commensted out would be nice to haves, but are not settable per mesh (sadly).

        # These settings are set in order to improve adhesion in case the loading dist is underestimated
        self.purge_cube_node.set_setting('line_width', '=1.1 * (machine_nozzle_size + layer_height)')
        # self.purge_cube_node.set_setting('layer_height_0', '=0.75 * machine_nozzle_size')
        # These settings are set to ensure that the cube is printed more or less consistently
        self.purge_cube_node.set_setting('infill_sparse_density', 100)
        self.purge_cube_node.set_setting('infill_pattern', 'lines')
        # Not super important, but nice to improve consistency
        self.purge_cube_node.set_setting('wall_line_count', 2)
        self.purge_cube_node.set_setting('skin_outline_count', 0)
        self.purge_cube_node.set_setting('infill_wall_line_count', 0)
        # Set a bit lower to preserve accuracy in amount of purging material, but not to make the cube look like trash
        self.purge_cube_node.set_setting('infill_overlap', 5)
        self.purge_cube_node.set_setting('skin_overlap', 5)
        # These settings are set preventatively to avoid unusual behaviour. Probably not very important.
        self.purge_cube_node.set_setting('material_flow', 100)
        self.purge_cube_node.set_setting('xy_offset', 0.0)
        self.purge_cube_node.set_setting('magic_fuzzy_skin_enabled', False)
        # self.purge_cube_node.set_setting('magic_spiralize', 'False')
        self.purge_cube_node.set_setting('ironing_enabled', False)
        self.purge_cube_node.set_setting('support_enable', False)
        self.purge_cube_node.set_setting('mold_enabled', False)
        self.purge_cube_node.set_setting('magic_mesh_surface_mode', 'normal')
        self.ppp.scriptListChanged.connect(self.on_script_list_change)

        apply_hack()

    def on_script_setting_change(self, key: str = None, property_name: str = 'value', force: bool = False):
        """ Called when any of the script settings are changed """
        if property_name != 'value' or self.purge_cube_node is None:
            return

        if key == 'extruder_used' or force:
            if (app := CuraApplication.getInstance()) is None:
                return
            if (global_stack := app.getGlobalContainerStack()) is None:
                return

            current_extruder = self.purge_cube_node.getPrintingExtruder()
            changed_extruder = global_stack.extruderList[int(self.getSettingValueByKey('extruder_used'))]
            if current_extruder.getId() != changed_extruder.getId():
                self.purge_cube_node.callDecoration('setActiveExtruder', changed_extruder.getId())
        if key in ['max_cube_height', 'min_cube_xy_bounds'] or force:
            if (app := CuraApplication.getInstance()) is not None:
                if (stack := app.getGlobalContainerStack()) is not None:
                    height = float(self.getSettingValueByKey('max_cube_height'))
                    min_width = float(self.getSettingValueByKey('min_cube_xy_bounds'))
                    self.purge_cube_node.size_bounds = np.array([
                        np.array([min_width, 0.2, min_width]),
                        np.array([
                            float(stack.getProperty('machine_width', 'value')),
                            height,
                            float(stack.getProperty('machine_depth', 'value')),
                        ])
                    ])
                    self.purge_cube_node.z_height = height

        # Always update the cube volume.
        self.purge_cube_node.volume = self.eval_purge_volume()

        # The default method of the Script. Just reset the slicing state, making the user reslice the models
        self._onPropertyChanged(key, property_name)

    def eval_purge_volume(self, load_rsp: LoadFilamentResult = None):
        extrude_length = float(self.getSettingValueByKey("filament_length"))
        extruder_idx = int(self.getSettingValueByKey("extruder_used"))

        app = CuraApplication.getInstance()
        mycura = app.getGlobalContainerStack()
        if mycura is None:
            raise RuntimeError('No global container stack')
        assert isinstance(mycura, GlobalStack)
        extruder = mycura.extruderList[extruder_idx]
        assert isinstance(extruder, ExtruderStack)

        material_diameter = float(extruder.getProperty('material_diameter', 'value'))

        if load_rsp is None:
            load_length = float(self.getSettingValueByKey("bowden_length"))
            static_drying_time = float(self.getSettingValueByKey('static_drying_time')) * 60
            printer_prepare_time = float(self.getSettingValueByKey('printer_prepare_time')) * 60
            bottom_print_speed = float(mycura.getProperty('speed_topbottom', 'value'))
            model_layer_height = float(mycura.getProperty('layer_height', 'value'))
            model_line_width = float(mycura.getProperty('line_width', 'value'))

            # To ensure that the filament is loaded at appropriate printing flowrate
            load_speed = (bottom_print_speed * model_layer_height * model_line_width) / (
                        math.pi * material_diameter ** 2 / 4)
            load_rsp = continuous_load_filament(
                total_extruder_dist=max(0.0, load_length - self.nozzle_heating_dist),
                static_cycle_time=static_drying_time - printer_prepare_time,
                punctuation_move_start=max(0.0, (20 - 5) * 60 - printer_prepare_time),
                continuous_extruder_speed=load_speed, punc_speed=55 / (5.0 * 60),
            )

        extra_filament = load_rsp.extra_filament_to_purge + load_rsp.extra_filament_to_print_slower
        length = extrude_length + extra_filament + self.dryer_t_to_dryer_output_dist
        return length * math.pi / 4 * material_diameter ** 2

    def initialize(self) -> None:
        """ Initializes the drywise script. Overridden from the base class

        Overridden from the base function, in order to:
        1. Allow the script to store values for the printer even if it is removed from the script list
        2. Allow the script to modify the default setting values stored within the `DefinitionContainer`
        for each printer

        """

        registry = typing.cast(ContainerRegistry, ContainerRegistry.getInstance())

        app = CuraApplication.getInstance()
        if app is None:
            return
        mycura = app.getGlobalContainerStack()
        if mycura is None:
            return

        machine_name = mycura.getProperty('machine_name', 'value')

        # When the script is initialized for the first time in this session, registry does not contain any
        # stacks or definitions. Thus, we will need to create them.
        # For subsequent cript initializations (e.g. change printer, remove script from list), the stack, definition
        # and instance remain the same, so we just find them again.
        stacks = registry.findContainerStacks(id=f'UseDrywiseDryerContainerStack_{machine_name}')
        if stacks:
            # Contains the setting definitions and instances. Allows accessing setting values.
            self._stack = stacks[0]
            # Definition contains the setting metadata. Basically, it contains everything about the setting except the
            # current setting value. Somewhat makes sense, since there should be multiple setting values stored
            # for every machine, profile and material.
            self._definition = self._stack.findContainer(id=f'UseDrywiseDryerDefinitionContainer_{machine_name}')
            # Instance allows accessing the settings values. Interestingly, the actual values are stored elsewhere so
            # that when the printer changes, the setting values are reassigned accordingly. So we do not need to change
            # the instance in this case, just reuse the old one. nice that we do not need to worry about that.
            self._instance = self._stack.findContainer(id=f'UseDrywiseDryerInstanceContainer_{machine_name}')
        else:
            self._stack = ContainerStack(stack_id=f'UseDrywiseDryerContainerStack_{machine_name}')
            registry.addContainer(self._stack)

            self._definition = DefinitionContainer(f'UseDrywiseDryerDefinitionContainer_{machine_name}')
            self._definition.deserialize(json.dumps(self.getSettingData()))
            # The definition must be added to registry or else no setting fields will be displayed
            registry.addContainer(self._definition)
            self._stack.addContainer(self._definition)

            self._instance = InstanceContainer(f"UseDrywiseDryerInstanceContainer_{machine_name}")
            self._instance.setDefinition(self._definition.getId())
            self._instance.setMetaDataEntry(
                "setting_version",
                self._definition.getMetaDataEntry("setting_version", default=0)
            )
            # Adding just to stack instead of to registry since `cura.Settings.CuraContainerRegistry.addContainer`
            # Raises the following error "Instance container ScriptInstanceContainer is outdated. Its setting
            # version is 0 but it should be 23". Something to do with compatibility of settings with the previous
            # versions. Do not want to muck around these waters for the time being.
            self._stack.addContainer(self._instance)
            self._instance.setDefinition(self._definition.getId())

        self._stack.propertyChanged.connect(self.on_script_setting_change)
        # Monitor if this script instance was removed from script list
        self.load_purge_cube_node()

    def getSettingData(self) -> Dict:
        mycura = Application.getInstance().getGlobalContainerStack()
        if mycura is None:
            raise RuntimeError('No global container stack')
        assert isinstance(mycura, GlobalStack)

        n_extruders = len(mycura.extruderList)

        bb_bed = [
            float(0.0),
            float(0.0),
            float(mycura.getProperty('machine_width', 'value')),
            float(mycura.getProperty('machine_depth', 'value')),
        ]
        bed_size = (bb_bed[2] - bb_bed[0], bb_bed[3] - bb_bed[1])
        bb_bed = [0.025 * bed_size[0], 0.025 * bed_size[1], 0.975 * bed_size[0], 0.975 * bed_size[1]]

        um_default = {'bowden_length': 810, 'filament_length': 330, "printer_prepare_time": 8.0, "bed_edge_offset": 10.0}
        cre_default = {'bowden_length': 40, 'filament_length': 820}
        default_settings = {
            **{k: um_default for k in ['Ultimaker 3', 'Ultimaker S5', 'Ultimaker S6', 'Ultimaker S7', 'Ultimaker S8']},
            'Ultimaker S3': {'bowden_length': 650, 'filament_length': 330, "printer_prepare_time": 8.0, "bed_edge_offset": 10.0},
            'Creality Ender-3 S1 Pro': cre_default,
        }

        data = {
            "name": "Use Drywise Dryer",
            "key": f"UseDrywiseDryer",
            "metadata": {},
            "version": 2,
            "settings": {
                "extruder_used": {
                    "label": "Extruder in Use",
                    "description": "Select the extruder to which the Drywise and the dried filament are connected for printing.",
                    "type": "extruder",
                },
                "bowden_length": {
                    "label": "Distance from extruder to nozzle",
                    "description": "The length of the tube fromt he extruder to the nozzle",
                    "default_value": "-1",
                    "type": "float",
                    "unit": "mm",
                },
                "filament_length": {
                    "label": "Distance from dryer output to extruder",
                    "description": "The length from Drywise output to the extruder of the printer",
                    "default_value": "-1",
                    "type": "float",
                    "unit": "mm",
                },
                "advanced": {
                    'label': "Show advanced parameters",
                    "description": "The length from Drywise output to the extruder of the printer",
                    "default_value": "false",
                    "type": "bool",
                },
                "cube_position": {
                    "label": "Position of the purge cube",
                    "description": "The location of the purge cube on the buildplate.",
                    "type": "enum",
                    "options": {
                        "left": "Left",
                        "right": "Right",
                        "top": "Top",
                        "bottom": "Bottom"
                    },
                    "default_value": "left",
                    "enabled": "advanced",
                },
                'max_cube_height': {
                    "label": "The maximum height of the cube",
                    "description": "See Issue #1 on the GitHub page of the script. No, seriously, do read through the issue before modifying this value.",
                    "type": "float",
                    "default_value": "1.5",
                    "unit": "mm",
                    "enabled": "advanced",
                },
                "min_cube_xy_bounds": {
                    "label": "The minimum length and/or width of the cube",
                    "description": "This is useful for two thing:\n1.The purge cube is not made too thin, which should improve the adhesion. After all, if the cube detaches, then the print will fail.\n2. During resizing of the cube in the cura UI, you might accidentally make it extremely small, so it becomes effectively a place. This is annoying, but I also had incidents when cura crashed or was bugged (e.g. the scaling arrows no longer appeared for other models). 10mm is a sensible default, I think.",
                    "type": "float",
                    "default_value": '10.0',
                    "unit": "mm",
                    "enabled": "advanced",
                },
                "bed_edge_offset": {
                    "label": "Distance of the purge cube from buildplate edge",
                    "description": "Defines the minimum distance of the purge cube from the buildplate edge.",
                    "type": "float",
                    "default_value": '5.0',
                    "unit": "mm",
                    "enabled": "advanced",
                },
                "static_drying_time": {
                    "label": "Drying time",
                    "description": "The static drying time for this material",
                    "type": "float",
                    "default_value": "30.0",
                    'unit': 'min',
                    "enabled": "advanced",
                },
                "printer_prepare_time": {
                    "label": "Printer prepare time",
                    "description": "Some printers (like Ultimaker printers) do some preparation before executing the gcode. This preparation is not controlled by the gcode itself, and therefore cannot be subverted. By default, the loading procedure assumes that there is no preparation for the printer. If there is preparation, then the timing will be incorrect and the dryer may go into idle mode during loading phase. This parameter allows taking into account the preparation time to correct the timing of the loading gcode.",
                    "type": "float",
                    "default_value": "0.5",
                    'unit': 'min',
                    "enabled": "advanced",
                },
                "loading_temperature": {
                    "label": "Loading temperature",
                    "description": "The temperature of the nozzle during loading. Probably all printers will not allow extrusion if the nozzle temperature is too low. However this value depends on the printer. From testing, UM printers allow extrusion even at 100C, Ender 3 allows extrusion at 140C, R3D N2 allow extrusion at 180C. Keeping the nozzle temperature low makes sense during loading in order to not accidentally decompose the material inside the nozzle, leading to a complete/partial clog. That said, if the temperature is low and the filament reaches the nozzle too early, then the extruder may start skipping steps and grinding the filament. In some severe cases, the filament might even buckle in the cold end. Make sure to set the loading distance appropriate to avoid the aforementioned problems.",
                    "type": "float",
                    "default_value": "140.0",
                    'unit': '°C',
                    "enabled": "advanced",
                },
                "min_purging_temperature": {
                    "label": "Purging temperature",
                    "description": "If the printer was loaded with a high temperature material (e.g. PAHT) and you print using the script with a low temperature material (e.g. PLA), the low temperature material will not be able to extrude because the high temperature material will not melt. This will lead to a jam, which in the best case scenario will result in a failed print and in the worst a very problematic nozzle clog and ground dust in the extruder.\nThis parameter aims to mitigate this issue. When the purge cube starts printing, the nozzle will preheat to this temperature (or the material temperature, which ever is higher). After 200 mm of purged material, the temperature will drop back to the material temperature.",
                    "type": "float",
                    "default_value": "260.0",
                    'unit': '°C',
                    "enabled": "advanced",
                },
                "verbose": {
                    "label": "Verbose",
                    "description": "Used for debugging",
                    "type": "bool",
                    "default_value": "False",
                    "enabled": "advanced",
                }
            }
        }

        machine_name = mycura.getProperty('machine_name', 'value')
        for k, v in default_settings.get(machine_name, dict()).items():
            data['settings'][k]['default_value'] = str(v)
        return data

    @error_handling_decorator(on_error=lambda self, data: data)
    def execute(self, data: List[str]) -> List[str]:
        """ Purges wet material until the dry material from Drywise emerges

        Parameters
        ----------
        data : list of str
            The gcode sliced. It is quite interesting that `data` is not a list of singular gcode commands,
            but rather a list of concatenated string that contain the gcode commands for each layer:
            0. The header that contains some basic info about cura version and printing settings
            1. Prep gcode that heats up the nozzle and does bed leveling
            2. First layer gcode. Always starts with the substring ';LAYER:0\n'
            n. Layer gcode. Always starts with the substring ';LAYER:{n-2}\n'
            len(data)-2: Appears to contain a single gcode command prompting the retraction just after printing
            len(data)-1: End of printing commands. Switch off heaters, fans, steppers.

        Returns
        -------
        The processed gcode
        """

        verbose = bool(self.getSettingValueByKey('verbose'))
        extruder_idx = int(self.getSettingValueByKey("extruder_used"))
        load_length = float(self.getSettingValueByKey("bowden_length"))
        static_drying_time = float(self.getSettingValueByKey('static_drying_time')) * 60
        printer_prepare_time = float(self.getSettingValueByKey('printer_prepare_time')) * 60
        min_purging_temperature = float(self.getSettingValueByKey('min_purging_temperature'))
        loading_temperature = float(self.getSettingValueByKey('loading_temperature'))

        if (app := CuraApplication.getInstance()) is None:
            raise RuntimeError("No cura app")
        elif (global_stack := app.getGlobalContainerStack()) is None:
            raise RuntimeError("No global stack")
        elif (extruder := self.purge_cube_node.getPrintingExtruder()) is None:
            raise RuntimeError("No extruder")

        if not extruder.isEnabled:
            raise DrywiseException(
                "The extruder selected for the purge cube is not enabled. Please, enable the extruder, or change the"
                "purge cube extruder to another extruder."
            )

        material_diameter = float(extruder.getProperty('material_diameter', 'value'))
        nozzle_temperature = float(extruder.getProperty('material_print_temperature', 'value'))
        bed_temperature = float(global_stack.getProperty('material_bed_temperature', 'value'))
        inner_wall_speed = float(global_stack.getProperty('speed_wall_x', 'value'))
        model_layer_height = float(global_stack.getProperty('layer_height', 'value'))
        model_line_width = float(global_stack.getProperty('line_width', 'value'))

        build_volume = (
            float(global_stack.getProperty('machine_width', 'value')),
            float(global_stack.getProperty('machine_depth', 'value')),
            float(global_stack.getProperty('machine_height', 'value'))
        )

        gantry_height = float(global_stack.getProperty('gantry_height', 'value'))

        # The filament is to be loaded roughly at the flowrate of the printer. Using the inner wall speed as it is
        # usually more indicative of the average flowrate during printing, since more often than not most time is
        # spent printing inner wall. top and bottom speed are also good candidates, but I think that these speeds
        # are usually somewhat lower than the inner wall speeds, so overall they might underestimate the
        # average flowrate during printing.
        load_speed = (inner_wall_speed * model_layer_height * model_line_width) / (math.pi * material_diameter ** 2 / 4)
        load_rsp = continuous_load_filament(
            total_extruder_dist=max(0.0, load_length - self.nozzle_heating_dist),
            static_cycle_time=max(0.0, static_drying_time - printer_prepare_time),
            continuous_extruder_speed=load_speed,
            punctuation_move_start=max(0.0, self.punctuation_move_start - printer_prepare_time),
            punc_speed=self.punc_speed,
        )

        # Insert preheating
        purging_temperature = max(min_purging_temperature, nozzle_temperature)
        loading_analyser = SimpleGcodeAnalyser(load_rsp.result)
        loading_analyser.insert_at([f'M104 S{purging_temperature} ;Preheat the nozzle to purging temperature'], t=-1.0 * 60.0)
        loading_analyser.insert_at([f'M140 S{bed_temperature} ;Preheat the bed'], t=-15.0 * 60.0)

        # Decorate the loading gcode
        load_gcode = '\n'.join([
            '',
            '; .:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:.',
            '; Drywise loading started!',
            'G28',
            f'T{extruder_idx}',
            'M82 ;absolute extrusion mode',
            'M140 S0 ;Switch off the bed heater',
            f"M104 S{loading_temperature} ;Heat up the nozzle just a bit so that the printer does not block extrusion",
            ";Approach loading position",
            f'G0 F900 Z{gantry_height}',
            f'G0 F3000 X{build_volume[0]/2} Y{build_volume[1]/2}',
            'G92 E0 ;Reset extruder value',
            *loading_analyser.gcode,
            'G92 E0 ;Reset extruder value',
            '; Drywise loading completed!',
            '; .:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:.',
            '\n',
        ])

        # Purge cube gcode generated by cura requires some modifications. In particular:
        # - The purging temperature is different from the nozzle temperature
        # - The total volume extruded needs to be checked. If it is too small for some reason, increase the flowrate
        #   to a limited extent
        # - If the loading dist is too small, some filament has to be printed slower than usual.
        purge_cube_gcode, (lb_purge, ub_purge) = self.extract_purge_cube_gcode(data)

        analyser = SimpleGcodeAnalyser(purge_cube_gcode)
        analyser.insert_at([f'M104 S{nozzle_temperature} ;Approach to normal printing nozzle temperature. Modified by UseDrywiseDryer script'], e=150)
        if load_rsp.extra_filament_to_print_slower > 0:
            slow_speed = (self.punc_speed * math.pi * material_diameter ** 2 / 4) / (model_line_width * model_layer_height)
            idx = np.searchsorted(analyser.data[:, 6], load_rsp.extra_filament_to_print_slower)
            analyser.data[:idx, 0] = np.where(analyser.delta[:idx, 6] > 0, slow_speed, analyser.data[:idx, 0])

        expected_volume = self.eval_purge_volume(load_rsp=load_rsp)
        actual_volume = analyser.data[-1, 6] * (math.pi * material_diameter ** 2 / 4)

        diff = 1 - actual_volume / expected_volume
        if abs(diff) > 0.05:
            print('Thats some deviation')

        # Decorate and reconstruct the purging cube gcode
        purge_cube_gcode = [
            '',
            '; .:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:.',
            '; Drywise purge cube printing started!',
            f"M109 S{purging_temperature}  ; Ensure purging temperature",
            *analyser.gcode,
            f"M109 S{nozzle_temperature}  ; Ensure normal printing temperature",
            '; Drywise purge cube printing completed!',
            '; .:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:._.:*~*:.',
            '\n',
        ]
        purge_cube_layers = "\n".join(purge_cube_gcode).split(';DRYWISE_LAYER_SPLIT\n')

        return [
            data[0],  # The header defining the slicing software and the settings used.
            load_gcode,  # Loading gcode. Should be executed before prep gcode to prevent unnecessary heating/cooling.
            *data[1:lb_purge],  # Printer prep gcode. Includes heating, bed leveling and printing purge line/blob.
            *purge_cube_layers,  # Modified purge cube gcode.
            *data[ub_purge:]  # Model printing gcode.
        ]

    def extract_purge_cube_gcode(self, data: List[str]) -> typing.Tuple[List[str], typing.Tuple[int, int]]:
        purge_cube_name = self.purge_cube_node.getName()

        # The purge cube is always printed in "one-at-a-time" mode, distinct from other models that can be printed
        # in whatever mode they like. Also, it is also _always_ printed first.
        # Ideally, this will allow us to find the gcode that prints the purge cube
        try:
            idx_purge_cube_start = 2
            while re.search(f';MESH:{self.purge_cube_node.getName()}', data[idx_purge_cube_start]) is None:
                idx_purge_cube_start += 1

            idx_purge_cube_end = idx_purge_cube_start
            while re.search(f';MESH:{self.purge_cube_node.getName()}', data[idx_purge_cube_end]) is not None:
                idx_purge_cube_end += 1
            idx_purge_cube_end += 1
        except Exception:
            raise DrywiseException(f'No {purge_cube_name} mesh was found in the gcode. How strange!')

        purge_cube_gcode = list()
        for layer in data[idx_purge_cube_start:idx_purge_cube_end]:
            purge_cube_gcode.extend(layer.split("\n"))
            purge_cube_gcode.append(';DRYWISE_LAYER_SPLIT')
        purge_cube_gcode.pop()

        return purge_cube_gcode, (idx_purge_cube_start, idx_purge_cube_end)

    # def remove_self_from_script_list(self):
    #     """ Mainly used to get rid of the script when the purge cube model is deleted by the user """
    #     from UM.PluginRegistry import PluginRegistry
    #
    #     if (registry := PluginRegistry.getInstance()) is None:
    #         raise RuntimeError(
    #             'Could not remove self from the PostProcessingPlugin script list since the '
    #             'PluginRegistry does not exist'
    #         )
    #
    #     from ..PostProcessingPlugin import PostProcessingPlugin
    #     ppp = registry.getPluginObject('PostProcessingPlugin')
    #     if not isinstance(ppp, PostProcessingPlugin):
    #         raise RuntimeError(f"{ppp} is not the PostProcessingPlugin")
    #
    #     key = self.getSettingData()['key']
    #     try:
    #         self_index = ppp.scriptList.index(key)
    #     except ValueError:
    #         raise RuntimeError(f"{key} is not in the script list of the PostProcessingPlugin")
    #     ppp.removeScriptByIndex(self_index)

    def on_script_list_change(self):
        for scr in self.ppp._script_list:
            if self == scr:
                # This script instance is still loaded, so we do nothing
                return

        Logger.info(f"User has removed {self} from `scriptList` of the PostProcessingPlugin")
        self.unload()

    def unload(self):
        """ Unloads this script instance and associated purge cube scene node """

        if self.purge_cube_node is not None:
            if (app := CuraApplication.getInstance()) is None:
                return
            root_node = app.getController().getScene().getRoot()
            for child in root_node.getChildren():
                if child is self.purge_cube_node:
                    root_node.removeChild(child)  # Remove reference to the purge cube in the root node.
                    break
            Logger.debug(f'All references to the associated purge cube {self.purge_cube_node} have been removed')
            self.purge_cube_node = None

        for i, scr in enumerate(self.ppp._script_list):
            if self == scr:
                self.ppp.removeScriptByIndex(i)
        Logger.info(f'Removed {self} from the script list of the PostProcessingPlugin')

    def __eq__(self, other : Script):
        return isinstance(other, UseDrywiseDryer) and other.script_id == self.script_id

    def __del__(self):
        Logger.debug(f'{self} has been garbage collected.')

    def __repr__(self):
        return f'{self.__class__.__name__}(id={self.script_id}, extruder={self.getSettingValueByKey("extruder_used")})'





def continuous_load_filament(
    total_extruder_dist: float, static_cycle_time: float, continuous_extruder_speed: float,
    punc_speed: float = 75 / (5 * 60), punctuation_move_start: float = 15 * 60,
    single_extrude_max_length: float = 25.0
) -> LoadFilamentResult:
    """ Loads the material in the printer, while allowing the drywise to dry the filament

    Basically, the filament loading is done in two stages:
    1. Static cycle. During this time the dryer is drying the first portion of the material. As a result,
    the printer does not move the material except just enough to ensure that the dryer does not stop
    drying because it detected that "Filament stopped moving"
    2. Dynamic cycle. Once the first portion is done, the material is continuously loaded into the printer
    roughly at the printing speed as if the printer is printing. In reality, the printer is stationary and
    cool, while the filament has not yet reached the nozzle. As soon as the filament reaches the nozzle,
    the dynamic cycle is supposed to stop.

    Note: There is no way to really know if the filament has reached the nozzle. We give it to the users to
    accurately measure the necessary filament length that needs to be extruded. If the filament reaches the
    nozzle too early, then either:
    1. The filament gets ground and the extruder will not be able to properly extrude the filament once the
    printing stage starts.
    2. The filament manages to extrude through the nozzle and there will be a mess on the buildplate, which
    may ruin the subsequent print.

    Parameters
    ----------
    total_extruder_dist : float
        The length of the filament that needs to be extruded. It is defines as the length of the ptfe tube
        from extruder gear to the nozzle. It is up to the user to measure the length correctly. See
        discussion in the definition of this function.
    static_cycle_time : float
        The length of the static cycle. Important for determination of how long the filament needs to be loaded
        at reduced punctuating speed
    continuous_extruder_speed : float
        The extruder speed. Has to be low enough for the material to dry properly in the dryer. Ideally, it is the
        rough speed at which the printer is going to print.
    punctuated_dist : float; default: 75 mm
        The minimum length of the filament that needs to be extruded regularly in order to prevent the dryer
        from switching off.
    punctuated_time : float; default: 300 seconds
        How often does the punctuated extrusion has to happen
    punctuation_move_start : float; default: 15*60 seconds
        Make printer wait without loading any filament for the specified time. Useful because the dryer remains
        on for the first 20 minutes even when there is no filament movement. We can take advantage
        of that, since we will not need to do any punctuating movement for the first 15 mins or so, reducing the
        amount of filament purged
    single_extrude_max_length : float; default: 25 mm
        In principle, loading can happen in 2 commands: 1 to do puntuated loading and 1 to do contious loading
        It is better to break up those commands:
         - To allow the user cancel printing.
         - To show status messages when `verbose=True`
        This parameter breaks the loading commands s.t. each command loads at most `single_extrude_max_length` length
        of filament


    Returns
    -------
    list of str
        The resulting gcode loads the material into the dryer.
    """

    ans = []
    e_value, t = 0.0, 0.0
    # The punctuation distance needed for the static cycle
    ideal_punc_dist = punc_speed * (static_cycle_time - punctuation_move_start)
    # If the loading distance is too small (mainly for direct drives), the punctuation distance will be smaller
    # than ideal. The remaining punctuation distance will need to be purged later in the purge cube
    actual_punc_dist = min(ideal_punc_dist, total_extruder_dist)
    # Expected time necessary to load the filament
    t_total_exp = (punctuation_move_start + actual_punc_dist / punc_speed +
                   (total_extruder_dist - actual_punc_dist) / continuous_extruder_speed)

    ans.append(f'M117 Drywise loading started!')

    # Initial wait. Punctuated moves not necessary since the dryer will be active for the first 20 mins
    while t < punctuation_move_start:
        # All this is just to provide the M117 messages. The printer should work fine even with a G4 command
        t += (dt := max(0.0, min(punctuation_move_start - t, 60.0)))
        ans.append(f'M117 Static cycle: e={e_value:.1f} mm, t={t/60:.1f} min, progress={100.0 * t / t_total_exp:.1f}%')
        ans.append(f'G4 S{dt:.3f}')

    for speed, abs_dist in [[punc_speed, actual_punc_dist], [continuous_extruder_speed, total_extruder_dist]]:
        # Loading the filament
        while (rem_dist := abs_dist - e_value) > 0:
            e_value += (de := min(single_extrude_max_length, rem_dist))
            t += de / speed
            ans.append(f'M117 Static cycle: e={e_value:.1f} mm, t={t/60:.1f} min, progress={100.0 * t / t_total_exp:.1f}%')
            ans.append(f'G1 F{speed * 60:.3f} E{e_value:.3f}')

    assert math.isclose(t, t_total_exp), \
        f"The expected time does not correspond to the total time taken. {t=}, {t_total_exp=}."
    assert math.isclose(e_value, total_extruder_dist), \
        f"The expected extruded value is not equal to the actual extruded value. {e_value=}, {total_extruder_dist=}."

    rem_punc_dist = max(0.0, ideal_punc_dist - actual_punc_dist)
    if rem_punc_dist > 0:
        ans.append(f'M117 Loading finished early: e={e_value:.1f} mm t={t / 60:.1f} min, rem_punc={rem_punc_dist:.1f}')
    else:
        ans.append(f'M117 Drywise loading complete! e={e_value:.1f} mm, t={t/60:.1f} min')

    # Add 'M400' before each 'M117' to ensure that the verbose messages are displayed at the correct times.
    # Otherwise, the messages would be displayed too early and would not be useful at all
    ans = [v for line in ans for v in (['M400', line] if line.startswith('M117') else [line])]
    return LoadFilamentResult(
        result=ans, loaded_filament=e_value, total_time=t,
        extra_filament_to_purge=actual_punc_dist,
        extra_filament_to_print_slower=rem_punc_dist,
    )

from abc import ABC, abstractmethod


class GcodeCommandDefinition(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def process_tok(self, tokens: Dict[str, float]) -> Dict:
        pass

    @abstractmethod
    def to_gcode(self, absolute: np.ndarray, delta: np.ndarray) -> str:
        pass

    def post_process(self, idx: int, data: np.ndarray):
        pass


class G01Command(GcodeCommandDefinition):
    def process_tok(self, tokens: Dict[str, float]) -> Dict:
        return tokens

    def to_gcode(self, absolute: np.ndarray, delta: np.ndarray) -> str:
        changed = ~np.isclose(delta, 0.0)
        if not np.any(changed):
            return ''
        return f'{self.name}{"".join([f" {tok}{absolute[i]:.3f}" for i, tok in enumerate("FXYZE") if changed[i]])}'


class G4Command(GcodeCommandDefinition):
    def process_tok(self, tokens: Dict[str, float]) -> Dict:
        if 'P' in tokens:
            return {'S': tokens['P'] / 1000.0}
        return tokens

    def to_gcode(self, absolute: np.ndarray, delta: np.ndarray) -> str:
        changed = ~np.isclose(delta, 0.0)
        if not np.any(changed):
            return ''
        return f'{self.name} S{delta[5]:.3f}'


class G28Command(GcodeCommandDefinition):
    def process_tok(self, tokens: Dict[str, float]) -> Dict:
        if len(tokens) == 0:
            return {'X': 0, 'Y': 0, 'Z': 0}
        return {tok: 0 for tok in tokens.keys()}

    def to_gcode(self, absolute: np.ndarray, delta: np.ndarray) -> str:
        zeroed = np.isclose(absolute[:3], 0.0)
        if np.all(zeroed):
            return ''
        return f'{self.name}{"".join([f" {tok}" for i, tok in enumerate("XYZ", start=1) if zeroed[i]])}'


class SimpleGcodeAnalyser:
    def __init__(self, gcode: List[str] = None):
        self.commands_defs: Dict[str, GcodeCommandDefinition] = {command.name: command for command in [
            G01Command('G0'), G01Command('G1'), G4Command('G4'), G28Command('G28'),
        ]}

        self.commands, self.data, self.unrecognized_gcode = self._gcode_to_numpy(gcode)

    @property
    def delta(self):
        return np.vstack([self.data[0, :], self.data[1:, :] - self.data[:-1, :]])

    @property
    def gcode(self):
        gcode = list()

        absolute, relative = self.data.copy(), self.delta.copy()
        absolute[:, 0] *= 60
        relative[:, 0] *= 60
        for idx, command in enumerate(self.commands):
            if idx in self.unrecognized_gcode:
                gcode.extend(self.unrecognized_gcode[idx])
            gcode.append(self.commands_defs[command].to_gcode(absolute[idx, :], relative[idx, :]))
        if len(self.commands) in self.unrecognized_gcode:
            gcode.extend(self.unrecognized_gcode[len(self.commands)])

        return gcode

    def tokenize(self, line: str) -> typing.Tuple[str | None, Dict[str, float | None], str | None]:
        line = line.strip()
        if line.startswith(';'):
            return None, dict(), line
        splt = line.split(';')
        tokens = splt[0].strip().split(' ')
        command = tokens[0]
        try:
            params = {tok[0]: (float(tok[1:]) if len(tok) > 1 else None) for tok in tokens[1:]}
        except ValueError:
            # Can be caused by some commands like M117, since it does not accept the usual parameters of a gcode
            # command.
            return None, dict(), line
        return command, params, f";{splt[1]}" if len(splt) > 1 else None
    
    def _gcode_to_numpy(self, gcode: List[str], init_state: np.ndarray = None) -> typing.Tuple[List[str], np.ndarray, Dict[int, List[str]]]:
        dict_data = list()
        commands = list()
        unrecognized_gcode = dict()
        idx = 0
        for line in gcode:
            command, params, comments = self.tokenize(line)
            if command is not None and (command_def := self.commands_defs.get(command)) is not None:
                dict_data.append(command_def.process_tok(params))
                commands.append(command)
                if comments:
                    unrecognized_gcode.setdefault(idx, list()).append(comments)
                idx += 1
            else:
                unrecognized_gcode.setdefault(idx, list()).append(line)

        data = np.empty((len(commands), 7))
        data.fill(np.nan)
        for i in range(data.shape[0]):
            line_data = dict_data[i]
            for j, letter in enumerate('FXYZES'):
                data[i][j] = line_data.get(letter, np.nan)

        data[:, 0] /= 60
        # Forward fill the nans for the xyze columns
        data[:, :5] = numpy_ffill(data[:, :5], axis=0)
        data = np.where(np.isnan(data), (init_state if init_state is not None else 0.0), data)

        # Evaluate the time taken for extrusion moves
        dxyz = np.sqrt(np.sum((data[1:, 1:4] - data[:-1, 1:4]) ** 2, axis=1))
        de = data[1:, 4] - data[:-1, 4]
        dt = np.where(data[1:, 0] > 0.0, np.where(dxyz > de, dxyz, de) / data[1:, 0], 0.0)
        data[1:, 5] += dt

        # Convert relative time to absolute
        data[:, 5] = np.cumsum(data[:, 5], axis=0)

        # Add an extra column representing the filament location
        data[:, 6] = np.maximum.accumulate(data[:, 4])
        
        return commands, data, unrecognized_gcode

    def _split_move(self, idx: int, frac: float) -> np.ndarray:
        if not (0.0 <= frac <= 1.0):
            raise ValueError
        return self.data[idx-1] + frac * (self.data[idx] - self.data[idx-1])

    def split(self, idx, frac: float):
        if not (0.0 <= frac <= 1.0):
            raise ValueError
        self._insert(
            idx=idx,
            commands=[self.commands[idx]],
            numpy_data=self.data[idx-1, :] + frac * (self.data[idx, :] - self.data[idx-1, :]),
            unrecog={},
        )

    def _insert(self, idx: int, commands: List[str], numpy_data: np.ndarray, unrecog: Dict[int, List[str]]):
        if len(commands) <= 0:
            self.unrecognized_gcode[idx] = unrecog[0]
            return

        self.commands = [*self.commands[:idx], *commands, self.commands[idx:]]
        self.data = np.vstack([self.data[:idx], numpy_data, self.data[idx:]])
        self.unrecognized_gcode = {(i if i < idx else i + len(commands)): lst for i, lst in self.unrecognized_gcode.items()}
        for i, lst in unrecog.items():
            self.unrecognized_gcode.setdefault(i+idx, list()).extend(lst)
        
    def insert(self, idx: int, lines: List[str], offset_idxs: List[int], split_frac: float = None):
        idx = idx if idx >= 0 else len(self.commands) + idx
        commands, numpy_data, unrecog = self._gcode_to_numpy(lines, init_state=self.data[idx-1] if idx > 0 else None)

        if len(commands) > 0:
            if split_frac is not None:
                numpy_data = np.vstack([self._split_move(idx, frac=split_frac), numpy_data])
            self.data[idx:, offset_idxs] += numpy_data[-1, offset_idxs]
        self._insert(idx, commands, numpy_data, unrecog)

    def insert_at(self, to_insert: List[str], t: float = None, e: float = None, allow_split: bool = True):
        if t is not None:
            value, column = (t if t > 0 else self.data[-1, 5] + t), 5
        elif e is not None:
            value, column = (e if e > 0 else self.data[-1, 6] + e), 6
        else:
            raise RuntimeError

        idx = np.searchsorted(self.data[:, column], value)

        frac = None
        if allow_split:
            frac = (value - self.data[idx-1, column]) / (self.data[idx, column] - self.data[idx-1, column])
        self.insert(idx, lines=to_insert, offset_idxs=[4, 5], split_frac=frac)


def gcode_to_numpy(data: List[str]) -> typing.Tuple[np.ndarray, np.ndarray]:
    """

    The time is evaluted by looking at G4 commands. Yes, the G0/G1 also take time to execute, but
    we can reasonably ignore them since G4 commands last minutes while G0/G1 commands last only seconds.
    And there are roughly as many G4 commands and G0/G1 commands. The inaccuracy is definitely lower than
    5% and the only reason why I am using this code is to estimate when the nozzle and bed should preheat,
    so it is not critical that I do not account for 30 seconds of movement during loading.

    """
    key = lambda k: rf'(?: {k}([0-9.]+))?'
    g014_pattern = re.compile(fr'G[01]{"".join(key(k) for k in "FXYZE")}|G4{"".join(key(k) for k in "SP")}')

    index, matrix = [], []
    for i, line in enumerate(data):
        match = g014_pattern.match(line)
        if not match:
            continue
        matrix.append([float(v) if v else np.nan for v in match.groups()])
        index.append(i)

    index, matrix = np.array(index), np.array([np.array(row) for row in matrix])
    # Convert the speed from mm/min to mm/s
    matrix[:, 0] /= 60
    # Combine the milliseconds with seconds
    matrix[:, 5] = np.where(np.isnan(matrix[:, 5]), np.where(np.isnan(matrix[:, 6]), 0.0, matrix[:, 6]), matrix[:, 5])
    matrix = matrix[:, :6]
    # Forward fill the nans for the xyze columns
    matrix[:, :5] = numpy_ffill(matrix[:, :5], axis=0)
    matrix = np.where(np.isnan(matrix), 0.0, matrix)

    # Evaluate the time taken for extrusion moves
    dxyz = np.sqrt(np.sum((matrix[1:, 1:4] - matrix[:-1, 1:4]) ** 2, axis=1))
    de = matrix[1:, 4] - matrix[:-1, 4]
    dt = np.where(matrix[1:, 0] > 0.0, np.where(dxyz > de, dxyz, de) / matrix[1:, 0], 0.0)
    matrix[1:, 5] += dt

    matrix[:, 5] = np.cumsum(matrix[:, 5], axis=0)
    return index, matrix



def insert_at(gcode: List[str], to_insert: List[str], t: float = None, e: float = None):
    # F, X, Y, Z, E, T
    index, load_gcode_data = gcode_to_numpy(gcode)

    if t is not None:
        t = t if t > 0 else load_gcode_data[-1, 5] + t
        idx = (load_gcode_data[:, 5] >= t).argmax(axis=0)
    elif e is not None:
        e = e if e > 0 else load_gcode_data[-1, 4] + e
        idx = (load_gcode_data[:, 4] >= e).argmax(axis=0)
    else:
        raise RuntimeError

    line_to_split = gcode[index[idx]]

    abs_ = load_gcode_data[idx, :]
    delta = load_gcode_data[idx, :] - (load_gcode_data[idx-1, :] if idx > 0 else np.zeros(load_gcode_data.shape[1]))

    speed = abs_[0]
    if t is not None:
        t_frac = (abs_[5] - t) / delta[5]
        if line_to_split.startswith('G4'):
            pre_insert, post_insert = f"G4 S{(1 - t_frac) * delta[5]}", f"G4 S{t_frac * delta[5]}"
        else:
            pre_insert = f"G1 F{speed * 60} " + ' '.join(
                f"{ch}{abs_[i] - t_frac * delta[i]}" for i, ch in enumerate('XYZE', start=1) if not np.isclose(delta[i], 0)
            )
            post_insert = f"G1 F{speed * 60} " + ' '.join(
                f"{ch}{abs_[i]}" for i, ch in enumerate('XYZE', start=1) if not np.isclose(delta[i], 0)
            )
    elif e is not None:
        assert line_to_split.startswith('G0') or line_to_split.startswith('G1')
        e_frac = (abs_[4] - e) / delta[4]
        pre_insert = f"G1 F{speed * 60} " + ' '.join(
            f"{ch}{abs_[i] - e_frac * delta[i]}" for i, ch in enumerate('XYZE', start=1) if not np.isclose(delta[i], 0)
        )
        post_insert = f"G1 F{speed * 60} " + ' '.join(
            f"{ch}{abs_[i]}" for i, ch in enumerate('XYZE', start=1) if not np.isclose(delta[i], 0)
        )
    else:
        raise RuntimeError

    return [
        *gcode[:index[idx]],
        pre_insert,
        *to_insert,
        post_insert,
        *gcode[index[idx]+1:]
    ]



def create_cube(height: float, layer_width: float, layer_height: float, total_extruder_dist: float,
                bb_bed: typing.Tuple[float, float, float, float],
                speed: float, filament_diameter: float, travel_speed: float = 150.0, first_layer_height: float = None,
                position: typing.Literal['left', 'right', 'top', 'bottom'] = 'left', slow_dist: float = 0.0,
                slow_flowrate: float = None, nozzle_offset: typing.Tuple[float, float] = (0, 0)) -> typing.List[str]:
    """ Creates purging lines for drywise.

    The gcode included:
    - Resets the extruder position to 0
    - Approaches the starting position using a zhop
    - Prints the lines
    - Resents the extruder position to 0
    - Moves upwards


    Parameters
    ----------
    width : float
        The width of the cube in the X direction
    height : float
        The height of the cube in the Z direction. Make sure that the cube does not hit the gantry
    length : float
        The length of the line. Do not confuse with the length of filament needed to be extruded.
    total_extruder_dist : float
        The length of filament need to be extruded (i.e. from drywise output to nozzle).
    flow_rate : float
        The material flowrate (in mm^3/s). Make sure it is not too high or it will clog.
    filament_diameter : float
        Diameter of the filament printed.

    Other Parameters
    ----------------
    separation : float; default: 0.0
        The separation between the individual lines
    start_loc : 2d tuple; default: (10.0, 10.0)
        The starting position of the lines
    travel_speed : float; default: 150.0
        The travel speed (in mm/s)

    Returns
    -------
    list of str
        The resulting gcode that prints lines
    """

    first_layer_height = first_layer_height if first_layer_height is not None else layer_height
    slow_speed = speed if slow_flowrate is None else slow_flowrate / (layer_height * layer_width)

    filament_xsection = math.pi * filament_diameter ** 2 / 4

    num_layers = math.ceil((height - first_layer_height) / layer_height) + 1
    height = first_layer_height + layer_height * (num_layers - 1)
    purge_cube_area = total_extruder_dist * filament_xsection / height

    if position == 'left' or position == 'right':
        line_direction = 1
        num_lines = math.ceil(max(10.0, purge_cube_area / (bb_bed[3] - bb_bed[1])) / layer_width)
        width = num_lines * layer_width
        start_loc = [bb_bed[0] + layer_width/2 if position == 'left' else bb_bed[2] - width - layer_width/2, bb_bed[1]]
    elif position == 'bottom' or position == 'top':
        line_direction = 0
        num_lines = math.ceil(max(10.0, purge_cube_area / (bb_bed[2] - bb_bed[0])) / layer_width)
        width = num_lines * layer_width
        start_loc = [bb_bed[0], bb_bed[1] + layer_width/2 if position == 'bottom' else bb_bed[3] - width - layer_width/2]
    else:
        raise ValueError

    length = purge_cube_area / width

    lengthwise_empty_space = (bb_bed[line_direction + 2] - bb_bed[line_direction]) - length
    start_loc[line_direction] = start_loc[line_direction] + lengthwise_empty_space / 2

    start_loc = [start_loc[0] + nozzle_offset[0], start_loc[1] + nozzle_offset[1]]

    ans = []
    loc = np.array([*start_loc, first_layer_height, 0.0])

    for layer_idx in range(num_layers):
        # Approach starting prosition
        ans.append(f'G0 F{travel_speed * 60} X{loc[0]} Y{loc[1]} Z{loc[2]}')

        line_extruder_length = (length * layer_width * layer_height) / filament_xsection
        first_layer_line_extruder_length = (length * layer_width * first_layer_height) / filament_xsection

        for line_idx in range(num_lines):
            # The lines are printed in zig-zag pattern.
            move_sign = 1 - 2 * (line_idx % 2)
            loc += np.array([
                move_sign * (1 - line_direction) * length,
                move_sign * line_direction * length,
                0,
                first_layer_line_extruder_length if layer_idx == 0 else line_extruder_length
            ])
            print_speed = speed if loc[3] > slow_dist else slow_speed
            ans.append(f'G1 F{print_speed * 60:.1f} X{loc[0]:.3f} Y{loc[1]:.3f} E{loc[3]:.3f}')
            loc += np.array([line_direction * layer_width, (1 - line_direction) * layer_width, 0, 0])
            ans.append(f'G1 F{travel_speed * 60:.1f} X{loc[0]:.3f} Y{loc[1]:.3f} ')

        # Move to next layer and go back to starting position.
        loc += np.array([0, 0, layer_height, 0])
        loc[:2] = start_loc
    assert math.isclose(total_extruder_dist, loc[3]), f"Extruded dist is wrong. Expected {total_extruder_dist}, Actual: {loc[3]}"
    # Reset the extruder value
    ans.append(f'G92 E0')  # Reset the extruder value

    return ans



def numpy_ffill(arr: np.ndarray, axis: int = 0):
    ''' Forward fills the NAs in numpy array

    Stolen from https://stackoverflow.com/questions/41190852/most-efficient-way-to-forward-fill-nan-values-in-numpy-array
    '''

    idx_shape = tuple([slice(None)] + [np.newaxis] * (len(arr.shape) - axis - 1))
    idx = np.where(~np.isnan(arr), np.arange(arr.shape[axis])[idx_shape], 0)
    np.maximum.accumulate(idx, axis=axis, out=idx)
    slc = [
        np.arange(k)[
            tuple([slice(None) if dim == i else np.newaxis
            for dim in range(len(arr.shape))])
        ]
        for i, k in enumerate(arr.shape)
    ]
    slc[axis] = idx
    return arr[tuple(slc)]






def test_cube():
    size = (None, 10.0, 1.5)
    start_loc = (10, 10)
    result = create_cube(
        size=size, layer_width=0.6, layer_height=0.3, total_extruder_dist=1500.0,
        speed=70.0, filament_diameter=2.85, start_loc=start_loc, first_layer_height=0.4
    )
    with open('cube.gcode', mode='w') as f:
        f.write('\n'.join(result))

    g1_pattern = re.compile('G[01](?: F([0-9.]+))?(?: X([0-9.]+))?(?: Y([0-9.]+))?(?: Z([0-9.]+))?(?: E([0-9.]+))?')
    g1_moves = np.array(
        [np.array([float(v) if v else np.nan for v in row]) for row in g1_pattern.findall('\n'.join(result))])
    g1_max = np.nanmax(g1_moves, axis=0)
    g1_min = np.nanmin(g1_moves, axis=0)

    # Verify tha the cube is of correct size and volume
    expected_width = math.ceil(10.0 / 0.6) * 0.6
    expected_height = 0.4 + math.ceil((1.5 - 0.4) / 0.3) * 0.3
    expected_length = math.pi * 2.85 ** 2 / 4 * 1500 / (expected_height * expected_width)
    expected_size = np.array([expected_length, expected_width, expected_height])
    observed_size = [g1_max[1] - g1_min[1], g1_max[2] - g1_min[2], g1_max[3]]
    assert np.all(np.isclose(expected_size, observed_size))
    assert np.isclose(np.prod(expected_size), np.prod(observed_size))

    # Verify that the first layer is of correct height
    z_locs = g1_moves[~np.isnan(g1_moves[:, 3]), 3]
    assert z_locs[0] == 0.4
