// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Controls 2.0
import QtGraphicalEffects 1.0
import UM 1.3 as UM

Item
{
    id: base

    property var currentIndex: 0
    property var tileWidth: 834 * screenScaleFactor // TODO: Theme!
    property var tileHeight: 216 * screenScaleFactor // TODO: Theme!
    property var tileSpacing: 60 * screenScaleFactor // TODO: Theme!

    // Array/model of printers to populate the carousel with
    property var printers: []

    // Maximum distance the carousel can be shifted
    property var maxOffset: (printers.length - 1) * (tileWidth + tileSpacing)

    height: centerSection.height
    width: maximumWidth
    
    // Enable keyboard navigation
    Keys.onLeftPressed: navigateTo(currentIndex - 1)
    Keys.onRightPressed: navigateTo(currentIndex + 1)

    Item
    {
        id: leftHint
        anchors
        {
            right: leftButton.left
            rightMargin: 12 * screenScaleFactor // TODO: Theme!
            left: parent.left
        }
        height: parent.height
        z: 10
        LinearGradient
        {
            anchors.fill: parent
            start: Qt.point(0, 0)
            end: Qt.point(leftHint.width, 0)
            gradient: Gradient
            {
                GradientStop
                {
                    position: 0.0
                    color: UM.Theme.getColor("monitor_stage_background")
                }
                GradientStop
                {
                    position: 1.0
                    color: UM.Theme.getColor("monitor_stage_background_fade")
                }
            }
        }
        MouseArea
        {
            anchors.fill: parent
            onClicked: navigateTo(currentIndex - 1)
        }
    }

    Button
    {
        id: leftButton
        anchors
        {
            verticalCenter: parent.verticalCenter
            right: centerSection.left
            rightMargin: 12 * screenScaleFactor // TODO: Theme!
        }
        width: 36 * screenScaleFactor // TODO: Theme!
        height: 72 * screenScaleFactor // TODO: Theme!
        visible: currentIndex > 0
        hoverEnabled: true
        z: 10
        onClicked: navigateTo(currentIndex - 1)
        background: Rectangle
        {
            color: leftButton.hovered ? UM.Theme.getColor("monitor_card_hover") : UM.Theme.getColor("monitor_card_background")
            border.width: 1 * screenScaleFactor // TODO: Theme!
            border.color: UM.Theme.getColor("monitor_card_border")
            radius: 2 * screenScaleFactor // TODO: Theme!
        }
        contentItem: Item
        {
            anchors.fill: parent
            UM.RecolorImage
            {
                anchors.centerIn: parent
                width: 18 // TODO: Theme!
                height: width // TODO: Theme!
                sourceSize.width: width // TODO: Theme!
                sourceSize.height: width // TODO: Theme!
                color: UM.Theme.getColor("monitor_text_primary")
                source: UM.Theme.getIcon("arrow_left")
            }
        }
    }

    Item
    {
        id: centerSection
        anchors
        {
            verticalCenter: parent.verticalCenter
            horizontalCenter: parent.horizontalCenter
        }
        width: tileWidth
        height: tiles.height
        z: 1

        Row
        {
            id: tiles
            height: childrenRect.height
            width: 5 * tileWidth + 4 * tileSpacing // TODO: Theme!
            x: 0
            z: 0
            Behavior on x
            {
                NumberAnimation
                {
                    duration: 200
                    easing.type: Easing.InOutCubic
                }
            }
            spacing: 60 * screenScaleFactor // TODO: Theme!
            
            Repeater
            {
                model: printers
                MonitorPrinterCard
                {
                    printer: modelData
                    enabled: model.index == currentIndex
                }
            }
        }
    }

    Button
    {
        id: rightButton
        anchors
        {
            verticalCenter: parent.verticalCenter
            left: centerSection.right
            leftMargin: 12 * screenScaleFactor // TODO: Theme!
        }
        width: 36 * screenScaleFactor // TODO: Theme!
        height: 72 * screenScaleFactor // TODO: Theme!
        z: 10
        visible: currentIndex < printers.length - 1
        onClicked: navigateTo(currentIndex + 1)
        hoverEnabled: true
        background: Rectangle
        {
            color: rightButton.hovered ? UM.Theme.getColor("monitor_card_hover") : UM.Theme.getColor("monitor_card_background")
            border.width: 1 * screenScaleFactor // TODO: Theme!
            border.color: UM.Theme.getColor("monitor_card_border")
            radius: 2 * screenScaleFactor // TODO: Theme!
        }
        contentItem: Item
        {
            anchors.fill: parent
            UM.RecolorImage
            {
                anchors.centerIn: parent
                width: 18 // TODO: Theme!
                height: width // TODO: Theme!
                sourceSize.width: width // TODO: Theme!
                sourceSize.height: width // TODO: Theme!
                color: UM.Theme.getColor("monitor_text_primary")
                source: UM.Theme.getIcon("arrow_right")
            }
        }
    }

    Item
    {
        id: rightHint
        anchors
        {
            left: rightButton.right
            leftMargin: 12 * screenScaleFactor // TODO: Theme!
            right: parent.right
        }
        height: centerSection.height
        z: 10

        LinearGradient
        {
            anchors.fill: parent
            start: Qt.point(0, 0)
            end: Qt.point(rightHint.width, 0)
            gradient: Gradient
            {
                GradientStop
                {
                    position: 0.0
                    color: UM.Theme.getColor("monitor_stage_background_fade")
                }
                GradientStop
                {
                    position: 1.0
                    color: UM.Theme.getColor("monitor_stage_background")
                }
            }
        }
        MouseArea
        {
            anchors.fill: parent
            onClicked: navigateTo(currentIndex + 1)
        }
    }

    Row
    {
        id: navigationDots
        anchors
        {
            horizontalCenter: centerSection.horizontalCenter
            top: centerSection.bottom
            topMargin: 36 * screenScaleFactor // TODO: Theme!
        }
        spacing: 8 * screenScaleFactor // TODO: Theme!
        visible: printers.length > 1
        Repeater
        {
            model: printers
            Button
            {
                background: Rectangle
                {
                    color: model.index == currentIndex ? UM.Theme.getColor("monitor_carousel_dot_current") : UM.Theme.getColor("monitor_carousel_dot")
                    radius: Math.floor(width / 2)
                    width: 12 * screenScaleFactor // TODO: Theme!
                    height: width // TODO: Theme!
                }
                onClicked: navigateTo(model.index)
            }
        }
    }

    function navigateTo( i ) {
        if (i >= 0 && i < printers.length)
        {
            tiles.x = -1 * i * (tileWidth + tileSpacing)
            currentIndex = i
        }
    }
}