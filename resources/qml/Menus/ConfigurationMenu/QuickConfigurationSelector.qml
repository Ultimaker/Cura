// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.11

import QtQuick.Controls 1.1 as OldControls

import UM 1.2 as UM
import Cura 1.0 as Cura


Cura.ExpandableComponent
{
    id: base

    Cura.ExtrudersModel
    {
        id: extrudersModel
    }

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    iconSource: expanded ? UM.Theme.getIcon("arrow_left") : UM.Theme.getIcon("arrow_bottom")

    headerItem: Item
    {
        // Horizontal list that shows the extruders
        ListView
        {
            id: extrudersList

            orientation: ListView.Horizontal
            anchors.fill: parent
            model: extrudersModel

            delegate: Item
            {
                height: parent.height
                width: Math.round(ListView.view.width / extrudersModel.rowCount())

                // Extruder icon. Shows extruder index and has the same color as the active material.
                Cura.ExtruderIcon
                {
                    id: extruderIcon
                    materialColor: model.color
                    height: parent.height
                    width: height
                }

                // Label for the brand of the material
                Label
                {
                    id: brandNameLabel

                    text: model.material_brand
                    elide: Text.ElideRight

                    anchors
                    {
                        left: extruderIcon.right
                        leftMargin: UM.Theme.getSize("default_margin").width
                        right: parent.right
                        rightMargin: UM.Theme.getSize("default_margin").width
                    }
                }

                // Label that shows the name of the material
                Label
                {
                    text: model.material
                    elide: Text.ElideRight

                    anchors
                    {
                        left: extruderIcon.right
                        leftMargin: UM.Theme.getSize("default_margin").width
                        right: parent.right
                        rightMargin: UM.Theme.getSize("default_margin").width
                        top: brandNameLabel.bottom
                    }
                }
            }
        }
    }

    popupItem: Item
    {
        width: base.width
        height: 200

        TabBar
        {
            id: tabBar
            onCurrentIndexChanged: Cura.ExtruderManager.setActiveExtruderIndex(currentIndex)
            width: parent.width
            height: 50
            Repeater
            {
                model: extrudersModel

                delegate: TabButton
                {
                    width: Math.round(ListView.view.width / extrudersModel.rowCount())
                    height: parent.height
                    contentItem: Item
                    {
                        Cura.ExtruderIcon
                        {
                            anchors.horizontalCenter: parent.horizontalCenter
                            materialColor: model.color
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
            anchors.top: tabBar.bottom
            anchors.bottom: parent.bottom
            property var model: extrudersModel.items[tabBar.currentIndex]
            property real textWidth: Math.round(width * 0.3)
            property real controlWidth: Math.round(width * 0.7)
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
                        checked: Cura.MachineManager.getExtruder(parent.model.index).isEnabled
                        onClicked: Cura.MachineManager.setExtruderEnabled(parent.model.index, checked)
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
                        property var valueWarning: ! Cura.MachineManager.isActiveQualitySupported

                        text: currentRootMaterialName
                        tooltip: currentRootMaterialName
                        visible: Cura.MachineManager.hasMaterials

                        enabled: !extrudersList.visible || Cura.ExtruderManager.activeExtruderIndex > -1

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

}

/*Item
{
    id: configurationSelector
    property var connectedDevice: Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null
    property var panelWidth: control.width

    // Make this component only visible when it's a network printer and it is connected
    visible: Cura.MachineManager.activeMachineNetworkKey != "" && Cura.MachineManager.printerConnected

    function switchPopupState()
    {
        popup.visible ? popup.close() : popup.open()
    }

    SyncButton
    {
        id: syncButton
        onClicked: switchPopupState()
        outputDevice: connectedDevice
    }

    Popup
    {
        // TODO Change once updating to Qt5.10 - The 'opened' property is in 5.10 but the behavior is now implemented with the visible property
        id: popup
        clip: true
        closePolicy: Popup.CloseOnPressOutsideParent
        y: configurationSelector.height - UM.Theme.getSize("default_lining").height
        x: configurationSelector.width - width
        width: panelWidth
        visible: false
        padding: UM.Theme.getSize("default_lining").width
        transformOrigin: Popup.Top
        contentItem: ConfigurationListView
        {
            id: configList
            width: panelWidth - 2 * popup.padding
            outputDevice: connectedDevice
        }
        background: Rectangle
        {
            color: UM.Theme.getColor("setting_control")
            border.color: UM.Theme.getColor("setting_control_border")
        }
        exit: Transition
        {
            // This applies a default NumberAnimation to any changes a state change makes to x or y properties
            NumberAnimation { property: "visible"; duration: 75; }
        }
        enter: Transition
        {
            // This applies a default NumberAnimation to any changes a state change makes to x or y properties
            NumberAnimation { property: "visible"; duration: 75; }
        }
        onClosed: visible = false
        onOpened: visible = true
    }
}*/