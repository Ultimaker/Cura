// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.4 as UM
import Cura 1.1 as Cura
// A row of buttons that control the view direction
Row
{
    id: viewOrientationControl

    spacing: UM.Theme.getSize("narrow_margin").width
    height: childrenRect.height
    width: childrenRect.width

    ViewOrientationButton
    {
        iconSource: UM.Theme.getIcon("View3D")
        onClicked: Cura.Actions.view3DCamera.trigger()

        UM.TooltipArea
        {
            anchors.fill: parent
            text: catalog.i18nc("@info:tooltip", "3D View")
            acceptedButtons: Qt.NoButton
        }
    }

    ViewOrientationButton
    {
        iconSource: UM.Theme.getIcon("ViewFront")
        onClicked: Cura.Actions.viewFrontCamera.trigger()

        UM.TooltipArea
        {
            anchors.fill: parent
            text: catalog.i18nc("@info:tooltip", "Front View")
            acceptedButtons: Qt.NoButton
        }
    }

    ViewOrientationButton
    {
        iconSource: UM.Theme.getIcon("ViewTop")
        onClicked: Cura.Actions.viewTopCamera.trigger()

        UM.TooltipArea
        {
            anchors.fill: parent
            text: catalog.i18nc("@info:tooltip", "Top View")
            acceptedButtons: Qt.NoButton
        }
    }

    ViewOrientationButton
    {
        iconSource: UM.Theme.getIcon("ViewLeft")
        onClicked: Cura.Actions.viewLeftSideCamera.trigger()

        UM.TooltipArea
        {
            anchors.fill: parent
            text: catalog.i18nc("@info:tooltip", "Left View")
            acceptedButtons: Qt.NoButton
        }
    }

    ViewOrientationButton
    {
        iconSource: UM.Theme.getIcon("ViewRight")
        onClicked: Cura.Actions.viewRightSideCamera.trigger()

        UM.TooltipArea
        {
            anchors.fill: parent
            text: catalog.i18nc("@info:tooltip", "Right View")
            acceptedButtons: Qt.NoButton
        }
    }
}
