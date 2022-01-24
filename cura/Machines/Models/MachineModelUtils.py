# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import TYPE_CHECKING

from UM.Settings.SettingFunction import SettingFunction

if TYPE_CHECKING:
    from cura.Machines.QualityGroup import QualityGroup

layer_height_unit = ""


def fetchLayerHeight(quality_group: "QualityGroup") -> float:
    from cura.CuraApplication import CuraApplication
    global_stack = CuraApplication.getInstance().getMachineManager().activeMachine

    default_layer_height = global_stack.definition.getProperty("layer_height", "value")

    # Get layer_height from the quality profile for the GlobalStack
    if quality_group.node_for_global is None:
        return float(default_layer_height)
    container = quality_group.node_for_global.container

    layer_height = default_layer_height
    if container and container.hasProperty("layer_height", "value"):
        layer_height = container.getProperty("layer_height", "value")
    else:
        # Look for layer_height in the GlobalStack from material -> definition
        container = global_stack.definition
        if container and container.hasProperty("layer_height", "value"):
            layer_height = container.getProperty("layer_height", "value")

    if isinstance(layer_height, SettingFunction):
        layer_height = layer_height(global_stack)

    return round(float(layer_height), 3)
