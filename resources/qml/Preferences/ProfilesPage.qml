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
    addText: catalog.i18nc("@label", "Duplicate")

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

    activeId: Cura.MachineManager.activeQualityId
    activeIndex: {
        for(var i = 0; i < model.rowCount(); i++) {
            if (model.getItem(i).id == Cura.MachineManager.activeQualityId) {
                return i;
            }
        }
        return -1;
    }

    onActivateObject: Cura.MachineManager.setActiveQuality(currentItem.id)
    onAddObject: {
        var selectedContainer;
        if (objectList.currentIndex == 0) {
            // Current settings
            selectedContainer = Cura.MachineManager.convertUserContainerToQuality();
        } else {
            selectedContainer = Cura.MachineManager.duplicateContainer(base.currentItem.id);
        }
        base.selectContainer(selectedContainer);

        renameDialog.removeWhenRejected = true;
        renameDialog.open();
        renameDialog.selectText();
    }
    onRemoveObject: confirmDialog.open();
    onRenameObject: { renameDialog.removeWhenRejected = false; renameDialog.open(); renameDialog.selectText(); }

    activateEnabled: currentItem != null ? currentItem.id != Cura.MachineManager.activeQualityId : false;
    addEnabled: currentItem != null;
    removeEnabled: currentItem != null ? !currentItem.metadata.read_only : false;
    renameEnabled: currentItem != null ? !currentItem.metadata.read_only : false;

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
            visible: base.currentItem.id == -1 || currentItem.id == Cura.MachineManager.activeQualityId

            anchors.left: parent.left
            anchors.top: profileName.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height

            Button
            {
                text: {
                    var profileName = Cura.MachineManager.activeQualityName;
                    profileName = (profileName.length > 20) ? profileName.substring(0, 20) + '...' : profileName;
                    return catalog.i18nc("@action:button", "Update \"%1\"".arg(profileName));
                }
                enabled: Cura.MachineManager.hasUserSettings && !Cura.MachineManager.isReadOnly(Cura.MachineManager.activeQualityId)
                onClicked: Cura.MachineManager.updateUserContainerToQuality()
            }

            Button
            {
                text: catalog.i18nc("@action:button", "Discard changes");
                enabled: Cura.MachineManager.hasUserSettings
                onClicked: Cura.MachineManager.clearUserSettings();
            }
        }

        ScrollView {
            id: scrollView

            anchors.left: parent.left
            anchors.top: currentSettingsActions.visible ? currentSettingsActions.bottom : profileName.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.right: parent.right
            anchors.bottom: parent.bottom

            ListView {
                model: base.currentItem ? base.currentItem.settings: null
                delegate: Row {
                    spacing: UM.Theme.getSize("default_margin").width
                    Label {
                        text: model.label
                        elide: Text.ElideMiddle
                        width: scrollView.width / 100 * 40
                    }
                    Label {
                        text: model.value.toString()
                    }
                    Label {
                        text: model.unit
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

    buttons: Row {

        Button
        {
            text: catalog.i18nc("@action:button", "Import");
            iconName: "document-import";
            onClicked: importDialog.open();
        }

        Button
        {
            text: catalog.i18nc("@action:button", "Export")
            iconName: "document-export"
            onClicked: exportDialog.open()
            enabled: currentItem != null
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
            nameFilters: base.model.getFileNameFiltersRead()
            folder: base.model.getDefaultPath()
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
            }
        }

        FileDialog
        {
            id: exportDialog;
            title: catalog.i18nc("@title:window", "Export Profile");
            selectExisting: false;
            nameFilters: base.model.getFileNameFiltersWrite()
            folder: base.model.getDefaultPath()
            onAccepted:
            {
                var result = base.model.exportProfile(base.currentItem.id, fileUrl)
                if(result && result.status == "error")
                {
                    messageDialog.icon = StandardIcon.Critical
                    messageDialog.text = result.message
                    messageDialog.open()
                }
                // else pop-up Message thing from python code
            }
        }
    }
}
