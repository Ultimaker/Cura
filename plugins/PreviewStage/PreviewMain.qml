// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.4
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.0 as UM
import Cura 1.0 as Cura

Item
{

    // Subtract the actionPanel from the safe area. This way the view won't draw interface elements under/over it
    Item {
        id: safeArea
        visible: false
        anchors.left: parent.left
        anchors.right: actionPanelWidget.left
        anchors.top: parent.top
        anchors.bottom: actionPanelWidget.top
    }

    Loader
    {
        id: previewMain
        anchors.fill: parent

        source: UM.Controller.activeView != null && UM.Controller.activeView.mainComponent != null ? UM.Controller.activeView.mainComponent : ""

        Binding
        {
            target: previewMain.item
            property: "safeArea"
            value:safeArea
        }
    }

    Cura.ActionPanelWidget
    {
        id: actionPanelWidget
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.rightMargin: UM.Theme.getSize("thick_margin").width
        anchors.bottomMargin: UM.Theme.getSize("thick_margin").height
        hasPreviewButton: false
    }
}