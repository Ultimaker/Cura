// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM

Rectangle
{
    id: base;

    property real progress: UM.Backend.progress;
    property bool activity: Printer.getPlatformActivity;
    Behavior on progress { NumberAnimation { duration: 250; } }
    property int totalHeight: childrenRect.height

    property variant printDuration: PrintInformation.currentPrintTime;
    property real printMaterialAmount: PrintInformation.materialAmount;
    UM.I18nCatalog { id: catalog; name:"cura"}
    Rectangle
    {
        id: background
        implicitWidth: base.width;
        implicitHeight: parent.height;
        color: UM.Theme.colors.save_button_background;
        border.width: UM.Theme.sizes.save_button_border.width
        border.color: UM.Theme.colors.save_button_border

        Rectangle
        {
            id: infoBox
            width: parent.width - UM.Theme.sizes.default_margin.width * 2;
            height: UM.Theme.sizes.save_button_slicing_bar.height

            anchors.top: parent.top
            anchors.topMargin: UM.Theme.sizes.default_margin.height;
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.sizes.default_margin.width;
            anchors.verticalCenter: parent.verticalCenter
            //font: UM.Theme.fonts.default;
            color: UM.Theme.colors.text_white
        }
        TextField
        {
            id: printJobTextfield
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.sizes.default_margin.width;
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width/100*55
            height: UM.Theme.sizes.sidebar_inputFields.height
            property int unremovableSpacing: 5
            text: "UM2" + "_" + "filename" ///TODO KOMT NOG
            onEditingFinished:
            {
                if (printJobTextfield.text != '')
                {
                    printJobTextfield.focus = false
                }
            }
            validator: RegExpValidator
            {
                regExp: /^[0-9a-zA-Z\_\-]*$/
            }
            style: TextFieldStyle
            {
                textColor: UM.Theme.colors.setting_control_text;
                font: UM.Theme.fonts.default;
                background: Rectangle
                {
                    radius: 0
                    implicitWidth: parent.width
                    implicitHeight: parent.height
                    border.width: 1;
                    border.color: UM.Theme.colors.slider_groove_border;
                }
            }
        }
    }

    Rectangle
    {
        id: specsRow
        implicitWidth: base.width
        implicitHeight: UM.Theme.sizes.sidebar_specs_bar.height
        anchors.top: printJobRow.bottom
        Item
        {
            id: time
            width: (parent.width / 100 * 45) - UM.Theme.sizes.default_margin.width * 2
            height: parent.height
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.sizes.default_margin.width
            anchors.top: parent.top
            visible: base.printMaterialAmount > 0 ? true : false
            UM.RecolorImage
            {
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
            Label
            {
                id: timeSpec
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: timeIcon.right
                anchors.leftMargin: UM.Theme.sizes.default_margin.width/2
                font: UM.Theme.fonts.default
                color: UM.Theme.colors.text
                text: (!base.printDuration || !base.printDuration.valid) ? "" : catalog.i18nc("@label","%1 h:m").arg(base.printDuration.getDisplayString(UM.DurationFormat.Short))
            }
        }
        Item
        {
            width: parent.width / 100 * 55
            height: parent.height
            anchors.left: time.right
            anchors.top: parent.top
            visible: base.printMaterialAmount > 0 ? true : false
            UM.RecolorImage
            {
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
            Label
            {
                id: lengthSpec
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: lengthIcon.right
                anchors.leftMargin: UM.Theme.sizes.default_margin.width/2
                font: UM.Theme.fonts.default
                color: UM.Theme.colors.text
                text: base.printMaterialAmount <= 0 ? "" : catalog.i18nc("@label","%1 m").arg(base.printMaterialAmount)
            }
        }
    }

    Item
    {
        id: saveRow
        implicitWidth: base.width / 100 * 55
        implicitHeight: saveToButton.height + (UM.Theme.sizes.default_margin.height / 2) // height + bottomMargin
        anchors.top: specsRow.bottom
        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.sizes.default_margin.width

        Button
        {
            id: saveToButton
            anchors.left: parent.left
            tooltip: UM.OutputDeviceManager.activeDeviceDescription;
            enabled: progress > 0.99 && base.activity == true

            width: parent.width - UM.Theme.sizes.save_button_save_to_button.height - 2
            height: UM.Theme.sizes.save_button_save_to_button.height

            text: UM.OutputDeviceManager.activeDeviceShortDescription;

            style: ButtonStyle
            {
                background: Rectangle
                {
                    color: control.hovered ? UM.Theme.colors.load_save_button_hover : UM.Theme.colors.load_save_button
                    Behavior on color { ColorAnimation { duration: 50; } }

                    Label
                    {
                        anchors.centerIn: parent
                        color: UM.Theme.colors.load_save_button_text
                        font: UM.Theme.fonts.default
                        text: control.text;
                    }
                }
                label: Item { }
            }
            onClicked: UM.OutputDeviceManager.requestWriteToDevice(UM.OutputDeviceManager.activeDevice)
        }

        Button
        {
            id: deviceSelectionMenu;
            tooltip: catalog.i18nc("@action:button","Select the active output device");
            anchors.right: parent.right
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

            menu: Menu
            {
                id: devicesMenu;
                Instantiator
                {
                    model: devicesModel;
                    MenuItem
                    {
                        text: model.description
                        checkable: true;
                        checked: model.id == UM.OutputDeviceManager.activeDevice;
                        exclusiveGroup: devicesMenuGroup;
                        onTriggered:
                        {
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