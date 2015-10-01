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
    property int totalHeight: childrenRect.height
    property string fileBaseName
    property variant activeMachineInstance: UM.MachineManager.activeMachineInstance

    onActiveMachineInstanceChanged:
    {
        base.createFileName()
    }

    UM.I18nCatalog { id: catalog; name:"cura"}

    property variant printDuration: PrintInformation.currentPrintTime;
    property real printMaterialAmount: PrintInformation.materialAmount;

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
            base.fileBaseName = name
            base.createFileName()
        }
    }

    Rectangle{
        id: printJobRow
        implicitWidth: base.width;
        implicitHeight: UM.Theme.sizes.save_button_header.height
        anchors.top: parent.top
        color: UM.Theme.colors.sidebar_header_bar
        Label{
            id: printJobTextfieldLabel
            text: catalog.i18nc("@label:textbox", "Printjob Name");
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.sizes.default_margin.width;
            anchors.verticalCenter: parent.verticalCenter
            font: UM.Theme.fonts.default;
            color: UM.Theme.colors.text_white
        }
        TextField {
            id: printJobTextfield
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.sizes.default_margin.width;
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width/100*55
            height: UM.Theme.sizes.sidebar_inputFields.height
            property int unremovableSpacing: 5
            text: ''
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
                    radius: 0
                    implicitWidth: parent.width
                    implicitHeight: parent.height
                    border.width: 1;
                    border.color: UM.Theme.colors.slider_groove_border;
                }
            }
        }
    }

    Rectangle {
        id: specsRow
        implicitWidth: base.width
        implicitHeight: UM.Theme.sizes.sidebar_specs_bar.height
        anchors.top: printJobRow.bottom
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

    Rectangle{
        id: saveRow
        width: base.width
        height: saveToButton.height + (UM.Theme.sizes.default_margin.height / 2) // height + bottomMargin
        anchors.top: specsRow.bottom
        anchors.left: parent.left

        Button {
            id: saveToButton
            property int resizedWidth
            x: base.width - saveToButton.resizedWidth - UM.Theme.sizes.default_margin.width - UM.Theme.sizes.save_button_save_to_button.height
            tooltip: UM.OutputDeviceManager.activeDeviceDescription;
            enabled: base.progress > 0.99 && base.activity == true
            height: UM.Theme.sizes.save_button_save_to_button.height
            width: 150
            anchors.top:parent.top
            text: UM.OutputDeviceManager.activeDeviceShortDescription
            onClicked:
            {
                UM.OutputDeviceManager.requestWriteToDevice(UM.OutputDeviceManager.activeDevice, Printer.jobName)
            }

            style: ButtonStyle {
                background: Rectangle {
                    //opacity: control.enabled ? 1.0 : 0.5
                    //Behavior on opacity { NumberAnimation { duration: 50; } }
                    color: {
                        if(!control.enabled){
                            return UM.Theme.colors.button;
                        }
                        else if(control.enabled && control.hovered) {
                            return UM.Theme.colors.load_save_button_hover
                        } else {
                            return UM.Theme.colors.load_save_button
                        }
                    }
                    Behavior on color { ColorAnimation { duration: 50; } }
                    width: {
                        var w = 0;
                        if (base.width*0.55 > actualLabel.width + (UM.Theme.sizes.default_margin.width * 2)){
                            saveToButton.resizedWidth = base.width*0.55
                            w = base.width*0.55
                        }
                        else {
                            saveToButton.resizedWidth = actualLabel.width + (UM.Theme.sizes.default_margin.width * 2)
                            w = actualLabel.width + (UM.Theme.sizes.default_margin.width * 2)
                        }
                        if(w < base.width * 0.55) {
                            w = base.width * 0.55;
                        }
                        return w;
                    }
                    Label {
                        id: actualLabel
                        opacity: control.enabled ? 1.0 : 0.4
                        //Behavior on opacity { NumberAnimation { duration: 50; } }
                        anchors.centerIn: parent
                        color:  UM.Theme.colors.load_save_button_text
                        font: UM.Theme.fonts.default
                        text: control.text;
                    }
                }
            label: Item { }
            }
        }

        Button {
            id: deviceSelectionMenu
            tooltip: catalog.i18nc("@info:tooltip","Select the active output device");
            anchors.top:parent.top
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.sizes.default_margin.width
            width: UM.Theme.sizes.save_button_save_to_button.height
            height: UM.Theme.sizes.save_button_save_to_button.height
            //iconSource: UM.Theme.icons[UM.OutputDeviceManager.activeDeviceIconName];

            style: ButtonStyle {
                background: Rectangle {
                    id: deviceSelectionIcon
                    color: control.hovered ? UM.Theme.colors.load_save_button_hover : UM.Theme.colors.load_save_button
                    Behavior on color { ColorAnimation { duration: 50; } }
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.sizes.save_button_text_margin.width / 2;
                    width: parent.height
                    height: parent.height

                    UM.RecolorImage {
                        id: lengthIcon
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: UM.Theme.sizes.standard_arrow.width
                        height: UM.Theme.sizes.standard_arrow.height
                        sourceSize.width: width
                        sourceSize.height: width
                        color: UM.Theme.colors.load_save_button_text
                        source: UM.Theme.icons.arrow_bottom
                    }
                }
                label: Label{ }
            }

            menu: Menu {
                id: devicesMenu;
                Instantiator {
                    model: devicesModel;
                    MenuItem {
                        text: model.description
                        checkable: true;
                        checked: model.id == UM.OutputDeviceManager.activeDevice;
                        exclusiveGroup: devicesMenuGroup;
                        onTriggered: {
                            UM.OutputDeviceManager.setActiveDevice(model.id);
                        }
                    }
                    onObjectAdded: devicesMenu.insertItem(index, object)
                    onObjectRemoved: devicesMenu.removeItem(object)
                }
                ExclusiveGroup { id: devicesMenuGroup; }
            }
        }
        UM.OutputDevicesModel { id: devicesModel; }
    }
}
