// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

UM.Dialog
{
    title: catalog.i18nc("@title:window", "Import workspace conflict")

    width: 500 * Screen.devicePixelRatio;
    minimumWidth: 500 * Screen.devicePixelRatio;
    maximumWidth: 500 * Screen.devicePixelRatio;

    height: 350 * Screen.devicePixelRatio;
    minimumHeight: 350 * Screen.devicePixelRatio;
    maximumHeight: 350 * Screen.devicePixelRatio;
    property int comboboxHeight: 20

    onClosing: manager.notifyClosed()
    onVisibleChanged:
    {
        if(visible)
        {
            machineResolveComboBox.currentIndex = 0
            qualityChangesResolveComboBox.currentIndex = 0
            materialConflictComboBox.currentIndex = 0
        }
    }
    Item
    {
        anchors.fill: parent

        UM.I18nCatalog
        {
            id: catalog;
            name: "cura";
        }

        ListModel
        {
            id: resolveStrategiesModel
            // Instead of directly adding the list elements, we add them afterwards.
            // This is because it's impossible to use setting function results to be bound to listElement properties directly.
            // See http://stackoverflow.com/questions/7659442/listelement-fields-as-properties
            Component.onCompleted:
            {
                append({"key": "override", "label": catalog.i18nc("@action:ComboBox option", "Update existing")});
                append({"key": "new", "label": catalog.i18nc("@action:ComboBox option", "Create new")});
            }
        }

        Column
        {
            anchors.fill: parent
            spacing: 2
            Label
            {
                id: titleLabel
                text: catalog.i18nc("@action:title", "Summary - Cura Project")
                font.pixelSize: 22
            }
            Rectangle
            {
                id: separator
                color: "black"
                width: parent.width
                height: 1
            }
            Item // Spacer
            {
                height: 5
                width: height
            }

            Label
            {
                text: catalog.i18nc("@action:label", "Printer settings")
                font.bold: true
            }

            Row
            {
                width: parent.width
                height: childrenRect.height
                Label
                {
                    text: catalog.i18nc("@action:label", "Name")
                    width: parent.width / 3
                }
                Label
                {
                    text: manager.machineName
                    width: parent.width / 3
                }

                UM.TooltipArea
                {
                    id: machineResolveTooltip
                    width: parent.width / 3
                    height: visible ? comboboxHeight : 0
                    visible: manager.machineConflict
                    text: catalog.i18nc("@info:tooltip", "How should the conflict in the machine be resolved?")
                    ComboBox
                    {
                        model: resolveStrategiesModel
                        textRole: "label"
                        id: machineResolveComboBox
                        width: parent.width
                        onActivated:
                        {
                            manager.setResolveStrategy("machine", resolveStrategiesModel.get(index).key)
                        }
                    }
                }
            }

            Label
            {
                text: catalog.i18nc("@action:label", "Profile settings")
                font.bold: true
            }

            Row
            {
                width: parent.width
                height: childrenRect.height
                Label
                {
                    text: catalog.i18nc("@action:label", "Name")
                    width: parent.width / 3
                }
                Label
                {
                    text: manager.qualityName
                    width: parent.width / 3
                }

                UM.TooltipArea
                {
                    id: qualityChangesResolveTooltip
                    width: parent.width / 3
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
                    text: catalog.i18nc("@action:label", "Derivative from")
                    width: parent.width / 3
                }
                Label
                {
                    text: catalog.i18nc("@action:label", "%1, %2 overrides" ).arg(manager.qualityType).arg(manager.numSettingsOverridenByQualityChanges)
                    width: parent.width / 3
                }
                visible: manager.numSettingsOverridenByQualityChanges != 0
            }

            Label
            {
                text: catalog.i18nc("@action:label", "Material settings")
                font.bold: true
            }

            Row
            {
                width: parent.width
                height: childrenRect.height
                Label
                {
                    text: catalog.i18nc("@action:label", "Type")
                    width: parent.width / 3
                }
                Label
                {
                    text: catalog.i18nc("@action:label", "TOCHANGE")
                    width: parent.width / 3
                }

                UM.TooltipArea
                {
                    id: materialResolveTooltip
                    width: parent.width / 3
                    height: visible ? comboboxHeight : 0
                    visible: manager.materialConflict
                    text: catalog.i18nc("@info:tooltip", "How should the conflict in the profile be resolved?")
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
                    width: parent.width / 3
                }
                Label
                {
                    text: manager.activeMode
                    width: parent.width / 3
                }
            }
            Row
            {
                width: parent.width
                height: childrenRect.height
                Label
                {
                    text: catalog.i18nc("@action:label", "Visible settings:")
                    width: parent.width / 3
                }
                Label
                {
                    text: catalog.i18nc("@action:label", "%1 out of %2" ).arg(manager.numVisibleSettings).arg(manager.totalNumberOfSettings)
                    width: parent.width / 3
                }
            }
        }
    }
    rightButtons: [
        Button
        {
            id: ok_button
            text: catalog.i18nc("@action:button","OK");
            onClicked: { manager.onOkButtonClicked() }
            enabled: true
        },
        Button
        {
            id: cancel_button
            text: catalog.i18nc("@action:button","Cancel");
            onClicked: { manager.onCancelButtonClicked() }
            enabled: true
        }
    ]
}