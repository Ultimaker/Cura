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

    width: 350 * Screen.devicePixelRatio;
    minimumWidth: 350 * Screen.devicePixelRatio;
    maximumWidth: 350 * Screen.devicePixelRatio;

    height: 250 * Screen.devicePixelRatio;
    minimumHeight: 250 * Screen.devicePixelRatio;
    maximumHeight: 250 * Screen.devicePixelRatio;

    onClosing: manager.notifyClosed()
    onVisibleChanged:
    {
        if(visible)
        {
            machineResolveComboBox.currentIndex = 0
            qualityChangesResolveComboBox.currentIndex = 0
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
                append({"key": "override", "label": catalog.i18nc("@action:ComboBox option", "Override existing")});
                append({"key": "new", "label": catalog.i18nc("@action:ComboBox option", "Create new")});
            }
        }

        Column
        {
            anchors.fill: parent
            Label
            {
                id: infoLabel
                width: parent.width
                text: catalog.i18nc("@action:label", "Cura detected a number of conflicts while importing the workspace. How would you like to resolve these?")
                wrapMode: Text.Wrap
                height: 50
            }
            UM.TooltipArea
            {
                id: machineResolveTooltip
                width: parent.width
                height: visible ? 25 : 0
                text: catalog.i18nc("@info:tooltip", "How should the conflict in the machine be resolved?")
                visible: manager.machineConflict
                Row
                {
                    width: parent.width
                    height: childrenRect.height
                    Label
                    {
                        text: catalog.i18nc("@action:label","Machine")
                        width: 150
                    }

                    ComboBox
                    {
                        model: resolveStrategiesModel
                        textRole: "label"
                        id: machineResolveComboBox
                        onActivated:
                        {
                            manager.setResolveStrategy("machine", resolveStrategiesModel.get(index).key)
                        }
                    }
                }
            }
            UM.TooltipArea
            {
                id: qualityChangesResolveTooltip
                width: parent.width
                height: visible ? 25 : 0
                text: catalog.i18nc("@info:tooltip", "How should the conflict in the profile be resolved?")
                visible: manager.qualityChangesConflict
                Row
                {
                    width: parent.width
                    height: childrenRect.height
                    Label
                    {
                        text: catalog.i18nc("@action:label","Profile")
                        width: 150
                    }

                    ComboBox
                    {
                        model: resolveStrategiesModel
                        textRole: "label"
                        id: qualityChangesResolveComboBox
                        onActivated:
                        {
                            manager.setResolveStrategy("machine", resolveStrategiesModel.get(index).key)
                        }
                    }
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