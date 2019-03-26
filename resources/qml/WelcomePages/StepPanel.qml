// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtGraphicalEffects 1.0 // For the dropshadow

import UM 1.3 as UM
import Cura 1.1 as Cura


Item
{
    id: base

    anchors.fill: parent
    clip: true

    property int roundCornerRadius: 4
    property int shadowOffset: 1
    property int stepBarHeight: 12
    property int contentMargins: 1

    property var currentItem: (model == null) ? null : model.getItem(model.currentPageIndex)
    property var model: null

    property var progressValue: model == null ? 0 : model.currentProgress
    property string pageUrl: currentItem == null ? null : currentItem.page_url

    signal showNextPage()
    signal showPreviousPage()
    signal goToPage(string page_id)  // Go to a specific page by the given page_id.

    // Call the corresponding functions in the model
    onShowNextPage: model.goToNextPage()
    onShowPreviousPage: model.goToPreviousPage()
    onGoToPage: model.goToPage(page_id)

    onVisibleChanged:
    {
        if (visible)
        {
            model.resetState()
        }
    }

    onModelChanged: model.resetState()

    // Panel background
    Rectangle
    {
        id: panelBackground
        anchors.fill: parent
        anchors.margins: 2
        color: "white"  // TODO
        radius: base.roundCornerRadius  // TODO
    }

    // Drop shadow around the panel
    DropShadow
    {
        id: shadow
        radius: UM.Theme.getSize("monitor_shadow_radius").width
        anchors.fill: parent
        source: parent
        horizontalOffset: base.shadowOffset
        verticalOffset: base.shadowOffset
        color: UM.Theme.getColor("monitor_shadow")
        transparentBorder: true
        // Should always be drawn behind the background.
        z: panelBackground.z - 1
    }

    Cura.ProgressBar
    {
        id: progressBar

        value: base.progressValue

        anchors
        {
            left: panelBackground.left
            right: panelBackground.right
            top: panelBackground.top
        }
        height: base.stepBarHeight
    }

    Loader
    {
        id: contentLoader
        anchors
        {
            margins: base.contentMargins
            top: progressBar.bottom
            bottom: parent.bottom
            left: parent.left
            right: parent.right
        }
        source: base.pageUrl
    }
}
