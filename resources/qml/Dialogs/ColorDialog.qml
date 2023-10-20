// Copyright (c) 2023 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.3
import QtQuick.Dialogs

// due for deprecation, use Qt Color Dialog instead
ColorDialog
{
    id: root

    property alias color: root.selectedColor

    Component.onCompleted: { console.warn("Cura.ColorDialog is deprecated, use the QtQuick's ColorDialog instead"); }
}