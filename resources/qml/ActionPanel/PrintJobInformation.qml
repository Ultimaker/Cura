// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1

import UM 1.1 as UM
import Cura 1.0 as Cura

Column
{
    id: base
    spacing: UM.Theme.getSize("default_margin").width

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    Column
    {
        id: timeSpecification
        width: parent.width
        topPadding: UM.Theme.getSize("default_margin").height
        leftPadding: UM.Theme.getSize("default_margin").width
        rightPadding: UM.Theme.getSize("default_margin").width

        Label
        {
            text: catalog.i18nc("@label", "Time specification").toUpperCase()
            color: UM.Theme.getColor("primary")
            font: UM.Theme.getFont("default_bold")
            renderType: Text.NativeRendering
        }

        Label
        {
            property var printDuration: PrintInformation.currentPrintTime

            text:
            {
                // All the time information for the different features is achieved
                var printTime = PrintInformation.getFeaturePrintTimes()
                var totalSeconds = parseInt(printDuration.getDisplayString(UM.DurationFormat.Seconds))

                // A message is created and displayed when the user hover the time label
                var text = "<table width=\"100%\">"
                for(var feature in printTime)
                {
                    if(!printTime[feature].isTotalDurationZero)
                    {
                        text += "<tr><td>" + feature + ":</td>" +
                            "<td align=\"right\" valign=\"bottom\">&nbsp;&nbsp;%1</td>".arg(printTime[feature].getDisplayString(UM.DurationFormat.ISO8601).slice(0,-3)) +
                            "<td align=\"right\" valign=\"bottom\">&nbsp;&nbsp;%1%</td>".arg(Math.round(100 * parseInt(printTime[feature].getDisplayString(UM.DurationFormat.Seconds)) / totalSeconds)) +
                            "</tr>"
                    }
                }
                text += "</table>"
                return text
            }
            width: parent.width - 2 * UM.Theme.getSize("default_margin").width
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("default")
            renderType: Text.NativeRendering
            textFormat: Text.RichText
        }
    }

    Column
    {
        id: materialSpecification
        width: parent.width
        bottomPadding: UM.Theme.getSize("default_margin").height
        leftPadding: UM.Theme.getSize("default_margin").width
        rightPadding: UM.Theme.getSize("default_margin").width

        Label
        {
            text: catalog.i18nc("@label", "Material specification").toUpperCase()
            color: UM.Theme.getColor("primary")
            font: UM.Theme.getFont("default_bold")
            renderType: Text.NativeRendering
        }
        
        Label
        {
            property var printMaterialLengths: PrintInformation.materialLengths
            property var printMaterialWeights: PrintInformation.materialWeights
            property var printMaterialCosts: PrintInformation.materialCosts
            property var printMaterialNames: PrintInformation.materialNames

            function formatRow(items)
            {
                var rowHTML = "<tr>"
                for(var item = 0; item < items.length; item++)
                {
                    if (item == 0)
                    {
                        rowHTML += "<td valign=\"bottom\">%1</td>".arg(items[item])
                    }
                    else
                    {
                        rowHTML += "<td align=\"right\" valign=\"bottom\">&nbsp;&nbsp;%1</td>".arg(items[item])
                    }
                }
                rowHTML += "</tr>"
                return rowHTML
            }

            text:
            {
                var lengths = []
                var weights = []
                var costs = []
                var names = []
                if(printMaterialLengths)
                {
                    for(var index = 0; index < printMaterialLengths.length; index++)
                    {
                        if(printMaterialLengths[index] > 0)
                        {
                            names.push(printMaterialNames[index])
                            lengths.push(printMaterialLengths[index].toFixed(2))
                            weights.push(String(Math.round(printMaterialWeights[index])))
                            var cost = printMaterialCosts[index] == undefined ? 0 : printMaterialCosts[index].toFixed(2)
                            costs.push(cost)
                        }
                    }
                }
                if(lengths.length == 0)
                {
                    lengths = ["0.00"]
                    weights = ["0"]
                    costs = ["0.00"]
                }

                var text = "<table width=\"100%\">"
                for(var index = 0; index < lengths.length; index++)
                {
                    text += formatRow([
                        "%1:".arg(names[index]),
                        catalog.i18nc("@label m for meter", "%1m").arg(lengths[index]),
                        catalog.i18nc("@label g for grams", "%1g").arg(weights[index]),
                        "%1&nbsp;%2".arg(UM.Preferences.getValue("cura/currency")).arg(costs[index]),
                    ])
                }
                text += "</table>"

                return text
            }
            width: parent.width - 2 * UM.Theme.getSize("default_margin").width
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("default")
            renderType: Text.NativeRendering
            textFormat: Text.RichText
        }
    }
}