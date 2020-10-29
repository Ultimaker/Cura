// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import UM 1.1 as UM

Item
{
    id: base
    property ButtonGroup buttonGroup: null

    property color activeColor: UM.Theme.getColor("primary")
    property color inactiveColor: UM.Theme.getColor("slider_groove")
    property color defaultItemColor: UM.Theme.getColor("slider_groove_fill")
    property color defaultItemFillColor: UM.Theme.getColor("main_background")
    property int checkboxSize: Math.round(UM.Theme.getSize("radio_button").height * 0.75)
    property int inactiveMarkerSize: 2 * barSize
    property int barSize: UM.Theme.getSize("slider_groove_radius").height
    property var isCheckedFunction // Function that accepts the modelItem and returns if the item should be active.

    implicitWidth: 200 * screenScaleFactor
    implicitHeight: checkboxSize

    property var dataModel: null

    // The horizontal inactive bar that sits behind the buttons
    Rectangle
    {
        id: inactiveLine
        color: inactiveColor

        height: barSize

        anchors
        {
            left: buttonBar.left
            right: buttonBar.right
            leftMargin: Math.round((checkboxSize - inactiveMarkerSize) / 2)
            rightMargin: Math.round((checkboxSize - inactiveMarkerSize) / 2)
            verticalCenter: parent.verticalCenter
        }
    }


    RowLayout
    {
        id: buttonBar
        anchors.top: parent.top
        height: checkboxSize
        width: parent.width
        spacing: 0

        Repeater
        {
            id: repeater
            model: base.dataModel
            height: checkboxSize
            Item
            {
                Layout.fillWidth: true
                Layout.fillHeight: true
                // The last item of the repeater needs to be shorter, as we don't need another part to fit
                // the horizontal bar. The others should essentially not be limited.
                Layout.maximumWidth: index + 1 === repeater.count ? activeComponent.width : 200000000

                property bool isEnabled: model.available
                // The horizontal bar between the checkable options.
                // Note that the horizontal bar points towards the previous item.
                Rectangle
                {
                    property Item previousItem: repeater.itemAt(index - 1)

                    height: barSize
                    width: Math.round(buttonBar.width / (repeater.count - 1) - activeComponent.width - 2)
                    color: defaultItemColor

                    anchors
                    {
                        right: activeComponent.left
                        verticalCenter: parent.verticalCenter
                    }
                    visible: previousItem !== null && previousItem.isEnabled && isEnabled
                }
                Loader
                {
                    id: activeComponent
                    sourceComponent: isEnabled? checkboxComponent : disabledComponent
                    width: checkboxSize

                    property var modelItem: model
                }
            }
        }
    }

    Component
    {
        id: disabledComponent
        Item
        {
            height: checkboxSize
            width: checkboxSize

            Rectangle
            {
                // This can (and should) be done wiht a verticalCenter. For some reason it does work in QtCreator
                // but not when using the exact same QML in Cura.
                anchors.verticalCenter: parent ? parent.verticalCenter : undefined
                anchors.horizontalCenter: parent ? parent.horizontalCenter : undefined
                height: inactiveMarkerSize
                width: inactiveMarkerSize
                radius: Math.round(width / 2)
                color: inactiveColor
            }
        }
    }

    Component
    {
        id: checkboxComponent
        CheckBox
        {
            id: checkbox
            ButtonGroup.group: buttonGroup
            width: checkboxSize
            height: checkboxSize
            property var modelData: modelItem

            checked: isCheckedFunction(modelItem)
            indicator: Rectangle
            {
                height: checkboxSize
                width: checkboxSize
                radius: Math.round(width / 2)

                border.color: defaultItemColor
                color: defaultItemFillColor

                Rectangle
                {
                    anchors
                    {
                        fill: parent
                    }
                    radius: Math.round(width / 2)
                    color: activeColor
                    visible: checkbox.checked
                }
            }
        }
    }
}
