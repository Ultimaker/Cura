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

//     Rectangle {
//         anchors.top: simpleModeGrid.top
//         anchors.left: simpleModeGrid.left
//         width: simpleModeGrid.width
//         height: simpleModeGrid.height
//         color: "blue"
//     }

    Grid {
        id: simpleModeGrid
        anchors.fill: parent;
        columns: 2
        spacing: 0

//         Rectangle{
//             id: infillLabelCell
//             width: base.width/100*45
//             height: 100
//             Column {
//                 spacing: 0
//                 anchors{
//                     top: parent.top
//                     topMargin: UM.Theme.sizes.default_margin.height
//                     right: parent.right
//                     rightMargin: UM.Theme.sizes.default_margin.width
//                     bottom: parent.bottom
//                     bottomMargin: UM.Theme.sizes.default_margin.height
//                     left: parent.left
//                     leftMargin: UM.Theme.sizes.default_margin.width
//                 }
//
//                 Label{
//                     id: infillLabel
//                     //: Infill selection label
//                     text: catalog.i18nc("@label","Infill:");
//                     font: UM.Theme.fonts.default;
//                 }
//                 Label{
//                     id: infillCaption
//                     width: infillLabelCell.width - UM.Theme.sizes.default_margin.width
//                     text: "hier staat overig tekst hier staat overig tekst hier staat overig tekst"
//                     font: UM.Theme.fonts.caption
//                     wrapMode: Text.Wrap
//                     color: UM.Theme.colors.text
//                 }
//             }
//         }
//
//         Rectangle{
//             id: infillCell
//             height: 100
//             width: base.width/100*55
//             Row {
//                 spacing: 0
//                 anchors.right: parent.right
//                 anchors.rightMargin: UM.Theme.sizes.default_margin.width
//                 Rectangle {
//                     id: infillWrapper
//                     width: infillCell.width/4;
//                     height: infillCell.height
//                     Rectangle{
//                         id: infillIconLining
//                         anchors.top: parent.top
//                         anchors.topMargin: UM.Theme.sizes.default_margin.height
//                         anchors.horizontalCenter: parent.horizontalCenter
//                         z: parent.z + 1
//                         width: parent.width - UM.Theme.sizes.default_margin.width/2
//                         height: parent.width  - UM.Theme.sizes.default_margin.width/2
//                         color: "grey"
//                         border.color: "black"
//                         border.width:1
//                         UM.RecolorImage {
//                             id: infillIcon
//                             z: parent.z + 1
//                             anchors.verticalCenter: parent.verticalCenter
//                             anchors.horizontalCenter: parent.horizontalCenter
//                             width: UM.Theme.sizes.save_button_specs_icons.width
//                             height: UM.Theme.sizes.save_button_specs_icons.height
//                             sourceSize.width: width
//                             sourceSize.height: width
//                             color: UM.Theme.colors.text_hover
//                             source: UM.Theme.icons.print_time;
//                         }
//                     }
//                     Label{
//                        //: Infill version label "light:
//                         text: catalog.i18nc("@label","Light");
//                         anchors.top: infillIconLining.bottom
//                         anchors.horizontalCenter: parent.horizontalCenter
//                         font.bold: true
//                     }
//                 }
//                 Rectangle {
//                     color: "green";
//                     width: infillCell.width/4;
//                     height: infillCell.height
//                 }
//                 Rectangle {
//                     color: "blue";
//                     width: infillCell.width/4;
//                     height: infillCell.height
//                 }
//                 Rectangle {
//                     color: "yellow";
//                     width: infillCell.width/4;
//                     height: infillCell.height
//                 }
//             }
//         }

        Rectangle {
            width: parent.width/100*45 - UM.Theme.sizes.default_margin.width
            height: 100
            Label{
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.sizes.default_margin.width
                //: Helpers selection label
                text: catalog.i18nc("@label","Helpers:");
                font: UM.Theme.fonts.default;
            }
        }
        Rectangle {
            width: parent.width/100*55 - UM.Theme.sizes.default_margin.width
            height: 100
            Column {
                spacing: 4

                CheckBox{
                    Layout.preferredHeight: UM.Theme.sizes.section.height;
                    //: Setting enable skirt adhesion checkbox
                    text: catalog.i18nc("@action:checkbox","Enable Skirt Adhesion");
                    style: UM.Theme.styles.checkbox;
                    checked: Printer.getSettingValue("skirt_line_count");
                    onCheckedChanged: Printer.setSettingValue("skirt_line_count", checked);
                }
                CheckBox{
                    Layout.preferredHeight: UM.Theme.sizes.section.height;

                    //: Setting enable support checkbox
                    text: catalog.i18nc("@action:checkbox","Enable Support");

                    style: UM.Theme.styles.checkbox;

                    checked: Printer.getSettingValue("support_enable");
                    onCheckedChanged: Printer.setSettingValue("support_enable", checked);
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
