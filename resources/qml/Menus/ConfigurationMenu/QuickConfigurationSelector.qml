// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.3

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
                    extruderEnabled: model.enabled
                    anchors.verticalCenter: parent.verticalCenter
                }

                // Label for the brand of the material
                Label
                {
                    id: brandNameLabel

                    text: model.material_brand
                    elide: Text.ElideRight
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")

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
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")

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

    contentItem: Item
    {
        width: base.width - 2 * UM.Theme.getSize("default_margin").width
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
                    width: ListView.view != null ?  Math.round(ListView.view.width / extrudersModel.rowCount()): 0
                    height: parent.height
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
            anchors.top: tabBar.bottom
            anchors.bottom: parent.bottom
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
                        renderType: Text.NativeRendering
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
                        renderType: Text.NativeRendering
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
                        renderType: Text.NativeRendering
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
