// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.2 as UM
import Cura 1.0 as Cura

Rectangle
{
    id: configurationItem

    property var configuration: null
    property var selected: false
    signal activateConfiguration()

    height: childrenRect.height
    border.width: UM.Theme.getSize("default_lining").width
    border.color: updateBorderColor()
    color: selected ? UM.Theme.getColor("configuration_item_active") : UM.Theme.getColor("configuration_item")
    property var textColor: selected ? UM.Theme.getColor("configuration_item_text_active") : UM.Theme.getColor("configuration_item_text")

    function updateBorderColor()
    {
        border.color = selected ? UM.Theme.getColor("configuration_item_border_active") : UM.Theme.getColor("configuration_item_border")
    }

    Column
    {
        id: contentColumn
        width: parent.width
        padding: UM.Theme.getSize("default_margin").width
        spacing: Math.round(UM.Theme.getSize("default_margin").height / 2)

        Row
        {
            id: extruderRow

            width: parent.width - 2 * parent.padding
            height: childrenRect.height

            spacing: UM.Theme.getSize("default_margin").width

            Repeater
            {
                id: repeater
                height: childrenRect.height
                model: configuration.extruderConfigurations
                delegate: PrintCoreConfiguration
                {
                    width: Math.round(parent.width / 2)
                    printCoreConfiguration: modelData
                    mainColor: textColor
                }
            }
        }

        //Buildplate row separator
        Rectangle
        {
            id: separator

            visible: buildplateInformation.visible
            width: parent.width - 2 * parent.padding
            height: visible ? Math.round(UM.Theme.getSize("sidebar_lining_thin").height / 2) : 0
            color: textColor
        }

        Item
        {
            id: buildplateInformation
            width: parent.width - 2 * parent.padding
            height: childrenRect.height
            visible: configuration.buildplateConfiguration != ""

            UM.RecolorImage {
                id: buildplateIcon
                anchors.left: parent.left
                width: UM.Theme.getSize("topbar_button_icon").width
                height: UM.Theme.getSize("topbar_button_icon").height
                sourceSize.width: width
                sourceSize.height: height
                source: UM.Theme.getIcon("buildplate")
                color: textColor
            }

            Label
            {
                id: buildplateLabel
                anchors.left: buildplateIcon.right
                anchors.verticalCenter: buildplateIcon.verticalCenter
                anchors.leftMargin: Math.round(UM.Theme.getSize("default_margin").height / 2)
                text: configuration.buildplateConfiguration
                renderType: Text.NativeRendering
                color: textColor
            }
        }
    }

    MouseArea
    {
        id: mouse
        anchors.fill: parent
        onClicked: activateConfiguration()
        cursorShape: Qt.PointingHandCursor
        hoverEnabled: true
        onEntered:
        {
            parent.border.color = UM.Theme.getColor("configuration_item_border_hover")
            if (configurationItem.selected == false)
            {
                configurationItem.color = UM.Theme.getColor("sidebar_lining")
            }
        }
        onExited:
        {
            updateBorderColor()
            if (configurationItem.selected == false)
            {
                configurationItem.color = UM.Theme.getColor("configuration_item")
            }
        }
    }

    Connections
    {
        target: Cura.MachineManager
        onCurrentConfigurationChanged: {
            configurationItem.selected = Cura.MachineManager.matchesConfiguration(configuration)
            updateBorderColor()
        }
    }

    Component.onCompleted:
    {
        configurationItem.selected = Cura.MachineManager.matchesConfiguration(configuration)
        updateBorderColor()
    }

    onVisibleChanged:
    {
        if(visible)
        {
            // I cannot trigger function updateBorderColor() after visibility change
            color = selected ? UM.Theme.getColor("configuration_item_active") : UM.Theme.getColor("configuration_item")
        }
    }
}