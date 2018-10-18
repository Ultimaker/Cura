// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

import UM 1.2 as UM
import Cura 1.0 as Cura

Rectangle
{
    id: base

    // We need a whole lot of print duration information.
    property variant printDuration: PrintInformation.currentPrintTime

    // This widget doesn't show tooltips by itself. Instead it emits signals so others can do something with it.
    signal showTooltip(Item item, point location, string text)
    signal hideTooltip()

    // Also add an extra margin, as we ant some breathing room around the edges.
    height: saveButton.height + UM.Theme.getSize("sidebar_margin").height
    Label
    {
        id: timeDetails
        anchors.left: parent.left
        anchors.bottom: costSpec.top
        anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width

        font: UM.Theme.getFont("large")
        color: UM.Theme.getColor("text_subtext")
        text: (!base.printDuration || !base.printDuration.valid) ? catalog.i18nc("@label Hours and minutes", "00h 00min") : base.printDuration.getDisplayString(UM.DurationFormat.Short)
        renderType: Text.NativeRendering

        MouseArea
        {
            id: timeDetailsMouseArea
            anchors.fill: parent
            hoverEnabled: true

            onEntered:
            {
                if(base.printDuration.valid && !base.printDuration.isTotalDurationZero)
                {
                    // All the time information for the different features is achieved
                    var print_time = PrintInformation.getFeaturePrintTimes();
                    var total_seconds = parseInt(base.printDuration.getDisplayString(UM.DurationFormat.Seconds))

                    // A message is created and displayed when the user hover the time label
                    var tooltip_html = "<b>%1</b><br/><table width=\"100%\">".arg(catalog.i18nc("@tooltip", "Time specification"));
                    for(var feature in print_time)
                    {
                        if(!print_time[feature].isTotalDurationZero)
                        {
                            tooltip_html += "<tr><td>" + feature + ":</td>" +
                                "<td align=\"right\" valign=\"bottom\">&nbsp;&nbsp;%1</td>".arg(print_time[feature].getDisplayString(UM.DurationFormat.ISO8601).slice(0,-3)) +
                                "<td align=\"right\" valign=\"bottom\">&nbsp;&nbsp;%1%</td>".arg(Math.round(100 * parseInt(print_time[feature].getDisplayString(UM.DurationFormat.Seconds)) / total_seconds)) +
                                "</td></tr>";
                        }
                    }
                    tooltip_html += "</table>";
                    base.showTooltip(parent, Qt.point(-UM.Theme.getSize("sidebar_margin").width, 0), tooltip_html);
                }
            }
            onExited:
            {
                base.hideTooltip();
            }
        }
    }

    Label
    {
        function formatRow(items)
        {
            var row_html = "<tr>";
            for(var item = 0; item < items.length; item++)
            {
                if (item == 0)
                {
                    row_html += "<td valign=\"bottom\">%1</td>".arg(items[item]);
                }
                else
                {
                    row_html += "<td align=\"right\" valign=\"bottom\">&nbsp;&nbsp;%1</td>".arg(items[item]);
                }
            }
            row_html += "</tr>";
            return row_html;
        }

        function getSpecsData()
        {
            var lengths = [];
            var total_length = 0;
            var weights = [];
            var total_weight = 0;
            var costs = [];
            var total_cost = 0;
            var some_costs_known = false;
            var names = [];
            if(base.printMaterialLengths)
            {
                for(var index = 0; index < base.printMaterialLengths.length; index++)
                {
                    if(base.printMaterialLengths[index] > 0)
                    {
                        names.push(base.printMaterialNames[index]);
                        lengths.push(base.printMaterialLengths[index].toFixed(2));
                        weights.push(String(Math.round(base.printMaterialWeights[index])));
                        var cost = base.printMaterialCosts[index] == undefined ? 0 : base.printMaterialCosts[index].toFixed(2);
                        costs.push(cost);
                        if(cost > 0)
                        {
                            some_costs_known = true;
                        }

                        total_length += base.printMaterialLengths[index];
                        total_weight += base.printMaterialWeights[index];
                        total_cost += base.printMaterialCosts[index];
                    }
                }
            }
            if(lengths.length == 0)
            {
                lengths = ["0.00"];
                weights = ["0"];
                costs = ["0.00"];
            }

            var tooltip_html = "<b>%1</b><br/><table width=\"100%\">".arg(catalog.i18nc("@label", "Cost specification"));
            for(var index = 0; index < lengths.length; index++)
            {
                tooltip_html += formatRow([
                    "%1:".arg(names[index]),
                    catalog.i18nc("@label m for meter", "%1m").arg(lengths[index]),
                    catalog.i18nc("@label g for grams", "%1g").arg(weights[index]),
                    "%1&nbsp;%2".arg(UM.Preferences.getValue("cura/currency")).arg(costs[index]),
                ]);
            }
            if(lengths.length > 1)
            {
                tooltip_html += formatRow([
                    catalog.i18nc("@label", "Total:"),
                    catalog.i18nc("@label m for meter", "%1m").arg(total_length.toFixed(2)),
                    catalog.i18nc("@label g for grams", "%1g").arg(Math.round(total_weight)),
                    "%1 %2".arg(UM.Preferences.getValue("cura/currency")).arg(total_cost.toFixed(2)),
                ]);
            }
            tooltip_html += "</table>";
            tooltipText = tooltip_html;

            return tooltipText
        }

        id: costSpec

        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.bottomMargin: UM.Theme.getSize("sidebar_margin").height
        anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width

        font: UM.Theme.getFont("very_small")
        renderType: Text.NativeRendering
        color: UM.Theme.getColor("text_subtext")
        elide: Text.ElideMiddle
        width: parent.width
        property string tooltipText
        text:
        {
            var lengths = [];
            var weights = [];
            var costs = [];
            var someCostsKnown = false;
            if(base.printMaterialLengths)
            {
                for(var index = 0; index < base.printMaterialLengths.length; index++)
                {
                    if(base.printMaterialLengths[index] > 0)
                    {
                        lengths.push(base.printMaterialLengths[index].toFixed(2));
                        weights.push(String(Math.round(base.printMaterialWeights[index])));
                        var cost = base.printMaterialCosts[index] == undefined ? 0 : base.printMaterialCosts[index].toFixed(2);
                        costs.push(cost);
                        if(cost > 0)
                        {
                            someCostsKnown = true;
                        }
                    }
                }
            }
            if(lengths.length == 0)
            {
                lengths = ["0.00"];
                weights = ["0"];
                costs = ["0.00"];
            }
            var result = lengths.join(" + ") + "m / ~ " + weights.join(" + ") + "g";
            if(someCostsKnown)
            {
                result += " / ~ " + costs.join(" + ") + " " + UM.Preferences.getValue("cura/currency");
            }
            return result;
        }

        MouseArea
        {
            id: costSpecMouseArea
            anchors.fill: parent
            hoverEnabled: true

            onEntered:
            {

                if(base.printDuration.valid && !base.printDuration.isTotalDurationZero)
                {
                    var show_data = costSpec.getSpecsData()

                    base.showTooltip(parent, Qt.point(-UM.Theme.getSize("sidebar_margin").width, 0), show_data);
                }
            }
            onExited:
            {
                base.hideTooltip();
            }
        }
    }

    SaveButton
    {
        id: saveButton
        width: parent.width
        height: 100
        anchors.bottom: parent.bottom
    }
}