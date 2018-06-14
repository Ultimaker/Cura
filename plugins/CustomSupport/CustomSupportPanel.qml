// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura

Item {
    id: base

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    width: childrenRect.width
    height: childrenRect.height

    Button
    {
        id: addSupportButton
        anchors.left: parent.left
        text: catalog.i18nc("@action:button", "Add support")
        iconSource: "add_support.svg"

        style: UM.Theme.styles.tool_button
        z: 1
    }
    Button
    {
        id: removeSupportButton
        anchors.left: addSupportButton.right
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        text: catalog.i18nc("@action:button", "Remove support")
        iconSource: "remove_support.svg"

        style: UM.Theme.styles.tool_button
    }
}