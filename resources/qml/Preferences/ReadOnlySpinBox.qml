// Copyright (c) 2016 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Dialogs 1.2

// Provides a SpinBox with the same readOnly property as a TextField
SpinBox
{
    id: base
    property bool readOnly: false

    Keys.enabled: !readOnly
    MouseArea
    {
        acceptedButtons: Qt.AllButtons;
        anchors.fill: parent;
        enabled: parent.readOnly;
        onWheel: wheel.accepted = true;
        cursorShape: enabled ? Qt.ArrowCursor : Qt.IBeamCursor;
    }
}
