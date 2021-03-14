// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.1 as UM
import Cura 1.0 as Cura

Button
{
    id: base
    anchors.left: parent.left
    anchors.right: parent.right
    // To avoid overlaping with the scrollBars
    anchors.rightMargin: 2 * UM.Theme.getSize("thin_margin").width
    hoverEnabled: true

    background: Rectangle
    {
        id: backgroundRectangle
        height: UM.Theme.getSize("section").height
        color:
        {
            if (!base.enabled)
            {
                return UM.Theme.getColor("setting_category_disabled")
            }
            else if (base.hovered)
            {
                return UM.Theme.getColor("setting_category_hover")
            }
            return UM.Theme.getColor("setting_category")
        }
        Behavior on color { ColorAnimation { duration: 50; } }
    }

    signal showTooltip(string text)
    signal hideTooltip()
    signal contextMenuRequested()
    signal showAllHiddenInheritedSettings(string category_id)
    signal focusReceived()
    signal setActiveFocusToNextSetting(bool forward)

    property var focusItem: base
    property bool expanded: definition.expanded


    property color text_color:
    {
        if (!base.enabled)
        {
            return UM.Theme.getColor("setting_category_disabled_text")
        } else if (base.hovered || base.pressed || base.activeFocus)
        {
            return UM.Theme.getColor("setting_category_active_text")
        }

        return UM.Theme.getColor("setting_category_text")

    }

    contentItem: Item
    {
        anchors.fill: parent

        Label
        {
            id: settingNameLabel
            anchors
            {
                left: parent.left
                leftMargin: 2 * UM.Theme.getSize("default_margin").width + UM.Theme.getSize("section_icon").width
                right: parent.right
                verticalCenter: parent.verticalCenter
            }
            text: definition.label
            textFormat: Text.PlainText
            renderType: Text.NativeRendering
            font: UM.Theme.getFont("medium_bold")
            color: base.text_color
            fontSizeMode: Text.HorizontalFit
            minimumPointSize: 8
        }

        UM.RecolorImage
        {
            id: category_arrow
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            width: UM.Theme.getSize("standard_arrow").width
            height: UM.Theme.getSize("standard_arrow").height
            sourceSize.height: width
            color: UM.Theme.getColor("setting_control_button")
            source: definition.expanded ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_left")
        }
    }

    UM.RecolorImage
    {
        id: icon
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("thin_margin").width
        color: base.text_color
        source: UM.Theme.getIcon(definition.icon)
        width: UM.Theme.getSize("section_icon").width
        height: UM.Theme.getSize("section_icon").height
        sourceSize.width: width + 15 * screenScaleFactor
        sourceSize.height: width + 15 * screenScaleFactor
    }

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
        height: Math.round(base.height * 0.6)
        width: Math.round(base.height * 0.6)

        anchors
        {
            right: inheritButton.visible ? inheritButton.left : parent.right
            // Use 1.9 as the factor because there is a 0.1 difference between the settings and inheritance warning icons
            rightMargin: inheritButton.visible ? Math.round(UM.Theme.getSize("default_margin").width / 2) : category_arrow.width + Math.round(UM.Theme.getSize("default_margin").width * 1.9)
            verticalCenter: parent.verticalCenter
        }

        color: UM.Theme.getColor("setting_control_button")
        hoverColor: UM.Theme.getColor("setting_control_button_hover")
        iconSource: UM.Theme.getIcon("settings")

        onClicked: Cura.Actions.configureSettingVisibility.trigger(definition)
    }

    UM.SimpleButton
    {
        id: inheritButton

        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        anchors.rightMargin: category_arrow.width + UM.Theme.getSize("default_margin").width * 2

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

        height: Math.round(parent.height / 2)
        width: height

        onClicked:
        {
            settingDefinitionsModel.expandRecursive(definition.key)
            base.showAllHiddenInheritedSettings(definition.key)
        }

        color: UM.Theme.getColor("setting_control_button")
        hoverColor: UM.Theme.getColor("setting_control_button_hover")
        iconSource: UM.Theme.getIcon("notice")

        onEntered: base.showTooltip(catalog.i18nc("@label","Some hidden settings use values different from their normal calculated value.\n\nClick to make these settings visible."))

        onExited: base.hideTooltip()
    }
}
