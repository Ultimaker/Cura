// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.1

import UM 1.6 as UM
import Cura 1.0 as Cura

Menu
{
    title: catalog.i18nc("@title:menu menubar:toplevel", "&Edit")

    UM.MenuItem { action: Cura.Actions.undo }
    UM.MenuItem { action: Cura.Actions.redo }
    MenuSeparator { }
    UM.MenuItem { action: Cura.Actions.selectAll }
    UM.MenuItem { action: Cura.Actions.arrangeAll }
    UM.MenuItem { action: Cura.Actions.multiplySelection }
    UM.MenuItem { action: Cura.Actions.deleteSelection }
    UM.MenuItem { action: Cura.Actions.deleteAll }
    UM.MenuItem { action: Cura.Actions.resetAllTranslation }
    UM.MenuItem { action: Cura.Actions.resetAll }
    MenuSeparator { }
    UM.MenuItem { action: Cura.Actions.groupObjects }
    UM.MenuItem { action: Cura.Actions.mergeObjects }
    UM.MenuItem { action: Cura.Actions.unGroupObjects }
}