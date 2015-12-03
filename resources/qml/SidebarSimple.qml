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

    signal showTooltip(Item item, point location, string text);
    signal hideTooltip();

    property Action configureSettings;
    property variant minimumPrintTime: PrintInformation.minimumPrintTime;
    property variant maximumPrintTime: PrintInformation.maximumPrintTime;

    Component.onCompleted: PrintInformation.enabled = true
    Component.onDestruction: PrintInformation.enabled = false
    UM.I18nCatalog { id: catalog; name:"cura"}

    Rectangle{
        id: speedCellLeft
        anchors.top: parent.top
        anchors.left: parent.left
        width: base.width/100*35 - UM.Theme.sizes.default_margin.width
        height: childrenRect.height

        Label{
            id: speedLabel
            //: Speed selection label
            text: catalog.i18nc("@label","Speed:");
            font: UM.Theme.fonts.default;
            color: UM.Theme.colors.text;
            anchors.top: parent.top
            anchors.topMargin: UM.Theme.sizes.default_margin.height
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.sizes.default_margin.width
        }
    }

    Rectangle {
        id: speedCellRight
        anchors.left: speedCellLeft.right
        anchors.top: speedCellLeft.top
        anchors.topMargin: UM.Theme.sizes.default_margin.height
        width: parent.width/100*65 - UM.Theme.sizes.default_margin.width
        height: childrenRect.height

        CheckBox{
            id: normalSpeedCheckBox
            property bool hovered_ex: false

            anchors.top: parent.top
            anchors.left: parent.left

            //: Normal speed checkbox
            text: catalog.i18nc("@option:check","Normal");
            style: UM.Theme.styles.checkbox;

            exclusiveGroup: speedCheckBoxGroup
            checked: UM.ActiveProfile.valid ? UM.ActiveProfile.settingValues.speed_print <= 60 : true;
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                onClicked:
                {
                    UM.MachineManager.setSettingValue("speed_print", 60)
                }
                onEntered:
                {
                    parent.hovered_ex = true
                    base.showTooltip(normalSpeedCheckBox, Qt.point(-speedCellRight.x, parent.height),
                        catalog.i18nc("@label", "Use normal printing speed. This will result in high quality prints."));
                }
                onExited:
                {
                    parent.hovered_ex = false
                    base.hideTooltip();
                }
            }
        }
        CheckBox{
            id: highSpeedCheckBox
            property bool hovered_ex: false

            anchors.top: parent.top
            anchors.left: normalSpeedCheckBox.right
            anchors.leftMargin: UM.Theme.sizes.default_margin.width

            //: High speed checkbox
            text: catalog.i18nc("@option:check","Fast");
            style: UM.Theme.styles.checkbox;

            exclusiveGroup: speedCheckBoxGroup
            checked: UM.ActiveProfile.valid ? UM.ActiveProfile.settingValues.speed_print > 60 : true;
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                onClicked:
                {
                    UM.MachineManager.setSettingValue("speed_print", 100)
                }
                onEntered:
                {
                    parent.hovered_ex = true
                    base.showTooltip(normalSpeedCheckBox, Qt.point(-speedCellRight.x, parent.height),
                        catalog.i18nc("@label", "Use high printing speed. This will reduce printing time, but may affect the quality of the print."));
                }
                onExited:
                {
                    parent.hovered_ex = false
                    base.hideTooltip();
                }
            }
        }
        ExclusiveGroup { id: speedCheckBoxGroup; }
    }

    Rectangle{
        id: infillCellLeft
        anchors.top: speedCellRight.bottom
        anchors.topMargin: UM.Theme.sizes.default_margin.height
        anchors.left: parent.left
        width: base.width/100* 35 - UM.Theme.sizes.default_margin.width
        height: childrenRect.height < UM.Theme.sizes.simple_mode_infill_caption.height ? UM.Theme.sizes.simple_mode_infill_caption.height : childrenRect.height

        Label{
            id: infillLabel
            //: Infill selection label
            text: catalog.i18nc("@label","Infill:");
            font: UM.Theme.fonts.default;
            color: UM.Theme.colors.text;
            anchors.top: parent.top
            anchors.topMargin: UM.Theme.sizes.default_margin.height
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.sizes.default_margin.width
        }
/*        Label{
            id: infillCaption
            width: infillCellLeft.width - UM.Theme.sizes.default_margin.width * 2
            text: infillModel.count > 0 && infillListView.activeIndex != -1 ? infillModel.get(infillListView.activeIndex).text : ""
            font: UM.Theme.fonts.caption
            wrapMode: Text.Wrap
            color: UM.Theme.colors.text_subtext
            anchors.top: infillLabel.bottom
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.sizes.default_margin.width
        } */
    }

    Flow {
        id: infillCellRight

        height: childrenRect.height;
        width: base.width / 100 * 65
        spacing: UM.Theme.sizes.default_margin.width

        anchors.left: infillCellLeft.right
        anchors.top: infillCellLeft.top
        anchors.topMargin: UM.Theme.sizes.default_margin.height

        Repeater {
            id: infillListView
            property int activeIndex: {
                if(!UM.ActiveProfile.valid)
                {
                    return -1;
                }

                var density = parseInt(UM.ActiveProfile.settingValues.infill_sparse_density);
                for(var i = 0; i < infillModel.count; ++i)
                {
                    if(infillModel.get(i).percentage == density)
                    {
                        return i;
                    }
                }

                return -1;
            }
            model: infillModel;

            Item {
                width: childrenRect.width;
                height: childrenRect.height;

                Rectangle{
                    id: infillIconLining

                    width: (infillCellRight.width - 3 * UM.Theme.sizes.default_margin.width) / 4;
                    height: width

                    border.color: (infillListView.activeIndex == index) ? UM.Theme.colors.setting_control_selected :
                                      (mousearea.containsMouse ? UM.Theme.colors.setting_control_border_highlight : UM.Theme.colors.setting_control_border)
                    border.width: UM.Theme.sizes.default_lining.width
                    color: infillListView.activeIndex == index ? UM.Theme.colors.setting_control_selected : "transparent"

                    UM.RecolorImage {
                        id: infillIcon
                        anchors.fill: parent;
                        anchors.margins: UM.Theme.sizes.infill_button_margin.width

                        sourceSize.width: width
                        sourceSize.height: width
                        source: UM.Theme.icons[model.icon];
                        color: (infillListView.activeIndex == index) ? UM.Theme.colors.text_white : UM.Theme.colors.text
                    }

                    MouseArea {
                        id: mousearea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            if (infillListView.activeIndex != index)
                            {
                                infillListView.activeIndex = index
                                UM.MachineManager.setSettingValue("infill_sparse_density", model.percentage)
                            }
                        }
                        onEntered: {
                            base.showTooltip(infillCellRight, Qt.point(-infillCellRight.x, parent.height), model.text);
                        }
                        onExited: {
                            base.hideTooltip();
                        }
                    }
                }
                Label{
                    id: infillLabel
                    anchors.top: infillIconLining.bottom
                    anchors.horizontalCenter: infillIconLining.horizontalCenter
                    color: infillListView.activeIndex == index ? UM.Theme.colors.setting_control_text : UM.Theme.colors.setting_control_border
                    text: name
                }
            }
        }

        ListModel {
            id: infillModel

            Component.onCompleted:
            {
                infillModel.append({
                    name: catalog.i18nc("@label", "Hollow"),
                    percentage: 0,
                    text: catalog.i18nc("@label", "No (0%) infill will leave your model hollow at the cost of low strength"),
                    icon: "hollow"
                })
                infillModel.append({
                    name: catalog.i18nc("@label", "Light"),
                    percentage: 20,
                    text: catalog.i18nc("@label", "Light (20%) infill will give your model an average strength"),
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
        anchors.top: infillCellRight.bottom
        anchors.topMargin: UM.Theme.sizes.default_margin.height
        anchors.left: parent.left
        width: parent.width/100*35 - UM.Theme.sizes.default_margin.width
        height: childrenRect.height

        Label{
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.sizes.default_margin.width
            //: Helpers selection label
            text: catalog.i18nc("@label:listbox","Helpers:");
            font: UM.Theme.fonts.default;
            color: UM.Theme.colors.text;
        }
    }
    Rectangle {
        id: helpersCellRight
        anchors.top: helpersCellLeft.top
        anchors.left: helpersCellLeft.right
        width: parent.width/100*65 - UM.Theme.sizes.default_margin.width
        height: childrenRect.height

        CheckBox{
            id: brimCheckBox
            property bool hovered_ex: false

            anchors.top: parent.top
            anchors.left: parent.left

            //: Setting enable skirt adhesion checkbox
            text: catalog.i18nc("@option:check","Generate Brim");
            style: UM.Theme.styles.checkbox;

            checked: UM.ActiveProfile.valid ? UM.ActiveProfile.settingValues.adhesion_type == "brim" : false;
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                onClicked:
                {
                    parent.checked = !parent.checked
                    UM.MachineManager.setSettingValue("adhesion_type", parent.checked?"brim":"skirt")
                }
                onEntered:
                {
                    parent.hovered_ex = true
                    base.showTooltip(brimCheckBox, Qt.point(-helpersCellRight.x, parent.height),
                        catalog.i18nc("@label", "Enable printing a brim. This will add a single-layer-thick flat area around your object which is easy to cut off afterwards."));
                }
                onExited:
                {
                    parent.hovered_ex = false
                    base.hideTooltip();
                }
            }
        }
        CheckBox{
            id: supportCheckBox
            property bool hovered_ex: false

            anchors.top: brimCheckBox.bottom
            anchors.topMargin: UM.Theme.sizes.default_lining.height
            anchors.left: parent.left

            //: Setting enable support checkbox
            text: catalog.i18nc("@option:check","Generate Support Structure");
            style: UM.Theme.styles.checkbox;

            checked: UM.ActiveProfile.valid ? UM.ActiveProfile.settingValues.support_enable : false;
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                onClicked:
                {
                    parent.checked = !parent.checked
                    UM.MachineManager.setSettingValue("support_enable", parent.checked)
                }
                onEntered:
                {
                    parent.hovered_ex = true
                    base.showTooltip(supportCheckBox, Qt.point(-helpersCellRight.x, parent.height),
                        catalog.i18nc("@label", "Enable printing support structures. This will build up supporting structures below the model to prevent the model from sagging or printing in mid air."));
                }
                onExited:
                {
                    parent.hovered_ex = false
                    base.hideTooltip();
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
