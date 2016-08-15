// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM
import Cura 1.0 as Cura

Rectangle {
    id: base

    property bool activity: Printer.getPlatformActivity
    property string fileBaseName
    property variant activeMachineName: Cura.MachineManager.activeMachineName

    onActiveMachineNameChanged:
    {
        printJobTextfield.text = PrintInformation.createJobName(base.fileBaseName);
    }

    UM.I18nCatalog { id: catalog; name:"cura"}

    property variant printDuration: PrintInformation.currentPrintTime
    property variant printMaterialLengths: PrintInformation.materialLengths
    property variant printMaterialWeights: PrintInformation.materialWeights

    height: childrenRect.height
    color: "transparent"

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
                    background: Rectangle
                    {
                        color: "transparent"
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

    Label{
        id: boundingSpec
        anchors.top: jobNameRow.bottom
        anchors.right: parent.right
        height: UM.Theme.getSize("jobspecs_line").height
        verticalAlignment: Text.AlignVCenter
        font: UM.Theme.getFont("small")
        color: UM.Theme.getColor("text_subtext")
        text: Printer.getSceneBoundingBoxString
    }

    Rectangle {
        id: specsRow
        anchors.top: boundingSpec.bottom
        anchors.right: parent.right
        height: UM.Theme.getSize("jobspecs_line").height

        Item{
            width: parent.width
            height: parent.height

            UM.RecolorImage {
                id: timeIcon
                anchors.right: timeSpec.left
                anchors.rightMargin: UM.Theme.getSize("default_margin").width/2
                anchors.verticalCenter: parent.verticalCenter
                width: UM.Theme.getSize("save_button_specs_icons").width
                height: UM.Theme.getSize("save_button_specs_icons").height
                sourceSize.width: width
                sourceSize.height: width
                color: UM.Theme.getColor("text_subtext")
                source: UM.Theme.getIcon("print_time")
            }
            Label{
                id: timeSpec
                anchors.right: lengthIcon.left
                anchors.rightMargin: UM.Theme.getSize("default_margin").width
                anchors.verticalCenter: parent.verticalCenter
                font: UM.Theme.getFont("small")
                color: UM.Theme.getColor("text_subtext")
                text: (!base.printDuration || !base.printDuration.valid) ? catalog.i18nc("@label", "00h 00min") : base.printDuration.getDisplayString(UM.DurationFormat.Short)
            }
            UM.RecolorImage {
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
            Label{
                id: lengthSpec
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                font: UM.Theme.getFont("small")
                color: UM.Theme.getColor("text_subtext")
                text:
                {
                    var lengths = [];
                    var weights = [];
                    if(base.printMaterialLengths) {
                        for(var index = 0; index < base.printMaterialLengths.length; index++) {
                            if(base.printMaterialLengths[index] > 0) {
                                lengths.push(base.printMaterialLengths[index].toFixed(2));
                                weights.push(String(Math.floor(base.printMaterialWeights[index])));
                            }
                        }
                    }
                    if(lengths.length == 0) {
                        lengths = ["0.00"];
                        weights = ["0"];
                    }
                    return catalog.i18nc("@label", "%1 m / ~ %2 g").arg(lengths.join(" + ")).arg(weights.join(" + "));
                }
            }
        }
    }
}
