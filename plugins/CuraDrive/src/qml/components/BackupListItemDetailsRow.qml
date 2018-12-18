// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.3 as UM

RowLayout
{
    id: detailsRow
    width: parent.width
    height: 40 * screenScaleFactor

    property var iconSource
    property var label
    property var value

    // Spacing.
    Item
    {
        width: 40 * screenScaleFactor
    }

    Icon
    {
        width: 18 * screenScaleFactor
        iconSource: detailsRow.iconSource
        color: UM.Theme.getColor("text")
    }

    Label
    {
        text: detailsRow.label
        color: UM.Theme.getColor("text")
        elide: Text.ElideRight
        Layout.minimumWidth: 50 * screenScaleFactor
        Layout.maximumWidth: 100 * screenScaleFactor
        Layout.fillWidth: true
        renderType: Text.NativeRendering
    }

    Label
    {
        text: detailsRow.value
        color: UM.Theme.getColor("text")
        elide: Text.ElideRight
        Layout.minimumWidth: 50 * screenScaleFactor
        Layout.maximumWidth: 100 * screenScaleFactor
        Layout.fillWidth: true
        renderType: Text.NativeRendering
    }
}
