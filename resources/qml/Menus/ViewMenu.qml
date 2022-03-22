// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.1

import UM 1.5 as UM
import Cura 1.0 as Cura

Cura.Menu
{
    id: base
    title: catalog.i18nc("@title:menu menubar:toplevel", "&View")

    Cura.Menu
    {
        title: catalog.i18nc("@action:inmenu menubar:view", "&Camera position")
        Cura.MenuItem { action: Cura.Actions.view3DCamera }
        Cura.MenuItem { action: Cura.Actions.viewFrontCamera }
        Cura.MenuItem { action: Cura.Actions.viewTopCamera }
        Cura.MenuItem { action: Cura.Actions.viewBottomCamera }
        Cura.MenuItem { action: Cura.Actions.viewLeftSideCamera }
        Cura.MenuItem { action: Cura.Actions.viewRightSideCamera }
    }

    Cura.Menu
    {
        id: cameraViewMenu

        title: catalog.i18nc("@action:inmenu menubar:view", "Camera view")
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

        Cura.MenuItem
        {
            text: catalog.i18nc("@action:inmenu menubar:view", "Perspective")
            checkable: true
            checked: cameraViewMenu.cameraMode == "perspective"
            onTriggered:
            {
                UM.Preferences.setValue("general/camera_perspective_mode", "perspective")
            }
        }

        Cura.MenuItem
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

    Cura.MenuSeparator {}

    Cura.MenuItem
    {
        action: Cura.Actions.toggleFullScreen
    }
}
