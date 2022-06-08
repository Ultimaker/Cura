// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.0 as Cura


/**
 * Menu that allows you to select the configuration of the current printer, such
 * as the nozzle sizes and materials in each extruder.
 */
Cura.ExpandablePopup
{
    id: base

    property var extrudersModel: CuraApplication.getExtrudersModel()
    property var activeMachine: Cura.MachineManager.activeMachine
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
    enabled: activeMachine ? activeMachine.hasMaterials || activeMachine.hasVariants || activeMachine.hasVariantBuildplates : false; //Only let it drop down if there is any configuration that you could change.

    headerItem: Item
    {
        id: headerBase

        // Horizontal list that shows the extruders and their materials
        RowLayout
        {
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            width: parent.width - UM.Theme.getSize("standard_arrow").width
            visible: activeMachine ? activeMachine.hasMaterials : false
            Repeater
            {
                model: extrudersModel
                delegate: Item
                {
                    id: extruderItem

                    Layout.preferredWidth: Math.floor(headerBase.width / extrudersModel.count)
                    Layout.maximumWidth: Math.floor(headerBase.width / extrudersModel.count)
                    Layout.preferredHeight: headerBase.height
                    Layout.maximumHeight: headerBase.height
                    Layout.fillHeight: true
                    Layout.alignment: Qt.AlignCenter

                    property var extruderStack: activeMachine ? activeMachine.extruderList[model.index]: null
                    property bool valueWarning: !Cura.ExtruderManager.getExtruderHasQualityForMaterial(extruderStack)
                    property bool valueError: activeMachine ? Cura.ContainerManager.getContainerMetaDataEntry(extruderStack.material.id, "compatible") != "True" : false

                    // Extruder icon. Shows extruder index and has the same color as the active material.
                    Cura.ExtruderIcon
                    {
                        id: extruderIcon
                        materialColor: model.color
                        extruderEnabled: model.enabled
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    MouseArea // Connection status tooltip hover area
                    {
                        id: tooltipHoverArea
                        anchors.fill: parent
                        hoverEnabled: tooltip.text != ""
                        acceptedButtons: Qt.NoButton // react to hover only, don't steal clicks

                        onEntered:
                        {
                            base.mouseArea.entered() // we want both this and the outer area to be entered
                            tooltip.show()
                        }
                        onExited: { tooltip.hide() }
                    }

                    UM.ToolTip
                    {
                        id: tooltip
                        x: 0
                        y: parent.height + UM.Theme.getSize("default_margin").height
                        width: UM.Theme.getSize("tooltip").width
                        targetPoint: Qt.point(Math.round(extruderIcon.width / 2), 0)
                        text:
                        {
                            if (!model.enabled)
                            {
                                return ""
                            }
                            if (extruderItem.valueError)
                            {
                                return catalog.i18nc("@tooltip", "The configuration of this extruder is not allowed, and prohibits slicing.")
                            }
                            if (extruderItem.valueWarning)
                            {
                                return catalog.i18nc("@tooltip", "There are no profiles matching the configuration of this extruder.")
                            }
                            return ""
                        }
                    }

                    // Warning icon that indicates if no qualities are available for the variant/material combination for this extruder
                    UM.ColorImage
                    {
                        id: badge
                        anchors
                        {
                            top: parent.top
                            topMargin: - Math.round(height * 1 / 6)
                            left: parent.left
                            leftMargin: extruderIcon.width - Math.round(width * 5 / 6)
                        }

                        width: UM.Theme.getSize("icon_indicator").width
                        height: UM.Theme.getSize("icon_indicator").height

                        visible: model.enabled && (extruderItem.valueError || extruderItem.valueWarning)

                        source:
                        {
                            if (extruderItem.valueError)
                            {
                                return UM.Theme.getIcon("ErrorBadge", "low")
                            }
                            if (extruderItem.valueWarning)
                            {
                                return UM.Theme.getIcon("WarningBadge", "low")
                            }
                            return ""
                        }

                        color:
                        {
                            if (extruderItem.valueError)
                            {
                                return UM.Theme.getColor("error")
                            }
                            if (extruderItem.valueWarning)
                            {
                                return UM.Theme.getColor("warning")
                            }
                            return "transparent"
                        }

                        // Make a themable circle in the background so we can change it in other themes
                        Rectangle
                        {
                            id: iconBackground
                            anchors.centerIn: parent
                            width: parent.width - 1.5  //1.5 pixels smaller, (at least sqrt(2), regardless of screen pixel scale) so that the circle doesn't show up behind the icon due to anti-aliasing.
                            height: parent.height - 1.5
                            radius: width / 2
                            z: parent.z - 1
                            color:
                            {
                                if (extruderItem.valueError)
                                {
                                    return UM.Theme.getColor("error_badge_background")
                                }
                                if (extruderItem.valueWarning)
                                {
                                    return UM.Theme.getColor("warning_badge_background")
                                }
                                return "transparent"
                            }
                        }
                    }

                    Column
                    {
                        opacity: model.enabled ? 1 : UM.Theme.getColor("extruder_disabled").a
                        spacing: 0
                        visible: width > 0
                        anchors
                        {
                            left: extruderIcon.right
                            leftMargin: UM.Theme.getSize("default_margin").width
                            verticalCenter: parent.verticalCenter
                            right: parent.right
                            rightMargin:  UM.Theme.getSize("default_margin").width
                        }
                        // Label for the brand of the material
                        UM.Label
                        {
                            id: materialBrandNameLabel

                            text:  model.material_brand + " " + model.material_name
                            elide: Text.ElideRight
                            wrapMode: Text.NoWrap
                            width: parent.width
                            visible: !truncated
                        }

                        UM.Label
                        {
                            id: materialNameLabel

                            text: model.material_name
                            elide: Text.ElideRight
                            width: parent.width
                            wrapMode: Text.NoWrap
                            visible: !materialBrandNameLabel.visible && !truncated
                        }

                        UM.Label
                        {
                            id: materialTypeLabel

                            text: model.material_type
                            elide: Text.ElideRight
                            width: parent.width
                            wrapMode: Text.NoWrap
                            visible: !materialBrandNameLabel.visible && !materialNameLabel.visible
                        }
                        // Label that shows the name of the variant
                        UM.Label
                        {
                            id: variantLabel

                            visible: activeMachine ? activeMachine.hasVariants : false

                            text: model.variant
                            elide: Text.ElideRight
                            wrapMode: Text.NoWrap
                            font: UM.Theme.getFont("default_bold")
                            Layout.preferredWidth: parent.width
                        }
                    }
                }
            }
        }

        // Placeholder text if there is a configuration to select but no materials (so we can't show the materials per extruder).
        UM.Label
        {
            text: catalog.i18nc("@label", "Select configuration")
            elide: Text.ElideRight
            font: UM.Theme.getFont("medium")

            visible: activeMachine ? !activeMachine.hasMaterials && (activeMachine.hasVariants || activeMachine.hasVariantBuildplates) : false

            anchors
            {
                left: parent.left
                leftMargin: UM.Theme.getSize("default_margin").width
                verticalCenter: parent.verticalCenter
            }
        }
    }

    contentWidth: UM.Theme.getSize("configuration_selector").width
    contentItem: Column
    {
        id: popupItem
        padding: UM.Theme.getSize("default_margin").height
        spacing: UM.Theme.getSize("default_margin").height

        property bool is_connected: false  // If current machine is connected to a printer. Only evaluated upon making popup visible.
        property int configuration_method: ConfigurationMenu.ConfigurationMethod.Custom  // Type of configuration being used. Only evaluated upon making popup visible.
        property int manual_selected_method: -1  // It stores the configuration method selected by the user. By default the selected method is

        onVisibleChanged:
        {
            is_connected = activeMachine.hasRemoteConnection && Cura.MachineManager.printerConnected && Cura.MachineManager.printerOutputDevices[0].uniqueConfigurations.length > 0 //Re-evaluate.

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

                iconSource: UM.Theme.getIcon("ChevronSingleRight")
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

                iconSource: UM.Theme.getIcon("ChevronSingleLeft")

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
        function onGlobalContainerChanged() { popupItem.manual_selected_method = -1 }  // When switching printers, reset the value of the manual selected method
    }
}
