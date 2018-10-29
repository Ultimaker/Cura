// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.2

import UM 1.3 as UM
import Cura 1.1 as Cura

import "Dialogs"
import "Menus"
import "MainWindow"

UM.MainWindow
{
    id: base

    // Cura application window title
    title: catalog.i18nc("@title:window", "Ultimaker Cura")
    backgroundColor: UM.Theme.getColor("viewport_background")

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    function showTooltip(item, position, text)
    {
        tooltip.text = text;
        position = item.mapToItem(backgroundItem, position.x - UM.Theme.getSize("default_arrow").width, position.y);
        tooltip.show(position);
    }

    function hideTooltip()
    {
        tooltip.hide();
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
        CuraApplication.purgeWindows()
    }

    Item
    {
        id: backgroundItem
        anchors.fill: parent

        signal hasMesh(string name) //this signal sends the filebase name so it can be used for the JobSpecs.qml
        function getMeshName(path)
        {
            //takes the path the complete path of the meshname and returns only the filebase
            var fileName = path.slice(path.lastIndexOf("/") + 1)
            var fileBase = fileName.slice(0, fileName.indexOf("."))
            return fileBase
        }

        //DeleteSelection on the keypress backspace event
        Keys.onPressed:
        {
            if (event.key == Qt.Key_Backspace)
            {
                Cura.Actions.deleteSelection.trigger()
            }
        }

        ApplicationMenu
        {
            id: applicationMenu
            window: base
        }

        MainWindowHeader
        {
            id: mainWindowHeader
            anchors
            {
                left: parent.left
                right: parent.right
                top: applicationMenu.bottom
            }
        }

        Item
        {
            id: contentItem

            anchors
            {
                top: mainWindowHeader.bottom
                bottom: parent.bottom
                left: parent.left
                right: parent.right
            }

            Keys.forwardTo: applicationMenu

            DropArea
            {
                // The drop area is here to handle files being dropped onto Cura.
                anchors.fill: parent
                onDropped:
                {
                    if (drop.urls.length > 0)
                    {

                        var nonPackages = [];
                        for (var i = 0; i < drop.urls.length; i++)
                        {
                            var filename = drop.urls[i];
                            if (filename.endsWith(".curapackage"))
                            {
                                // Try to install plugin & close.
                                CuraApplication.getPackageManager().installPackageViaDragAndDrop(filename);
                                packageInstallDialog.text = catalog.i18nc("@label", "This package will be installed after restarting.");
                                packageInstallDialog.icon = StandardIcon.Information;
                                packageInstallDialog.open();
                            }
                            else
                            {
                                nonPackages.push(filename);
                            }
                        }
                        openDialog.handleOpenFileUrls(nonPackages);
                    }
                }
            }

            Rectangle
            {
                anchors
                {
                    left: parent.left
                    right: parent.right
                    top: parent.top
                }
                visible: stageMenu.source != ""
                height: Math.round(UM.Theme.getSize("stage_menu").height / 2)
                color: UM.Theme.getColor("main_window_header_background")
            }

            Loader
            {
                // The stage menu is, as the name implies, a menu that is defined by the active stage.
                // Note that this menu does not need to be set at all! It's perfectly acceptable to have a stage
                // without this menu!
                id: stageMenu

                anchors
                {
                    left: parent.left
                    right: parent.right
                    top: parent.top
                }

                height: UM.Theme.getSize("stage_menu").height
                source: UM.Controller.activeStage != null ? UM.Controller.activeStage.stageMenuComponent : ""
            }

            Connections
            {
                target: stageMenu.item
                onShowTooltip: base.showTooltip(item, location, text)
                onHideTooltip: base.hideTooltip()
            }

            JobSpecs
            {
                id: jobSpecs
                anchors
                {
                    bottom: parent.bottom
                    bottomMargin: UM.Theme.getSize("default_margin").height
                }
            }

            Toolbar
            {
                // The toolbar is the left bar that is populated by all the tools (which are dynamicly populated by
                // plugins)
                id: toolbar

                property int mouseX: base.mouseX
                property int mouseY: base.mouseY

                anchors
                {
                    verticalCenter: parent.verticalCenter
                    left: parent.left
                }
            }

            ObjectsList
            {
                id: objectsList
                visible: UM.Preferences.getValue("cura/use_multi_build_plate")
                anchors
                {
                    bottom: parent.bottom
                    left: parent.left
                }
            }

            ViewOrientationControls
            {
                id: viewOrientationControls

                anchors
                {
                    left: parent.left
                    margins: UM.Theme.getSize("default_margin").width

                    bottom: parent.bottom
                }
            }

            ComboBox
            {
                // This item contains the views selector, a combobox that is dynamically created from
                // the list of available Views (packages that create different visualizations of the
                // scene).
                id: viewModeButton

                anchors.left: viewOrientationControls.right
                anchors.bottom: viewOrientationControls.bottom

                style: UM.Theme.styles.combobox

                model: UM.ViewModel { }
                textRole: "name"

                // update the model's active index
                function updateItemActiveFlags()
                {
                    currentIndex = getActiveIndex()
                    for (var i = 0; i < model.rowCount(); i++)
                    {
                        model.getItem(i).active = (i == currentIndex)
                    }
                }

                // get the index of the active model item on start
                function getActiveIndex ()
                {
                    for (var i = 0; i < model.rowCount(); i++)
                    {
                        if (model.getItem(i).active)
                        {
                            return i;
                        }
                    }
                    return 0
                }

                // set the active index
                function setActiveIndex(index)
                {
                    UM.Controller.setActiveView(index)
                    // the connection to UM.ActiveView will trigger update so there is no reason to call it manually here
                }

                onCurrentIndexChanged:
                {
                    if (model.getItem(currentIndex).id != undefined)
                    {
                        viewModeButton.setActiveIndex(model.getItem(currentIndex).id)
                    }
                }
                currentIndex: getActiveIndex()

                // watch the active view proxy for changes made from the menu item
                Connections
                {
                    target: UM.ActiveView
                    onActiveViewChanged: viewModeButton.updateItemActiveFlags()
                }
            }

            Loader
            {
                id: viewPanel

                anchors.bottom: viewModeButton.top
                anchors.topMargin: UM.Theme.getSize("default_margin").height
                anchors.right: viewModeButton.right

                property var buttonTarget: Qt.point(viewModeButton.x + Math.round(viewModeButton.width / 2), viewModeButton.y + Math.round(viewModeButton.height / 2))

                height: childrenRect.height
                width: childrenRect.width

                source: UM.ActiveView.valid ? UM.ActiveView.activeViewPanel : ""
            }

            Cura.ActionPanelWidget
            {
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.rightMargin: UM.Theme.getSize("thick_margin").width
                anchors.bottomMargin: UM.Theme.getSize("thick_margin").height
//                onShowTooltip:
//                {
//                    base.showTooltip(item, location, text)
//                }
//                onHideTooltip:
//                {
//                    base.hideTooltip()
//                }
            }

            Loader
            {
                // A stage can control this area. If nothing is set, it will therefore show the 3D view.
                id: main

                anchors.fill: parent

                MouseArea
                {
                    visible: parent.source != ""
                    anchors.fill: parent
                    acceptedButtons: Qt.AllButtons
                    onWheel: wheel.accepted = true
                }

                source: UM.Controller.activeStage != null ? UM.Controller.activeStage.mainComponent : ""
            }

            UM.MessageStack
            {
                anchors
                {
                    horizontalCenter: parent.horizontalCenter
                    top: parent.verticalCenter
                    bottom: parent.bottom
                    bottomMargin:  UM.Theme.getSize("default_margin").height
                }
            }
        }

        SidebarTooltip
        {
            id: tooltip
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

            insertPage(3, catalog.i18nc("@title:tab", "Materials"), Qt.resolvedUrl("Preferences/Materials/MaterialsPage.qml"));

            insertPage(4, catalog.i18nc("@title:tab", "Profiles"), Qt.resolvedUrl("Preferences/ProfilesPage.qml"));

            // Remove plug-ins page because we will use the shiny new plugin browser:
            removePage(5);

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

    Connections
    {
        target: Cura.Actions.preferences
        onTriggered: preferences.visible = true
    }

    Connections
    {
        target: CuraApplication
        onShowPreferencesWindow: preferences.visible = true
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
            if(source && source.key)
            {
                preferences.getCurrentItem().scrollToSection(source.key);
            }
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

    ContextMenu
    {
        id: contextMenu
    }

    onPreClosing:
    {
        close.accepted = CuraApplication.getIsAllChecksPassed();
        if (!close.accepted)
        {
            CuraApplication.checkAndExitApplication();
        }
    }

    MessageDialog
    {
        id: exitConfirmationDialog
        title: catalog.i18nc("@title:window", "Closing Cura")
        text: catalog.i18nc("@label", "Are you sure you want to exit Cura?")
        icon: StandardIcon.Question
        modality: Qt.ApplicationModal
        standardButtons: StandardButton.Yes | StandardButton.No
        onYes: CuraApplication.callConfirmExitDialogCallback(true)
        onNo: CuraApplication.callConfirmExitDialogCallback(false)
        onRejected: CuraApplication.callConfirmExitDialogCallback(false)
        onVisibilityChanged:
        {
            if (!visible)
            {
                // reset the text to default because other modules may change the message text.
                text = catalog.i18nc("@label", "Are you sure you want to exit Cura?");
            }
        }
    }

    Connections
    {
        target: CuraApplication
        onShowConfirmExitDialog:
        {
            exitConfirmationDialog.text = message;
            exitConfirmationDialog.open();
        }
    }

    Connections
    {
        target: Cura.Actions.quit
        onTriggered: CuraApplication.checkAndExitApplication();
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
        id: packageInstallDialog
        title: catalog.i18nc("@window:title", "Install Package");
        standardButtons: StandardButton.Ok
        modality: Qt.ApplicationModal
    }

    MessageDialog
    {
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

    Connections
    {
        target: CuraApplication
        onOpenProjectFile:
        {
            askOpenAsProjectOrModelsDialog.fileUrl = project_file;
            askOpenAsProjectOrModelsDialog.show();
        }
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
            if(Qt.platform.os == "linux") {
                Qt.openUrlExternally(UM.Resources.getPath(UM.Resources.Resources, ""));
            }
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
        target: CuraApplication
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
        target: CuraApplication
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
            else if(Cura.MachineManager.activeMachine == null)
            {
                addMachineDialog.open();
            }
        }
    }
}
