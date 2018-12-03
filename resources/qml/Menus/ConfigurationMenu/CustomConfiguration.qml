// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.6
import QtQuick.Controls 2.0
import QtQuick.Controls 1.1 as OldControls

import Cura 1.0 as Cura
import UM 1.3 as UM

Item
{
    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

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
        visible: Cura.MachineManager.numberExtrudersEnabled > 1

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

        radius: tabBar.visible ? UM.Theme.getSize("default_radius").width : 0
        border.width: tabBar.visible ? UM.Theme.getSize("default_lining").width : 0
        border.color: UM.Theme.getColor("lining")
        color: UM.Theme.getColor("main_background")

        //Remove rounding and lining at the top.
        Rectangle
        {
            width: parent.width
            height: parent.radius
            anchors.top: parent.top
            color: UM.Theme.getColor("lining")
            visible: tabBar.visible
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
                    checked: Cura.MachineManager.activeStack != null ? Cura.MachineManager.activeStack.isEnabled : false
                    enabled: !checked || Cura.MachineManager.numberExtrudersEnabled > 1 //Disable if it's the last enabled extruder.
                    height: UM.Theme.getSize("setting_control").height
                    style: UM.Theme.styles.checkbox

                    /* Use a MouseArea to process the click on this checkbox.
                       This is necessary because actually clicking the checkbox
                       causes the "checked" property to be overwritten. After
                       it's been overwritten, the original link that made it
                       depend on the active extruder stack is broken. */
                    MouseArea
                    {
                        anchors.fill: parent
                        onClicked: Cura.MachineManager.setExtruderEnabled(Cura.ExtruderManager.activeExtruderIndex, !parent.checked)
                        enabled: parent.enabled
                    }
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

                    property var valueError: Cura.MachineManager.activeStack != null ? Cura.ContainerManager.getContainerMetaDataEntry(Cura.MachineManager.activeStack.material.id, "compatible", "") != "True" : true
                    property var valueWarning: !Cura.MachineManager.isActiveQualitySupported

                    text: Cura.MachineManager.activeStack != null ? Cura.MachineManager.activeStack.material.name : ""
                    tooltip: text
                    visible: Cura.MachineManager.hasMaterials

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