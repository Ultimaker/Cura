// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import UM 1.5 as UM


UM.SimpleButton
{
    id: modelCheckerButton

    visible: manager.hasWarnings
    onClicked: manager.showWarnings()

    width: UM.Theme.getSize("save_button_specs_icons").width
    height: UM.Theme.getSize("save_button_specs_icons").height
    iconSource: Qt.resolvedUrl("model_checker.svg")
    anchors.verticalCenter: parent ? parent.verticalCenter : undefined
    color: UM.Theme.getColor("text_scene")
    hoverColor: UM.Theme.getColor("text_scene_hover")
}
