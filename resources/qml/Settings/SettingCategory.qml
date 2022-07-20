// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.5 as UM
import Cura 1.5 as Cura

Cura.CategoryButton
{
    id: base
    anchors.left: parent.left
    anchors.right: parent.right

    categoryIcon: UM.Theme.getIcon(definition.icon)
    expanded: definition.expanded
    labelText: definition.label

    signal showTooltip(string text)
    signal hideTooltip()
    signal contextMenuRequested()
    signal showAllHiddenInheritedSettings(string category_id)
    signal focusReceived()
    signal setActiveFocusToNextSetting(bool forward)

    property var focusItem: base

    onClicked:
    {
        if (definition.expanded)
        {
            settingDefinitionsModel.collapseRecursive(definition.key)
        }
        else
        {
            settingDefinitionsModel.expandRecursive(definition.key)
        }
        //Set focus so that tab navigation continues from this point on.
        //NB: This must be set AFTER collapsing/expanding the category so that the scroll position is correct.
        forceActiveFocus()
    }
    onActiveFocusChanged:
    {
        if (activeFocus)
        {
            base.focusReceived()
        }
    }

    Keys.onTabPressed: base.setActiveFocusToNextSetting(true)
    Keys.onBacktabPressed: base.setActiveFocusToNextSetting(false)

    UM.SimpleButton
    {
        id: settingsButton

        visible: base.hovered || settingsButton.hovered
        height: UM.Theme.getSize("small_button_icon").height
        width: height

        anchors
        {
            right: inheritButton.visible ? inheritButton.left : parent.right
            // Use 1.9 as the factor because there is a 0.1 difference between the settings and inheritance warning icons
            rightMargin: inheritButton.visible ? Math.round(UM.Theme.getSize("default_margin").width / 2) : arrow.width + Math.round(UM.Theme.getSize("default_margin").width * 1.9)
            verticalCenter: parent.verticalCenter
        }

        color: UM.Theme.getColor("setting_control_button")
        hoverColor: UM.Theme.getColor("setting_control_button_hover")
        iconSource: UM.Theme.getIcon("Sliders")

        onClicked: Cura.Actions.configureSettingVisibility.trigger(definition)
    }

    UM.SimpleButton
    {
        id: inheritButton

        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        anchors.rightMargin: arrow.width + UM.Theme.getSize("default_margin").width * 2

        visible:
        {
            if (Cura.SettingInheritanceManager.settingsWithInheritanceWarning.indexOf(definition.key) >= 0)
            {
                var children_with_override = Cura.SettingInheritanceManager.getChildrenKeysWithOverride(definition.key)
                for (var i = 0; i < children_with_override.length; i++)
                {
                    if (!settingDefinitionsModel.getVisible(children_with_override[i]))
                    {
                        return true
                    }
                }
                return false
            }
            return false
        }

        height: UM.Theme.getSize("small_button_icon").height
        width: height

        onClicked:
        {
            settingDefinitionsModel.expandRecursive(definition.key)
            base.showAllHiddenInheritedSettings(definition.key)
        }

        color: UM.Theme.getColor("setting_control_button")
        hoverColor: UM.Theme.getColor("setting_control_button_hover")
        iconSource: UM.Theme.getIcon("Information")

        onEntered: base.showTooltip(catalog.i18nc("@label","Some hidden settings use values different from their normal calculated value.\n\nClick to make these settings visible."))

        onExited: base.hideTooltip()
    }
}
