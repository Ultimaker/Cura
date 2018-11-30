// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.6
import QtQuick.Controls 2.0
import QtQuick.Controls 1.1 as OldControls

import Cura 1.0 as Cura
import UM 1.3 as UM

Item
{
    width: parent.width
    height: visible ? childrenRect.height : 0

    Label
    {
        id: header
        text: catalog.i18nc("@header", "Custom")
        font: UM.Theme.getFont("large")
        color: UM.Theme.getColor("text")
        height: contentHeight

        anchors
        {
            top: parent.top
            left: parent.left
            right: parent.right
        }
    }

    UM.TabRow
    {
        id: tabBar
        anchors.top: header.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height

        currentIndex: Math.max(Cura.ExtruderManager.activeExtruderIndex, 0)

        Repeater
        {
            id: repeater
            model: extrudersModel
            delegate: UM.TabRowButton
            {
                contentItem: Item
                {
                    Cura.ExtruderIcon
                    {
                        anchors.horizontalCenter: parent.horizontalCenter
                        materialColor: model.color
                        extruderEnabled: model.enabled
                        width: parent.height
                        height: parent.height
                    }
                }
                onClicked:
                {
                    Cura.ExtruderManager.setActiveExtruderIndex(tabBar.currentIndex)
                }
            }
        }

        //When the model of the extruders is rebuilt, the list of extruders is briefly emptied and rebuilt.
        //This causes the currentIndex of the tab to be in an invalid position which resets it to 0.
        //Therefore we need to change it back to what it was: The active extruder index.
        Connections
        {
            target: repeater.model
            onModelChanged:
            {
                tabBar.currentIndex = Math.max(Cura.ExtruderManager.activeExtruderIndex, 0)
            }
        }
    }

    Rectangle
    {
        width: parent.width
        height: childrenRect.height
        anchors.top: tabBar.bottom

        radius: UM.Theme.getSize("default_radius").width
        border.width: UM.Theme.getSize("default_lining").width
        border.color: UM.Theme.getColor("lining")
        color: UM.Theme.getColor("secondary")

        //Remove rounding and lining at the top.
        Rectangle
        {
            width: parent.width
            height: parent.radius
            anchors.top: parent.top
            color: UM.Theme.getColor("lining")
            Rectangle
            {
                anchors
                {
                    left: parent.left
                    leftMargin: parent.parent.border.width
                    right: parent.right
                    rightMargin: parent.parent.border.width
                    top: parent.top
                }
                height: parent.parent.radius
                color: parent.parent.color
            }
        }

        Column
        {
            id: selectors
            padding: UM.Theme.getSize("default_margin").width
            spacing: UM.Theme.getSize("default_margin").height

            property var model: extrudersModel.items[tabBar.currentIndex]

            readonly property real paddedWidth: parent.width - padding * 2
            property real textWidth: Math.round(paddedWidth * 0.3)
            property real controlWidth: paddedWidth - textWidth

            Row
            {
                height: UM.Theme.getSize("print_setup_item").height

                Label
                {
                    text: catalog.i18nc("@label", "Enabled")
                    verticalAlignment: Text.AlignVCenter
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                    height: parent.height
                    width: selectors.textWidth
                }

                OldControls.CheckBox
                {
                    checked: selectors.model != null ? Cura.MachineManager.getExtruder(selectors.model.index).isEnabled: false
                    onClicked: Cura.MachineManager.setExtruderEnabled(selectors.model.index, checked)
                    height: UM.Theme.getSize("setting_control").height
                    style: UM.Theme.styles.checkbox
                }
            }

            Row
            {
                height: UM.Theme.getSize("print_setup_item").height
                Label
                {
                    text: catalog.i18nc("@label", "Material")
                    verticalAlignment: Text.AlignVCenter
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                    height: parent.height
                    width: selectors.textWidth
                    visible: materialSelection.visible
                }

                OldControls.ToolButton
                {
                    id: materialSelection

                    property var activeExtruder: Cura.MachineManager.activeStack
                    property var hasActiveExtruder: activeExtruder != null
                    property var currentRootMaterialName: hasActiveExtruder ? activeExtruder.material.name : ""
                    property var valueError: hasActiveExtruder ? Cura.ContainerManager.getContainerMetaDataEntry(activeExtruder.material.id, "compatible", "") != "True" : true
                    property var valueWarning: !Cura.MachineManager.isActiveQualitySupported

                    text: currentRootMaterialName
                    tooltip: currentRootMaterialName
                    visible: Cura.MachineManager.hasMaterials

                    enabled: Cura.ExtruderManager.activeExtruderIndex > -1

                    height: UM.Theme.getSize("setting_control").height
                    width: selectors.controlWidth

                    style: UM.Theme.styles.sidebar_header_button
                    activeFocusOnPress: true
                    menu: Cura.MaterialMenu
                    {
                        extruderIndex: Cura.ExtruderManager.activeExtruderIndex
                    }
                }
            }

            Row
            {
                height: UM.Theme.getSize("print_setup_item").height

                Label
                {
                    text: Cura.MachineManager.activeDefinitionVariantsName
                    verticalAlignment: Text.AlignVCenter
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                    height: parent.height
                    width: selectors.textWidth
                    visible: variantSelection.visible
                }

                OldControls.ToolButton
                {
                    id: variantSelection
                    text: Cura.MachineManager.activeVariantName
                    tooltip: Cura.MachineManager.activeVariantName;
                    visible: Cura.MachineManager.hasVariants

                    height: UM.Theme.getSize("setting_control").height
                    width: selectors.controlWidth
                    style: UM.Theme.styles.sidebar_header_button
                    activeFocusOnPress: true;

                    menu: Cura.NozzleMenu { extruderIndex: Cura.ExtruderManager.activeExtruderIndex }
                }
            }
        }
    }
}