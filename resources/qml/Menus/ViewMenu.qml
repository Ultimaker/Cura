// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.1

import UM 1.5 as UM
import Cura 1.0 as Cura

Menu
{
    id: base
    title: catalog.i18nc("@title:menu menubar:toplevel", "&View")

    Menu
    {
        title: catalog.i18nc("@action:inmenu menubar:view", "&Camera position")
        UM.MenuItem { action: Cura.Actions.view3DCamera }
        UM.MenuItem { action: Cura.Actions.viewFrontCamera }
        UM.MenuItem { action: Cura.Actions.viewTopCamera }
        UM.MenuItem { action: Cura.Actions.viewBottomCamera }
        UM.MenuItem { action: Cura.Actions.viewLeftSideCamera }
        UM.MenuItem { action: Cura.Actions.viewRightSideCamera }
    }

    Menu
    {
        id: cameraViewMenu

        title: catalog.i18nc("@action:inmenu menubar:view","Camera view")
        property string cameraMode: UM.Preferences.getValue("general/camera_perspective_mode")

        Connections
        {
            target: UM.Preferences
            function onPreferenceChanged(preference)
            {
                if (preference !== "general/camera_perspective_mode")
                {
                    return
                }
                cameraViewMenu.cameraMode = UM.Preferences.getValue("general/camera_perspective_mode")
            }
        }

        MenuItem
        {
            text: catalog.i18nc("@action:inmenu menubar:view", "Perspective")
            checkable: true
            checked: cameraViewMenu.cameraMode == "perspective"
            onTriggered:
            {
                UM.Preferences.setValue("general/camera_perspective_mode", "perspective")
            }
        }

        MenuItem
        {
            text: catalog.i18nc("@action:inmenu menubar:view", "Orthographic")
            checkable: true
            checked: cameraViewMenu.cameraMode == "orthographic"
            onTriggered:
            {
                UM.Preferences.setValue("general/camera_perspective_mode", "orthographic")
            }
        }
    }

    MenuSeparator {}

    UM.MenuItem
    {
        action: Cura.Actions.toggleFullScreen
    }
}
