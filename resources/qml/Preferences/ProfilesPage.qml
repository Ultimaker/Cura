// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Dialogs 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura

UM.ManagementPage
{
    id: base;

    title: catalog.i18nc("@title:tab", "Profiles");

    model: UM.InstanceContainersModel
    {
        filter:
        {
            var result = { "type": "quality" };
            if(Cura.MachineManager.filterQualityByMachine)
            {
                result.definition = Cura.MachineManager.activeDefinitionId;
                if(Cura.MachineManager.hasMaterials)
                {
                    result.material = Cura.MachineManager.activeMaterialId;
                }
            }
            else
            {
                result.definition = "fdmprinter"
            }
            return result
        }
    }

    section.property: "readOnly"
    section.delegate: Rectangle
    {
        height: childrenRect.height;

        Label
        {
            anchors.left: parent.left;
            anchors.leftMargin: UM.Theme.getSize("default_lining").width;
            text: section == "true" ? catalog.i18nc("@label", "Protected profiles") : catalog.i18nc("@label", "Custom profiles")
            font.bold: true
        }
    }

    activeId: Cura.MachineManager.activeQualityId
    activeIndex: {
        for(var i = 0; i < model.rowCount(); i++) {
            if (model.getItem(i).id == Cura.MachineManager.activeQualityId) {
                return i;
            }
        }
        return -1;
    }

    buttons: [
        Button
        {
            text: catalog.i18nc("@action:button", "Activate");
            iconName: "list-activate";
            enabled: base.currentItem != null ? base.currentItem.id != Cura.MachineManager.activeQualityId : false;
            onClicked: Cura.MachineManager.setActiveQuality(base.currentItem.id)
        },
        Button
        {
            text: base.currentItem && (base.currentItem.id == Cura.MachineManager.activeQualityId) ? catalog.i18nc("@label", "Create") : catalog.i18nc("@label", "Duplicate")
            iconName: "list-add";

            onClicked:
            {
                var selectedContainer;
                if (base.currentItem.id == Cura.MachineManager.activeQualityId) {
                    selectedContainer = Cura.MachineManager.newQualityContainerFromQualityAndUser();
                } else {
                    selectedContainer = Cura.MachineManager.duplicateContainer(base.currentItem.id);
                }
                base.selectContainer(selectedContainer);

                renameDialog.removeWhenRejected = true;
                renameDialog.open();
                renameDialog.selectText();
            }
        },
        Button
        {
            text: catalog.i18nc("@action:button", "Remove");
            iconName: "list-remove";
            enabled: base.currentItem != null ? !base.currentItem.readOnly : false;
            onClicked: confirmDialog.open();
        },
        Button
        {
            text: catalog.i18nc("@action:button", "Rename");
            iconName: "edit-rename";
            enabled: base.currentItem != null ? !base.currentItem.readOnly : false;
            onClicked: { renameDialog.removeWhenRejected = false; renameDialog.open(); renameDialog.selectText(); }
        },
        Button
        {
            text: catalog.i18nc("@action:button", "Import");
            iconName: "document-import";
            onClicked: importDialog.open();
        },
        Button
        {
            text: catalog.i18nc("@action:button", "Export")
            iconName: "document-export"
            onClicked: exportDialog.open()
            enabled: currentItem != null
        }
    ]

    scrollviewCaption: catalog.i18nc("@label %1 is printer name","Printer: %1").arg(Cura.MachineManager.activeMachineName)

    signal showProfileNameDialog()
    onShowProfileNameDialog: { renameDialog.removeWhenRejected = true; renameDialog.open(); renameDialog.selectText(); }

    signal selectContainer(string id)
    onSelectContainer: {
        objectList.currentIndex = objectList.model.find("id", id);
    }

    Item {
        visible: base.currentItem != null
        anchors.fill: parent

        Label {
            id: profileName
            text: base.currentItem ? base.currentItem.name : ""
            font: UM.Theme.getFont("large")
            width: parent.width
            elide: Text.ElideRight
        }

        Row {
            id: currentSettingsActions
            visible: currentItem && currentItem.id == Cura.MachineManager.activeQualityId

            anchors.left: parent.left
            anchors.top: profileName.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height

            Button
            {
                text: {
                    return catalog.i18nc("@action:button", "Update profile with current settings");
                }
                enabled: Cura.MachineManager.hasUserSettings && !Cura.MachineManager.isReadOnly(Cura.MachineManager.activeQualityId)
                onClicked: Cura.MachineManager.updateQualityContainerFromUserContainer()
            }

            Button
            {
                text: catalog.i18nc("@action:button", "Discard current settings");
                enabled: Cura.MachineManager.hasUserSettings
                onClicked: Cura.MachineManager.clearUserSettings();
            }
        }

        Column {
            id: profileNotices
            anchors.top: currentSettingsActions.visible ? currentSettingsActions.bottom : currentSettingsActions.anchors.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: parent.left
            anchors.right: parent.right
            spacing: UM.Theme.getSize("default_margin").height

            Label {
                id: defaultsMessage
                visible: currentItem && !currentItem.metadata.has_settings
                text: catalog.i18nc("@action:label", "This profile has no settings and uses the defaults specified by the printer.")
                wrapMode: Text.WordWrap
                width: parent.width
            }
            Label {
                id: noCurrentSettingsMessage
                visible: currentItem && currentItem.id == Cura.MachineManager.activeQualityId && !Cura.MachineManager.hasUserSettings
                text: catalog.i18nc("@action:label", "Your current settings match the selected profile.")
                wrapMode: Text.WordWrap
                width: parent.width
            }
        }

        ScrollView {
            id: scrollView

            anchors.left: parent.left
            anchors.top: profileNotices.visible ? profileNotices.bottom : profileNotices.anchors.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.right: parent.right
            anchors.bottom: parent.bottom

            ListView {
                model: Cura.ContainerSettingsModel
                {
                    containers:
                    {
                        if (!currentItem) {
                            return []
                        } else if (currentItem.id == Cura.MachineManager.activeQualityId) {
                            return [base.currentItem.id, Cura.MachineManager.activeUserProfileId]
                        } else {
                            return [base.currentItem.id]
                        }
                    }
                }
                delegate: Row {
                    property variant setting: model
                    spacing: UM.Theme.getSize("default_margin").width/2
                    Label {
                        text: model.label
                        elide: Text.ElideMiddle
                        width: scrollView.width / 100 * 40
                    }
                    Repeater {
                        model: setting.values.length
                        Label {
                            text: setting.values[index].toString()
                            width: scrollView.width / 100 * 15
                            elide: Text.ElideRight
                            font.strikeout: index < setting.values.length - 1 && setting.values[index + 1] != ""
                            opacity: font.strikeout ? 0.5 : 1
                        }
                    }
                    Label {
                        text: model.unit
                    }
                }
                header: Row {
                    visible: currentItem && currentItem.id == Cura.MachineManager.activeQualityId
                    spacing: UM.Theme.getSize("default_margin").width
                    Label {
                        text: catalog.i18nc("@action:label", "Profile:")
                        width: scrollView.width / 100 * 55
                        horizontalAlignment: Text.AlignRight
                        font.bold: true
                    }
                    Label {
                        text: catalog.i18nc("@action:label", "Current:")
                        visible: currentItem && currentItem.id == Cura.MachineManager.activeQualityId
                        font.bold: true
                    }
                }
                section.property: "category"
                section.criteria: ViewSection.FullString
                section.delegate: Label {
                    text: section
                    font.bold: true
                }
            }
        }
    }

    Item
    {
        UM.I18nCatalog { id: catalog; name: "uranium"; }

        UM.ConfirmRemoveDialog
        {
            id: confirmDialog
            object: base.currentItem != null ? base.currentItem.name : ""
            onYes: Cura.MachineManager.removeQualityContainer(base.currentItem.id)
        }
        UM.RenameDialog
        {
            id: renameDialog;
            object: base.currentItem != null ? base.currentItem.name : ""
            property bool removeWhenRejected: false
            onAccepted: Cura.MachineManager.renameQualityContainer(base.currentItem.id, newName)
            onRejected: {
                if(removeWhenRejected) {
                    Cura.MachineManager.removeQualityContainer(base.currentItem.id)
                }
            }
        }
        MessageDialog
        {
            id: messageDialog
            title: catalog.i18nc("@window:title", "Import Profile");
            standardButtons: StandardButton.Ok
            modality: Qt.ApplicationModal
        }

        FileDialog
        {
            id: importDialog;
            title: catalog.i18nc("@title:window", "Import Profile");
            selectExisting: true;
            nameFilters: base.model.getFileNameFilters("profile_reader")
            folder: CuraApplication.getDefaultPath("dialog_profile_path")
            onAccepted:
            {
                var result = base.model.importProfile(fileUrl)
                messageDialog.text = result.message
                if(result.status == "ok")
                {
                    messageDialog.icon = StandardIcon.Information
                }
                else if(result.status == "duplicate")
                {
                    messageDialog.icon = StandardIcon.Warning
                }
                else
                {
                    messageDialog.icon = StandardIcon.Critical
                }
                messageDialog.open()
                CuraApplication.setDefaultPath("dialog_profile_path", folder)
            }
        }

        FileDialog
        {
            id: exportDialog;
            title: catalog.i18nc("@title:window", "Export Profile");
            selectExisting: false;
            nameFilters: base.model.getFileNameFilters("profile_writer")
            folder: CuraApplication.getDefaultPath("dialog_profile_path")
            onAccepted:
            {
                var result = base.model.exportProfile(base.currentItem.id, fileUrl, selectedNameFilter)
                if(result && result.status == "error")
                {
                    messageDialog.icon = StandardIcon.Critical
                    messageDialog.text = result.message
                    messageDialog.open()
                }
                // else pop-up Message thing from python code
                CuraApplication.setDefaultPath("dialog_profile_path", folder)
            }
        }
    }
}
