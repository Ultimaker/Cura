// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import UM 1.1 as UM

Item
{
    property alias open: openAction;
    property alias quit: quitAction;

    property alias undo: undoAction;
    property alias redo: redoAction;

    property alias deleteSelection: deleteSelectionAction;

    property alias deleteObject: deleteObjectAction;
    property alias centerObject: centerObjectAction;
    property alias groupObjects: groupObjectsAction;
    property alias unGroupObjects:unGroupObjectsAction;
    property alias mergeObjects: mergeObjectsAction;
    //property alias unMergeObjects: unMergeObjectsAction;
    
    property alias multiplyObject: multiplyObjectAction;

    property alias deleteAll: deleteAllAction;
    property alias reloadAll: reloadAllAction;
    property alias resetAllTranslation: resetAllTranslationAction;
    property alias resetAll: resetAllAction;

    property alias addMachine: addMachineAction;
    property alias configureMachines: settingsAction;
    property alias addProfile: addProfileAction;
    property alias manageProfiles: manageProfilesAction;

    property alias preferences: preferencesAction;

    property alias showEngineLog: showEngineLogAction;
    property alias documentation: documentationAction;
    property alias reportBug: reportBugAction;
    property alias about: aboutAction;

    property alias toggleFullScreen: toggleFullScreenAction;

    UM.I18nCatalog{id: catalog; name:"cura"}

    Action
    {
        id:toggleFullScreenAction
        text: catalog.i18nc("@action:inmenu","Toggle Fu&ll Screen");
        iconName: "view-fullscreen";
    }

    Action
    {
        id: undoAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","&Undo");
        iconName: "edit-undo";
        shortcut: StandardKey.Undo;
    }

    Action
    {
        id: redoAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","&Redo");
        iconName: "edit-redo";
        shortcut: StandardKey.Redo;
    }

    Action
    {
        id: quitAction;
        text: catalog.i18nc("@action:inmenu menubar:file","&Quit");
        iconName: "application-exit";
        shortcut: StandardKey.Quit;
    }

    Action
    {
        id: preferencesAction;
        text: catalog.i18nc("@action:inmenu menubar:settings","&Preferences...");
        iconName: "configure";
    }

    Action
    {
        id: addMachineAction;
        text: catalog.i18nc("@action:inmenu menubar:printer","&Add Printer...");
    }

    Action
    {
        id: settingsAction;
        text: catalog.i18nc("@action:inmenu menubar:printer","Manage Pr&inters...");
        iconName: "configure";
    }

    Action
    {
        id: addProfileAction;
        text: catalog.i18nc("@action:inmenu menubar:profile","&Add Profile...");
    }

    Action
    {
        id: manageProfilesAction;
        text: catalog.i18nc("@action:inmenu menubar:profile","Manage Profiles...");
        iconName: "configure";
    }

    Action
    {
        id: documentationAction;
        text: catalog.i18nc("@action:inmenu menubar:help","Show Online &Documentation");
        iconName: "help-contents";
        shortcut: StandardKey.Help;
    }

    Action {
        id: reportBugAction;
        text: catalog.i18nc("@action:inmenu menubar:help","Report a &Bug");
        iconName: "tools-report-bug";
    }

    Action
    {
        id: aboutAction;
        text: catalog.i18nc("@action:inmenu menubar:help","&About...");
        iconName: "help-about";
    }

    Action
    {
        id: deleteSelectionAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","Delete &Selection");
        enabled: UM.Controller.toolsEnabled;
        iconName: "edit-delete";
        shortcut: StandardKey.Delete;
    }

    Action
    {
        id: deleteObjectAction;
        text: catalog.i18nc("@action:inmenu","Delete Object");
        enabled: UM.Controller.toolsEnabled;
        iconName: "edit-delete";
    }

    Action
    {
        id: centerObjectAction;
        text: catalog.i18nc("@action:inmenu","Ce&nter Object on Platform");
    }

    Action
    {
        id: groupObjectsAction
        text: catalog.i18nc("@action:inmenu menubar:edit","&Group Objects");
        enabled: UM.Scene.numObjectsSelected > 1 ? true: false
        iconName: "object-group"
    }

    Action
    {
        id: unGroupObjectsAction
        text: catalog.i18nc("@action:inmenu menubar:edit","Ungroup Objects");
        enabled: UM.Scene.isGroupSelected
        iconName: "object-ungroup"
    }
    
    Action
    {
        id: mergeObjectsAction
        text: catalog.i18nc("@action:inmenu menubar:edit","&Merge Objects");
        enabled: UM.Scene.numObjectsSelected > 1 ? true: false
        iconName: "merge";
    }

    Action
    {
        id: multiplyObjectAction;
        text: catalog.i18nc("@action:inmenu","&Duplicate Object");
        iconName: "edit-duplicate"
    }

    Action
    {
        id: deleteAllAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","&Clear Build Platform");
        enabled: UM.Controller.toolsEnabled;
        iconName: "edit-delete";
        shortcut: "Ctrl+D";
    }

    Action
    {
        id: reloadAllAction;
        text: catalog.i18nc("@action:inmenu menubar:file","Re&load All Objects");
        iconName: "document-revert";
    }

    Action
    {
        id: resetAllTranslationAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","Reset All Object Positions");
    }

    Action
    {
        id: resetAllAction;
        text: catalog.i18nc("@action:inmenu menubar:edit","Reset All Object &Transformations");
    }

    Action
    {
        id: openAction;
        text: catalog.i18nc("@action:inmenu menubar:file","&Open File...");
        iconName: "document-open";
        shortcut: StandardKey.Open;
    }

    Action
    {
        id: showEngineLogAction;
        text: catalog.i18nc("@action:inmenu menubar:help","Show Engine &Log...");
        iconName: "view-list-text";
        shortcut: StandardKey.WhatsThis;
    }
}
