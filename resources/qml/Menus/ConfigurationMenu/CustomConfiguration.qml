// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.0
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
        anchors.topMargin: UM.Theme.getSize("default_margin").height + header.height

        onCurrentIndexChanged: Cura.ExtruderManager.setActiveExtruderIndex(currentIndex)

        Repeater
        {
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
            }
        }
    }

    Item
    {
        id: tabControl
        width: parent.width
        height: childrenRect.height
        anchors.top: tabBar.bottom
        property var model: extrudersModel.items[tabBar.currentIndex]
        property real textWidth: Math.round(width * 0.3)
        property real controlWidth: width - textWidth
        Column
        {
            spacing: UM.Theme.getSize("default_margin").height

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
                    width: tabControl.textWidth
                }

                OldControls.CheckBox
                {
                    checked: tabControl.model != null ? Cura.MachineManager.getExtruder(tabControl.model.index).isEnabled: false
                    onClicked: Cura.MachineManager.setExtruderEnabled(tabControl.model.index, checked)
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
                    width: tabControl.textWidth
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
                    width: tabControl.controlWidth

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
                    width: tabControl.textWidth
                }

                OldControls.ToolButton
                {
                    id: variantSelection
                    text: Cura.MachineManager.activeVariantName
                    tooltip: Cura.MachineManager.activeVariantName;
                    visible: Cura.MachineManager.hasVariants

                    height: UM.Theme.getSize("setting_control").height
                    width: tabControl.controlWidth
                    style: UM.Theme.styles.sidebar_header_button
                    activeFocusOnPress: true;

                    menu: Cura.NozzleMenu { extruderIndex: Cura.ExtruderManager.activeExtruderIndex }
                }
            }
        }
    }
}