// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM

Rectangle {
    id: base;

    property bool activity: Printer.getPlatformActivity;
    property string fileBaseName
    property variant activeMachineInstance: UM.MachineManager.activeMachineInstance

    onActiveMachineInstanceChanged:
    {
        base.createFileName()
    }

    UM.I18nCatalog { id: catalog; name:"cura"}

    property variant printDuration: PrintInformation.currentPrintTime;
    property real printMaterialAmount: PrintInformation.materialAmount;

    width: UM.Theme.sizes.jobspecs.width
    height: childrenRect.height
    color: "transparent"

    function createFileName(){
        var splitMachineName = UM.MachineManager.activeMachineInstance.split(" ")
        var abbrMachine = ''
            for (var i = 0; i < splitMachineName.length; i++){
                if (splitMachineName[i].search(/ultimaker/i) != -1){
                    abbrMachine += 'UM'
                }
                else{
                    if (splitMachineName[i].charAt(0).search(/[0-9]/g) == -1)
                        abbrMachine += splitMachineName[i].charAt(0)
                }
                var regExpAdditives = /[0-9\+]/g;
                var resultAdditives = splitMachineName[i].match(regExpAdditives);
                if (resultAdditives != null){
                    for (var j = 0; j < resultAdditives.length; j++){
                        abbrMachine += resultAdditives[j]

                    }
                }
            }
        printJobTextfield.text = abbrMachine + '_' + base.fileBaseName
    }

     Connections {
        target: openDialog
        onHasMesh: {
            if(base.fileBaseName == ''){
                base.fileBaseName = name
                base.createFileName()
            }
        }
    }

    onActivityChanged: {
        if (activity == false){
            base.fileBaseName = ''
            base.createFileName()
        }
    }

    Rectangle 
    {
        id: jobNameRow
        anchors.top: parent.top
        anchors.right: parent.right
        height: UM.Theme.sizes.jobspecs_line.height
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
                width: UM.Theme.sizes.save_button_specs_icons.width
                height: UM.Theme.sizes.save_button_specs_icons.height

                onClicked: 
                {
                    printJobTextfield.selectAll()
                    printJobTextfield.focus = true
                }
                style: ButtonStyle
                {
                    background: Rectangle
                    {
                        color: "transparent"
                        UM.RecolorImage 
                        {
                            width: UM.Theme.sizes.save_button_specs_icons.width
                            height: UM.Theme.sizes.save_button_specs_icons.height
                            sourceSize.width: width
                            sourceSize.height: width
                            color: UM.Theme.colors.setting_control_text
                            source: UM.Theme.icons.pencil;
                        }
                    }
                }
            }

            TextField 
            {
                id: printJobTextfield
                anchors.right: printJobPencilIcon.left
                anchors.rightMargin: UM.Theme.sizes.default_margin.width/2
                height: UM.Theme.sizes.jobspecs_line.height
                width: base.width
                property int unremovableSpacing: 5
                text: ''
                horizontalAlignment: TextInput.AlignRight
                onTextChanged: Printer.setJobName(text)
                onEditingFinished: {
                    if (printJobTextfield.text != ''){
                        printJobTextfield.focus = false
                    }
                }
                validator: RegExpValidator {
                    regExp: /^[^\\ \/ \.]*$/
                }
                style: TextFieldStyle{
                    textColor: UM.Theme.colors.setting_control_text;
                    font: UM.Theme.fonts.default_bold;
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
        height: UM.Theme.sizes.jobspecs_line.height
        verticalAlignment: Text.AlignVCenter
        font: UM.Theme.fonts.small
        color: UM.Theme.colors.text_subtext
        text: Printer.getSceneBoundingBoxString
    }

    Rectangle {
        id: specsRow
        anchors.top: boundingSpec.bottom
        anchors.right: parent.right
        height: UM.Theme.sizes.jobspecs_line.height

        Item{
            width: parent.width
            height: parent.height

            UM.RecolorImage {
                id: timeIcon
                anchors.right: timeSpec.left
                anchors.rightMargin: UM.Theme.sizes.default_margin.width/2
                anchors.verticalCenter: parent.verticalCenter
                width: UM.Theme.sizes.save_button_specs_icons.width
                height: UM.Theme.sizes.save_button_specs_icons.height
                sourceSize.width: width
                sourceSize.height: width
                color: UM.Theme.colors.text_subtext
                source: UM.Theme.icons.print_time;
            }
            Label{
                id: timeSpec
                anchors.right: lengthIcon.left
                anchors.rightMargin: UM.Theme.sizes.default_margin.width
                anchors.verticalCenter: parent.verticalCenter
                font: UM.Theme.fonts.small
                color: UM.Theme.colors.text_subtext
                text: (!base.printDuration || !base.printDuration.valid) ? "00h 00min" : base.printDuration.getDisplayString(UM.DurationFormat.Short)
            }
            UM.RecolorImage {
                id: lengthIcon
                anchors.right: lengthSpec.left
                anchors.rightMargin: UM.Theme.sizes.default_margin.width/2
                anchors.verticalCenter: parent.verticalCenter
                width: UM.Theme.sizes.save_button_specs_icons.width
                height: UM.Theme.sizes.save_button_specs_icons.height
                sourceSize.width: width
                sourceSize.height: width
                color: UM.Theme.colors.text_subtext
                source: UM.Theme.icons.category_material;
            }
            Label{
                id: lengthSpec
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                font: UM.Theme.fonts.small
                color: UM.Theme.colors.text_subtext
                text: base.printMaterialAmount <= 0 ? "0.0 m" : catalog.i18nc("@label %1 is length of filament","%1 m").arg(base.printMaterialAmount)
            }
        }
    }
}
