// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura

Item
{
    id: previewMenu

    property real itemHeight: height - 2 * UM.Theme.getSize("default_lining").width

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    // Item to ensure that all of the buttons are nicely centered.
    Item
    {
        anchors.horizontalCenter: parent.horizontalCenter
        width: stageMenuRow.width
        height: parent.height

        RowLayout
        {
            id: stageMenuRow
            width: Math.round(0.85 * previewMenu.width)
            height: parent.height
            spacing: 0

            Cura.ViewsSelector
            {
                id: viewsSelector
                headerCornerSide: Cura.RoundedRectangle.Direction.Left
                Layout.minimumWidth: UM.Theme.getSize("views_selector").width
                Layout.maximumWidth: UM.Theme.getSize("views_selector").width
                Layout.fillWidth: true
                Layout.fillHeight: true
            }

            // Separator line
            Rectangle
            {
                height: parent.height
                // If there is no viewPanel, we only need a single spacer, so hide this one.
                visible: viewPanel.source != ""
                width: UM.Theme.getSize("default_lining").width

                color: UM.Theme.getColor("lining")
            }

            Loader
            {
                id: viewPanel
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredWidth: stageMenuRow.width - viewsSelector.width - printSetupSelectorItem.width - 2 * UM.Theme.getSize("default_lining").width
                source: UM.Controller.activeView != null && UM.Controller.activeView.stageMenuComponent != null ? UM.Controller.activeView.stageMenuComponent : ""
            }

            // Separator line
            Rectangle
            {
                height: parent.height
                width: UM.Theme.getSize("default_lining").width
                color: UM.Theme.getColor("lining")
            }

            Item
            {
                id: printSetupSelectorItem
                // This is a work around to prevent the printSetupSelector from having to be re-loaded every time
                // a stage switch is done.
                children: [printSetupSelector]
                height: childrenRect.height
                width: childrenRect.width
            }
        }
    }
}
