// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    title: catalog.i18nc("@title:menu menubar:toplevel", "&View")
    id: base

    property var multiBuildPlateModel: CuraApplication.getMultiBuildPlateModel()

    Menu
    {
        title: catalog.i18nc("@action:inmenu menubar:view","&Camera position");
        MenuItem { action: Cura.Actions.view3DCamera; }
        MenuItem { action: Cura.Actions.viewFrontCamera; }
        MenuItem { action: Cura.Actions.viewTopCamera; }
        MenuItem { action: Cura.Actions.viewLeftSideCamera; }
        MenuItem { action: Cura.Actions.viewRightSideCamera; }
    }

    Menu
    {
        id: cameraViewMenu
        property string cameraMode: UM.Preferences.getValue("general/camera_perspective_mode")
        Connections
        {
            target: UM.Preferences
            onPreferenceChanged:
            {
                if (preference !== "general/camera_perspective_mode")
                {
                    return
                }
                cameraViewMenu.cameraMode = UM.Preferences.getValue("general/camera_perspective_mode")
            }
        }

        title: catalog.i18nc("@action:inmenu menubar:view","Camera view")
        MenuItem
        {
            text: catalog.i18nc("@action:inmenu menubar:view", "Perspective")
            checkable: true
            checked: cameraViewMenu.cameraMode == "perspective"
            onTriggered:
            {
                UM.Preferences.setValue("general/camera_perspective_mode", "perspective")
                checked = cameraViewMenu.cameraMode == "perspective"
            }
            exclusiveGroup: group
        }
        MenuItem
        {
            text: catalog.i18nc("@action:inmenu menubar:view", "Orthographic")
            checkable: true
            checked: cameraViewMenu.cameraMode == "orthogonal"
            onTriggered:
            {
                UM.Preferences.setValue("general/camera_perspective_mode", "orthogonal")
                checked = cameraViewMenu.cameraMode == "orthogonal"
            }
            exclusiveGroup: group
        }
        ExclusiveGroup { id: group }
    }

    MenuSeparator
    {
        visible: UM.Preferences.getValue("cura/use_multi_build_plate")
    }

    Menu
    {
        id: buildPlateMenu;
        title: catalog.i18nc("@action:inmenu menubar:view","&Build plate")
        visible: UM.Preferences.getValue("cura/use_multi_build_plate")
        Instantiator
        {
            model: base.multiBuildPlateModel
            MenuItem
            {
                text: base.multiBuildPlateModel.getItem(index).name;
                onTriggered: Cura.SceneController.setActiveBuildPlate(base.multiBuildPlateModel.getItem(index).buildPlateNumber)
                checkable: true
                checked: base.multiBuildPlateModel.getItem(index).buildPlateNumber == base.multiBuildPlateModel.activeBuildPlate
                exclusiveGroup: buildPlateGroup
                visible: UM.Preferences.getValue("cura/use_multi_build_plate")
            }
            onObjectAdded: buildPlateMenu.insertItem(index, object)
            onObjectRemoved: buildPlateMenu.removeItem(object)
        }
        ExclusiveGroup
        {
            id: buildPlateGroup
        }
    }

    MenuSeparator {}

    MenuItem
    {
        action: Cura.Actions.toggleFullScreen
    }
}
