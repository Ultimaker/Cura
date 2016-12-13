// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.2 as UM
import Cura 1.0 as Cura

UM.Dialog
{
    title: catalog.i18nc("@title:window", "Save Project")

    width: 550
    minimumWidth: 550
    maximumWidth: 550

    height: 350
    minimumHeight: 350
    maximumHeight: 350
    property int spacerHeight: 10

    property bool dontShowAgain: true

    signal yes();


    onClosing:
    {
        UM.Preferences.setValue("cura/asked_dialog_on_project_save", true)
        UM.Preferences.setValue("cura/dialog_on_project_save", !dontShowAgainCheckbox.checked)
    }

    onVisibleChanged:
    {
        if(visible)
        {
            if (UM.Preferences.getValue("cura/asked_dialog_on_project_save"))
            {
                dontShowAgain = true
            } else { dontShowAgain = UM.Preferences.setValue("cura/dialog_on_project_save")}
        }
    }

    Item
    {
        anchors.fill: parent
        UM.SettingDefinitionsModel
        {
            id: definitionsModel
            containerId: Cura.MachineManager.activeDefinitionId
            showAll: true
            exclude: ["command_line_settings"]
            showAncestors: true
            expanded: ["*"]
            visibilityHandler: UM.SettingPreferenceVisibilityHandler { }
        }
        UM.I18nCatalog
        {
            id: catalog;
            name: "cura";
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
                height: spacerHeight
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
                    text: Cura.MachineManager.activeMachineName
                    width: parent.width / 3
                }

            }
            Item // Spacer
            {
                height: spacerHeight
                width: height
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
                    text: Cura.MachineManager.activeQualityName
                    width: parent.width / 3
                }

            }
            Item // Spacer
            {
                height: spacerHeight
                width: height
            }

            Label
            {
                text: catalog.i18nc("@action:label", "Material settings")
                font.bold: true
            }

            Repeater
            {
                model: Cura.MachineManager.activeMaterialNames
                delegate: Row
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
                        text: modelData
                        width: parent.width / 3
                    }
                }
            }


            Item // Spacer
            {
                height: spacerHeight
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
                    text: catalog.i18nc("@action:label", "Visible settings:")
                    width: parent.width / 3
                }
                Label
                {
                    text: catalog.i18nc("@action:label", "%1 out of %2" ).arg(definitionsModel.visibleCount).arg(Cura.MachineManager.totalNumberOfSettings)
                    width: parent.width / 3
                }
            }
            CheckBox
            {
                id: dontShowAgainCheckbox
                text: catalog.i18nc("@action:label", "Don't show project summary on save again")
                checked: dontShowAgain
            }
        }
    }
    rightButtons: [
        Button
        {
            id: cancel_button
            text: catalog.i18nc("@action:button","Cancel");
            enabled: true
            onClicked: close()
        },
        Button
        {
            id: ok_button
            text: catalog.i18nc("@action:button","Save");
            enabled: true
            onClicked: {
                close(); yes() }
        }
    ]
}