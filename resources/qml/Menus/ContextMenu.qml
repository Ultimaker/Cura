// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Dialogs 1.2
import QtQuick.Window 2.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: base

    // Selection-related actions.
    MenuItem { action: Cura.Actions.centerSelection; }
    MenuItem { action: Cura.Actions.deleteSelection; }
    MenuItem { action: Cura.Actions.multiplySelection; }

    // Global actions
    MenuSeparator { }
    MenuItem { action: Cura.Actions.selectAll; }
    MenuItem { action: Cura.Actions.arrangeAll; }
    MenuItem { action: Cura.Actions.deleteAll; }
    MenuItem { action: Cura.Actions.reloadAll; }
    MenuItem { action: Cura.Actions.resetAllTranslation; }
    MenuItem { action: Cura.Actions.resetAll; }

    // Group actions
    MenuSeparator { }
    MenuItem { action: Cura.Actions.groupObjects; }
    MenuItem { action: Cura.Actions.mergeObjects; }
    MenuItem { action: Cura.Actions.unGroupObjects; }

    Connections
    {
        target: UM.Controller
        onContextMenuRequested: base.popup();
    }

    Connections
    {
        target: Cura.Actions.multiplySelection
        onTriggered: multiplyDialog.open()
    }

    Dialog
    {
        id: multiplyDialog

        title: catalog.i18ncp("@title:window", "Multiply Selected Model", "Multiply Selected Models", UM.Selection.selectionCount)

        width: 400 * Screen.devicePixelRatio
        height: 80 * Screen.devicePixelRatio

        signal reset()
        onReset:
        {
            copiesField.value = 1;
            copiesField.focus = true;
        }

        standardButtons: StandardButton.Ok | StandardButton.Cancel

        Row
        {
            spacing: UM.Theme.getSize("default_margin").width

            Label
            {
                text: catalog.i18nc("@label", "Number of Copies")
                anchors.verticalCenter: copiesField.verticalCenter
            }

            SpinBox
            {
                id: copiesField
                minimumValue: 1
                maximumValue: 99
            }
        }
    }

    function findItemIndex(item)
    {
        for(var i in base.items)
        {
            if(base.items[i] == item)
                return i;
        }
        return -1;
    }

    UM.I18nCatalog { id: catalog; name: "cura" }
}
