// Copyright (c) 2024 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtQuick.Window 2.2

import UM 1.8 as UM
import Cura 1.1 as Cura

RowLayout
{
    id: settingSelection

    UM.CheckBox
    {
        text: modelData.name
        Layout.preferredWidth: UM.Theme.getSize("setting").width
        checked: modelData.selected
        onClicked: modelData.selected = checked
        tooltip: modelData.selectable ? "" :catalog.i18nc("@tooltip Don't translate 'Universal Cura Project'", "This setting may not perform well while exporting to Universal Cura Project. Users are asked to add it at their own risk.")
    }

    UM.Label
    {
        text: modelData.valuename
    }

    UM.HelpIcon
    {
        UM.I18nCatalog { id: catalog; name: "cura" }
        text: catalog.i18nc("@tooltip Don't translate 'Universal Cura Project'",
                            "This setting may not perform well while exporting to Universal Cura Project, Users are asked to add it at their own risk.")
        visible: !modelData.selectable
    }


}
