// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: base;

    signal showTooltip(Item item, point location, string text);
    signal hideTooltip();

    property Action configureSettings;
    property variant minimumPrintTime: PrintInformation.minimumPrintTime;
    property variant maximumPrintTime: PrintInformation.maximumPrintTime;
    property bool settingsEnabled: ExtruderManager.activeExtruderStackId || ExtruderManager.extruderCount == 0

    Component.onCompleted: PrintInformation.enabled = true
    Component.onDestruction: PrintInformation.enabled = false
    UM.I18nCatalog { id: catalog; name:"cura"}

    Rectangle{
        id: infillCellLeft
        anchors.top: parent.top
        anchors.left: parent.left
        width: base.width / 100 * 35 - UM.Theme.getSize("default_margin").width
        height: childrenRect.height

        Label{
            id: infillLabel
            //: Infill selection label
            text: catalog.i18nc("@label", "Infill:");
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
                var density = parseInt(infillDensity.properties.value)
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
                        if(!base.settingsEnabled)
                        {
                            return UM.Theme.getColor("setting_control_disabled_border")
                        }
                        else if(infillListView.activeIndex == index)
                        {
                            return UM.Theme.getColor("setting_control_selected")
                        }
                        else if(infillMouseArea.containsMouse)
                        {
                            return UM.Theme.getColor("setting_control_border_highlight")
                        }
                        return UM.Theme.getColor("setting_control_border")
                    }
                    border.width: UM.Theme.getSize("default_lining").width
                    color: {
                        if(infillListView.activeIndex == index)
                        {
                            if(!base.settingsEnabled)
                            {
                                return UM.Theme.getColor("setting_control_disabled_text")
                            }
                            return UM.Theme.getColor("setting_control_selected")
                        }
                        return "transparent"
                    }

                    UM.RecolorImage {
                        id: infillIcon
                        anchors.fill: parent;
                        anchors.margins: UM.Theme.getSize("infill_button_margin").width

                        sourceSize.width: width
                        sourceSize.height: width
                        source: UM.Theme.getIcon(model.icon);
                        color: {
                            if(infillListView.activeIndex == index)
                            {
                                return UM.Theme.getColor("text_reversed")
                            }
                            if(!base.settingsEnabled)
                            {
                                return UM.Theme.getColor("setting_control_disabled_text")
                            }
                            return UM.Theme.getColor("text")
                        }
                    }

                    MouseArea {
                        id: infillMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: base.settingsEnabled
                        onClicked: {
                            if (infillListView.activeIndex != index)
                            {
                                infillDensity.setPropertyValue("value", model.percentage)
                            }
                        }
                        onEntered: {
                            base.showTooltip(infillCellRight, Qt.point(-infillCellRight.x, 0), model.text);
                        }
                        onExited: {
                            base.hideTooltip();
                        }
                    }
                }
                Label{
                    id: infillLabel
                    font: UM.Theme.getFont("default")
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
        id: helpersCell
        anchors.top: infillCellRight.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.left: parent.left
        anchors.right: parent.right
        height: childrenRect.height

        Label{
            id: adhesionHelperLabel
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: adhesionCheckBox.verticalCenter
            width: parent.width / 100 * 35 - 3 * UM.Theme.getSize("default_margin").width
            //: Bed adhesion label
            text: catalog.i18nc("@label", "Helper Parts:");
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
        }

        CheckBox{
            id: adhesionCheckBox
            property alias _hovered: adhesionMouseArea.containsMouse

            anchors.top: parent.top
            anchors.left: adhesionHelperLabel.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width

            //: Setting enable printing build-plate adhesion helper checkbox
            text: catalog.i18nc("@option:check", "Print Build Plate Adhesion");
            style: UM.Theme.styles.checkbox;
            enabled: base.settingsEnabled

            checked: platformAdhesionType.properties.value != "skirt"

            MouseArea {
                id: adhesionMouseArea
                anchors.fill: parent
                hoverEnabled: true
                enabled: base.settingsEnabled
                onClicked:
                {
                    var adhesionType = "skirt";
                    if(!parent.checked)
                    {
                        // Remove the "user" setting to see if the rest of the stack prescribes a brim or a raft
                        platformAdhesionType.removeFromContainer(0);
                        adhesionType = platformAdhesionType.properties.value;
                        if(adhesionType == "skirt")
                        {
                            // If the rest of the stack doesn't prescribe an adhesion-type, default to a brim
                            adhesionType = "brim";
                        }
                    }
                    platformAdhesionType.setPropertyValue("value", adhesionType);
                }
                onEntered:
                {
                    base.showTooltip(adhesionCheckBox, Qt.point(-adhesionCheckBox.x, 0),
                        catalog.i18nc("@label", "Enable printing a brim or raft. This will add a flat area around or under your object which is easy to cut off afterwards."));
                }
                onExited:
                {
                    base.hideTooltip();
                }
            }
        }

        Label{
            id: supportHelperLabel
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: supportCheckBox.verticalCenter
            width: parent.width / 100 * 35 - 3 * UM.Theme.getSize("default_margin").width
            //: Support label
            text: "";
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
        }

        CheckBox{
            id: supportCheckBox
            visible: machineExtruderCount.properties.value <= 1
            property alias _hovered: supportMouseArea.containsMouse

            anchors.top: adhesionCheckBox.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: supportHelperLabel.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width

            //: Setting enable support checkbox
            text: catalog.i18nc("@option:check", "Print Support Structure");
            style: UM.Theme.styles.checkbox;
            enabled: base.settingsEnabled

            checked: supportEnabled.properties.value == "True"
            MouseArea {
                id: supportMouseArea
                anchors.fill: parent
                hoverEnabled: true
                enabled: base.settingsEnabled
                onClicked:
                {
                    supportEnabled.setPropertyValue("value", !parent.checked)
                }
                onEntered:
                {
                    base.showTooltip(supportCheckBox, Qt.point(-supportCheckBox.x, 0),
                        catalog.i18nc("@label", "Enable printing support structures. This will build up supporting structures below the model to prevent the model from sagging or printing in mid air."));
                }
                onExited:
                {
                    base.hideTooltip();
                }
            }
        }

        ComboBox {
            id: supportExtruderCombobox
            visible: machineExtruderCount.properties.value > 1
            model: extruderModel

            anchors.top: adhesionCheckBox.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: supportHelperLabel.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            width: parent.width / 100 * 45

            style: UM.Theme.styles.combobox
            enabled: base.settingsEnabled
            property alias _hovered: supportExtruderMouseArea.containsMouse

            currentIndex: supportEnabled.properties.value == "True" ? parseFloat(supportExtruderNr.properties.value) + 1 : 0
            onActivated: {
                if(index==0) {
                    supportEnabled.setPropertyValue("value", false);
                } else {
                    supportEnabled.setPropertyValue("value", true);
                    // Send the extruder nr as a string.
                    supportExtruderNr.setPropertyValue("value", String(index - 1));
                }
            }
            MouseArea {
                id: supportExtruderMouseArea
                anchors.fill: parent
                hoverEnabled: true
                enabled: base.settingsEnabled
                acceptedButtons: Qt.NoButton
                onEntered:
                {
                    base.showTooltip(supportExtruderCombobox, Qt.point(-supportExtruderCombobox.x, 0),
                        catalog.i18nc("@label", "Select which extruder to use for support. This will build up supporting structures below the model to prevent the model from sagging or printing in mid air."));
                }
                onExited:
                {
                    base.hideTooltip();
                }
            }
        }

        ListModel {
            id: extruderModel
            Component.onCompleted: populateExtruderModel()
        }

        //: Model used to populate the extrudelModel
        Cura.ExtrudersModel
        {
            id: extruders
            onModelChanged: populateExtruderModel()
        }
    }

    function populateExtruderModel()
    {
        extruderModel.clear();
        extruderModel.append({
            text: catalog.i18nc("@label", "Don't print support"),
            color: ""
        })
        for(var extruderNumber = 0; extruderNumber < extruders.rowCount() ; extruderNumber++) {
            extruderModel.append({
                text: catalog.i18nc("@label", "Print support using %1").arg(extruders.getItem(extruderNumber).name),
                color: extruders.getItem(extruderNumber).color
            })
        }
    }

    Rectangle {
        id: tipsCell
        anchors.top: helpersCell.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.left: parent.left
        width: parent.width
        height: childrenRect.height

        Label{
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            wrapMode: Text.WordWrap
            //: Tips label
            text: catalog.i18nc("@label", "Need help improving your prints? Read the <a href='%1'>Ultimaker Troubleshooting Guides</a>").arg("https://ultimaker.com/en/troubleshooting");
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
            linkColor: UM.Theme.getColor("text_link")
            onLinkActivated: Qt.openUrlExternally(link)
        }
    }

    UM.SettingPropertyProvider
    {
        id: infillDensity

        containerStackId: Cura.MachineManager.activeStackId
        key: "infill_sparse_density"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: platformAdhesionType

        containerStackId: Cura.MachineManager.activeStackId
        key: "adhesion_type"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: supportEnabled

        containerStackId: Cura.MachineManager.activeStackId
        key: "support_enable"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: machineExtruderCount

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_extruder_count"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: supportExtruderNr

        containerStackId: Cura.MachineManager.activeStackId
        key: "support_extruder_nr"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }
}
