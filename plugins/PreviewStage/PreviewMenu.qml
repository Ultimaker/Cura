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

    anchors
    {
        left: parent.left
        right: parent.right
        leftMargin: UM.Theme.getSize("wide_margin").width * 2
        rightMargin: UM.Theme.getSize("wide_margin").width * 2
    }

    Row
    {
        id: stageMenuRow

        anchors.fill: parent
        // This is a trick to make sure that the borders of the two adjacent buttons' borders overlap. Otherwise
        // there will be double border (one from each button)
        spacing: -UM.Theme.getSize("default_lining").width

        Cura.ViewsSelector
        {
            id: viewsSelector
            height: parent.height
            width: Math.max(Math.round((parent.width - printSetupSelectorItem.width) / 3), UM.Theme.getSize("views_selector").width)
            headerCornerSide: Cura.RoundedRectangle.Direction.Left
        }

        // This component will grow freely up to complete the width of the row.
        Loader
        {
            id: viewPanel
            height: parent.height
            width: source != "" ? (parent.width - viewsSelector.width - printSetupSelectorItem.width) : 0
            source: UM.Controller.activeView != null && UM.Controller.activeView.stageMenuComponent != null ? UM.Controller.activeView.stageMenuComponent : ""
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
