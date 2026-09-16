// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.1

import UM 1.6 as UM
import Cura 1.0 as Cura

Cura.Menu
{
    title: catalog.i18nc("@title:menu menubar:toplevel", "&Edit")

    Cura.MenuItem { action: Cura.Actions.undo }
    Cura.MenuItem { action: Cura.Actions.redo }
    Cura.MenuSeparator { }
    Cura.MenuItem { action: Cura.Actions.selectAll }
    Cura.MenuItem { action: Cura.Actions.arrangeAll }
    Cura.MenuItem { action: Cura.Actions.multiplySelection }
    Cura.MenuItem { action: Cura.Actions.deleteSelection }
    Cura.MenuItem { action: Cura.Actions.deleteAll }
    Cura.MenuItem { action: Cura.Actions.resetAllTranslation }
    Cura.MenuItem { action: Cura.Actions.resetAll }
    Cura.MenuItem { action: Cura.Actions.dropAll }
    Cura.MenuSeparator { }
    Cura.MenuItem { action: Cura.Actions.groupObjects }
    Cura.MenuItem { action: Cura.Actions.mergeObjects }
    Cura.MenuItem { action: Cura.Actions.unGroupObjects }

    // Edit print sequence actions
    Cura.MenuSeparator { visible: PrintOrderManager.shouldShowEditPrintOrderActions }
    Cura.MenuItem
    {
        action: Cura.Actions.printObjectBeforePrevious
        visible: PrintOrderManager.shouldShowEditPrintOrderActions
    }
    Cura.MenuItem
    {
        action: Cura.Actions.printObjectAfterNext
        visible: PrintOrderManager.shouldShowEditPrintOrderActions
    }
}