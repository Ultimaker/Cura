// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.4

import UM 1.5 as UM
import Cura 1.0 as Cura

Cura.Menu
{
    id: preferencesMenu

    //On MacOS, don't translate the "Preferences" word.
    //Qt moves the "preferences" entry to a different place, and if it got renamed can't find it again when it
    //attempts to delete the item upon closing the application, causing a crash.
    //In the new location, these items are translated automatically according to the system's language.
    //For more information, see:
    //- https://doc.qt.io/qt-5/macos-issues.html#menu-bar
    //- https://doc.qt.io/qt-5/qmenubar.html#qmenubar-as-a-global-menu-bar
    title: (Qt.platform.os == "osx") ? "&Preferences" : catalog.i18nc("@title:menu menubar:toplevel", "P&references")

    Cura.MenuItem { action: Cura.Actions.preferences }
}

