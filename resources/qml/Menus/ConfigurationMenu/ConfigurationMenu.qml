// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.3

import UM 1.2 as UM
import Cura 1.0 as Cura


/**
 * Menu that allows you to select the configuration of the current printer, such
 * as the nozzle sizes and materials in each extruder.
 */
Cura.ExpandablePopup
{
    id: base

    property var extrudersModel: CuraApplication.getExtrudersModel()

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    enum ConfigurationMethod
    {
        Auto,
        Custom
    }

    contentPadding: UM.Theme.getSize("default_lining").width
    enabled: Cura.MachineManager.activeMachine.hasMaterials || Cura.MachineManager.activeMachine.hasVariants || Cura.MachineManager.activeMachine.hasVariantBuildplates; //Only let it drop down if there is any configuration that you could change.

    headerItem: Item
    {
        // Horizontal list that shows the extruders and their materials
        RowLayout
        {
            anchors.fill: parent
            Repeater
            {
                model: extrudersModel
                delegate: Item
                {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    // Extruder icon. Shows extruder index and has the same color as the active material.
                    Cura.ExtruderIcon
                    {
                        id: extruderIcon
                        materialColor: model.color
                        extruderEnabled: model.enabled
                        height: parent.height
                        width: height
                    }

                    // Label for the brand of the material
                    Label
                    {
                        id: typeAndBrandNameLabel

                        text: model.material_brand + " " + model.material
                        elide: Text.ElideRight
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")
                        renderType: Text.NativeRendering

                        anchors
                        {
                            top: extruderIcon.top
                            left: extruderIcon.right
                            leftMargin: UM.Theme.getSize("default_margin").width
                            right: parent.right
                            rightMargin: UM.Theme.getSize("default_margin").width
                        }
                    }
                    // Label that shows the name of the variant
                    Label
                    {
                        id: variantLabel

                        visible: Cura.MachineManager.activeMachine.hasVariants

                        text: model.variant
                        elide: Text.ElideRight
                        font: UM.Theme.getFont("default_bold")
                        color: UM.Theme.getColor("text")
                        renderType: Text.NativeRendering

                        anchors
                        {
                            left: extruderIcon.right
                            leftMargin: UM.Theme.getSize("default_margin").width
                            top: typeAndBrandNameLabel.bottom
                            right: parent.right
                            rightMargin:  UM.Theme.getSize("default_margin").width
                        }
                    }
                }
            }
        }

        // Placeholder text if there is a configuration to select but no materials (so we can't show the materials per extruder).
        Label
        {
            text: catalog.i18nc("@label", "Select configuration")
            elide: Text.ElideRight
            font: UM.Theme.getFont("medium")
            color: UM.Theme.getColor("text")
            renderType: Text.NativeRendering

            visible: !Cura.MachineManager.activeMachine.hasMaterials && (Cura.MachineManager.activeMachine.hasVariants || Cura.MachineManager.activeMachine.hasVariantBuildplates)

            anchors
            {
                left: parent.left
                leftMargin: UM.Theme.getSize("default_margin").width
                verticalCenter: parent.verticalCenter
            }
        }
    }

    contentItem: Column
    {
        id: popupItem
        width: UM.Theme.getSize("configuration_selector").width
        height: implicitHeight  // Required because ExpandableComponent will try to use this to determine the size of the background of the pop-up.
        padding: UM.Theme.getSize("default_margin").height
        spacing: UM.Theme.getSize("default_margin").height

        property bool is_connected: false  // If current machine is connected to a printer. Only evaluated upon making popup visible.
        property int configuration_method: ConfigurationMenu.ConfigurationMethod.Custom  // Type of configuration being used. Only evaluated upon making popup visible.
        property int manual_selected_method: -1  // It stores the configuration method selected by the user. By default the selected method is

        onVisibleChanged:
        {
            is_connected = Cura.MachineManager.activeMachine.hasRemoteConnection && Cura.MachineManager.printerConnected && Cura.MachineManager.printerOutputDevices[0].uniqueConfigurations.length > 0 //Re-evaluate.

            // If the printer is not connected or does not have configurations, we switch always to the custom mode. If is connected instead, the auto mode
            // or the previous state is selected
            configuration_method = is_connected ? (manual_selected_method == -1 ? ConfigurationMenu.ConfigurationMethod.Auto : manual_selected_method) : ConfigurationMenu.ConfigurationMethod.Custom
        }

        Item
        {
            width: parent.width - 2 * parent.padding
            height:
            {
                var height = 0
                if (autoConfiguration.visible)
                {
                    height += autoConfiguration.height
                }
                if (customConfiguration.visible)
                {
                    height += customConfiguration.height
                }
                return height
            }

            AutoConfiguration
            {
                id: autoConfiguration
                visible: popupItem.configuration_method == ConfigurationMenu.ConfigurationMethod.Auto
            }

            CustomConfiguration
            {
                id: customConfiguration
                visible: popupItem.configuration_method == ConfigurationMenu.ConfigurationMethod.Custom
            }
        }

        Rectangle
        {
            id: separator
            visible: buttonBar.visible
            x: -parent.padding

            width: parent.width
            height: UM.Theme.getSize("default_lining").height

            color: UM.Theme.getColor("lining")
        }

        //Allow switching between custom and auto.
        Item
        {
            id: buttonBar
            visible: popupItem.is_connected //Switching only makes sense if the "auto" part is possible.

            width: parent.width - 2 * parent.padding
            height: childrenRect.height

            Cura.SecondaryButton
            {
                id: goToCustom
                visible: popupItem.configuration_method == ConfigurationMenu.ConfigurationMethod.Auto
                text: catalog.i18nc("@label", "Custom")

                anchors.right: parent.right

                iconSource: UM.Theme.getIcon("arrow_right")
                isIconOnRightSide: true

                onClicked:
                {
                    popupItem.configuration_method = ConfigurationMenu.ConfigurationMethod.Custom
                    popupItem.manual_selected_method = popupItem.configuration_method
                }
            }

            Cura.SecondaryButton
            {
                id: goToAuto
                visible: popupItem.configuration_method == ConfigurationMenu.ConfigurationMethod.Custom
                text: catalog.i18nc("@label", "Configurations")

                iconSource: UM.Theme.getIcon("arrow_left")

                onClicked:
                {
                    popupItem.configuration_method = ConfigurationMenu.ConfigurationMethod.Auto
                    popupItem.manual_selected_method = popupItem.configuration_method
                }
            }
        }
    }

    Connections
    {
        target: Cura.MachineManager
        onGlobalContainerChanged: popupItem.manual_selected_method = -1  // When switching printers, reset the value of the manual selected method
    }
}
