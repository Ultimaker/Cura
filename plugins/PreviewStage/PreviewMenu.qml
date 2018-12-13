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

    Row
    {
        id: stageMenuRow
        anchors.centerIn: parent
        height: parent.height
        width: childrenRect.width

        // We want this row to have a preferred with equals to the 85% of the parent
        property int preferredWidth: Math.round(0.85 * previewMenu.width)

        Cura.ViewsSelector
        {
            id: viewsSelector
            height: parent.height
            width: UM.Theme.getSize("views_selector").width
            headerCornerSide: Cura.RoundedRectangle.Direction.Left
        }

        // Separator line
        Rectangle
        {
            height: parent.height
            // If there is no viewPanel, we only need a single spacer, so hide this one.
            visible: viewPanel.source != ""
            width: visible ? UM.Theme.getSize("default_lining").width : 0

            color: UM.Theme.getColor("lining")
        }

        // This component will grow freely up to complete the preferredWidth of the row.
        Loader
        {
            id: viewPanel
            height: parent.height
            width: source != "" ? (stageMenuRow.preferredWidth - viewsSelector.width - printSetupSelectorItem.width - 2 * UM.Theme.getSize("default_lining").width) : 0
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
