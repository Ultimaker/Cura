// Copyright (c) 2019 Ultimaker B.V.
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
            id: byLineType

            property var printDuration: PrintInformation.currentPrintTime
            property var columnWidthMultipliers: [ 0.45, 0.3, 0.25 ]
            property var columnHorizontalAligns: [ Text.AlignLeft, Text.AlignHCenter, Text.AlignRight ]

            function getMaterialTable()
            {
                var result = []

                // All the time information for the different features is achieved
                var printTime = PrintInformation.getFeaturePrintTimes()
                var totalSeconds = parseInt(printDuration.getDisplayString(UM.DurationFormat.Seconds))

                // A message is created and displayed when the user hover the time label
                for(var feature in printTime)
                {
                    if(!printTime[feature].isTotalDurationZero)
                    {
                        var row = []
                        row.push(feature + ": ")
                        row.push("%1".arg(printTime[feature].getDisplayString(UM.DurationFormat.ISO8601).slice(0,-3)))
                        row.push("%1%".arg(Math.round(100 * parseInt(printTime[feature].getDisplayString(UM.DurationFormat.Seconds)) / totalSeconds)))
                        result.push(row)
                    }
                }

                return result
            }

            Column
            {
                Repeater
                {
                    model: byLineType.getMaterialTable()
                    Row
                    {
                        Repeater
                        {
                            model: modelData
                            Label
                            {
                                width: Math.round(byLineType.width * byLineType.columnWidthMultipliers[index])
                                height: contentHeight
                                horizontalAlignment: byLineType.columnHorizontalAligns[index]
                                color: UM.Theme.getColor("text")
                                font: UM.Theme.getFont("default")
                                wrapMode: Text.WrapAnywhere
                                text: modelData
                                renderType: Text.NativeRendering
                            }
                        }
                    }
                }
            }

            width: parent.width - 2 * UM.Theme.getSize("default_margin").width
            height: childrenRect.height
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
            id: byMaterialType

            property var printMaterialLengths: PrintInformation.materialLengths
            property var printMaterialWeights: PrintInformation.materialWeights
            property var printMaterialCosts: PrintInformation.materialCosts
            property var printMaterialNames: PrintInformation.materialNames
            property var columnWidthMultipliers: [ 0.46, 0.18, 0.18, 0.18 ]
            property var columnHorizontalAligns: [ Text.AlignLeft, Text.AlignHCenter, Text.AlignHCenter, Text.AlignRight ]

            function getMaterialTable()
            {
                var result = []

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

                for(var index = 0; index < lengths.length; index++)
                {
                    var row = []
                    row.push("%1".arg(names[index]))
                    row.push(catalog.i18nc("@label m for meter", "%1m").arg(lengths[index]))
                    row.push(catalog.i18nc("@label g for grams", "%1g").arg(weights[index]))
                    row.push("%1 %2".arg(UM.Preferences.getValue("cura/currency")).arg(costs[index]))
                    result.push(row)
                }

                return result
            }

            Column
            {
                Repeater
                {
                    model: byMaterialType.getMaterialTable()
                    Row
                    {
                        Repeater
                        {
                            model: modelData
                            Label
                            {
                                width: Math.round(byMaterialType.width * byMaterialType.columnWidthMultipliers[index])
                                height: contentHeight
                                horizontalAlignment: byMaterialType.columnHorizontalAligns[index]
                                color: UM.Theme.getColor("text")
                                font: UM.Theme.getFont("default")
                                wrapMode: Text.WrapAnywhere
                                text: modelData
                                renderType: Text.NativeRendering
                            }
                        }
                    }
                }
            }

            width: parent.width - 2 * UM.Theme.getSize("default_margin").width
            height: childrenRect.height
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("default")
            renderType: Text.NativeRendering
            textFormat: Text.RichText
        }
    }
}