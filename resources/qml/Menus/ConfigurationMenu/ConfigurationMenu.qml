// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura


/**
 * Menu that allows you to select the configuration of the current printer, such
 * as the nozzle sizes and materials in each extruder.
 */
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

    enum ConfigurationMethod
    {
        AUTO,
        CUSTOM
    }

    iconSource: expanded ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_left")
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
                width: Math.round(ListView.view.width / extrudersModel.count)

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
                    id: brandNameLabel

                    text: model.material_brand
                    elide: Text.ElideRight
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text_inactive")

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

    popupItem: Column
    {
        id: popupItem
        width: base.width - 2 * UM.Theme.getSize("default_margin").width
        height: implicitHeight //Required because ExpandableComponent will try to use this to determine the size of the background of the pop-up.
        spacing: UM.Theme.getSize("default_margin").height

        property bool is_connected: false //If current machine is connected to a printer. Only evaluated upon making popup visible.
        onVisibleChanged:
        {
            is_connected = Cura.MachineManager.activeMachineNetworkKey !== "" && Cura.MachineManager.printerConnected //Re-evaluate.
        }

        property int configuration_method: is_connected ? ConfigurationMenu.ConfigurationMethod.AUTO : ConfigurationMenu.ConfigurationMethod.CUSTOM //Auto if connected to a printer at start-up, or Custom if not.

        Item
        {
            width: parent.width
            height: childrenRect.height
            AutoConfiguration
            {
                id: autoConfiguration
                visible: popupItem.configuration_method == ConfigurationMenu.ConfigurationMethod.AUTO
            }

            CustomConfiguration
            {
                id: customConfiguration
                visible: popupItem.configuration_method == ConfigurationMenu.ConfigurationMethod.CUSTOM
            }
        }

        Rectangle
        {
            id: separator
            visible: buttonBar.visible

            width: parent.width
            height: UM.Theme.getSize("default_lining").height

            color: UM.Theme.getColor("lining")
        }

        //Allow switching between custom and auto.
        Item
        {
            id: buttonBar
            visible: popupItem.is_connected //Switching only makes sense if the "auto" part is possible.

            width: parent.width
            height: childrenRect.height

            Cura.SecondaryButton
            {
                id: goToCustom
                visible: popupItem.configuration_method == ConfigurationMenu.ConfigurationMethod.AUTO
                text: catalog.i18nc("@label", "Custom")

                anchors.right: parent.right

                iconSource: UM.Theme.getIcon("arrow_right")
                isIconOnRightSide: true

                onClicked: popupItem.configuration_method = ConfigurationMenu.ConfigurationMethod.CUSTOM
            }

            Cura.SecondaryButton
            {
                id: goToAuto
                visible: popupItem.configuration_method == ConfigurationMenu.ConfigurationMethod.CUSTOM
                text: catalog.i18nc("@label", "Configurations")

                iconSource: UM.Theme.getIcon("arrow_left")

                onClicked: popupItem.configuration_method = ConfigurationMenu.ConfigurationMethod.AUTO
            }
        }
    }
}
