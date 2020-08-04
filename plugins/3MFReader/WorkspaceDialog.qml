// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtQuick.Window 2.2

import UM 1.1 as UM

UM.Dialog
{
    id: base
    title: catalog.i18nc("@title:window", "Open Project")

    minimumWidth: UM.Theme.getSize("popup_dialog").width
    minimumHeight: UM.Theme.getSize("popup_dialog").height
    width: minimumWidth
    height: minimumHeight

    property int comboboxHeight: 15 * screenScaleFactor
    property int spacerHeight: 10 * screenScaleFactor
    property int doubleSpacerHeight: 20 * screenScaleFactor

    onClosing: manager.notifyClosed()
    onVisibleChanged:
    {
        if (visible)
        {
            machineResolveComboBox.currentIndex = 0
            qualityChangesResolveComboBox.currentIndex = 0
            materialResolveComboBox.currentIndex = 0
        }
    }

    Item
    {
        anchors.fill: parent
        anchors.margins: 10 * screenScaleFactor

        UM.I18nCatalog
        {
            id: catalog
            name: "cura"
        }
        SystemPalette
        {
            id: palette
        }

        ListModel
        {
            id: resolveStrategiesModel
            // Instead of directly adding the list elements, we add them afterwards.
            // This is because it's impossible to use setting function results to be bound to listElement properties directly.
            // See http://stackoverflow.com/questions/7659442/listelement-fields-as-properties
            Component.onCompleted:
            {
                append({"key": "override", "label": catalog.i18nc("@action:ComboBox Update/override existing profile", "Update existing")});
                append({"key": "new", "label": catalog.i18nc("@action:ComboBox Save settings in a new profile", "Create new")});
            }
        }

        Column
        {
            anchors.fill: parent
            spacing: 2 * screenScaleFactor
            Label
            {
                id: titleLabel
                text: catalog.i18nc("@action:title", "Summary - Cura Project")
                font.pointSize: 18
            }
            Rectangle
            {
                id: separator
                color: palette.text
                width: parent.width
                height: 1
            }
            Item // Spacer
            {
                height: doubleSpacerHeight
                width: height
            }

            Row
            {
                height: childrenRect.height
                width: parent.width
                Label
                {
                    text: catalog.i18nc("@action:label", "Printer settings")
                    font.bold: true
                    width: (parent.width / 3) | 0
                }
                Item
                {
                    // spacer
                    height: spacerHeight
                    width: (parent.width / 3) | 0
                }
                UM.TooltipArea
                {
                    id: machineResolveStrategyTooltip
                    width: (parent.width / 3) | 0
                    height: visible ? comboboxHeight : 0
                    visible: base.visible && machineResolveComboBox.model.count > 1
                    text: catalog.i18nc("@info:tooltip", "How should the conflict in the machine be resolved?")
                    ComboBox
                    {
                        id: machineResolveComboBox
                        model: manager.updatableMachinesModel
                        visible: machineResolveStrategyTooltip.visible
                        textRole: "displayName"
                        width: parent.width
                        onCurrentIndexChanged:
                        {
                            if (model.getItem(currentIndex).id == "new"
                                && model.getItem(currentIndex).type == "default_option")
                            {
                                manager.setResolveStrategy("machine", "new")
                            }
                            else
                            {
                                manager.setResolveStrategy("machine", "override")
                                manager.setMachineToOverride(model.getItem(currentIndex).id)
                            }
                        }

                        onVisibleChanged:
                        {
                            if (!visible) {return}

                            currentIndex = 0
                            // If the project printer exists in Cura, set it as the default dropdown menu option.
                            // No need to check object 0, which is the "Create new" option
                            for (var i = 1; i < model.count; i++)
                            {
                                if (model.getItem(i).name == manager.machineName)
                                {
                                    currentIndex = i
                                    break
                                }
                            }
                            // The project printer does not exist in Cura. If there is at least one printer of the same
                            // type, select the first one, else set the index to "Create new"
                            if (currentIndex == 0 && model.count > 1)
                            {
                                currentIndex = 1
                            }
                        }
                    }
                }
            }
            Row
            {
                width: parent.width
                height: childrenRect.height
                Label
                {
                    text: catalog.i18nc("@action:label", "Type")
                    width: (parent.width / 3) | 0
                }
                Label
                {
                    text: manager.machineType
                    width: (parent.width / 3) | 0
                }
            }

            Row
            {
                width: parent.width
                height: childrenRect.height
                Label
                {
                    text: catalog.i18nc("@action:label", manager.isPrinterGroup ? "Printer Group" : "Printer Name")
                    width: (parent.width / 3) | 0
                }
                Label
                {
                    text: manager.machineName
                    width: (parent.width / 3) | 0
                }
            }

            Item // Spacer
            {
                height: doubleSpacerHeight
                width: height
            }
            Row
            {
                height: childrenRect.height
                width: parent.width
                Label
                {
                    text: catalog.i18nc("@action:label", "Profile settings")
                    font.bold: true
                    width: (parent.width / 3) | 0
                }
                Item
                {
                    // spacer
                    height: spacerHeight
                    width: (parent.width / 3) | 0
                }
                UM.TooltipArea
                {
                    id: qualityChangesResolveTooltip
                    width: (parent.width / 3) | 0
                    height: visible ? comboboxHeight : 0
                    visible: manager.qualityChangesConflict
                    text: catalog.i18nc("@info:tooltip", "How should the conflict in the profile be resolved?")
                    ComboBox
                    {
                        model: resolveStrategiesModel
                        textRole: "label"
                        id: qualityChangesResolveComboBox
                        width: parent.width
                        onActivated:
                        {
                            manager.setResolveStrategy("quality_changes", resolveStrategiesModel.get(index).key)
                        }
                    }
                }
            }
            Row
            {
                width: parent.width
                height: childrenRect.height
                Label
                {
                    text: catalog.i18nc("@action:label", "Name")
                    width: (parent.width / 3) | 0
                }
                Label
                {
                    text: manager.qualityName
                    width: (parent.width / 3) | 0
                }
            }
            Row
            {
                width: parent.width
                height: childrenRect.height
                Label
                {
                    text: catalog.i18nc("@action:label", "Intent")
                    width: (parent.width / 3) | 0
                }
                Label
                {
                    text: manager.intentName
                    width: (parent.width / 3) | 0
                }
            }
            Row
            {
                width: parent.width
                height: manager.numUserSettings != 0 ? childrenRect.height : 0
                Label
                {
                    text: catalog.i18nc("@action:label", "Not in profile")
                    width: (parent.width / 3) | 0
                }
                Label
                {
                    text: catalog.i18ncp("@action:label", "%1 override", "%1 overrides", manager.numUserSettings).arg(manager.numUserSettings)
                    width: (parent.width / 3) | 0
                }
                visible: manager.numUserSettings != 0
            }
            Row
            {
                width: parent.width
                height: manager.numSettingsOverridenByQualityChanges != 0 ? childrenRect.height : 0
                Label
                {
                    text: catalog.i18nc("@action:label", "Derivative from")
                    width: (parent.width / 3) | 0
                }
                Label
                {
                    text: catalog.i18ncp("@action:label", "%1, %2 override", "%1, %2 overrides", manager.numSettingsOverridenByQualityChanges).arg(manager.qualityType).arg(manager.numSettingsOverridenByQualityChanges)
                    width: (parent.width / 3) | 0
                }
                visible: manager.numSettingsOverridenByQualityChanges != 0
            }
            Item // Spacer
            {
                height: doubleSpacerHeight
                width: height
            }
            Row
            {
                height: childrenRect.height
                width: parent.width
                Label
                {
                    text: catalog.i18nc("@action:label", "Material settings")
                    font.bold: true
                    width: (parent.width / 3) | 0
                }
                Item
                {
                    // spacer
                    height: spacerHeight
                    width: (parent.width / 3) | 0
                }
                UM.TooltipArea
                {
                    id: materialResolveTooltip
                    width: (parent.width / 3) | 0
                    height: visible ? comboboxHeight : 0
                    visible: manager.materialConflict
                    text: catalog.i18nc("@info:tooltip", "How should the conflict in the material be resolved?")
                    ComboBox
                    {
                        model: resolveStrategiesModel
                        textRole: "label"
                        id: materialResolveComboBox
                        width: parent.width
                        onActivated:
                        {
                            manager.setResolveStrategy("material", resolveStrategiesModel.get(index).key)
                        }
                    }
                }
            }

            Repeater
            {
                model: manager.materialLabels
                delegate: Row
                {
                    width: parent.width
                    height: childrenRect.height
                    Label
                    {
                        text: catalog.i18nc("@action:label", "Name")
                        width: (parent.width / 3) | 0
                    }
                    Label
                    {
                        text: modelData
                        width: (parent.width / 3) | 0
                    }
                }
            }

            Item // Spacer
            {
                height: doubleSpacerHeight
                width: height
            }

            Label
            {
                text: catalog.i18nc("@action:label", "Setting visibility")
                font.bold: true
            }
            Row
            {
                width: parent.width
                height: childrenRect.height
                Label
                {
                    text: catalog.i18nc("@action:label", "Mode")
                    width: (parent.width / 3) | 0
                }
                Label
                {
                    text: manager.activeMode
                    width: (parent.width / 3) | 0
                }
            }
            Row
            {
                width: parent.width
                height: childrenRect.height
                visible: manager.hasVisibleSettingsField
                Label
                {
                    text: catalog.i18nc("@action:label", "Visible settings:")
                    width: (parent.width / 3) | 0
                }
                Label
                {
                    text: catalog.i18nc("@action:label", "%1 out of %2" ).arg(manager.numVisibleSettings).arg(manager.totalNumberOfSettings)
                    width: (parent.width / 3) | 0
                }
            }
            Item // Spacer
            {
                height: spacerHeight
                width: height
            }
            Row
            {
                width: parent.width
                height: childrenRect.height
                visible: manager.hasObjectsOnPlate
                UM.RecolorImage
                {
                    width: warningLabel.height
                    height: width

                    source: UM.Theme.getIcon("notice")
                    color: palette.text

                }
                Label
                {
                    id: warningLabel
                    text: catalog.i18nc("@action:warning", "Loading a project will clear all models on the build plate.")
                    wrapMode: Text.Wrap
                }
            }
        }
        Button
        {
            id: cancel_button
            text: catalog.i18nc("@action:button","Cancel");
            onClicked: { manager.onCancelButtonClicked() }
            enabled: true
            anchors.bottom: parent.bottom
            anchors.right: ok_button.left
            anchors.rightMargin: 2 * screenScaleFactor
        }
        Button
        {
            id: ok_button
            text: catalog.i18nc("@action:button","Open");
            onClicked: { manager.closeBackend(); manager.onOkButtonClicked() }
            anchors.bottom: parent.bottom
            anchors.right: parent.right
        }
    }

    function accept() {
        manager.closeBackend();
        manager.onOkButtonClicked();
        base.visible = false;
        base.accept();
    }

    function reject() {
        manager.onCancelButtonClicked();
        base.visible = false;
        base.rejected();
    }
}
