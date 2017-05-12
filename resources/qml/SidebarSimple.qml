// Copyright (c) 2016 Ultimaker B.V.
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
    property bool settingsEnabled: ExtruderManager.activeExtruderStackId || machineExtruderCount.properties.value == 1

    Component.onCompleted: PrintInformation.enabled = true
    Component.onDestruction: PrintInformation.enabled = false
    UM.I18nCatalog { id: catalog; name:"cura"}

    Item
    {
        id: infillCellLeft
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: base.width * .45 - UM.Theme.getSize("default_margin").width
        height: childrenRect.height

        Text
        {
            id: infillLabel
            //: Infill selection label
            text: catalog.i18nc("@label", "Infill");
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
        }
    }

    Row
    {
        id: infillCellRight

        height: childrenRect.height;
        width: base.width * .5

        spacing: UM.Theme.getSize("default_margin").width

        anchors.left: infillCellLeft.right
        anchors.top: infillCellLeft.top

        Repeater
        {
            id: infillListView
            property int activeIndex:
            {
                var density = parseInt(infillDensity.properties.value);
                var steps = parseInt(infillSteps.properties.value);
                for(var i = 0; i < infillModel.count; ++i)
                {
                    if(density > infillModel.get(i).percentageMin && density <= infillModel.get(i).percentageMax && steps > infillModel.get(i).stepsMin && steps <= infillModel.get(i).stepsMax)
                    {
                        return i;
                    }
                }

                return -1;
            }
            model: infillModel;

            Item
            {
                width: childrenRect.width;
                height: childrenRect.height;

                Rectangle
                {
                    id: infillIconLining

                    width: (infillCellRight.width - ((infillModel.count - 1)  * UM.Theme.getSize("default_margin").width)) / (infillModel.count);
                    height: width

                    border.color:
                    {
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
                    color:
                    {
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

                    UM.RecolorImage
                    {
                        id: infillIcon
                        anchors.fill: parent;
                        anchors.margins: 2

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
                            return UM.Theme.getColor("setting_control_disabled_text")
                        }
                    }

                    MouseArea
                    {
                        id: infillMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: base.settingsEnabled
                        onClicked: {
                            if (infillListView.activeIndex != index)
                            {
                                infillDensity.setPropertyValue("value", model.percentage)
                                infillSteps.setPropertyValue("value", model.steps)
                            }
                        }
                        onEntered:
                        {
                            base.showTooltip(infillCellRight, Qt.point(-infillCellRight.x, 0), model.text);
                        }
                        onExited:
                        {
                            base.hideTooltip();
                        }
                    }
                }
                Text
                {
                    id: infillLabel
                    font: UM.Theme.getFont("default")
                    anchors.top: infillIconLining.bottom
                    anchors.horizontalCenter: infillIconLining.horizontalCenter
                    color: infillListView.activeIndex == index ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_border")
                    text: name
                }
            }
        }

        ListModel
        {
            id: infillModel

            Component.onCompleted:
            {
                infillModel.append({
                    name: catalog.i18nc("@label", "0%"),
                    percentage: 0,
                    steps: 0,
                    percentageMin: -1,
                    percentageMax: 0,
                    stepsMin: -1,
                    stepsMax: 0,
                    text: catalog.i18nc("@label", "Empty infill will leave your model hollow with low strength."),
                    icon: "hollow"
                })
                infillModel.append({
                    name: catalog.i18nc("@label", "20%"),
                    percentage: 20,
                    steps: 0,
                    percentageMin: 0,
                    percentageMax: 30,
                    stepsMin: -1,
                    stepsMax: 0,
                    text: catalog.i18nc("@label", "Light (20%) infill will give your model an average strength."),
                    icon: "sparse"
                })
                infillModel.append({
                    name: catalog.i18nc("@label", "50%"),
                    percentage: 50,
                    steps: 0,
                    percentageMin: 30,
                    percentageMax: 70,
                    stepsMin: -1,
                    stepsMax: 0,
                    text: catalog.i18nc("@label", "Dense (50%) infill will give your model an above average strength."),
                    icon: "dense"
                })
                infillModel.append({
                    name: catalog.i18nc("@label", "100%"),
                    percentage: 100,
                    steps: 0,
                    percentageMin: 70,
                    percentageMax: 9999999999,
                    stepsMin: -1,
                    stepsMax: 0,
                    text: catalog.i18nc("@label", "Solid (100%) infill will make your model completely solid."),
                    icon: "solid"
                })
                infillModel.append({
                    name: catalog.i18nc("@label", "Gradual"),
                    percentage: 90,
                    steps: 5,
                    percentageMin: 0,
                    percentageMax: 9999999999,
                    stepsMin: 0,
                    stepsMax: 9999999999,
                    infill_layer_height: 1.5,
                    text: catalog.i18nc("@label", "Gradual infill will gradually increase the amount of infill towards the top."),
                    icon: "gradual"
                })
            }
        }
    }

    Item
    {
        id: helpersCell
        anchors.top: infillCellRight.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height * 2
        anchors.left: parent.left
        anchors.right: parent.right
        height: childrenRect.height

        Text
        {
            id: enableSupportLabel
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: enableSupportCheckBox.verticalCenter
            width: parent.width * .45 - 3 * UM.Theme.getSize("default_margin").width
            text: catalog.i18nc("@label", "Generate Support");
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
        }

        CheckBox
        {
            id: enableSupportCheckBox
            property alias _hovered: enableSupportMouseArea.containsMouse

            anchors.top: parent.top
            anchors.left: enableSupportLabel.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width

            style: UM.Theme.styles.checkbox;
            enabled: base.settingsEnabled

            checked: supportEnabled.properties.value == "True";

            MouseArea
            {
                id: enableSupportMouseArea
                anchors.fill: parent
                hoverEnabled: true
                enabled: true
                onClicked:
                {
                    // The value is a string "True" or "False"
                    supportEnabled.setPropertyValue("value", supportEnabled.properties.value != "True");
                }
                onEntered:
                {
                    base.showTooltip(enableSupportCheckBox, Qt.point(-enableSupportCheckBox.x, 0),
                        catalog.i18nc("@label", "Generate structures to support parts of the model which have overhangs. Without these structures, such parts would collapse during printing."));
                }
                onExited:
                {
                    base.hideTooltip();
                }
            }
        }

        Text
        {
            id: supportExtruderLabel
            visible: (supportEnabled.properties.value == "True") && (machineExtruderCount.properties.value > 1)
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: supportExtruderCombobox.verticalCenter
            width: parent.width * .45 - 3 * UM.Theme.getSize("default_margin").width
            text: catalog.i18nc("@label", "Support Extruder");
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
        }

        ComboBox
        {
            id: supportExtruderCombobox
            visible: (supportEnabled.properties.value == "True") && (machineExtruderCount.properties.value > 1)
            model: extruderModel

            property string color_override: ""  // for manually setting values
            property string color:  // is evaluated automatically, but the first time is before extruderModel being filled
            {
                var current_extruder = extruderModel.get(currentIndex);
                color_override = "";
                if (current_extruder === undefined) {
                    return "";
                }
                var model_color = current_extruder.color;
                return (model_color) ? model_color : "";
            }

            textRole: 'text'  // this solves that the combobox isn't populated in the first time Cura is started

            anchors.top: enableSupportCheckBox.bottom
            anchors.topMargin:
            {
                if ((supportEnabled.properties.value == "True") && (machineExtruderCount.properties.value > 1))
                {
                    return UM.Theme.getSize("default_margin").height;
                }
                else
                {
                    return 0;
                }
            }
            anchors.left: supportExtruderLabel.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            width: parent.width * .55
            height:
            {
                if ((supportEnabled.properties.value == "True") && (machineExtruderCount.properties.value > 1))
                {
                    // default height when control is enabled
                    return UM.Theme.getSize("setting_control").height;
                }
                else
                {
                    return 0;
                }
            }
            Behavior on height { NumberAnimation { duration: 100 } }

            style: UM.Theme.styles.combobox_color
            enabled: base.settingsEnabled
            property alias _hovered: supportExtruderMouseArea.containsMouse

            currentIndex: supportExtruderNr.properties !== null ? parseFloat(supportExtruderNr.properties.value) : 0
            onActivated:
            {
                // Send the extruder nr as a string.
                supportExtruderNr.setPropertyValue("value", String(index));
            }
            MouseArea
            {
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

            function updateCurrentColor()
            {
                var current_extruder = extruderModel.get(currentIndex);
                if (current_extruder !== undefined) {
                    supportExtruderCombobox.color_override = current_extruder.color;
                }
            }

        }

        Text
        {
            id: adhesionHelperLabel
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: adhesionCheckBox.verticalCenter
            width: parent.width * .45 - 3 * UM.Theme.getSize("default_margin").width
            text: catalog.i18nc("@label", "Build Plate Adhesion");
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
        }

        CheckBox
        {
            id: adhesionCheckBox
            property alias _hovered: adhesionMouseArea.containsMouse

            anchors.top: supportExtruderCombobox.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height * 2
            anchors.left: adhesionHelperLabel.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width

            //: Setting enable printing build-plate adhesion helper checkbox
            style: UM.Theme.styles.checkbox;
            enabled: base.settingsEnabled

            checked: platformAdhesionType.properties.value != "skirt" && platformAdhesionType.properties.value != "none"

            MouseArea
            {
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

        ListModel
        {
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
        for(var extruderNumber = 0; extruderNumber < extruders.rowCount() ; extruderNumber++)
        {
            extruderModel.append({
                text: extruders.getItem(extruderNumber).name,
                color: extruders.getItem(extruderNumber).color
            })
        }
        supportExtruderCombobox.updateCurrentColor();
    }

    Item
    {
        id: tipsCell
        anchors.top: helpersCell.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height * 2
        anchors.left: parent.left
        width: parent.width
        height: childrenRect.height

        Text
        {
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            wrapMode: Text.WordWrap
            //: Tips label
            text: catalog.i18nc("@label", "Need help improving your prints?<br>Read the <a href='%1'>Ultimaker Troubleshooting Guides</a>").arg("https://ultimaker.com/en/troubleshooting");
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
        id: infillSteps

        containerStackId: Cura.MachineManager.activeStackId
        key: "gradual_infill_steps"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: platformAdhesionType

        containerStackId: Cura.MachineManager.activeMachineId
        key: "adhesion_type"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: supportEnabled

        containerStackId: Cura.MachineManager.activeMachineId
        key: "support_enable"
        watchedProperties: [ "value", "description" ]
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

        containerStackId: Cura.MachineManager.activeMachineId
        key: "support_extruder_nr"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }
}
