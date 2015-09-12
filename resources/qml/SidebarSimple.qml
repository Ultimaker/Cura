// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM

Item
{
    id: base;
    anchors.fill: parent;

    property Action configureSettings;
    property variant minimumPrintTime: PrintInformation.minimumPrintTime;
    property variant maximumPrintTime: PrintInformation.maximumPrintTime;

    Component.onCompleted: PrintInformation.enabled = true
    Component.onDestruction: PrintInformation.enabled = false
    UM.I18nCatalog { id: catalog; name:"cura"}

    Rectangle{
        id: infillCellLeft
        anchors.top: parent.top
        anchors.left: parent.left
        width: base.width/100*55 - UM.Theme.sizes.default_margin.width
        height: childrenRect.height < UM.Theme.sizes.simple_mode_infill_caption.height ? UM.Theme.sizes.simple_mode_infill_caption.height : childrenRect.height

        Label{
            id: infillLabel
            //: Infill selection label
            text: catalog.i18nc("@label","Infill:");
            font: UM.Theme.fonts.default;
            anchors.top: parent.top
            anchors.topMargin: UM.Theme.sizes.default_margin.height
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.sizes.default_margin.width
        }
        Label{
            id: infillCaption
            width: infillCellLeft.width - UM.Theme.sizes.default_margin.width
            text: infillModel.get(infillListView.activeIndex).text
            font: UM.Theme.fonts.caption
            wrapMode: Text.Wrap
            color: UM.Theme.colors.text
            anchors.top: infillLabel.bottom
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.sizes.default_margin.width
        }
    }

    Rectangle{
        id: infillCellRight
        height: 100
        width: base.width/100*45
        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.sizes.default_margin.width  - (UM.Theme.sizes.default_margin.width/4)
        anchors.top: parent.top
        anchors.topMargin: UM.Theme.sizes.default_margin.height
        Component{
            id: infillDelegate
            Item{
                width: infillCellRight.width/3
                x: index * (infillCellRight.width/3)
                anchors.top: parent.top
                Rectangle{
                    id: infillIconLining
                    anchors.top: parent.top
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: parent.width - (UM.Theme.sizes.default_margin.width/2)
                    height: parent.width - (UM.Theme.sizes.default_margin.width/2)
                    border.color: infillListView.activeIndex == index ? UM.Theme.colors.setting_control_text : UM.Theme.colors.setting_control_border
                    border.width: infillListView.activeIndex == index ? 2 : 1
                    color: infillListView.activeIndex == index ? UM.Theme.colors.setting_category_active : "transparent"
                    UM.RecolorImage {
                        id: infillIcon
                        z: parent.z + 1
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: parent.width - UM.Theme.sizes.default_margin.width
                        height: parent.width - UM.Theme.sizes.default_margin.width
                        sourceSize.width: width
                        sourceSize.height: width
                        color: UM.Theme.colors.setting_control_text
                        source: UM.Theme.icons[model.icon];
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            infillListView.activeIndex = index
                        }
                    }
                }
                Label{
                    id: infillLabel
                    anchors.top: infillIconLining.bottom
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: infillListView.activeIndex == index ? UM.Theme.colors.setting_control_text : UM.Theme.colors.setting_control_border
                    text: name
                    //font.bold: infillListView.activeIndex == index ? true : false
                }
            }
        }
        ListView{
            id: infillListView
            property int activeIndex: 0
            model: infillModel
            delegate: infillDelegate
            anchors.fill: parent
        }
        ListModel {
            id: infillModel

            Component.onCompleted:
            {
                infillModel.append({
                    name: catalog.i18nc("@label", "Sparse"),
                    percentage: 20,
                    text: catalog.i18nc("@label", "Sparse (20%) infill will give your model an average strength"),
                    icon: "sparse"
                })
                infillModel.append({
                    name: catalog.i18nc("@label", "Dense"),
                    percentage: 50,
                    text: catalog.i18nc("@label", "Dense (50%) infill will give your model an above average strength"),
                    icon: "dense"
                })
                infillModel.append({
                    name: catalog.i18nc("@label", "Solid"),
                    percentage: 100,
                    text: catalog.i18nc("@label", "Solid (100%) infill will make your model completely solid"),
                    icon: "solid"
                })
            }
        }
    }

    Rectangle {
        id: helpersCellLeft
        anchors.top: infillCellLeft.bottom
        anchors.topMargin: UM.Theme.sizes.default_margin.height
        anchors.left: parent.left
        width: parent.width/100*45 - UM.Theme.sizes.default_margin.width
        height: childrenRect.height
        Label{
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.sizes.default_margin.width
            //: Helpers selection label
            text: catalog.i18nc("@label:listbox","Helpers:");
            font: UM.Theme.fonts.default;
        }
    }
    Rectangle {
        id: helpersCellRight
        anchors.top: helpersCellLeft.top
        anchors.topMargin: UM.Theme.sizes.default_margin.height
        anchors.left: helpersCellLeft.right
        width: parent.width/100*55 - UM.Theme.sizes.default_margin.width
        height: childrenRect.height

        CheckBox{
            id: skirtCheckBox
            anchors.top: parent.top
            anchors.left: parent.left
            Layout.preferredHeight: UM.Theme.sizes.section.height;
            //: Setting enable skirt adhesion checkbox
            text: catalog.i18nc("@option:check","Enable Skirt Adhesion");
            style: UM.Theme.styles.checkbox;
            checked: Printer.getSettingValue("skirt_line_count") == null ? false: Printer.getSettingValue("skirt_line_count");
            onCheckedChanged:
            {
                if(checked != Printer.getSettingValue("skirt_line_count"))
                {
                    Printer.setSettingValue("skirt_line_count", checked)
                }
            }
        }
        CheckBox{
            anchors.top: skirtCheckBox.bottom
            anchors.topMargin: UM.Theme.sizes.default_lining.height
            anchors.left: parent.left
            Layout.preferredHeight: UM.Theme.sizes.section.height;

            //: Setting enable support checkbox
            text: catalog.i18nc("@option:check","Enable Support");

            style: UM.Theme.styles.checkbox;

            checked: Printer.getSettingValue("support_enable") == null? false: Printer.getSettingValue("support_enable");
            onCheckedChanged:
            {
                if(checked != Printer.getSettingValue("support_enable"))
                {
                    Printer.setSettingValue("support_enable", checked)
                }
            }
        }
    }

/*
        Item
        {
            Layout.fillWidth: true;
            Layout.preferredHeight: UM.Theme.sizes.section.height;

            Label
            {
                anchors.left: parent.left;
                anchors.verticalCenter: parent.verticalCenter;
                text: base.minimumPrintTime.valid ? base.minimumPrintTime.getDisplayString(UM.DurationFormat.Short) : "??:??";
                font: UM.Theme.fonts.timeslider_time;
                color: UM.Theme.colors.primary;
            }
            Label
            {
                anchors.centerIn: parent;
                text: //: Sidebar configuration label
                {
                    if (UM.Backend.progress < 0)
                    {
                        return catalog.i18nc("@label","No Model Loaded");
                    }
                    else if (!base.minimumPrintTime.valid || !base.maximumPrintTime.valid)
                    {
                        return catalog.i18nc("@label","Calculating...")
                    }
                    else
                    {
                        return catalog.i18nc("@label","Estimated Print Time");
                    }
                }
                color: UM.Theme.colors.text;
                font: UM.Theme.fonts.default;
            }
            Label
            {
                anchors.right: parent.right;
                anchors.verticalCenter: parent.verticalCenter;
                text: base.maximumPrintTime.valid ? base.maximumPrintTime.getDisplayString(UM.DurationFormat.Short) : "??:??";
                font: UM.Theme.fonts.timeslider_time;
                color: UM.Theme.colors.primary;
            }
        }

        Slider
        {
            Layout.fillWidth: true;
            Layout.preferredHeight: UM.Theme.sizes.section.height;

            minimumValue: 0;
            maximumValue: 100;

            value: PrintInformation.timeQualityValue;
            onValueChanged: PrintInformation.setTimeQualityValue(value);

            style: UM.Theme.styles.slider;
        }

        Item
        {
            Layout.fillWidth: true;
            Layout.preferredHeight: UM.Theme.sizes.section.height;

            Label
            {
                anchors.left: parent.left;
                anchors.verticalCenter: parent.verticalCenter;

                //: Quality slider label
                text: catalog.i18nc("@label","Minimum\nDraft");
                color: UM.Theme.colors.text;
                font: UM.Theme.fonts.default;
            }

            Label
            {
                anchors.right: parent.right;
                anchors.verticalCenter: parent.verticalCenter;

                //: Quality slider label
                text: catalog.i18nc("@label","Maximum\nQuality");
                horizontalAlignment: Text.AlignRight;
                color: UM.Theme.colors.text;
                font: UM.Theme.fonts.default;
            }
        }

        CheckBox
        {
            Layout.fillWidth: true;
            Layout.preferredHeight: UM.Theme.sizes.section.height;

            //: Setting checkbox
            text: catalog.i18nc("@action:checkbox","Enable Support");

            style: UM.Theme.styles.checkbox;

            checked: Printer.getSettingValue("support_enable");
            onCheckedChanged: Printer.setSettingValue("support_enable", checked);
        }

        Item { Layout.fillWidth: true; Layout.fillHeight: true; }
    }*/
}
