// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.15
import QtQuick.Dialogs

import UM 1.5 as UM
import Cura 1.1 as Cura

import "Dialogs"
import "Menus"
import "MainWindow"
import "WelcomePages"

UM.MainWindow
{
    id: base

    Item
    {
        id: mainWindow
        anchors.fill: parent
    }

    // Cura application window title
    title:
    {
        let result = "";
        if(PrintInformation !== null && PrintInformation.jobName != "")
        {
            result += PrintInformation.jobName + " - ";
        }
        result += CuraApplication.applicationDisplayName;
        return result;
    }

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

    MouseArea
    {
        // Hack introduced when switching to qt6
        // We used to be able to let the main window's default handlers control this, but something seems to be changed
        // for qt6 in the ordering. TODO; We should find out what changed and have a less hacky fix for that.
        enabled: parent.visible
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.AllButtons
        onPositionChanged: (mouse) => {base.mouseMoved(mouse);}
        onPressed: (mouse) => { base.mousePressed(mouse);}
        onReleased: (mouse) => { base.mouseReleased(mouse);}
        onWheel: (wheel) => {base.wheel(wheel)}

    }

    Rectangle
    {
        id: greyOutBackground
        anchors.fill: parent
        visible: welcomeDialogItem.visible
        color: UM.Theme.getColor("window_disabled_background")
        opacity: 0.7
        z: stageMenu.z + 1

        MouseArea
        {
            // Prevent all mouse events from passing through.
            enabled: parent.visible
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.AllButtons
        }
    }

    WelcomeDialogItem
    {
        id: welcomeDialogItem
        visible: false
        z: greyOutBackground.z + 1
    }

    Component.onCompleted:
    {
        CuraApplication.setMinimumWindowSize(UM.Theme.getSize("window_minimum_size"))
        CuraApplication.purgeWindows()
    }

    Connections
    {
        // This connection is used when there is no ActiveMachine and the user is logged in
        target: CuraApplication
        function onShowAddPrintersUncancellableDialog()
        {
            Cura.Actions.parent = backgroundItem

            // Reuse the welcome dialog item to show "Add a printer" only.
            welcomeDialogItem.model = CuraApplication.getAddPrinterPagesModelWithoutCancel()
            welcomeDialogItem.progressBarVisible = false
            welcomeDialogItem.visible = true
        }
    }

    Connections
    {
        target: CuraApplication
        function onInitializationFinished()
        {
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

            if (CuraApplication.shouldShowWelcomeDialog())
            {
                welcomeDialogItem.visible = true
            }
            else
            {
                welcomeDialogItem.visible = false
            }

            // Reuse the welcome dialog item to show "What's New" only.
            if (CuraApplication.shouldShowWhatsNewDialog())
            {
                welcomeDialogItem.model = CuraApplication.getWhatsNewPagesModel()
                welcomeDialogItem.progressBarVisible = false
                welcomeDialogItem.visible = true
            }

            // Reuse the welcome dialog item to show the "Add printers" dialog. Triggered when there is no active
            // machine and the user is logged in.
            if (!Cura.MachineManager.activeMachine && Cura.API.account.isLoggedIn)
            {
                welcomeDialogItem.model = CuraApplication.getAddPrinterPagesModelWithoutCancel()
                welcomeDialogItem.progressBarVisible = false
                welcomeDialogItem.visible = true
            }
        }
    }

    Item
    {
        id: backgroundItem
        anchors.fill: parent

        //DeleteSelection on the keypress backspace event
        Keys.onPressed: (event) =>
        {
            if (event.key == Qt.Key_Backspace)
            {
                Cura.Actions.deleteSelection.trigger()
            }
        }

        ApplicationMenu
        {
            id: applicationMenu
        }

        Item
        {
            id: headerBackground
            anchors
            {
                top: applicationMenu.bottom
                left: parent.left
                right: parent.right
            }
            height: stageMenu.source != "" ? Math.round(mainWindowHeader.height + stageMenu.height / 2) : mainWindowHeader.height

            Rectangle
            {
                anchors.fill: parent
                color: UM.Theme.getColor("main_window_header_background")
            }

            // This is a placeholder for adding a pattern in the header
            Image
            {
                id: backgroundPattern
                anchors.fill: parent
                fillMode: Image.Tile
                source: UM.Theme.getImage("header_pattern")
                horizontalAlignment: Image.AlignLeft
                verticalAlignment: Image.AlignTop
            }
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
                onDropped: (drop) =>
                {
                    if (drop.urls.length > 0)
                    {

                        var nonPackages = [];
                        for (var i = 0; i < drop.urls.length; i++)
                        {
                            var filename = drop.urls[i];
                            if (filename.toString().toLowerCase().endsWith(".curapackage"))
                            {
                                // Try to install plugin & close.
                                CuraApplication.installPackageViaDragAndDrop(filename);
                                packageInstallDialog.text = catalog.i18nc("@label", "This package will be installed after restarting.");
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

            ObjectSelector
            {
                id: objectSelector
                visible: CuraApplication.platformActivity
                anchors
                {
                    bottom: jobSpecs.top
                    left: toolbar.right
                    leftMargin: UM.Theme.getSize("default_margin").width
                    rightMargin: UM.Theme.getSize("default_margin").width
                    bottomMargin: UM.Theme.getSize("narrow_margin").height
                }
            }

            JobSpecs
            {
                id: jobSpecs
                visible: CuraApplication.platformActivity
                anchors
                {
                    left: toolbar.right
                    bottom: viewOrientationControls.top
                    leftMargin: UM.Theme.getSize("default_margin").width
                    rightMargin: UM.Theme.getSize("default_margin").width
                    bottomMargin: UM.Theme.getSize("thin_margin").width
                    topMargin: UM.Theme.getSize("thin_margin").width
                }
            }

            ViewOrientationControls
            {
                id: viewOrientationControls

                anchors
                {
                    left: toolbar.right
                    bottom: parent.bottom
                    margins: UM.Theme.getSize("default_margin").width
                }
            }

            Toolbar
            {
                // The toolbar is the left bar that is populated by all the tools
                // (which are dynamically populated by plugins)
                id: toolbar

                property int mouseX: base.mouseX
                property int mouseY: base.mouseY
                property bool tallerThanParent: height > parent.height

                anchors
                {
                    verticalCenter: tallerThanParent ? undefined : parent.verticalCenter
                    left: parent.left
                }
                visible: CuraApplication.platformActivity && !PrintInformation.preSliced
            }

            // A hint for the loaded content view. Overlay items / controls can safely be placed in this area
            Item {
                id: mainSafeArea
                anchors.left: viewOrientationControls.right
                anchors.right: main.right
                anchors.top: main.top
                anchors.bottom: main.bottom
            }

            Loader
            {
                // A stage can control this area. If nothing is set, it will therefore show the 3D view.
                id: main

                anchors
                {
                    // Align to the top of the stageMenu since the stageMenu may not exist
                    top: stageMenu.source ? stageMenu.verticalCenter : parent.top
                    left: parent.left
                    right: parent.right
                    bottom: parent.bottom
                }

                source: UM.Controller.activeStage != null ? UM.Controller.activeStage.mainComponent : ""

                onLoaded: {
                    if (main.item.safeArea !== undefined){
                       main.item.safeArea = Qt.binding(function() { return mainSafeArea });
                    }
                }
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

                //  HACK: This is to ensure that the parent never gets set to null, as this wreaks havoc on the focus.
                function onParentDestroyed()
                {
                    printSetupSelector.parent = stageMenu
                    printSetupSelector.visible = false
                }
                property Item oldParent: null

                // The printSetupSelector is defined here so that the setting list doesn't need to get re-instantiated
                // Every time the stage is changed.
                property var printSetupSelector: Cura.PrintSetupSelector
                {
                   width: UM.Theme.getSize("print_setup_widget").width
                   height: UM.Theme.getSize("stage_menu").height
                   headerCornerSide: RoundedRectangle.Direction.Right
                   onParentChanged:
                   {
                       if(stageMenu.oldParent !=null)
                       {
                           stageMenu.oldParent.Component.destruction.disconnect(stageMenu.onParentDestroyed)
                       }
                       stageMenu.oldParent = parent
                       visible = parent != stageMenu
                       parent.Component.destruction.connect(stageMenu.onParentDestroyed)
                   }
                }
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

                primaryButton: Component
                {
                    Cura.PrimaryButton
                    {
                        text: model.name
                        iconSource: UM.Theme.getIcon(model.icon)
                        height: UM.Theme.getSize("message_action_button").height
                    }
                }

                secondaryButton: Component
                {
                    Cura.SecondaryButton
                    {
                        text: model.name
                        iconSource: UM.Theme.getIcon(model.icon)
                        height: UM.Theme.getSize("message_action_button").height
                    }
                }
                link: Component
                {
                    Cura.TertiaryButton
                    {
                        text: model.name
                        iconSource:
                        {
                            if (model.icon == null || model.icon == "")
                            {
                                return UM.Theme.getIcon("LinkExternal")
                            }
                            return UM.Theme.getIcon(model.icon)
                        }
                        height: UM.Theme.getSize("message_action_button").height
                    }
                }
            }
        }

        PrintSetupTooltip
        {
            id: tooltip
            sourceWidth: UM.Theme.getSize("print_setup_widget").width
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
            currentPage = 0;
        }

        onVisibleChanged:
        {
            // When the dialog closes, switch to the General page.
            // This prevents us from having a heavy page like Setting Visibility active in the background.
            setPage(0);
        }
    }

    Connections
    {
        target: Cura.Actions.preferences
        function onTriggered() { preferences.visible = true }
    }

    Connections
    {
        target: CuraApplication
        function onShowPreferencesWindow() { preferences.visible = true }
    }

    Connections
    {
        target: Cura.Actions.addProfile
        function onTriggered()
        {
            createNewQualityDialog.visible = true;
        }
    }

    Connections
    {
        target: Cura.Actions.configureMachines
        function onTriggered()
        {
            preferences.visible = true;
            preferences.setPage(2);
        }
    }

    Connections
    {
        target: Cura.Actions.manageProfiles
        function onTriggered()
        {
            preferences.visible = true;
            preferences.setPage(4);
        }
    }

    Connections
    {
        target: Cura.Actions.manageMaterials
        function onTriggered()
        {
            preferences.visible = true;
            preferences.setPage(3)
        }
    }

    Connections
    {
        target: Cura.Actions.configureSettingVisibility
        function onTriggered(source)
        {
            preferences.visible = true;
            preferences.setPage(1);
            if(source && source.key)
            {
                preferences.getCurrentItem().scrollToSection(source.key);
            }
        }
    }

    // BlurSettings is a way to force the focus away from any of the setting items.
    // We need to do this in order to keep the bindings intact.
    Connections
    {
        target: Cura.MachineManager
        function onBlurSettings()
        {
            contentItem.forceActiveFocus()
        }
    }

    ContextMenu
    {
        id: contextMenu
    }

    onPreClosing: (close) =>
    {
        close.accepted = CuraApplication.getIsAllChecksPassed();
        if (!close.accepted)
        {
            CuraApplication.checkAndExitApplication();
        }
    }

    Cura.MessageDialog
    {
        id: exitConfirmationDialog
        title: catalog.i18nc("@title:window %1 is the application name", "Closing %1").arg(CuraApplication.applicationDisplayName)
        text: catalog.i18nc("@label %1 is the application name", "Are you sure you want to exit %1?").arg(CuraApplication.applicationDisplayName)
        standardButtons: Dialog.Yes | Dialog.No
        onAccepted: CuraApplication.callConfirmExitDialogCallback(true)
        onRejected: CuraApplication.callConfirmExitDialogCallback(false)
        onClosed:
        {
            if (!visible)
            {
                // reset the text to default because other modules may change the message text.
                text = catalog.i18nc("@label %1 is the application name", "Are you sure you want to exit %1?").arg(CuraApplication.applicationDisplayName);
            }
        }
    }

    Connections
    {
        target: CuraApplication
        function onShowConfirmExitDialog(message)
        {
            exitConfirmationDialog.text = message;
            exitConfirmationDialog.open();
        }
    }

    Connections
    {
        target: Cura.Actions.quit
        function onTriggered() { CuraApplication.checkAndExitApplication(); }
    }

    Connections
    {
        target: Cura.Actions.toggleFullScreen
        function onTriggered() { base.toggleFullscreen() }
    }

    Connections
    {
        target: Cura.Actions.exitFullScreen
        function onTriggered() { base.exitFullscreen() }
    }

    FileDialog
    {
        id: openDialog;

        //: File open dialog title
        title: catalog.i18nc("@title:window","Open file(s)")
        modality: Qt.WindowModal
        fileMode: FileDialog.FileMode.OpenFiles
        nameFilters: UM.MeshFileHandler.supportedReadFileTypes;
        currentFolder: CuraApplication.getDefaultPath("dialog_load_path")
        onAccepted:
        {
            // Because several implementations of the file dialog only update the folder
            // when it is explicitly set.
            var f = currentFolder;
            currentFolder = f;

            CuraApplication.setDefaultPath("dialog_load_path", currentFolder);

            handleOpenFileUrls(selectedFiles);
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
            // Make sure the files opened through the openFilesIncludingProjectDialog are added to the recent files list
            openFilesIncludingProjectsDialog.addToRecent = true;

            // we only allow opening one project file
            if (selectedMultipleFiles && hasProjectFile)
            {
                openFilesIncludingProjectsDialog.fileUrls = fileUrlList.slice();
                openFilesIncludingProjectsDialog.show();
                return;
            }

            if (hasProjectFile)
            {
                var projectFile = projectFileUrlList[0]
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
                    askOpenAsProjectOrModelsDialog.is_ucp = CuraApplication.isProjectUcp(projectFile);
                    askOpenAsProjectOrModelsDialog.fileUrl = projectFile;
                    askOpenAsProjectOrModelsDialog.addToRecent = true;
                    askOpenAsProjectOrModelsDialog.show();
                }
            }
            else
            {
                openFilesIncludingProjectsDialog.loadModelFiles(fileUrlList.slice());
            }
        }
    }

    Cura.MessageDialog
    {
        id: packageInstallDialog
        title: catalog.i18nc("@window:title", "Install Package")
        standardButtons: Dialog.Ok
    }

    Cura.MessageDialog
    {
        id: infoMultipleFilesWithGcodeDialog
        title: catalog.i18nc("@title:window", "Open File(s)")
        standardButtons: Dialog.Ok
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
        function onTriggered() { openDialog.open() }
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
        function onOpenProjectFile(project_file, add_to_recent_files)
        {
            askOpenAsProjectOrModelsDialog.is_ucp = CuraApplication.isProjectUcp(project_file);
            askOpenAsProjectOrModelsDialog.fileUrl = project_file;
            askOpenAsProjectOrModelsDialog.addToRecent = add_to_recent_files;
            askOpenAsProjectOrModelsDialog.show();
        }
    }

    Connections
    {
        target: Cura.Actions.showProfileFolder
        function onTriggered()
        {
            var path = UM.Resources.getPath(UM.Resources.Preferences, "");
            if(Qt.platform.os == "windows")
            {
                path = path.replace(/\\/g,"/");
            }
            Qt.openUrlExternally(path);
            if(Qt.platform.os == "linux")
            {
                Qt.openUrlExternally(UM.Resources.getPath(UM.Resources.Resources, ""));
            }
        }
    }

    Component
    {
        id: discardOrKeepProfileChangesDialogComponent
        DiscardOrKeepProfileChangesDialog { }
    }
    Loader
    {
        id: discardOrKeepProfileChangesDialogLoader
    }
    Connections
    {
        target: CuraApplication
        function onShowCompareAndSaveProfileChanges(profileState)
        {
            discardOrKeepProfileChangesDialogLoader.sourceComponent = discardOrKeepProfileChangesDialogComponent
            discardOrKeepProfileChangesDialogLoader.item.buttonState = profileState
            discardOrKeepProfileChangesDialogLoader.item.show()
        }
        function onShowDiscardOrKeepProfileChanges()
        {
            onShowCompareAndSaveProfileChanges(DiscardOrKeepProfileChangesDialog.ButtonsType.DiscardOrKeep)
        }
    }

    property var wizardDialog
    Component
    {
        id: addMachineDialogLoader

        Cura.WizardDialog
        {
            title: catalog.i18nc("@title:window", "Add Printer")
            maximumWidth: Screen.width * 2
            maximumHeight: Screen.height * 2
            model: CuraApplication.getAddPrinterPagesModel()
            progressBarVisible: false
            onVisibleChanged:
            {
                if(!visible)
                {
                    wizardDialog = null
                    Cura.API.account.startSyncing()
                }
            }
        }
    }

    Cura.WizardDialog
    {
        id: whatsNewDialog
        title: catalog.i18nc("@title:window", "What's New")
        minimumWidth: UM.Theme.getSize("welcome_wizard_window").width
        minimumHeight: UM.Theme.getSize("welcome_wizard_window").height
        model: CuraApplication.getWhatsNewPagesModel()
        progressBarVisible: false
        visible: false
    }

    Connections
    {
        target: Cura.Actions.whatsNew
        function onTriggered() { whatsNewDialog.show() }
    }

    Connections
    {
        target: Cura.Actions.addMachine
        function onTriggered()
        {
            Cura.API.account.stopSyncing()
            wizardDialog = addMachineDialogLoader.createObject()
            wizardDialog.show()
        }
    }

    AboutDialog
    {
        id: aboutDialog
    }

    Connections
    {
        target: Cura.Actions.about
        function onTriggered() { aboutDialog.visible = true; }
    }

    Timer
    {
        id: startupTimer
        interval: 100
        repeat: false
        running: true
        onTriggered:
        {
            if (!base.visible)
            {
                base.visible = true
            }
        }
    }

    Cura.RenameDialog
    {
        id: createNewQualityDialog
        title: catalog.i18nc("@title:window", "Save Custom Profile")
        objectPlaceholder: catalog.i18nc("@textfield:placeholder", "New Custom Profile")
        explanation: catalog.i18nc("@info", "Custom profile name:")
        extraInfo:
        [
            UM.ColorImage
            {
                width: UM.Theme.getSize("message_type_icon").width
                height: UM.Theme.getSize("message_type_icon").height
                source: UM.Theme.getIcon("Information")
                color: UM.Theme.getColor("text")
            },
            Column
            {
                UM.Label
                {
                    text: catalog.i18nc
                    (
                        "@label %i will be replaced with a profile name",
                        "<b>Only user changed settings will be saved in the custom profile.</b><br/>" +
                        "For materials that support it, the new custom profile will inherit properties from <b>%1</b>."
                    ).arg(Cura.MachineManager.activeQualityOrQualityChangesName)
                    wrapMode: Text.WordWrap
                    width: parent.parent.width - 2 * UM.Theme.getSize("message_type_icon").width
                }
                Cura.TertiaryButton
                {
                    text: catalog.i18nc("@action:button", "Learn more about Cura print profiles")
                    iconSource: UM.Theme.getIcon("LinkExternal")
                    isIconOnRightSide: true
                    leftPadding: 0
                    rightPadding: 0
                    onClicked: Qt.openUrlExternally("https://support.ultimaker.com/s/article/1667337576882")
                }
            }
        ]
        okButtonText: catalog.i18nc("@button", "Save new profile")
        onAccepted: CuraApplication.getQualityManagementModel().createQualityChanges(newName, true);
    }

    /**
     * Function to check whether a QML object has a certain type.
     * Taken from StackOverflow: https://stackoverflow.com/a/28384228 and
     * adapted to our code style.
     * Licensed under CC BY-SA 3.0.
     * \param obj The QtObject to get the name of.
     * \param class_name (str) The name of the class to check against. Has to be
     * the QtObject class name, not the QML entity name.
     */
    function qmlTypeOf(obj, class_name)
    {
        //className plus "(" is the class instance without modification.
        //className plus "_QML" is the class instance with user-defined properties.
        var str = obj.toString();
        return str.indexOf(class_name + "(") == 0 || str.indexOf(class_name + "_QML") == 0;
    }
}
