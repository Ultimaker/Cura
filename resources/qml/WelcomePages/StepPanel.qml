// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtGraphicalEffects 1.0 // For the dropshadow

import Cura 1.1 as Cura
Item
{
    id: base

    anchors.fill: parent
    clip: true

    property int roundCornerRadius: 4
    property int shadowOffset: 2
    property int stepBarHeight: 12
    property int contentMargins: 4

    property int totalSteps: 0
    property int currentStep: -1

    property var currentItem: null
    property var model: null

    onVisibleChanged:
    {
        if (visible)
        {
            base.currentStep = 0
            base.currentItem = base.model.getItem(base.currentStep)
        }
    }

    onCurrentStepChanged:
    {
        base.currentItem = base.model.getItem(base.currentStep)
    }

    onModelChanged:
    {
        base.totalSteps = base.model.count
        base.currentStep = 0
        base.currentItem = base.model.getItem(base.currentStep)
    }

    // Panel background
    Rectangle
    {
        id: panelBackground
        anchors.fill: parent
        anchors.margins: 10
        color: "white"  // TODO
        radius: base.roundCornerRadius  // TODO
    }

    // Drop shadow around the panel
    DropShadow
    {
        id: shadow
        // Don't blur the shadow
        radius: base.roundCornerRadius + 2
        anchors.fill: parent
        source: parent
        horizontalOffset: base.shadowOffset
        verticalOffset: base.shadowOffset
        visible: true
        color: UM.Theme.getColor("action_button_shadow")
        // Should always be drawn behind the background.
        z: panelBackground.z - 1
    }

    StepIndicatorBar
    {
        id: stepIndicatorBar
        //anchors.margins: 10

        totalSteps: base.totalSteps
        currentStep: base.currentStep
        radius: base.roundCornerRadius

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
            top: stepIndicatorBar.bottom
            bottom: parent.bottom
            left: parent.left
            right: parent.right
        }
        source: base.currentItem.page_url
    }
}
