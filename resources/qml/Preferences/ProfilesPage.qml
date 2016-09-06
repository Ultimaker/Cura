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
    property var extrudersModel: Cura.ExtrudersModel{}
    //Cura.ExtrudersModel { id: extrudersModel}

    model: UM.InstanceContainersModel
    {
        filter:
        {
            var result = { "type": "quality*", "extruder": null };
            if(Cura.MachineManager.filterQualityByMachine)
            {
                result.definition = Cura.MachineManager.activeDefinitionId;
                if(Cura.MachineManager.hasMaterials)
                {
                    result.material = Cura.MachineManager.allActiveMaterialIds[Cura.MachineManager.activeMachineId];
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

    function canCreateProfile() {
        return base.currentItem && (base.currentItem.id == Cura.MachineManager.activeQualityId) && Cura.MachineManager.hasUserSettings;
    }

    buttons: [
        Button
        {
            text: catalog.i18nc("@action:button", "Activate");
            iconName: "list-activate";
            enabled: base.currentItem != null ? base.currentItem.id != Cura.MachineManager.activeQualityId : false;
            onClicked: Cura.MachineManager.setActiveQuality(base.currentItem.id)
        },

        // Create button
        Button
        {
            text: catalog.i18nc("@label", "Create")
            enabled: base.canCreateProfile()
            visible: base.canCreateProfile()
            iconName: "list-add";

            onClicked:
            {
                newNameDialog.object = base.currentItem != null ? base.currentItem.name : "";
                newNameDialog.open();
                newNameDialog.selectText();
            }
        },

        // Duplicate button
        Button
        {
            text: catalog.i18nc("@label", "Duplicate")
            enabled: ! base.canCreateProfile()
            visible: ! base.canCreateProfile()
            iconName: "list-add";

            onClicked:
            {
                newDuplicateNameDialog.object = base.currentItem.name;
                newDuplicateNameDialog.open();
                newDuplicateNameDialog.selectText();
            }
        },

        Button
        {
            text: catalog.i18nc("@action:button", "Remove");
            iconName: "list-remove";
            enabled: base.currentItem != null ? !base.currentItem.readOnly && !Cura.ContainerManager.isContainerUsed(base.currentItem.id) : false;
            onClicked: confirmDialog.open();
        },
        Button
        {
            text: catalog.i18nc("@action:button", "Rename");
            iconName: "edit-rename";
            enabled: base.currentItem != null ? !base.currentItem.readOnly : false;
            onClicked:
            {
                renameDialog.open();
                renameDialog.selectText();
            }
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

    signal createProfile()
    onCreateProfile:
    {
        newNameDialog.object = base.currentItem != null ? base.currentItem.name : "";
        newNameDialog.open();
        newNameDialog.selectText();
    }

    signal selectContainer(string name)
    onSelectContainer:
    {
        objectList.currentIndex = objectList.model.find("name", name);
    }

    Item {
        visible: base.currentItem != null
        anchors.fill: parent

        Label {
            id: profileName
            text: base.currentItem ? base.currentItem.name: ""
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
                onClicked: Cura.ContainerManager.updateQualityChanges()
            }

            Button
            {
                text: catalog.i18nc("@action:button", "Discard current settings");
                enabled: Cura.MachineManager.hasUserSettings
                onClicked: Cura.ContainerManager.clearUserContainers();
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
                visible: false
                text: catalog.i18nc("@action:label", "This profile uses the defaults specified by the printer, so it has no settings in the list below.")
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

        TabView
        {
            anchors.left: parent.left
            anchors.top: profileNotices.visible ? profileNotices.bottom : profileNotices.anchors.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.right: parent.right
            anchors.bottom: parent.bottom

            ProfileTab
            {
                title: catalog.i18nc("@title:tab", "Global Settings");
                quality: base.currentItem != null ? base.currentItem.id : "";
                material: Cura.MachineManager.allActiveMaterialIds[Cura.MachineManager.activeMachineId]
            }

            Repeater
            {
                model: base.extrudersModel

                ProfileTab
                {
                    title: model.name;
                    extruderId: model.id;
                    quality: base.currentItem != null ? base.currentItem.id : "";
                    material: Cura.MachineManager.allActiveMaterialIds[model.id]
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
            onYes:
            {
                var name = base.currentItem.name;
                Cura.ContainerManager.removeQualityChanges(name)
                if(Cura.MachineManager.activeQualityName == name)
                {
                    Cura.MachineManager.setActiveQuality(base.model.getItem(0).name)
                }
                objectList.currentIndex = -1 //Reset selection.
            }
        }

        UM.RenameDialog
        {
            title: catalog.i18nc("@title:window", "Rename Profile")
            id: renameDialog;
            object: base.currentItem != null ? base.currentItem.name : ""
            onAccepted:
            {
                Cura.ContainerManager.renameQualityChanges(base.currentItem.name, newName)
                objectList.currentIndex = -1 //Reset selection.
            }
        }

        // Dialog to request a name when creating a new profile
        UM.RenameDialog
        {
            title: catalog.i18nc("@title:window", "Create Profile")
            id: newNameDialog;
            object: "<new name>";
            onAccepted:
            {
                var selectedContainer = Cura.ContainerManager.createQualityChanges(newName);
                base.selectContainer(selectedContainer);
                objectList.currentIndex = -1 //Reset selection.
            }
        }

        // Dialog to request a name when duplicating a new profile
        UM.RenameDialog
        {
            title: catalog.i18nc("@title:window", "Duplicate Profile")
            id: newDuplicateNameDialog;
            object: "<new name>";
            onAccepted:
            {
                var selectedContainer = Cura.ContainerManager.duplicateQualityOrQualityChanges(base.currentItem.name, newName);
                base.selectContainer(selectedContainer);
                objectList.currentIndex = -1 //Reset selection.
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
                var profiles_to_export = [base.currentItem.id]
                for(var extruder_nr in base.extrudersModel.items)
                {
                    profiles_to_export.push(ExtruderManager.getQualityChangesIdByExtruderStackId(base.extrudersModel.items[extruder_nr].id))
                }
                var result = base.model.exportProfile(profiles_to_export, fileUrl, selectedNameFilter)
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
