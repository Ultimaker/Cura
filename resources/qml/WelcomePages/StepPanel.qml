// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtGraphicalEffects 1.0 // For the dropshadow

import Cura 1.1 as Cura

import "../Widgets"


Item
{
    id: base

    anchors.fill: parent
    clip: true

    property int roundCornerRadius: 4
    property int shadowOffset: 1
    property int stepBarHeight: 12
    property int contentMargins: 1

    property int currentStep: 0
    property int totalStepCount: (model == null) ? 0 : model.count
    property real progressValue: (totalStepCount == 0) ? 0 : (currentStep / totalStepCount)

    property var currentItem: (model == null) ? null : model.getItem(currentStep)
    property var model: null

    signal showNextPage()
    signal showPreviousPage()
    signal passLastPage()  // Emitted when there is no more page to show

    onShowNextPage:
    {
        if (currentStep < totalStepCount - 1)
        {
            currentStep++
        }
        else {
            passLastPage()
        }
    }

    onShowPreviousPage:
    {
        if (currentStep > 0)
        {
            currentStep--
        }
    }

    onVisibleChanged:
    {
        if (visible)
        {
            base.currentStep = 0
            base.currentItem = base.model.getItem(base.currentStep)
        }
    }

    onModelChanged:
    {
        base.currentStep = 0
    }

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
        visible: true
        color: UM.Theme.getColor("monitor_shadow")
        transparentBorder: true
        // Should always be drawn behind the background.
        z: panelBackground.z - 1
    }

    CuraProgressBar
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
        source: base.currentItem.page_url
    }
}
