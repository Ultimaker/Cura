// Copyright (c) 2019 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.2

import UM 1.2 as UM
import Cura 1.6 as Cura


Item
{
    id: base

    property var resetEnabled: false  // Keep PreferencesDialog happy
    property var extrudersModel: CuraApplication.getExtrudersModel()
    property var qualityManagementModel: CuraApplication.getQualityManagementModel()

    UM.I18nCatalog { id: catalog; name: "cura"; }

    Label
    {
        id: titleLabel
        anchors
        {
            top: parent.top
            left: parent.left
            right: parent.right
            margins: 5 * screenScaleFactor
        }
        font.pointSize: 18
        text: catalog.i18nc("@title:tab", "Profiles")
    }

    property var hasCurrentItem: base.currentItem != null

    property var currentItem:
    {
        var current_index = qualityListView.currentIndex;
        return (current_index == -1) ? null : base.qualityManagementModel.getItem(current_index);
    }

    property var currentItemName: hasCurrentItem ? base.currentItem.name : ""
    property var currentItemDisplayName: hasCurrentItem ? base.qualityManagementModel.getQualityItemDisplayName(base.currentItem) : ""

    property var isCurrentItemActivated:
    {
        if (!base.currentItem)
        {
            return false;
        }
        if (base.currentItem.is_read_only)
        {
            return (base.currentItem.name == Cura.MachineManager.activeQualityOrQualityChangesName) && (base.currentItem.intent_category == Cura.MachineManager.activeIntentCategory);
        }
        else
        {
            return base.currentItem.name == Cura.MachineManager.activeQualityOrQualityChangesName;
        }
    }

    property var canCreateProfile:
    {
        return isCurrentItemActivated && Cura.MachineManager.hasUserSettings;
    }

    Row  // Button Row
    {
        id: buttonRow
        anchors
        {
            left: parent.left
            right: parent.right
            top: titleLabel.bottom
        }
        height: childrenRect.height

        // Activate button
        Button
        {
            id: activateMenuButton
            text: catalog.i18nc("@action:button", "Activate")
            iconName: "list-activate"
            enabled: !isCurrentItemActivated
            onClicked:
            {
                if (base.currentItem.is_read_only)
                {
                    Cura.IntentManager.selectIntent(base.currentItem.intent_category, base.currentItem.quality_type);
                }
                else
                {
                    Cura.MachineManager.setQualityChangesGroup(base.currentItem.quality_changes_group);
                }
            }
        }

        // Create button
        Button
        {
            id: createMenuButton
            text: catalog.i18nc("@label", "Create")
            iconName: "list-add"
            enabled: base.canCreateProfile && !Cura.MachineManager.stacksHaveErrors
            visible: base.canCreateProfile

            onClicked:
            {
                createQualityDialog.object = Cura.ContainerManager.makeUniqueName(base.currentItem.name);
                createQualityDialog.open();
                createQualityDialog.selectText();
            }
        }

        // Duplicate button
        Button
        {
            id: duplicateMenuButton
            text: catalog.i18nc("@label", "Duplicate")
            iconName: "list-add"
            enabled: !base.canCreateProfile
            visible: !base.canCreateProfile

            onClicked:
            {
                duplicateQualityDialog.object = Cura.ContainerManager.makeUniqueName(base.currentItem.name);
                duplicateQualityDialog.open();
                duplicateQualityDialog.selectText();
            }
        }

        // Remove button
        Button
        {
            id: removeMenuButton
            text: catalog.i18nc("@action:button", "Remove")
            iconName: "list-remove"
            enabled: base.hasCurrentItem && !base.currentItem.is_read_only && !base.isCurrentItemActivated
            onClicked:
            {
                forceActiveFocus();
                confirmRemoveQualityDialog.open();
            }
        }

        // Rename button
        Button
        {
            id: renameMenuButton
            text: catalog.i18nc("@action:button", "Rename")
            iconName: "edit-rename"
            enabled: base.hasCurrentItem && !base.currentItem.is_read_only
            onClicked:
            {
                renameQualityDialog.object = base.currentItem.name;
                renameQualityDialog.open();
                renameQualityDialog.selectText();
            }
        }

        // Import button
        Button
        {
            id: importMenuButton
            text: catalog.i18nc("@action:button", "Import")
            iconName: "document-import"
            onClicked:
            {
                importDialog.open();
            }
        }

        // Export button
        Button
        {
            id: exportMenuButton
            text: catalog.i18nc("@action:button", "Export")
            iconName: "document-export"
            enabled: base.hasCurrentItem && !base.currentItem.is_read_only
            onClicked:
            {
                exportDialog.open();
            }
        }
    }

    // Click create profile from ... in Profile context menu
    signal createProfile()
    onCreateProfile:
    {
        createQualityDialog.object = Cura.ContainerManager.makeUniqueName(Cura.MachineManager.activeQualityOrQualityChangesName);
        createQualityDialog.open();
        createQualityDialog.selectText();
    }

    // Dialog to request a name when creating a new profile
    UM.RenameDialog
    {
        id: createQualityDialog
        title: catalog.i18nc("@title:window", "Create Profile")
        object: "<new name>"
        explanation: catalog.i18nc("@info", "Please provide a name for this profile.")
        onAccepted:
        {
            base.newQualityNameToSelect = newName;  // We want to switch to the new profile once it's created
            base.toActivateNewQuality = true;
            base.qualityManagementModel.createQualityChanges(newName);
        }
    }

    property string newQualityNameToSelect: ""
    property bool toActivateNewQuality: false

    // This connection makes sure that we will switch to the correct quality after the model gets updated
    Connections
    {
        target: base.qualityManagementModel
        onItemsChanged:
        {
            var toSelectItemName = base.currentItem == null ? "" : base.currentItem.name;
            if (newQualityNameToSelect != "")
            {
                toSelectItemName = newQualityNameToSelect;
            }

            var newIdx = -1;  // Default to nothing if nothing can be found
            if (toSelectItemName != "")
            {
                // Select the required quality name if given
                for (var idx = 0; idx < base.qualityManagementModel.count; ++idx)
                {
                    var item = base.qualityManagementModel.getItem(idx);
                    if (item.name == toSelectItemName)
                    {
                        // Switch to the newly created profile if needed
                        newIdx = idx;
                        if (base.toActivateNewQuality)
                        {
                            // Activate this custom quality if required
                            Cura.MachineManager.setQualityChangesGroup(item.quality_changes_group);
                        }
                        break;
                    }
                }
            }
            qualityListView.currentIndex = newIdx;

            // Reset states
            base.newQualityNameToSelect = "";
            base.toActivateNewQuality = false;
        }
    }

    // Dialog to request a name when duplicating a new profile
    UM.RenameDialog
    {
        id: duplicateQualityDialog
        title: catalog.i18nc("@title:window", "Duplicate Profile")
        object: "<new name>"
        onAccepted:
        {
            base.qualityManagementModel.duplicateQualityChanges(newName, base.currentItem);
        }
    }

    // Confirmation dialog for removing a profile
    MessageDialog
    {
        id: confirmRemoveQualityDialog

        icon: StandardIcon.Question;
        title: catalog.i18nc("@title:window", "Confirm Remove")
        text: catalog.i18nc("@label (%1 is object name)", "Are you sure you wish to remove %1? This cannot be undone!").arg(base.currentItemName)
        standardButtons: StandardButton.Yes | StandardButton.No
        modality: Qt.ApplicationModal

        onYes:
        {
            base.qualityManagementModel.removeQualityChangesGroup(base.currentItem.quality_changes_group);
            // reset current item to the first if available
            qualityListView.currentIndex = -1;  // Reset selection.
        }
    }

    // Dialog to rename a quality profile
    UM.RenameDialog
    {
        id: renameQualityDialog
        title: catalog.i18nc("@title:window", "Rename Profile")
        object: "<new name>"
        onAccepted:
        {
            var actualNewName = base.qualityManagementModel.renameQualityChangesGroup(base.currentItem.quality_changes_group, newName);
            base.newQualityNameToSelect = actualNewName;  // Select the new name after the model gets updated
        }
    }

    // Dialog for importing a quality profile
    FileDialog
    {
        id: importDialog
        title: catalog.i18nc("@title:window", "Import Profile")
        selectExisting: true
        nameFilters: base.qualityManagementModel.getFileNameFilters("profile_reader")
        folder: CuraApplication.getDefaultPath("dialog_profile_path")
        onAccepted:
        {
            var result = Cura.ContainerManager.importProfile(fileUrl);
            messageDialog.text = result.message;
            if (result.status == "ok")
            {
                messageDialog.icon = StandardIcon.Information;
            }
            else if (result.status == "duplicate")
            {
                messageDialog.icon = StandardIcon.Warning;
            }
            else
            {
                messageDialog.icon = StandardIcon.Critical;
            }
            messageDialog.open();
            CuraApplication.setDefaultPath("dialog_profile_path", folder);
        }
    }

    // Dialog for exporting a quality profile
    FileDialog
    {
        id: exportDialog
        title: catalog.i18nc("@title:window", "Export Profile")
        selectExisting: false
        nameFilters: base.qualityManagementModel.getFileNameFilters("profile_writer")
        folder: CuraApplication.getDefaultPath("dialog_profile_path")
        onAccepted:
        {
            var result = Cura.ContainerManager.exportQualityChangesGroup(base.currentItem.quality_changes_group,
                                                                         fileUrl, selectedNameFilter);

            if (result && result.status == "error")
            {
                messageDialog.icon = StandardIcon.Critical;
                messageDialog.text = result.message;
                messageDialog.open();
            }

            // else pop-up Message thing from python code
            CuraApplication.setDefaultPath("dialog_profile_path", folder);
        }
    }

    Item
    {
        id: contentsItem

        anchors
        {
            top: titleLabel.bottom
            left: parent.left
            right: parent.right
            bottom: parent.bottom
            margins: 5 * screenScaleFactor
            bottomMargin: 0
        }

        clip: true
    }

    Item
    {
        anchors
        {
            top: buttonRow.bottom
            topMargin: UM.Theme.getSize("default_margin").height
            left: parent.left
            right: parent.right
            bottom: parent.bottom
        }

        SystemPalette
        {
            id: palette
        }

        Label
        {
            id: captionLabel
            anchors
            {
                top: parent.top
                left: parent.left
            }
            visible: text != ""
            text: catalog.i18nc("@label %1 is printer name", "Printer: %1").arg(Cura.MachineManager.activeMachineName)
            width: profileScrollView.width
            elide: Text.ElideRight
        }

        ScrollView
        {
            id: profileScrollView
            anchors
            {
                top: captionLabel.visible ? captionLabel.bottom : parent.top
                topMargin: captionLabel.visible ? UM.Theme.getSize("default_margin").height : 0
                bottom: parent.bottom
                left: parent.left
            }

            Rectangle
            {
                parent: viewport
                anchors.fill: parent
                color: palette.light
            }

            width: true ? (parent.width * 0.4) | 0 : parent.width
            frameVisible: true
            clip: true

            ListView
            {
                id: qualityListView

                model: base.qualityManagementModel

                Component.onCompleted:
                {
                    var selectedItemName = Cura.MachineManager.activeQualityOrQualityChangesName;

                    // Select the required quality name if given
                    for (var idx = 0; idx < base.qualityManagementModel.count; idx++)
                    {
                        var item = base.qualityManagementModel.getItem(idx);
                        if (item.name == selectedItemName)
                        {
                            currentIndex = idx;
                            break;
                        }
                    }
                }

                section.property: "section_name"
                section.delegate: Rectangle
                {
                    height: childrenRect.height

                    Label
                    {
                        anchors.left: parent.left
                        anchors.leftMargin: UM.Theme.getSize("default_lining").width
                        text: section
                        font.bold: true
                    }
                }

                delegate: Rectangle
                {
                    width: profileScrollView.width
                    height: childrenRect.height

                    // Added this property to identify custom profiles in automated system tests (Squish)
                    property bool isReadOnly: model.is_read_only

                    property bool isCurrentItem: ListView.isCurrentItem
                    color: isCurrentItem ? palette.highlight : (model.index % 2) ? palette.base : palette.alternateBase

                    Label
                    {
                        anchors.left: parent.left
                        anchors.leftMargin: UM.Theme.getSize("default_margin").width
                        anchors.right: parent.right
                        width: Math.floor((parent.width * 0.8))
                        text: model.name
                        elide: Text.ElideRight
                        font.italic:
                        {
                            if (model.is_read_only)
                            {
                                // For built-in qualities, it needs to match both the intent category and the quality name
                                return model.name == Cura.MachineManager.activeQualityOrQualityChangesName && model.intent_category == Cura.MachineManager.activeIntentCategory
                            }
                            else
                            {
                                // For custom qualities, it only needs to match the name
                                return model.name == Cura.MachineManager.activeQualityOrQualityChangesName
                            }
                        }
                        color: parent.isCurrentItem ? palette.highlightedText : palette.text
                    }

                    MouseArea
                    {
                        anchors.fill: parent
                        onClicked:
                        {
                            parent.ListView.view.currentIndex = model.index;
                        }
                    }
                }
            }
        }

        // details panel on the right
        Item
        {
            id: detailsPanel

            anchors
            {
                left: profileScrollView.right
                leftMargin: UM.Theme.getSize("default_margin").width
                top: parent.top
                bottom: parent.bottom
                right: parent.right
            }

            Item
            {
                anchors.fill: parent
                visible: base.currentItem != null

                Item    // Profile title Label
                {
                    id: profileName

                    width: parent.width
                    height: childrenRect.height

                    Label
                    {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        text: base.currentItemDisplayName
                        font: UM.Theme.getFont("large_bold")
                        elide: Text.ElideRight
                        renderType: Text.NativeRendering
                    }
                }

                Flow
                {
                    id: currentSettingsActions
                    visible: base.hasCurrentItem && base.currentItem.name == Cura.MachineManager.activeQualityOrQualityChangesName && base.currentItem.intent_category == Cura.MachineManager.activeIntentCategory
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: profileName.bottom
                    anchors.topMargin: UM.Theme.getSize("default_margin").height

                    Button
                    {
                        text: catalog.i18nc("@action:button", "Update profile with current settings/overrides")
                        enabled: Cura.MachineManager.hasUserSettings && !base.currentItem.is_read_only
                        onClicked: Cura.ContainerManager.updateQualityChanges()
                    }

                    Button
                    {
                        text: catalog.i18nc("@action:button", "Discard current changes");
                        enabled: Cura.MachineManager.hasUserSettings
                        onClicked: Cura.ContainerManager.clearUserContainers();
                    }
                }

                Column
                {
                    id: profileNotices
                    anchors.top: currentSettingsActions.visible ? currentSettingsActions.bottom : currentSettingsActions.anchors.top
                    anchors.topMargin: UM.Theme.getSize("default_margin").height
                    anchors.left: parent.left
                    anchors.right: parent.right
                    spacing: UM.Theme.getSize("default_margin").height

                    Label
                    {
                        id: defaultsMessage
                        visible: false
                        text: catalog.i18nc("@action:label", "This profile uses the defaults specified by the printer, so it has no settings/overrides in the list below.")
                        wrapMode: Text.WordWrap
                        width: parent.width
                    }
                    Label
                    {
                        id: noCurrentSettingsMessage
                        visible: base.isCurrentItemActivated && !Cura.MachineManager.hasUserSettings
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

                    currentIndex: 0

                    ProfileTab
                    {
                        title: catalog.i18nc("@title:tab", "Global Settings")
                        qualityItem: base.currentItem
                    }

                    Repeater
                    {
                        model: base.extrudersModel

                        ProfileTab
                        {
                            title: model.name
                            extruderPosition: model.index
                            qualityItem: base.currentItem
                        }
                    }
                }
            }
        }
    }
}
