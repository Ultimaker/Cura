// Copyright (c) 2026 UltiMaker
// The PostProcessingPlugin is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.15
import QtQml.Models 2.15 as Models
import QtQuick.Layouts 1.1
import QtQuick.Window 2.2

import UM 1.5 as UM
import Cura 1.0 as Cura

Item
{
    id: base
    objectName: "postProcessingSaveAreaButton"
    visible: manager.scriptList.length > 0
    height: UM.Theme.getSize("action_button").height
    width: height

    signal clicked

    Cura.SecondaryButton
    {
        height: UM.Theme.getSize("action_button").height
        tooltip:
        {
            var tipText = catalog.i18nc("@info:tooltip", "Change active post-processing scripts.");
            if (manager.scriptList.length > 0)
            {
                tipText += "<br><br>" + catalog.i18ncp("@info:tooltip",
                    "The following script is active:",
                    "The following scripts are active:",
                    manager.scriptList.length
                ) + "<ul>";
                for(var i = 0; i < manager.scriptList.length; i++)
                {
                    tipText += "<li>" + manager.getScriptLabelByKey(manager.scriptList[i]) + "</li>";
                }
                tipText += "</ul>";
            }
            return tipText
        }
        toolTipContentAlignment: UM.Enums.ContentAlignment.AlignLeft
        onClicked: base.clicked()
        iconSource: Qt.resolvedUrl("Script.svg")
        fixedWidthMode: false
    }

    Cura.NotificationIcon
    {
        id: activeScriptCountIcon
        visible: manager.scriptList.length > 0
        anchors
        {
            horizontalCenter: parent.right
            verticalCenter: parent.top
        }

        labelText: manager.scriptList.length
    }
}
