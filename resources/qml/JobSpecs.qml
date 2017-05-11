// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM
import Cura 1.0 as Cura

Item {
    id: base

    property bool activity: CuraApplication.platformActivity
    property string fileBaseName
    property variant activeMachineName: Cura.MachineManager.activeMachineName

    onActiveMachineNameChanged:
    {
        printJobTextfield.text = PrintInformation.createJobName(base.fileBaseName);
    }

    UM.I18nCatalog { id: catalog; name:"cura"}

    property variant printDuration: PrintInformation.currentPrintTime
    property variant printDurationPerFeature: PrintInformation.printTimesPerFeature
    property variant printMaterialLengths: PrintInformation.materialLengths
    property variant printMaterialWeights: PrintInformation.materialWeights
    property variant printMaterialCosts: PrintInformation.materialCosts

    height: childrenRect.height

    Connections
    {
        target: backgroundItem
        onHasMesh:
        {
            base.fileBaseName = name
        }
    }

    onActivityChanged: {
        if (activity == true && base.fileBaseName == ''){
            //this only runs when you open a file from the terminal (or something that works the same way; for example when you drag a file on the icon in MacOS or use 'open with' on Windows)
            base.fileBaseName = PrintInformation.jobName; //get the fileBaseName from PrintInformation.py because this saves the filebase when the file is opened using the terminal (or something alike)
            printJobTextfield.text = PrintInformation.createJobName(base.fileBaseName);
        }
        if (activity == true && base.fileBaseName != ''){
            //this runs in all other cases where there is a mesh on the buildplate (activity == true). It uses the fileBaseName from the hasMesh signal
            printJobTextfield.text = PrintInformation.createJobName(base.fileBaseName);
        }
        if (activity == false){
            //When there is no mesh in the buildplate; the printJobTextField is set to an empty string so it doesn't set an empty string as a jobName (which is later used for saving the file)
            printJobTextfield.text = '';
        }
    }

    Rectangle
    {
        id: jobNameRow
        anchors.top: parent.top
        anchors.right: parent.right
        height: UM.Theme.getSize("jobspecs_line").height
        visible: base.activity

        Item
        {
            width: parent.width
            height: parent.height

            Button
            {
                id: printJobPencilIcon
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                width: UM.Theme.getSize("save_button_specs_icons").width
                height: UM.Theme.getSize("save_button_specs_icons").height

                onClicked:
                {
                    printJobTextfield.selectAll();
                    printJobTextfield.focus = true;
                }
                style: ButtonStyle
                {
                    background: Item
                    {
                        UM.RecolorImage
                        {
                            width: UM.Theme.getSize("save_button_specs_icons").width;
                            height: UM.Theme.getSize("save_button_specs_icons").height;
                            sourceSize.width: width;
                            sourceSize.height: width;
                            color: control.hovered ? UM.Theme.getColor("setting_control_button_hover") : UM.Theme.getColor("text");
                            source: UM.Theme.getIcon("pencil");
                        }
                    }
                }
            }

            TextField
            {
                id: printJobTextfield
                anchors.right: printJobPencilIcon.left
                anchors.rightMargin: UM.Theme.getSize("default_margin").width/2
                height: UM.Theme.getSize("jobspecs_line").height
                width: Math.max(__contentWidth + UM.Theme.getSize("default_margin").width, 50)
                maximumLength: 120
                property int unremovableSpacing: 5
                text: ''
                horizontalAlignment: TextInput.AlignRight
                onTextChanged: {
                    PrintInformation.setJobName(text);
                }
                onEditingFinished: {
                    if (printJobTextfield.text != ''){
                        printJobTextfield.focus = false;
                    }
                }
                validator: RegExpValidator {
                    regExp: /^[^\\ \/ \*\?\|\[\]]*$/
                }
                style: TextFieldStyle{
                    textColor: UM.Theme.getColor("setting_control_text");
                    font: UM.Theme.getFont("default_bold");
                    background: Rectangle {
                        opacity: 0
                        border.width: 0
                    }
                }
            }
        }
    }

    Text
    {
        id: boundingSpec
        anchors.top: jobNameRow.bottom
        anchors.right: parent.right
        height: UM.Theme.getSize("jobspecs_line").height
        verticalAlignment: Text.AlignVCenter
        font: UM.Theme.getFont("small")
        color: UM.Theme.getColor("text_subtext")
        text: CuraApplication.getSceneBoundingBoxString
    }

    Rectangle
    {
        id: specsRow
        anchors.top: boundingSpec.bottom
        anchors.right: parent.right
        height: UM.Theme.getSize("jobspecs_line").height

        Item
        {
            width: parent.width
            height: parent.height

            UM.RecolorImage
            {
                id: timeIcon
                anchors.right: timeSpecPerFeatureTooltipArea.left
                anchors.rightMargin: UM.Theme.getSize("default_margin").width/2
                anchors.verticalCenter: parent.verticalCenter
                width: UM.Theme.getSize("save_button_specs_icons").width
                height: UM.Theme.getSize("save_button_specs_icons").height
                sourceSize.width: width
                sourceSize.height: width
                color: UM.Theme.getColor("text_subtext")
                source: UM.Theme.getIcon("print_time")
            }
            UM.TooltipArea
            {
                id: timeSpecPerFeatureTooltipArea
                text: {
                    var order = ["inset_0", "inset_x", "skin", "infill", "support_infill", "support_interface", "support", "travel", "retract", "none"];
                    var visible_names = {
                        "inset_0": catalog.i18nc("@tooltip", "Outer Wall"),
                        "inset_x": catalog.i18nc("@tooltip", "Inner Walls"),
                        "skin": catalog.i18nc("@tooltip", "Skin"),
                        "infill": catalog.i18nc("@tooltip", "Infill"),
                        "support_infill": catalog.i18nc("@tooltip", "Support Infill"),
                        "support_interface": catalog.i18nc("@tooltip", "Support Interface"),
                        "support": catalog.i18nc("@tooltip", "Support"),
                        "travel": catalog.i18nc("@tooltip", "Travel"),
                        "retract": catalog.i18nc("@tooltip", "Retractions"),
                        "none": catalog.i18nc("@tooltip", "Other")
                    };
                    var result = "";
                    for(var feature in order)
                    {
                        feature = order[feature];
                        if(base.printDurationPerFeature[feature] && base.printDurationPerFeature[feature].totalSeconds > 0)
                        {
                            result += "<br/>" + visible_names[feature] + ": " + base.printDurationPerFeature[feature].getDisplayString(UM.DurationFormat.Short);
                        }
                    }
                    result = result.replace(/^\<br\/\>/, ""); // remove newline before first item
                    return result;
                }
                width: childrenRect.width
                height: childrenRect.height
                anchors.right: lengthIcon.left
                anchors.rightMargin: UM.Theme.getSize("default_margin").width
                anchors.verticalCenter: parent.verticalCenter

                Text
                {
                    id: timeSpec
                    anchors.left: parent.left
                    anchors.top: parent.top
                    font: UM.Theme.getFont("small")
                    color: UM.Theme.getColor("text_subtext")
                    text: (!base.printDuration || !base.printDuration.valid) ? catalog.i18nc("@label", "00h 00min") : base.printDuration.getDisplayString(UM.DurationFormat.Short)
                }
            }
            UM.RecolorImage
            {
                id: lengthIcon
                anchors.right: lengthSpec.left
                anchors.rightMargin: UM.Theme.getSize("default_margin").width/2
                anchors.verticalCenter: parent.verticalCenter
                width: UM.Theme.getSize("save_button_specs_icons").width
                height: UM.Theme.getSize("save_button_specs_icons").height
                sourceSize.width: width
                sourceSize.height: width
                color: UM.Theme.getColor("text_subtext")
                source: UM.Theme.getIcon("category_material")
            }
            Text
            {
                id: lengthSpec
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                font: UM.Theme.getFont("small")
                color: UM.Theme.getColor("text_subtext")
                text:
                {
                    var lengths = [];
                    var weights = [];
                    var costs = [];
                    var someCostsKnown = false;
                    if(base.printMaterialLengths) {
                        for(var index = 0; index < base.printMaterialLengths.length; index++)
                        {
                            if(base.printMaterialLengths[index] > 0)
                            {
                                lengths.push(base.printMaterialLengths[index].toFixed(2));
                                weights.push(String(Math.floor(base.printMaterialWeights[index])));
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
                    if(someCostsKnown)
                    {
                        return catalog.i18nc("@label", "%1 m / ~ %2 g / ~ %4 %3").arg(lengths.join(" + "))
                                .arg(weights.join(" + ")).arg(costs.join(" + ")).arg(UM.Preferences.getValue("cura/currency"));
                    }
                    else
                    {
                        return catalog.i18nc("@label", "%1 m / ~ %2 g").arg(lengths.join(" + ")).arg(weights.join(" + "));
                    }
                }
            }
        }
    }
}
