// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.11

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
                width: Math.round(ListView.view.width / extrudersModel.rowCount())

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

    popupItem: Item
    {
        id: popupItem
        width: base.width - 2 * UM.Theme.getSize("default_margin").width
        height: 200

        property var is_connected: false //If current machine is connected to a printer. Only evaluated upon making popup visible.
        onVisibleChanged:
        {
            is_connected = Cura.MachineManager.activeMachineNetworkKey != "" && Cura.MachineManager.printerConnected //Re-evaluate.
        }

        property var configuration_method: buttonBar.visible ? "auto" : "custom" //Auto if connected to a printer at start-up, or Custom if not.

        AutoConfiguration
        {
            id: autoConfiguration
            visible: popupItem.configuration_method === "auto"
            anchors.top: parent.top
        }

        CustomConfiguration
        {
            id: customConfiguration
            visible: popupItem.configuration_method === "custom"
            anchors.top: parent.top
        }

        Rectangle
        {
            id: separator
            visible: buttonBar.visible

            anchors
            {
                left: parent.left
                right: parent.right
                bottom: buttonBar.top
                bottomMargin: UM.Theme.getSize("default_margin").height
            }
            height: UM.Theme.getSize("default_lining").height

            color: UM.Theme.getColor("lining")
        }

        //Allow switching between custom and auto.
        Rectangle
        {
            id: buttonBar
            visible: popupItem.is_connected //Switching only makes sense if the "auto" part is possible.

            anchors
            {
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            height: childrenRect.height

            Cura.ActionButton
            {
                id: goToCustom
                visible: popupItem.configuration_method === "auto"
                text: catalog.i18nc("@label", "Custom")

                anchors
                {
                    right: parent.right
                    bottom: parent.bottom
                }

                color: UM.Theme.getColor("secondary")
                hoverColor: UM.Theme.getColor("secondary")
                textColor: UM.Theme.getColor("primary")
                textHoverColor: UM.Theme.getColor("text")

                iconSource: UM.Theme.getIcon("arrow_right")
                iconOnRightSide: true

                onClicked: popupItem.configuration_method = "custom"
            }

            Cura.ActionButton
            {
                id: goToAuto
                visible: popupItem.configuration_method === "custom"
                text: catalog.i18nc("@label", "Configurations")

                anchors
                {
                    left: parent.left
                    bottom: parent.bottom
                }

                color: UM.Theme.getColor("secondary")
                hoverColor: UM.Theme.getColor("secondary")
                textColor: UM.Theme.getColor("primary")
                textHoverColor: UM.Theme.getColor("text")

                iconSource: UM.Theme.getIcon("arrow_left")

                onClicked: popupItem.configuration_method = "auto"
            }
        }
    }
}
