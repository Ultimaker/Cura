// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3
import QtQuick.Controls 1.4 as Controls1

import UM 1.1 as UM
import Cura 1.0 as Cura

Column
{
    id: widget

    spacing: UM.Theme.getSize("thin_margin").height

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    Item
    {
        id: information
        width: parent.width
        height: childrenRect.height

        Column
        {
            id: timeAndCostsInformation
            spacing: UM.Theme.getSize("thin_margin").height

            anchors
            {
                left: parent.left
                right: moreInformationIcon.left
                rightMargin: UM.Theme.getSize("thin_margin").height
            }

            Cura.IconLabel
            {
                id: estimatedTime
                width: parent.width

                property var printDuration: PrintInformation.currentPrintTime

                text: printDuration.getDisplayString(UM.DurationFormat.Long)
                source: UM.Theme.getIcon("clock")
                font: UM.Theme.getFont("small")
            }

            Cura.IconLabel
            {
                id: estimatedCosts
                width: parent.width

                property var printMaterialLengths: PrintInformation.materialLengths
                property var printMaterialWeights: PrintInformation.materialWeights

                function getText()
                {
                    var lengths = []
                    var weights = []
                    if(printMaterialLengths)
                    {
                        for(var index = 0; index < printMaterialLengths.length; index++)
                        {
                            if(printMaterialLengths[index] > 0)
                            {
                                lengths.push(printMaterialLengths[index].toFixed(2))
                                weights.push(String(Math.round(printMaterialWeights[index])))
                            }
                        }
                    }
                    if(lengths.length == 0)
                    {
                        lengths = ["0.00"]
                        weights = ["0"]
                    }
                    return weights.join(" + ") + "g · " + lengths.join(" + ") + "m"
                }

                text: getText()
                source: UM.Theme.getIcon("spool")
                font: UM.Theme.getFont("very_small")
            }
        }

        UM.RecolorImage
        {
            id: moreInformationIcon

            anchors
            {
                right: parent.right
                verticalCenter: timeAndCostsInformation.verticalCenter
            }

            source: UM.Theme.getIcon("info")
            width: UM.Theme.getSize("section_icon").width
            height: UM.Theme.getSize("section_icon").height

            sourceSize.width: width
            sourceSize.height: height

            color: UM.Theme.getColor("text_medium")
        }
    }

    Row
    {
        id: buttonRow
        spacing: UM.Theme.getSize("default_margin").width

        Cura.ActionButton
        {
            height: UM.Theme.getSize("action_panel_button").height
            text: catalog.i18nc("@button", "Preview")
            color: UM.Theme.getColor("secondary")
            hoverColor: UM.Theme.getColor("secondary")
            textColor: UM.Theme.getColor("primary")
            textHoverColor: UM.Theme.getColor("text")
            onClicked: console.log("Clicking preview")
        }

        Cura.OutputDevicesActionButton
        {
            width: UM.Theme.getSize("action_panel_button").width
            height: UM.Theme.getSize("action_panel_button").height
        }
    }
}