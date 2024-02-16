// Copyright (c) 2022 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 2.1

import UM 1.5 as UM

Item
{
    // Use the depth of the model to move the item, but also leave space for the visibility / enabled exclamation mark.

    // Align checkbox with SettingVisibilityCategory icon with + 5
    x: definition ? definition.depth * UM.Theme.getSize("narrow_margin").width : UM.Theme.getSize("default_margin").width

    UM.TooltipArea
    {
        text: definition ? definition.description : ""

        width: childrenRect.width;
        height: childrenRect.height;
        id: checkboxTooltipArea
        x: check.height
        UM.CheckBox
        {
            id: check

            text: definition ? definition.label: ""
            checked: definition ? definition.visible: false
            enabled: definition ? !definition.prohibited: false

            MouseArea
            {
                anchors.fill: parent
                onClicked: definitionsModel.setVisible(definition.key, !check.checked)
            }
        }
    }

    UM.TooltipArea
    {
        width: height
        height: check.height
        anchors.right: checkboxTooltipArea.left
        anchors.leftMargin: 2 * screenScaleFactor

        text:
        {
            if(provider.properties.enabled == "True")
            {
                return ""
            }
            var key = definition ? definition.key : ""
            var requires = settingDefinitionsModel.getRequires(key, "enabled")
            if (requires.length == 0)
            {
                return catalog.i18nc("@item:tooltip", "This setting has been hidden by the active machine and will not be visible.");
            }
            else
            {
                var requires_text = ""
                for (var i in requires)
                {
                    if (requires_text == "")
                    {
                        requires_text = requires[i].label
                    }
                    else
                    {
                        requires_text += ", " + requires[i].label
                    }
                }

                return catalog.i18ncp("@item:tooltip %1 is list of setting names", "This setting has been hidden by the value of %1. Change the value of that setting to make this setting visible.", "This setting has been hidden by the values of %1. Change the values of those settings to make this setting visible.", requires.length) .arg(requires_text);
            }
        }

        UM.ColorImage
        {
            anchors.centerIn: parent
            width: Math.round(check.height * 0.75) | 0
            height: width

            source: UM.Theme.getIcon("Information")

            color: UM.Theme.getColor("small_button_text")
        }

        visible: provider.properties.enabled == "False"
    }

    UM.SettingPropertyProvider
    {
        id: provider

        containerStackId: "global"
        watchedProperties: [ "enabled" ]
        key: definition ? definition.key : ""
    }
}
