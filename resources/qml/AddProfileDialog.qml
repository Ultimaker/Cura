// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

UM.Dialog
{
    id: base

    //: About dialog title
    title: catalog.i18nc("@title:window","Add profile")
    width: 400
    height: childrenRect.height

    rightButtons: Row
    {
        spacing: UM.Theme.sizes.default_margin.width

        Button
        {
            text: catalog.i18nc("@action:button","Add");
            isDefault: true
        }
        Button
        {
            text: catalog.i18nc("@action:button","Cancel");

            onClicked: base.visible = false;
        }
    }
}

