// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1

Item
{
    id: base

    property alias text: textArea.text
    property alias wrapMode: textArea.wrapMode

    signal editingFinished();

    property bool readOnly: false

    width: textArea.width
    height: textArea.height

    TextArea
    {
        id: textArea

        enabled: !base.readOnly
        opacity: base.readOnly ? 0.5 : 1.0

        anchors.fill: parent

        Keys.onReturnPressed:
        {
            base.editingFinished()
        }

        Keys.onEnterPressed:
        {
            base.editingFinished()
        }

        onActiveFocusChanged:
        {
            if(!activeFocus)
            {
                base.editingFinished()
            }
        }
    }
}
