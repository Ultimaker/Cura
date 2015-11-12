// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM

Rectangle {
    id: base;

    property real progress: UM.Backend.progress;
    property bool activity: Printer.getPlatformActivity;
    Behavior on progress { NumberAnimation { duration: 250; } }
    property int totalHeight: childrenRect.height + UM.Theme.sizes.default_margin.height*1.5
    property string fileBaseName
    property variant activeMachineInstance: UM.MachineManager.activeMachineInstance

    onActiveMachineInstanceChanged:
    {
        base.createFileName()
    }

    UM.I18nCatalog { id: catalog; name:"cura"}

    property variant printDuration: PrintInformation.currentPrintTime;
    property real printMaterialAmount: PrintInformation.materialAmount;

    width: 240
    height: 50
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


    TextField {
        id: printJobTextfield
        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.sizes.default_margin.width;
        height: UM.Theme.sizes.sidebar_inputFields.height
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
            font: UM.Theme.fonts.default;
            background: Rectangle {
                opacity: 0
                border.width: 0
            }
        }
    }

    Rectangle {
        id: specsRow
        implicitWidth: base.width
        implicitHeight: UM.Theme.sizes.sidebar_specs_bar.height
        anchors.top: printJobTextfield.bottom
        color: "transparent"
        visible: base.progress > 0.99 && base.activity == true
        Item{
            id: time
            width: childrenRect.width;
            height: parent.height
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.sizes.default_margin.width
            anchors.top: parent.top
            visible: base.printMaterialAmount > 0 ? true : false
            UM.RecolorImage {
                id: timeIcon
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                width: UM.Theme.sizes.save_button_specs_icons.width
                height: UM.Theme.sizes.save_button_specs_icons.height
                sourceSize.width: width
                sourceSize.height: width
                color: UM.Theme.colors.text_hover
                source: UM.Theme.icons.print_time;
            }
            Label{
                id: timeSpec
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: timeIcon.right
                anchors.leftMargin: UM.Theme.sizes.default_margin.width/2
                font: UM.Theme.fonts.default
                color: UM.Theme.colors.text
                text: (!base.printDuration || !base.printDuration.valid) ? "" : base.printDuration.getDisplayString(UM.DurationFormat.Short)
            }
        }
        Item{
            width: parent.width / 100 * 55
            height: parent.height
            anchors.left: time.right
            anchors.leftMargin: UM.Theme.sizes.default_margin.width;
            anchors.top: parent.top
            visible: base.printMaterialAmount > 0 ? true : false
            UM.RecolorImage {
                id: lengthIcon
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                width: UM.Theme.sizes.save_button_specs_icons.width
                height: UM.Theme.sizes.save_button_specs_icons.height
                sourceSize.width: width
                sourceSize.height: width
                color: UM.Theme.colors.text_hover
                source: UM.Theme.icons.category_material;
            }
            Label{
                id: lengthSpec
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: lengthIcon.right
                anchors.leftMargin: UM.Theme.sizes.default_margin.width/2
                font: UM.Theme.fonts.default
                color: UM.Theme.colors.text
                text: base.printMaterialAmount <= 0 ? "" : catalog.i18nc("@label %1 is length of filament","%1 m").arg(base.printMaterialAmount)
            }
        }
    }
}
