import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura


Item
{
    property alias color: background.color
    property var extruderModel
    property var position: index
    //width: index == machineExtruderCount.properties.value - 1 && index % 2 == 0 ? extrudersGrid.width : Math.floor(extrudersGrid.width / 2 - UM.Theme.getSize("sidebar_lining_thin").width / 2)
    implicitWidth: parent.width
    implicitHeight: UM.Theme.getSize("sidebar_extruder_box").height
    Rectangle
    {
        id: background
        anchors.fill: parent

        Label //Extruder name.
        {
            text: Cura.ExtruderManager.getExtruderName(position) != "" ? Cura.ExtruderManager.getExtruderName(position) : catalog.i18nc("@label", "Extruder")
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("default")
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.margins: UM.Theme.getSize("default_margin").width
        }

        Label //Target temperature.
        {
            id: extruderTargetTemperature
            text: Math.round(extruderModel.targetHotendTemperature) + "°C"
            //text: (connectedPrinter != null && connectedPrinter.hotendIds[index] != null && connectedPrinter.targetHotendTemperatures[index] != null) ? Math.round(connectedPrinter.targetHotendTemperatures[index]) + "°C" : ""
            font: UM.Theme.getFont("small")
            color: UM.Theme.getColor("text_inactive")
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.bottom: extruderTemperature.bottom

            MouseArea //For tooltip.
            {
                id: extruderTargetTemperatureTooltipArea
                hoverEnabled: true
                anchors.fill: parent
                onHoveredChanged:
                {
                    if (containsMouse)
                    {
                        base.showTooltip(
                            base,
                            {x: 0, y: extruderTargetTemperature.mapToItem(base, 0, -parent.height / 4).y},
                            catalog.i18nc("@tooltip", "The target temperature of the hotend. The hotend will heat up or cool down towards this temperature. If this is 0, the hotend heating is turned off.")
                        );
                    }
                    else
                    {
                        base.hideTooltip();
                    }
                }
            }
        }
        Label //Temperature indication.
        {
            id: extruderTemperature
            text: Math.round(extruderModel.hotendTemperature) + "°C"
            //text: (connectedPrinter != null && connectedPrinter.hotendIds[index] != null && connectedPrinter.hotendTemperatures[index] != null) ? Math.round(connectedPrinter.hotendTemperatures[index]) + "°C" : ""
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("large")
            anchors.right: extruderTargetTemperature.left
            anchors.top: parent.top
            anchors.margins: UM.Theme.getSize("default_margin").width

            MouseArea //For tooltip.
            {
                id: extruderTemperatureTooltipArea
                hoverEnabled: true
                anchors.fill: parent
                onHoveredChanged:
                {
                    if (containsMouse)
                    {
                        base.showTooltip(
                            base,
                            {x: 0, y: parent.mapToItem(base, 0, -parent.height / 4).y},
                            catalog.i18nc("@tooltip", "The current temperature of this extruder.")
                        );
                    }
                    else
                    {
                        base.hideTooltip();
                    }
                }
            }
        }

        Rectangle //Material colour indication.
        {
            id: materialColor
            width: Math.floor(materialName.height * 0.75)
            height: Math.floor(materialName.height * 0.75)
            radius: width / 2
            color: extruderModel.activeMaterial ? extruderModel.activeMaterial.color: "#00000000"
            border.width: UM.Theme.getSize("default_lining").width
            border.color: UM.Theme.getColor("lining")
            visible: extruderModel.activeMaterial != null
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: materialName.verticalCenter

            MouseArea //For tooltip.
            {
                id: materialColorTooltipArea
                hoverEnabled: true
                anchors.fill: parent
                onHoveredChanged:
                {
                    if (containsMouse)
                    {
                        base.showTooltip(
                            base,
                            {x: 0, y: parent.mapToItem(base, 0, -parent.height / 2).y},
                            catalog.i18nc("@tooltip", "The colour of the material in this extruder.")
                        );
                    }
                    else
                    {
                        base.hideTooltip();
                    }
                }
            }
        }
        Label //Material name.
        {
            id: materialName
            text: extruderModel.activeMaterial != null ? extruderModel.activeMaterial.type : ""
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text")
            anchors.left: materialColor.right
            anchors.bottom: parent.bottom
            anchors.margins: UM.Theme.getSize("default_margin").width

            MouseArea //For tooltip.
            {
                id: materialNameTooltipArea
                hoverEnabled: true
                anchors.fill: parent
                onHoveredChanged:
                {
                    if (containsMouse)
                    {
                        base.showTooltip(
                            base,
                            {x: 0, y: parent.mapToItem(base, 0, 0).y},
                            catalog.i18nc("@tooltip", "The material in this extruder.")
                        );
                    }
                    else
                    {
                        base.hideTooltip();
                    }
                }
            }
        }
        Label //Variant name.
        {
            id: variantName
            text: extruderModel.hotendID
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text")
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: UM.Theme.getSize("default_margin").width

            MouseArea //For tooltip.
            {
                id: variantNameTooltipArea
                hoverEnabled: true
                anchors.fill: parent
                onHoveredChanged:
                {
                    if (containsMouse)
                    {
                        base.showTooltip(
                            base,
                            {x: 0, y: parent.mapToItem(base, 0, -parent.height / 4).y},
                            catalog.i18nc("@tooltip", "The nozzle inserted in this extruder.")
                        );
                    }
                    else
                    {
                        base.hideTooltip();
                    }
                }
            }
        }
    }
}