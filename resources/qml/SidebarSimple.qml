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

    signal showTooltip(Item item, point location, string text);
    signal hideTooltip();

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
        width: base.width/100* 35 - UM.Theme.getSize("default_margin").width
        height: childrenRect.height

        Label{
            id: infillLabel
            //: Infill selection label
            text: catalog.i18nc("@label","Infill:");
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
        }
    }

    Flow {
        id: infillCellRight

        height: childrenRect.height;
        width: base.width / 100 * 65
        spacing: UM.Theme.getSize("default_margin").width

        anchors.left: infillCellLeft.right
        anchors.top: infillCellLeft.top

        Repeater {
            id: infillListView
            property int activeIndex: {
                if(!UM.ActiveProfile.valid)
                {
                    return -1;
                }

                var density = parseInt(UM.ActiveProfile.settingValues.getValue("infill_sparse_density"));
                for(var i = 0; i < infillModel.count; ++i)
                {
                    if(density > infillModel.get(i).percentageMin && density <= infillModel.get(i).percentageMax )
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

                    width: (infillCellRight.width - 3 * UM.Theme.getSize("default_margin").width) / 4;
                    height: width

                    border.color: {
                        if(infillListView.activeIndex == index)
                        {
                            return UM.Theme.getColor("setting_control_selected")
                        }
                        else if(mousearea.containsMouse)
                        {
                            return UM.Theme.getColor("setting_control_border_highlight")
                        }
                        return UM.Theme.getColor("setting_control_border")
                    }
                    border.width: UM.Theme.getSize("default_lining").width
                    color: infillListView.activeIndex == index ? UM.Theme.getColor("setting_control_selected") : "transparent"

                    UM.RecolorImage {
                        id: infillIcon
                        anchors.fill: parent;
                        anchors.margins: UM.Theme.getSize("infill_button_margin").width

                        sourceSize.width: width
                        sourceSize.height: width
                        source: UM.Theme.getIcon(model.icon);
                        color: (infillListView.activeIndex == index) ? UM.Theme.getColor("text_white") : UM.Theme.getColor("text")
                    }

                    MouseArea {
                        id: mousearea
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            if (infillListView.activeIndex != index)
                            {
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
                    color: infillListView.activeIndex == index ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_border")
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
                    percentageMin: -1,
                    percentageMax: 0,
                    text: catalog.i18nc("@label", "No (0%) infill will leave your model hollow at the cost of low strength"),
                    icon: "hollow"
                })
                infillModel.append({
                    name: catalog.i18nc("@label", "Light"),
                    percentage: 20,
                    percentageMin: 0,
                    percentageMax: 30,
                    text: catalog.i18nc("@label", "Light (20%) infill will give your model an average strength"),
                    icon: "sparse"
                })
                infillModel.append({
                    name: catalog.i18nc("@label", "Dense"),
                    percentage: 50,
                    percentageMin: 30,
                    percentageMax: 70,
                    text: catalog.i18nc("@label", "Dense (50%) infill will give your model an above average strength"),
                    icon: "dense"
                })
                infillModel.append({
                    name: catalog.i18nc("@label", "Solid"),
                    percentage: 100,
                    percentageMin: 70,
                    percentageMax: 100,
                    text: catalog.i18nc("@label", "Solid (100%) infill will make your model completely solid"),
                    icon: "solid"
                })
            }
        }
    }

    Rectangle {
        id: helpersCellLeft
        anchors.top: infillCellRight.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.left: parent.left
        width: parent.width/100*35 - UM.Theme.getSize("default_margin").width
        height: childrenRect.height

        Label{
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            //: Helpers selection label
            text: catalog.i18nc("@label:listbox","Helpers:");
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
        }
    }
    Rectangle {
        id: helpersCellRight
        anchors.top: helpersCellLeft.top
        anchors.left: helpersCellLeft.right
        width: parent.width/100*65 - UM.Theme.getSize("default_margin").width
        height: childrenRect.height

        CheckBox{
            id: brimCheckBox
            property bool hovered_ex: false

            anchors.top: parent.top
            anchors.left: parent.left

            //: Setting enable skirt adhesion checkbox
            text: catalog.i18nc("@option:check","Generate Brim");
            style: UM.Theme.styles.checkbox;

            checked: UM.ActiveProfile.valid ? UM.ActiveProfile.settingValues.getValue("adhesion_type") == "brim" : false;
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                onClicked:
                {
                    UM.MachineManager.setSettingValue("adhesion_type", !parent.checked?"brim":"skirt")
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
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: parent.left

            //: Setting enable support checkbox
            text: catalog.i18nc("@option:check","Generate Support Structure");
            style: UM.Theme.styles.checkbox;

            checked: UM.ActiveProfile.valid ? UM.ActiveProfile.settingValues.getValue("support_enable") : false;
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                onClicked:
                {
                    UM.MachineManager.setSettingValue("support_enable", !parent.checked)
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

    Rectangle {
        id: tipsCell
        anchors.top: helpersCellRight.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.left: parent.left
        width: parent.width
        height: childrenRect.height

        Label{
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            width: parent.width
            wrapMode: Text.WordWrap
            //: Tips label
            text: catalog.i18nc("@label","Need help improving your prints? Read the <a href='%1'>Ultimaker Troubleshooting Guides</a>").arg("https://ultimaker.com/en/troubleshooting");
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
            linkColor: UM.Theme.getColor("text_link")
            onLinkActivated: Qt.openUrlExternally(link)
        }
    }
}
