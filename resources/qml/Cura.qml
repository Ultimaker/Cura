// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1

import UM 1.3 as UM
import Cura 1.0 as Cura

import "Menus"

UM.MainWindow
{
    id: base
    //: Cura application window title
    title: catalog.i18nc("@title:window","Ultimaker Cura");
    viewportRect: Qt.rect(0, 0, (base.width - sidebar.width) / base.width, 1.0)
    property bool showPrintMonitor: false

    Connections
    {
        target: Printer
        onShowPrintMonitor: {
            if (show) {
                topbar.startMonitoringPrint()
            } else {
                topbar.stopMonitoringPrint()
            }
        }
    }

    Component.onCompleted:
    {
        CuraApplication.setMinimumWindowSize(UM.Theme.getSize("window_minimum_size"))
        // Workaround silly issues with QML Action's shortcut property.
        //
        // Currently, there is no way to define shortcuts as "Application Shortcut".
        // This means that all Actions are "Window Shortcuts". The code for this
        // implements a rather naive check that just checks if any of the action's parents
        // are a window. Since the "Actions" object is a singleton it has no parent by
        // default. If we set its parent to something contained in this window, the
        // shortcut will activate properly because one of its parents is a window.
        //
        // This has been fixed for QtQuick Controls 2 since the Shortcut item has a context property.
        Cura.Actions.parent = backgroundItem
    }

    Item
    {
        id: backgroundItem;
        anchors.fill: parent;
        UM.I18nCatalog{id: catalog; name:"cura"}

        signal hasMesh(string name) //this signal sends the filebase name so it can be used for the JobSpecs.qml
        function getMeshName(path){
            //takes the path the complete path of the meshname and returns only the filebase
            var fileName = path.slice(path.lastIndexOf("/") + 1)
            var fileBase = fileName.slice(0, fileName.indexOf("."))
            return fileBase
        }

        //DeleteSelection on the keypress backspace event
        Keys.onPressed: {
            if (event.key == Qt.Key_Backspace)
            {
                Cura.Actions.deleteSelection.trigger()
            }
        }

        UM.ApplicationMenu
        {
            id: menu
            window: base

            Menu
            {
                id: fileMenu
                title: catalog.i18nc("@title:menu menubar:toplevel","&File");
                MenuItem
                {
                    action: Cura.Actions.newProject;
                }

                MenuItem
                {
                    action: Cura.Actions.open;
                }

                RecentFilesMenu { }

                MenuSeparator { }

                MenuItem
                {
                    text: catalog.i18nc("@action:inmenu menubar:file", "&Save Selection to File");
                    enabled: UM.Selection.hasSelection;
                    iconName: "document-save-as";
                    onTriggered: UM.OutputDeviceManager.requestWriteSelectionToDevice("local_file", PrintInformation.jobName, { "filter_by_machine": false, "preferred_mimetype": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml"});
                }

                MenuItem
                {
                    id: saveAsMenu
                    text: catalog.i18nc("@title:menu menubar:file", "Save &As...")
                    onTriggered:
                    {
                        var localDeviceId = "local_file";
                        UM.OutputDeviceManager.requestWriteToDevice(localDeviceId, PrintInformation.jobName, { "filter_by_machine": false, "preferred_mimetype": "application/vnd.ms-package.3dmanufacturing-3dmodel+xml"});
                    }
                }

                MenuItem
                {
                    id: saveWorkspaceMenu
                    text: catalog.i18nc("@title:menu menubar:file","Save project")
                    onTriggered:
                    {
                        if(UM.Preferences.getValue("cura/dialog_on_project_save"))
                        {
                            saveWorkspaceDialog.open()
                        }
                        else
                        {
                            UM.OutputDeviceManager.requestWriteToDevice("local_file", PrintInformation.jobName, { "filter_by_machine": false, "file_type": "workspace" })
                        }
                    }
                }

                MenuItem { action: Cura.Actions.reloadAll; }

                MenuSeparator { }

                MenuItem { action: Cura.Actions.quit; }
            }

            Menu
            {
                title: catalog.i18nc("@title:menu menubar:toplevel","&Edit");

                MenuItem { action: Cura.Actions.undo; }
                MenuItem { action: Cura.Actions.redo; }
                MenuSeparator { }
                MenuItem { action: Cura.Actions.selectAll; }
                MenuItem { action: Cura.Actions.arrangeAll; }
                MenuItem { action: Cura.Actions.deleteSelection; }
                MenuItem { action: Cura.Actions.deleteAll; }
                MenuItem { action: Cura.Actions.resetAllTranslation; }
                MenuItem { action: Cura.Actions.resetAll; }
                MenuSeparator { }
                MenuItem { action: Cura.Actions.groupObjects;}
                MenuItem { action: Cura.Actions.mergeObjects;}
                MenuItem { action: Cura.Actions.unGroupObjects;}
            }

            ViewMenu { title: catalog.i18nc("@title:menu", "&View") }

            Menu
            {
                id: settingsMenu
                title: catalog.i18nc("@title:menu", "&Settings")

                PrinterMenu { title: catalog.i18nc("@title:menu menubar:toplevel", "&Printer") }

                Instantiator
                {
                    model: Cura.ExtrudersModel { simpleNames: true }
                    Menu {
                        title: model.name
                        visible: machineExtruderCount.properties.value > 1

                        NozzleMenu { title: Cura.MachineManager.activeDefinitionVariantsName; visible: Cura.MachineManager.hasVariants; extruderIndex: index }
                        MaterialMenu { title: catalog.i18nc("@title:menu", "&Material"); visible: Cura.MachineManager.hasMaterials; extruderIndex: index }
                        ProfileMenu { title: catalog.i18nc("@title:menu", "&Profile"); }

                        MenuSeparator { }

                        MenuItem { text: catalog.i18nc("@action:inmenu", "Set as Active Extruder"); onTriggered: ExtruderManager.setActiveExtruderIndex(model.index) }
                    }
                    onObjectAdded: settingsMenu.insertItem(index, object)
                    onObjectRemoved: settingsMenu.removeItem(object)
                }

                NozzleMenu { title: Cura.MachineManager.activeDefinitionVariantsName; visible: machineExtruderCount.properties.value <= 1 && Cura.MachineManager.hasVariants }
                MaterialMenu { title: catalog.i18nc("@title:menu", "&Material"); visible: machineExtruderCount.properties.value <= 1 && Cura.MachineManager.hasMaterials }
                ProfileMenu { title: catalog.i18nc("@title:menu", "&Profile"); visible: machineExtruderCount.properties.value <= 1 }

                MenuSeparator { }

                MenuItem { action: Cura.Actions.configureSettingVisibility }
            }

            Menu
            {
                id: extension_menu
                title: catalog.i18nc("@title:menu menubar:toplevel","E&xtensions");

                Instantiator
                {
                    id: extensions
                    model: UM.ExtensionModel { }

                    Menu
                    {
                        id: sub_menu
                        title: model.name;
                        visible: actions != null
                        enabled: actions != null
                        Instantiator
                        {
                            model: actions
                            MenuItem
                            {
                                text: model.text
                                onTriggered: extensions.model.subMenuTriggered(name, model.text)
                            }
                            onObjectAdded: sub_menu.insertItem(index, object)
                            onObjectRemoved: sub_menu.removeItem(object)
                        }
                    }

                    onObjectAdded: extension_menu.insertItem(index, object)
                    onObjectRemoved: extension_menu.removeItem(object)
                }
            }

            Menu
            {
                id: plugin_menu
                title: catalog.i18nc("@title:menu menubar:toplevel", "P&lugins")

                MenuItem { action: Cura.Actions.browsePlugins }
                MenuItem { action: Cura.Actions.configurePlugins }
            }

            Menu
            {
                title: catalog.i18nc("@title:menu menubar:toplevel","P&references");

                MenuItem { action: Cura.Actions.preferences; }
            }

            Menu
            {
                //: Help menu
                title: catalog.i18nc("@title:menu menubar:toplevel","&Help");

                MenuItem { action: Cura.Actions.showProfileFolder; }
                MenuItem { action: Cura.Actions.documentation; }
                MenuItem { action: Cura.Actions.reportBug; }
                MenuSeparator { }
                MenuItem { action: Cura.Actions.about; }
            }
        }

        UM.SettingPropertyProvider
        {
            id: machineExtruderCount

            containerStackId: Cura.MachineManager.activeMachineId
            key: "machine_extruder_count"
            watchedProperties: [ "value" ]
            storeIndex: 0
        }

        Item
        {
            id: contentItem;

            y: menu.height
            width: parent.width;
            height: parent.height - menu.height;

            Keys.forwardTo: menu

            DropArea
            {
                anchors.fill: parent;
                onDropped:
                {
                    if (drop.urls.length > 0)
                    {
                        // As the drop area also supports plugins, first check if it's a plugin that was dropped.
                        if (drop.urls.length == 1)
                        {
                            if (PluginRegistry.isPluginFile(drop.urls[0]))
                            {
                                // Try to install plugin & close.
                                var result = PluginRegistry.installPlugin(drop.urls[0]);
                                pluginInstallDialog.text = result.message;
                                if (result.status == "ok")
                                {
                                    pluginInstallDialog.icon = StandardIcon.Information;
                                }
                                else if (result.status == "duplicate")
                                {
                                    pluginInstallDialog.icon = StandardIcon.Warning;
                                }
                                else
                                {
                                    pluginInstallDialog.icon = StandardIcon.Critical;
                                }
                                pluginInstallDialog.open();
                                return;
                            }
                        }

                        openDialog.handleOpenFileUrls(drop.urls);
                    }
                }
            }

            JobSpecs
            {
                id: jobSpecs
                anchors
                {
                    bottom: parent.bottom;
                    right: sidebar.left;
                    bottomMargin: UM.Theme.getSize("default_margin").height;
                    rightMargin: UM.Theme.getSize("default_margin").width;
                }
            }

            Button
            {
                id: openFileButton;
                text: catalog.i18nc("@action:button","Open File");
                iconSource: UM.Theme.getIcon("load")
                style: UM.Theme.styles.tool_button
                tooltip: '';
                anchors
                {
                    top: topbar.bottom;
                    topMargin: UM.Theme.getSize("default_margin").height;
                    left: parent.left;
                }
                action: Cura.Actions.open;
            }

            Toolbar
            {
                id: toolbar;

                property int mouseX: base.mouseX
                property int mouseY: base.mouseY

                anchors {
                    top: openFileButton.bottom;
                    topMargin: UM.Theme.getSize("window_margin").height;
                    left: parent.left;
                }
            }

            Topbar
            {
                id: topbar
                anchors.left:parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                monitoringPrint: base.showPrintMonitor
                onStartMonitoringPrint: base.showPrintMonitor = true
                onStopMonitoringPrint: base.showPrintMonitor = false
            }

            Sidebar
            {
                id: sidebar;

                anchors
                {
                    top: topbar.bottom;
                    bottom: parent.bottom;
                    right: parent.right;
                }
                z: 1
                width: UM.Theme.getSize("sidebar").width;
                monitoringPrint: base.showPrintMonitor
            }

            Rectangle
            {
                id: viewportOverlay

                color: UM.Theme.getColor("viewport_overlay")
                anchors
                {
                    top: topbar.bottom
                    bottom: parent.bottom
                    left:parent.left
                    right: sidebar.left
                }
                visible: opacity > 0
                opacity: base.showPrintMonitor ? 1 : 0

                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.AllButtons

                    onWheel: wheel.accepted = true
                }
            }

            Loader
            {
                sourceComponent: Cura.MachineManager.printerOutputDevices.length > 0 ? Cura.MachineManager.printerOutputDevices[0].monitorItem: null
                visible: base.showPrintMonitor
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenterOffset: - UM.Theme.getSize("sidebar").width / 2
                anchors.verticalCenterOffset: UM.Theme.getSize("sidebar_header").height / 2
                property real maximumWidth: viewportOverlay.width
                property real maximumHeight: viewportOverlay.height
            }

            UM.MessageStack
            {
                anchors
                {
                    horizontalCenter: parent.horizontalCenter
                    horizontalCenterOffset: -(UM.Theme.getSize("sidebar").width/ 2)
                    top: parent.verticalCenter;
                    bottom: parent.bottom;
                }
            }
        }
    }

    UM.PreferencesDialog
    {
        id: preferences

        Component.onCompleted:
        {
            //; Remove & re-add the general page as we want to use our own instead of uranium standard.
            removePage(0);
            insertPage(0, catalog.i18nc("@title:tab","General"), Qt.resolvedUrl("Preferences/GeneralPage.qml"));

            removePage(1);
            insertPage(1, catalog.i18nc("@title:tab","Settings"), Qt.resolvedUrl("Preferences/SettingVisibilityPage.qml"));

            insertPage(2, catalog.i18nc("@title:tab", "Printers"), Qt.resolvedUrl("Preferences/MachinesPage.qml"));

            insertPage(3, catalog.i18nc("@title:tab", "Materials"), Qt.resolvedUrl("Preferences/MaterialsPage.qml"));

            insertPage(4, catalog.i18nc("@title:tab", "Profiles"), Qt.resolvedUrl("Preferences/ProfilesPage.qml"));

            //Force refresh
            setPage(0);
        }

        onVisibleChanged:
        {
            // When the dialog closes, switch to the General page.
            // This prevents us from having a heavy page like Setting Visiblity active in the background.
            setPage(0);
        }
    }

    WorkspaceSummaryDialog
    {
        id: saveWorkspaceDialog
        onYes: UM.OutputDeviceManager.requestWriteToDevice("local_file", PrintInformation.jobName, { "filter_by_machine": false, "file_type": "workspace" })
    }

    Connections
    {
        target: Cura.Actions.preferences
        onTriggered: preferences.visible = true
    }

    MessageDialog
    {
        id: newProjectDialog
        modality: Qt.ApplicationModal
        title: catalog.i18nc("@title:window", "New project")
        text: catalog.i18nc("@info:question", "Are you sure you want to start a new project? This will clear the build plate and any unsaved settings.")
        standardButtons: StandardButton.Yes | StandardButton.No
        icon: StandardIcon.Question
        onYes:
        {
            CuraApplication.deleteAll();
            Cura.Actions.resetProfile.trigger();
        }
    }

    Connections
    {
        target: Cura.Actions.newProject
        onTriggered:
        {
            if(Printer.platformActivity || Cura.MachineManager.hasUserSettings)
            {
                newProjectDialog.visible = true
            }
        }
    }

    Connections
    {
        target: Cura.Actions.addProfile
        onTriggered:
        {

            preferences.show();
            preferences.setPage(4);
            // Create a new profile after a very short delay so the preference page has time to initiate
            createProfileTimer.start();
        }
    }

    Connections
    {
        target: Cura.Actions.configureMachines
        onTriggered:
        {
            preferences.visible = true;
            preferences.setPage(2);
        }
    }

    Connections
    {
        target: Cura.Actions.manageProfiles
        onTriggered:
        {
            preferences.visible = true;
            preferences.setPage(4);
        }
    }

    Connections
    {
        target: Cura.Actions.manageMaterials
        onTriggered:
        {
            preferences.visible = true;
            preferences.setPage(3)
        }
    }

    Connections
    {
        target: Cura.Actions.configureSettingVisibility
        onTriggered:
        {
            preferences.visible = true;
            preferences.setPage(1);
            preferences.getCurrentItem().scrollToSection(source.key);
        }
    }

    // show the installed plugins page in the preferences dialog
    Connections
    {
        target: Cura.Actions.configurePlugins
        onTriggered:
        {
            preferences.visible = true
            preferences.setPage(5)
        }
    }

    UM.ExtensionModel {
        id: curaExtensions
    }

    // show the plugin browser dialog
    Connections
    {
        target: Cura.Actions.browsePlugins
        onTriggered: {
            curaExtensions.callExtensionMethod("Plugin Browser", "browsePlugins")
        }
    }

    Timer
    {
        id: createProfileTimer
        repeat: false
        interval: 1

        onTriggered: preferences.getCurrentItem().createProfile()
    }

    // BlurSettings is a way to force the focus away from any of the setting items.
    // We need to do this in order to keep the bindings intact.
    Connections
    {
        target: Cura.MachineManager
        onBlurSettings:
        {
            contentItem.forceActiveFocus()
        }
    }

    ContextMenu {
        id: contextMenu
    }

    Connections
    {
        target: Cura.Actions.quit
        onTriggered: CuraApplication.closeApplication();
    }

    Connections
    {
        target: Cura.Actions.toggleFullScreen
        onTriggered: base.toggleFullscreen();
    }

    FileDialog
    {
        id: openDialog;

        //: File open dialog title
        title: catalog.i18nc("@title:window","Open file(s)")
        modality: UM.Application.platform == "linux" ? Qt.NonModal : Qt.WindowModal;
        selectMultiple: true
        nameFilters: UM.MeshFileHandler.supportedReadFileTypes;
        folder: CuraApplication.getDefaultPath("dialog_load_path")
        onAccepted:
        {
            // Because several implementations of the file dialog only update the folder
            // when it is explicitly set.
            var f = folder;
            folder = f;

            CuraApplication.setDefaultPath("dialog_load_path", folder);

            handleOpenFileUrls(fileUrls);
        }

        // Yeah... I know... it is a mess to put all those things here.
        // There are lots of user interactions in this part of the logic, such as showing a warning dialog here and there,
        // etc. This means it will come back and forth from time to time between QML and Python. So, separating the logic
        // and view here may require more effort but make things more difficult to understand.
        function handleOpenFileUrls(fileUrlList)
        {
            // look for valid project files
            var projectFileUrlList = [];
            var hasGcode = false;
            var nonGcodeFileList = [];
            for (var i in fileUrlList)
            {
                var endsWithG = /\.g$/;
                var endsWithGcode = /\.gcode$/;
                if (endsWithG.test(fileUrlList[i]) || endsWithGcode.test(fileUrlList[i]))
                {
                    continue;
                }
                else if (CuraApplication.checkIsValidProjectFile(fileUrlList[i]))
                {
                    projectFileUrlList.push(fileUrlList[i]);
                }
                nonGcodeFileList.push(fileUrlList[i]);
            }
            hasGcode = nonGcodeFileList.length < fileUrlList.length;

            // show a warning if selected multiple files together with Gcode
            var hasProjectFile = projectFileUrlList.length > 0;
            var selectedMultipleFiles = fileUrlList.length > 1;
            if (selectedMultipleFiles && hasGcode)
            {
                infoMultipleFilesWithGcodeDialog.selectedMultipleFiles = selectedMultipleFiles;
                infoMultipleFilesWithGcodeDialog.hasProjectFile = hasProjectFile;
                infoMultipleFilesWithGcodeDialog.fileUrls = nonGcodeFileList.slice();
                infoMultipleFilesWithGcodeDialog.projectFileUrlList = projectFileUrlList.slice();
                infoMultipleFilesWithGcodeDialog.open();
            }
            else
            {
                handleOpenFiles(selectedMultipleFiles, hasProjectFile, fileUrlList, projectFileUrlList);
            }
        }

        function handleOpenFiles(selectedMultipleFiles, hasProjectFile, fileUrlList, projectFileUrlList)
        {
            // we only allow opening one project file
            if (selectedMultipleFiles && hasProjectFile)
            {
                openFilesIncludingProjectsDialog.fileUrls = fileUrlList.slice();
                openFilesIncludingProjectsDialog.show();
                return;
            }

            if (hasProjectFile)
            {
                var projectFile = projectFileUrlList[0];

                // check preference
                var choice = UM.Preferences.getValue("cura/choice_on_open_project");
                if (choice == "open_as_project")
                {
                    openFilesIncludingProjectsDialog.loadProjectFile(projectFile);
                }
                else if (choice == "open_as_model")
                {
                    openFilesIncludingProjectsDialog.loadModelFiles([projectFile].slice());
                }
                else    // always ask
                {
                    // ask whether to open as project or as models
                    askOpenAsProjectOrModelsDialog.fileUrl = projectFile;
                    askOpenAsProjectOrModelsDialog.show();
                }
            }
            else
            {
                openFilesIncludingProjectsDialog.loadModelFiles(fileUrlList.slice());
            }
        }
    }

    MessageDialog
    {
        id: pluginInstallDialog
        title: catalog.i18nc("@window:title", "Install Plugin");
        standardButtons: StandardButton.Ok
        modality: Qt.ApplicationModal
    }

    MessageDialog {
        id: infoMultipleFilesWithGcodeDialog
        title: catalog.i18nc("@title:window", "Open File(s)")
        icon: StandardIcon.Information
        standardButtons: StandardButton.Ok
        text: catalog.i18nc("@text:window", "We have found one or more G-Code files within the files you have selected. You can only open one G-Code file at a time. If you want to open a G-Code file, please just select only one.")

        property var selectedMultipleFiles
        property var hasProjectFile
        property var fileUrls
        property var projectFileUrlList

        onAccepted:
        {
            openDialog.handleOpenFiles(selectedMultipleFiles, hasProjectFile, fileUrls, projectFileUrlList);
        }
    }

    Connections
    {
        target: Cura.Actions.open
        onTriggered: openDialog.open()
    }

    OpenFilesIncludingProjectsDialog
    {
        id: openFilesIncludingProjectsDialog
    }

    AskOpenAsProjectOrModelsDialog
    {
        id: askOpenAsProjectOrModelsDialog
    }

    EngineLog
    {
        id: engineLog;
    }

    Connections
    {
        target: Cura.Actions.showProfileFolder
        onTriggered:
        {
            var path = UM.Resources.getPath(UM.Resources.Preferences, "");
            if(Qt.platform.os == "windows") {
                path = path.replace(/\\/g,"/");
            }
            Qt.openUrlExternally(path);
        }
    }

    AddMachineDialog
    {
        id: addMachineDialog
        onMachineAdded:
        {
            machineActionsWizard.firstRun = addMachineDialog.firstRun
            machineActionsWizard.start(id)
        }
    }

    // Dialog to handle first run machine actions
    UM.Wizard
    {
        id: machineActionsWizard;

        title: catalog.i18nc("@title:window", "Add Printer")
        property var machine;

        function start(id)
        {
            var actions = Cura.MachineActionManager.getFirstStartActions(id)
            resetPages() // Remove previous pages

            for (var i = 0; i < actions.length; i++)
            {
                actions[i].displayItem.reset()
                machineActionsWizard.appendPage(actions[i].displayItem, catalog.i18nc("@title", actions[i].label));
            }

            //Only start if there are actions to perform.
            if (actions.length > 0)
            {
                machineActionsWizard.currentPage = 0;
                show()
            }
        }
    }

    MessageDialog
    {
        id: messageDialog
        modality: Qt.ApplicationModal
        onAccepted: CuraApplication.messageBoxClosed(clickedButton)
        onApply: CuraApplication.messageBoxClosed(clickedButton)
        onDiscard: CuraApplication.messageBoxClosed(clickedButton)
        onHelp: CuraApplication.messageBoxClosed(clickedButton)
        onNo: CuraApplication.messageBoxClosed(clickedButton)
        onRejected: CuraApplication.messageBoxClosed(clickedButton)
        onReset: CuraApplication.messageBoxClosed(clickedButton)
        onYes: CuraApplication.messageBoxClosed(clickedButton)
    }

    Connections
    {
        target: Printer
        onShowMessageBox:
        {
            messageDialog.title = title
            messageDialog.text = text
            messageDialog.informativeText = informativeText
            messageDialog.detailedText = detailedText
            messageDialog.standardButtons = buttons
            messageDialog.icon = icon
            messageDialog.visible = true
        }
    }

    DiscardOrKeepProfileChangesDialog
    {
        id: discardOrKeepProfileChangesDialog
    }

    Connections
    {
        target: CuraApplication
        onShowDiscardOrKeepProfileChanges:
        {
            discardOrKeepProfileChangesDialog.show()
        }
    }

    Connections
    {
        target: Cura.Actions.addMachine
        onTriggered: addMachineDialog.visible = true;
    }

    AboutDialog
    {
        id: aboutDialog
    }

    Connections
    {
        target: Cura.Actions.about
        onTriggered: aboutDialog.visible = true;
    }

    Connections
    {
        target: Printer
        onRequestAddPrinter:
        {
            addMachineDialog.visible = true
            addMachineDialog.firstRun = false
        }
    }

    Timer
    {
        id: startupTimer;
        interval: 100;
        repeat: false;
        running: true;
        onTriggered:
        {
            if(!base.visible)
            {
                base.visible = true;
            }

            // check later if the user agreement dialog has been closed
            if (CuraApplication.needToShowUserAgreement)
            {
                restart();
            }
            else if(Cura.MachineManager.activeMachineId == null || Cura.MachineManager.activeMachineId == "")
            {
                addMachineDialog.open();
            }
        }
    }
}
