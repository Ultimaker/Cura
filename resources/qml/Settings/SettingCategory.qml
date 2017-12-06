// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM
import Cura 1.0 as Cura

Button {
    id: base;

    style: UM.Theme.styles.sidebar_category;

    signal showTooltip(string text)
    signal hideTooltip()
    signal contextMenuRequested()
    signal showAllHiddenInheritedSettings(string category_id)
    signal focusReceived()
    signal setActiveFocusToNextSetting(bool forward)

    property var focusItem: base

    text: definition.label
    iconSource: UM.Theme.getIcon(definition.icon)

    checkable: true
    checked: definition.expanded

    onClicked:
    {
        forceActiveFocus();
        if(definition.expanded)
        {
            settingDefinitionsModel.collapse(definition.key);
        } else {
            settingDefinitionsModel.expandAll(definition.key);
        }
    }
    onActiveFocusChanged:
    {
        if(activeFocus)
        {
            base.focusReceived();
        }
    }

    Keys.onTabPressed:
    {
        base.setActiveFocusToNextSetting(true)
    }
    Keys.onBacktabPressed:
    {
        base.setActiveFocusToNextSetting(false)
    }

    UM.SimpleButton
    {
        id: settingsButton

        visible: base.hovered || settingsButton.hovered
        height: base.height * 0.6
        width: base.height * 0.6

        anchors {
            right: inheritButton.visible ? inheritButton.left : parent.right
            rightMargin: inheritButton.visible? UM.Theme.getSize("default_margin").width / 2 : UM.Theme.getSize("setting_preferences_button_margin").width
            verticalCenter: parent.verticalCenter;
        }

        color: UM.Theme.getColor("setting_control_button");
        hoverColor: UM.Theme.getColor("setting_control_button_hover")
        iconSource: UM.Theme.getIcon("settings");

        onClicked: {
            Cura.Actions.configureSettingVisibility.trigger(definition)
        }
    }

    UM.SimpleButton
    {
        id: inheritButton;

        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.getSize("setting_preferences_button_margin").width

        visible:
        {
            if(Cura.SettingInheritanceManager.settingsWithInheritanceWarning.indexOf(definition.key) >= 0)
            {
                var children_with_override = Cura.SettingInheritanceManager.getChildrenKeysWithOverride(definition.key)
                for(var i = 0; i < children_with_override.length; i++)
                {
                    if(!settingDefinitionsModel.getVisible(children_with_override[i]))
                    {
                        return true
                    }
                }
                return false
            }
            return false
        }

        height: parent.height / 2
        width: height

        onClicked:
        {
            settingDefinitionsModel.expandAll(definition.key);
            base.checked = true;
            base.showAllHiddenInheritedSettings(definition.key);
        }

        color: UM.Theme.getColor("setting_control_button")
        hoverColor: UM.Theme.getColor("setting_control_button_hover")
        iconSource: UM.Theme.getIcon("notice")

        onEntered:
        {
            base.showTooltip(catalog.i18nc("@label","Some hidden settings use values different from their normal calculated value.\n\nClick to make these settings visible."))
        }

        onExited:
        {
            base.hideTooltip();
        }

        UM.I18nCatalog { id: catalog; name: "cura" }
    }
}
