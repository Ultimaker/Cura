// Copyright (c) 2023 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

pragma Singleton

import QtQuick 2.10
import QtQuick.Controls 2.4
import UM 1.1 as UM
import Cura 1.5 as Cura

Item
{
    property alias newProject: newProjectAction
    property alias open: openAction
    property alias quit: quitAction

    property alias undo: undoAction
    property alias redo: redoAction

    property alias view3DCamera: view3DCameraAction
    property alias viewFrontCamera: viewFrontCameraAction
    property alias viewTopCamera: viewTopCameraAction
    property alias viewBottomCamera: viewBottomCameraAction
    property alias viewLeftSideCamera: viewLeftSideCameraAction
    property alias viewRightSideCamera: viewRightSideCameraAction

    property alias deleteSelection: deleteSelectionAction
    property alias centerSelection: centerSelectionAction
    property alias multiplySelection: multiplySelectionAction

    property alias deleteObject: deleteObjectAction
    property alias centerObject: centerObjectAction
    property alias groupObjects: groupObjectsAction
    property alias unGroupObjects:unGroupObjectsAction
    property alias mergeObjects: mergeObjectsAction
    //property alias unMergeObjects: unMergeObjectsAction

    property alias printObjectBeforePrevious: printObjectBeforePreviousAction
    property alias printObjectAfterNext: printObjectAfterNextAction

    property alias multiplyObject: multiplyObjectAction
    property alias dropAll: dropAllAction
    property alias selectAll: selectAllAction
    property alias deleteAll: deleteAllAction
    property alias reloadAll: reloadAllAction
    property alias arrangeAll: arrangeAllAction
    property alias arrangeAllGrid: arrangeAllGridAction
    property alias resetAllTranslation: resetAllTranslationAction
    property alias resetAll: resetAllAction

    property alias addMachine: addMachineAction
    property alias configureMachines: settingsAction
    property alias addProfile: addProfileAction
    property alias updateProfile: updateProfileAction
    property alias resetProfile: resetProfileAction
    property alias manageProfiles: manageProfilesAction

    property alias manageMaterials: manageMaterialsAction
    property alias marketplaceMaterials: marketplaceMaterialsAction

    property alias preferences: preferencesAction

    property alias showProfileFolder: showProfileFolderAction
    property alias documentation: documentationAction
    property alias showTroubleshooting: showTroubleShootingAction
    property alias openSponsershipPage: openSponsershipPageAction
    property alias reportBug: reportBugAction
    property alias whatsNew: whatsNewAction
    property alias about: aboutAction

    property alias toggleFullScreen: toggleFullScreenAction
    property alias exitFullScreen: exitFullScreenAction

    property alias configureSettingVisibility: configureSettingVisibilityAction

    property alias browsePackages: browsePackagesAction

    property alias paste: pasteAction
    property alias copy: copyAction
    property alias cut: cutAction

    readonly property bool copy_paste_enabled: {
        const all_enabled_packages = CuraApplication.getPackageManager().allEnabledPackages;
        return all_enabled_packages.includes("3MFReader") && all_enabled_packages.includes("3MFWriter");
    }

    UM.I18nCatalog{id: catalog; name: "cura"}


    Action
    {
        id: showTroubleShootingAction
        onTriggered: Qt.openUrlExternally("https://ultimaker.com/en/troubleshooting?utm_source=cura&utm_medium=software&utm_campaign=dropdown-troubleshooting")
        text: catalog.i18nc("@action:inmenu", "Show Online Troubleshooting")
    }

    Action
    {
        id: openSponsershipPageAction
        onTriggered: Qt.openUrlExternally("https://ultimaker.com/software/ultimaker-cura/sponsor/")
        text: catalog.i18nc("@action:inmenu", "Sponsor Cura")
    }

    Action
    {
        id: toggleFullScreenAction
        shortcut: StandardKey.FullScreen
        text: catalog.i18nc("@action:inmenu", "Toggle Full Screen")
        icon.name: "view-fullscreen"
    }

    Action
    {
        id: exitFullScreenAction
        text: catalog.i18nc("@action:inmenu", "Exit Full Screen")
        icon.name: "view-fullscreen"
    }

    Action
    {
        id: undoAction
        text: catalog.i18nc("@action:inmenu menubar:edit", "&Undo")
        icon.name: "edit-undo"
        shortcut: StandardKey.Undo
        onTriggered: CuraActions.undo()
        enabled: CuraActions.canUndo
    }

    Action
    {
        id: redoAction
        text: catalog.i18nc("@action:inmenu menubar:edit", "&Redo")
        icon.name: "edit-redo"
        shortcut: StandardKey.Redo
        onTriggered: CuraActions.redo()
        enabled: CuraActions.canRedo
    }

    Action
    {
        id: quitAction

        //On MacOS, don't translate the "Quit" word.
        //Qt moves the "quit" entry to a different place, and if it got renamed can't find it again when it attempts to
        //delete the item upon closing the application, causing a crash.
        //In the new location, these items are translated automatically according to the system's language.
        //For more information, see:
        //- https://doc.qt.io/qt-5/macos-issues.html#menu-bar
        //- https://doc.qt.io/qt-5/qmenubar.html#qmenubar-as-a-global-menu-bar
        text: (Qt.platform.os == "osx") ? "&Quit" : catalog.i18nc("@action:inmenu menubar:file", "&Quit")
        icon.name: "application-exit"
        shortcut: StandardKey.Quit
    }

    Action
    {
        id: view3DCameraAction
        text: catalog.i18nc("@action:inmenu menubar:view", "3D View")
        onTriggered: UM.Controller.setCameraRotation("3d", 0)
    }

    Action
    {
        id: viewFrontCameraAction
        text: catalog.i18nc("@action:inmenu menubar:view", "Front View")
        onTriggered: UM.Controller.setCameraRotation("home", 0)
    }

    Action
    {
        id: viewTopCameraAction
        text: catalog.i18nc("@action:inmenu menubar:view", "Top View")
        onTriggered: UM.Controller.setCameraRotation("y", 90)
    }

    Action
    {
        id: viewBottomCameraAction
        text: catalog.i18nc("@action:inmenu menubar:view", "Bottom View")
        onTriggered: UM.Controller.setCameraRotation("y", -90)
    }

    Action
    {
        id: viewLeftSideCameraAction
        text: catalog.i18nc("@action:inmenu menubar:view", "Left Side View")
        onTriggered: UM.Controller.setCameraRotation("x", 90)
    }

    Action
    {
        id: viewRightSideCameraAction
        text: catalog.i18nc("@action:inmenu menubar:view", "Right Side View")
        onTriggered: UM.Controller.setCameraRotation("x", -90)
    }

    Action
    {
        id: preferencesAction
        //On MacOS, don't translate the "Configure" word.
        //Qt moves the "configure" entry to a different place, and if it got renamed can't find it again when it
        //attempts to delete the item upon closing the application, causing a crash.
        //In the new location, these items are translated automatically according to the system's language.
        //For more information, see:
        //- https://doc.qt.io/qt-5/macos-issues.html#menu-bar
        //- https://doc.qt.io/qt-5/qmenubar.html#qmenubar-as-a-global-menu-bar
        text: (Qt.platform.os == "osx") ? "Configure Cura..." : catalog.i18nc("@action:inmenu", "Configure Cura...")
        icon.name: "configure"
        // on MacOS it us customary to assign the ctrl+, hotkey to open a general settings menu
        shortcut: (Qt.platform.os == "osx") ? "Ctrl+," : ""
    }

    Action
    {
        id: addMachineAction
        text: catalog.i18nc("@action:inmenu menubar:printer", "&Add Printer...")
    }

    Action
    {
        id: settingsAction
        text: catalog.i18nc("@action:inmenu menubar:printer", "Manage Pr&inters...")
        icon.name: "configure"
    }

    Action
    {
        id: manageMaterialsAction
        text: catalog.i18nc("@action:inmenu", "Manage Materials...")
        icon.name: "configure"
        shortcut: "Ctrl+K"
    }

    Action
    {
        id: marketplaceMaterialsAction
        text: catalog.i18nc("@action:inmenu Marketplace is a brand name of UltiMaker's, so don't translate.", "Add more materials from Marketplace")
    }

    Action
    {
        id: updateProfileAction
        enabled: !Cura.MachineManager.stacksHaveErrors && Cura.MachineManager.hasUserSettings && Cura.MachineManager.activeQualityChangesGroup != null
        text: catalog.i18nc("@action:inmenu menubar:profile", "&Update profile with current settings/overrides");
        onTriggered: Cura.ContainerManager.updateQualityChanges()
    }

    Action
    {
        id: resetProfileAction
        enabled: Cura.MachineManager.hasUserSettings
        text: catalog.i18nc("@action:inmenu menubar:profile", "&Discard current changes")
        onTriggered:
        {
            forceActiveFocus()
            Cura.ContainerManager.clearUserContainers()
        }
    }

    Action
    {
        id: addProfileAction
        enabled: !Cura.MachineManager.stacksHaveErrors && Cura.MachineManager.hasUserSettings
        text: catalog.i18nc("@action:inmenu menubar:profile", "&Create profile from current settings/overrides...")
    }

    Action
    {
        id: manageProfilesAction
        text: catalog.i18nc("@action:inmenu menubar:profile", "Manage Profiles...")
        icon.name: "configure"
        shortcut: "Ctrl+J"
    }

    Action
    {
        id: documentationAction
        text: catalog.i18nc("@action:inmenu menubar:help", "Show Online &Documentation")
        icon.name: "help-contents"
        shortcut: StandardKey.Help
        onTriggered: CuraActions.openDocumentation()
    }

    Action {
        id: reportBugAction
        text: catalog.i18nc("@action:inmenu menubar:help", "Report a &Bug")
        icon.name: "tools-report-bug"
        onTriggered: CuraActions.openBugReportPage()
    }

    Action
    {
        id: whatsNewAction
        text: catalog.i18nc("@action:inmenu menubar:help", "What's New")
    }

    Action
    {
        id: aboutAction

        //On MacOS, don't translate the "About" word.
        //Qt moves the "about" entry to a different place, and if it got renamed can't find it again when it
        //attempts to delete the item upon closing the application, causing a crash.
        //In the new location, these items are translated automatically according to the system's language.
        //For more information, see:
        //- https://doc.qt.io/qt-5/macos-issues.html#menu-bar
        //- https://doc.qt.io/qt-5/qmenubar.html#qmenubar-as-a-global-menu-bar
        text: (Qt.platform.os == "osx") ? "About..." : catalog.i18nc("@action:inmenu menubar:help", "About...")
        icon.name: "help-about"
    }

    Action
    {
        id: deleteSelectionAction
        text: catalog.i18nc("@action:inmenu menubar:edit", "Delete Selected")
        enabled: UM.Controller.toolsEnabled && UM.Selection.hasSelection
        icon.name: "edit-delete"
        shortcut: StandardKey.Delete | "Backspace"
        onTriggered: CuraActions.deleteSelection()
    }

    Action
    {
        id: centerSelectionAction
        text: catalog.i18nc("@action:inmenu menubar:edit", "Center Selected")
        enabled: UM.Controller.toolsEnabled && UM.Selection.hasSelection
        icon.name: "align-vertical-center"
        onTriggered: CuraActions.centerSelection()
    }

    Action
    {
        id: copyAction
        text: catalog.i18nc("@action:inmenu menubar:edit", "Copy to clipboard")
        onTriggered: CuraActions.copy()
        enabled: UM.Controller.toolsEnabled && UM.Selection.hasSelection && copy_paste_enabled
        shortcut: StandardKey.Copy
    }

    Action
    {
        id: pasteAction
        text: catalog.i18nc("@action:inmenu menubar:edit", "Paste from clipboard")
        onTriggered: CuraActions.paste()
        enabled: UM.Controller.toolsEnabled && copy_paste_enabled
        shortcut: StandardKey.Paste
    }

    Action
    {
        id: cutAction
        text: catalog.i18nc("@action:inmenu menubar:edit", "Cut")
        onTriggered: CuraActions.cut()
        enabled: UM.Controller.toolsEnabled && UM.Selection.hasSelection && copy_paste_enabled
        shortcut: StandardKey.Cut
    }

    Action
    {
        id: multiplySelectionAction
        text: catalog.i18nc("@action:inmenu menubar:edit", "Multiply Selected")
        enabled: UM.Controller.toolsEnabled && UM.Selection.hasSelection
        icon.name: "edit-duplicate"
        shortcut: "Ctrl+M"
    }

    Action
    {
        id: deleteObjectAction
        text: catalog.i18nc("@action:inmenu","Delete Model")
        enabled: UM.Controller.toolsEnabled
        icon.name: "edit-delete"
    }

    Action
    {
        id: centerObjectAction
        text: catalog.i18nc("@action:inmenu","Ce&nter Model on Platform")
    }

    Action
    {
        id: groupObjectsAction
        text: catalog.i18nc("@action:inmenu menubar:edit","&Group Models")
        enabled: UM.Selection.selectionCount > 1 ? true: false
        icon.name: "object-group"
        shortcut: "Ctrl+G"
        onTriggered: CuraApplication.groupSelected()
    }

    Action
    {
        id: reloadQmlAction
        onTriggered:
        {
            CuraApplication.reloadQML()
        }
        shortcut: "Shift+F5"
    }

    Action
    {
        id: unGroupObjectsAction
        text: catalog.i18nc("@action:inmenu menubar:edit","Ungroup Models")
        enabled: UM.Selection.isGroupSelected
        icon.name: "object-ungroup"
        shortcut: "Ctrl+Shift+G"
        onTriggered: CuraApplication.ungroupSelected()
    }

    Action
    {
        id: printObjectBeforePreviousAction
        text: catalog.i18nc("@action:inmenu menubar:edit","Print Before") + " " + PrintOrderManager.previousNodeName
        enabled: PrintOrderManager.shouldEnablePrintBeforeAction
        icon.name: "print-before"
        shortcut: "PgUp"
        onTriggered: PrintOrderManager.swapSelectedAndPreviousNodes()
    }

    Action
    {
        id: printObjectAfterNextAction
        text: catalog.i18nc("@action:inmenu menubar:edit","Print After") + " " + PrintOrderManager.nextNodeName
        enabled: PrintOrderManager.shouldEnablePrintAfterAction
        icon.name: "print-after"
        shortcut: "PgDown"
        onTriggered: PrintOrderManager.swapSelectedAndNextNodes()
    }

    Action
    {
        id: mergeObjectsAction
        text: catalog.i18nc("@action:inmenu menubar:edit","&Merge Models")
        enabled: UM.Selection.selectionCount > 1 ? true: false
        icon.name: "merge"
        shortcut: "Ctrl+Alt+G"
        onTriggered: CuraApplication.mergeSelected()
    }

    Action
    {
        id: multiplyObjectAction
        text: catalog.i18nc("@action:inmenu","&Multiply Model...")
        icon.name: "edit-duplicate"
    }

    Action
    {
        id: selectAllAction
        text: catalog.i18nc("@action:inmenu menubar:edit","Select All Models")
        enabled: UM.Controller.toolsEnabled
        icon.name: "edit-select-all"
        shortcut: "Ctrl+A"
        onTriggered: CuraApplication.selectAll()
    }

    Action
    {
        id: deleteAllAction
        text: catalog.i18nc("@action:inmenu menubar:edit","Clear Build Plate")
        enabled: UM.Controller.toolsEnabled
        icon.name: "edit-delete"
        shortcut: "Ctrl+D"
        onTriggered: CuraApplication.deleteAll()
    }

    Action
    {
        id: reloadAllAction
        text: catalog.i18nc("@action:inmenu menubar:file","Reload All Models")
        icon.name: "document-revert"
        shortcut: "F5"
        onTriggered: CuraApplication.reloadAll()
    }

    Action
    {
        id: arrangeAllAction
        text: catalog.i18nc("@action:inmenu menubar:edit","Arrange All Models")
        onTriggered: Printer.arrangeAll()
        shortcut: "Ctrl+R"
    }

    Action
    {
        id: arrangeAllGridAction
        text: catalog.i18nc("@action:inmenu menubar:edit","Arrange All Models in a grid")
        onTriggered: Printer.arrangeAllInGrid()
        shortcut: "Shift+Ctrl+R"
    }

    Action
    {
        id: dropAllAction
        text: catalog.i18nc("@action:inmenu menubar:edit","Drop All Models to buildplate")
        shortcut: "Ctrl+B"
        onTriggered: CuraApplication.setWorkplaceDropToBuildplate()
    }

    Action
    {
        id: resetAllTranslationAction
        text: catalog.i18nc("@action:inmenu menubar:edit","Reset All Model Positions")
        onTriggered: CuraApplication.resetAllTranslation()
    }

    Action
    {
        id: resetAllAction
        text: catalog.i18nc("@action:inmenu menubar:edit","Reset All Model Transformations")
        onTriggered: CuraApplication.resetAll()
    }

    Action
    {
        id: openAction
        property var fileProviderModel: CuraApplication.getFileProviderModel()

        text: catalog.i18nc("@action:inmenu menubar:file","&Open File(s)...")
        icon.name: "document-open"
        // Unassign the shortcut when there are more than one file providers, since then the file provider's shortcut is
        // enabled instead, and Ctrl+O is assigned to the local file provider
        shortcut: fileProviderModel.count == 1 ? StandardKey.Open : ""
    }

    Action
    {
        id: arrangeSelectionAction
        text: catalog.i18nc("@action:inmenu menubar:edit", "Arrange Selection")
        onTriggered: Printer.arrangeSelection()
    }

    Action
    {
        id: newProjectAction
        text: catalog.i18nc("@action:inmenu menubar:file","&New Project...")
        shortcut: StandardKey.New
    }

    Action
    {
        id: showProfileFolderAction
        text: catalog.i18nc("@action:inmenu menubar:help","Show Configuration Folder")
    }


    Action
    {
        id: configureSettingVisibilityAction
        text: catalog.i18nc("@action:menu", "Configure setting visibility...")
        icon.name: "configure"
    }

    Action
    {
        id: browsePackagesAction
        text: "&Marketplace"
        icon.name: "plugins_browse"
    }
}
