// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.4

import UM 1.5 as UM
import Cura 1.0 as Cura


Cura.Menu
{
    id: helpMenu
    title: catalog.i18nc("@title:menu menubar:toplevel", "&Help")

    Cura.MenuItem { action: Cura.Actions.showProfileFolder }
    Cura.MenuItem { action: Cura.Actions.showTroubleshooting}
    Cura.MenuItem { action: Cura.Actions.documentation }
    Cura.MenuItem { action: Cura.Actions.reportBug }
    Cura.MenuItem { action: Cura.Actions.openSponsershipPage }
    Cura.MenuSeparator { }
    Cura.MenuItem { action: Cura.Actions.whatsNew }
    Cura.MenuItem { action: Cura.Actions.about }
}