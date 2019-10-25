// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Layouts 1.2
import QtQuick.Controls 2.0

import UM 1.1 as UM
import Cura 1.0 as Cura

import "."

Item
{
    id: base

    height: UM.Theme.getSize("section").height
    anchors.left: parent.left
    anchors.right: parent.right
    // To avoid overlaping with the scrollBars
    anchors.rightMargin: 2 * UM.Theme.getSize("thin_margin").width

    property alias contents: controlContainer.children
    property alias hovered: mouse.containsMouse

    property bool showRevertButton: true
    property bool showInheritButton: true
    property bool showLinkedSettingIcon: true
    property bool doDepthIndentation: true
    property bool doQualityUserSettingEmphasis: true
    property var settingKey: definition.key //Used to detect each individual setting more easily in Squish GUI tests.

    // Create properties to put property provider stuff in (bindings break in qt 5.5.1 otherwise)
    property var state: propertyProvider.properties.state
    property var resolve: propertyProvider.properties.resolve
    property var stackLevels: propertyProvider.stackLevels
    property var stackLevel: stackLevels[0]
    // A list of stack levels that will trigger to show the revert button
    property var showRevertStackLevels: [0]
    property bool resetButtonVisible: {
        var is_revert_stack_level = false;
        for (var i in base.showRevertStackLevels)
        {
            if (base.stackLevel == i)
            {
                is_revert_stack_level = true
                break
            }
        }
        return is_revert_stack_level && base.showRevertButton
    }

    signal focusReceived()
    signal setActiveFocusToNextSetting(bool forward)
    signal contextMenuRequested()
    signal showTooltip(string text)
    signal hideTooltip()
    signal showAllHiddenInheritedSettings(string category_id)

    function createTooltipText()
    {
        var affects = settingDefinitionsModel.getRequiredBy(definition.key, "value")
        var affected_by = settingDefinitionsModel.getRequires(definition.key, "value")

        var affected_by_list = ""
        for (var i in affected_by)
        {
            affected_by_list += "<li>%1</li>\n".arg(affected_by[i].label)
        }

        var affects_list = ""
        for (var i in affects)
        {
            affects_list += "<li>%1</li>\n".arg(affects[i].label)
        }

        var tooltip = "<b>%1</b>\n<p>%2</p>".arg(definition.label).arg(definition.description)

        if(!propertyProvider.isValueUsed)
        {
            tooltip += "<i>%1</i><br/><br/>".arg(catalog.i18nc("@label", "This setting is not used because all the settings that it influences are overridden."))
        }

        if (affects_list != "")
        {
            tooltip += "<b>%1</b><ul>%2</ul>".arg(catalog.i18nc("@label Header for list of settings.", "Affects")).arg(affects_list)
        }

        if (affected_by_list != "")
        {
            tooltip += "<b>%1</b><ul>%2</ul>".arg(catalog.i18nc("@label Header for list of settings.", "Affected By")).arg(affected_by_list)
        }

        return tooltip
    }

    MouseArea
    {
        id: mouse

        anchors.fill: parent

        acceptedButtons: Qt.RightButton
        hoverEnabled: true;

        onClicked: base.contextMenuRequested()

        onEntered:
        {
            hoverTimer.start()
        }

        onExited:
        {
            if (controlContainer.item && controlContainer.item.hovered)
            {
                return
            }
            hoverTimer.stop()
            base.hideTooltip()
        }

        Timer
        {
            id: hoverTimer
            interval: 500
            repeat: false

            onTriggered:
            {
                base.showTooltip(base.createTooltipText())
            }
        }

        Label
        {
            id: label

            anchors.left: parent.left
            anchors.leftMargin: doDepthIndentation ? Math.round(UM.Theme.getSize("thin_margin").width + ((definition.depth - 1) * UM.Theme.getSize("setting_control_depth_margin").width)) : 0
            anchors.right: settingControls.left
            anchors.verticalCenter: parent.verticalCenter

            text: definition.label
            elide: Text.ElideMiddle
            renderType: Text.NativeRendering
            textFormat: Text.PlainText

            color: UM.Theme.getColor("setting_control_text")
            opacity: (definition.visible) ? 1 : 0.5
            // emphasize the setting if it has a value in the user or quality profile
            font: base.doQualityUserSettingEmphasis && base.stackLevel !== undefined && base.stackLevel <= 1 ? UM.Theme.getFont("default_italic") : UM.Theme.getFont("default")
        }

        Row
        {
            id: settingControls

            height: Math.round(parent.height / 2)
            spacing: Math.round(UM.Theme.getSize("thick_margin").height / 2)

            anchors
            {
                right: controlContainer.left
                rightMargin: Math.round(UM.Theme.getSize("thick_margin").width / 2)
                verticalCenter: parent.verticalCenter
            }

            UM.SimpleButton
            {
                id: linkedSettingIcon;

                visible: (!definition.settable_per_extruder || String(globalPropertyProvider.properties.limit_to_extruder) != "-1") && base.showLinkedSettingIcon

                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: height

                color: UM.Theme.getColor("setting_control_button")
                hoverColor: UM.Theme.getColor("setting_control_button")

                iconSource: UM.Theme.getIcon("link")

                onEntered:
                {
                    hoverTimer.stop()
                    var tooltipText = catalog.i18nc("@label", "This setting is always shared between all extruders. Changing it here will change the value for all extruders.")
                    if ((resolve !== "None") && (stackLevel !== 0))
                    {
                        // We come here if a setting has a resolve and the setting is not manually edited.
                        tooltipText += " " + catalog.i18nc("@label", "The value is resolved from per-extruder values ") + "[" + Cura.ExtruderManager.getInstanceExtruderValues(definition.key) + "]."
                    }
                    base.showTooltip(tooltipText)
                }
                onExited: base.showTooltip(base.createTooltipText())
            }

            UM.SimpleButton
            {
                id: revertButton

                visible: base.resetButtonVisible

                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: height

                color: UM.Theme.getColor("setting_control_button")
                hoverColor: UM.Theme.getColor("setting_control_button_hover")

                iconSource: UM.Theme.getIcon("reset")

                onClicked:
                {
                    revertButton.focus = true

                    if (externalResetHandler)
                    {
                        externalResetHandler(propertyProvider.key)
                    }
                    else
                    {
                        Cura.MachineManager.clearUserSettingAllCurrentStacks(propertyProvider.key)
                    }
                }

                onEntered:
                {
                    hoverTimer.stop()
                    base.showTooltip(catalog.i18nc("@label", "This setting has a value that is different from the profile.\n\nClick to restore the value of the profile."))
                }
                onExited: base.showTooltip(base.createTooltipText())
            }

            UM.SimpleButton
            {
                // This button shows when the setting has an inherited function, but is overridden by profile.
                id: inheritButton
                // Inherit button needs to be visible if;
                // - User made changes that override any loaded settings
                // - This setting item uses inherit button at all
                // - The type of the value of any deeper container is an "object" (eg; is a function)
                visible:
                {
                    if (!base.showInheritButton)
                    {
                        return false
                    }

                    if (!propertyProvider.properties.enabled)
                    {
                        // Note: This is not strictly necessary since a disabled setting is hidden anyway.
                        // But this will cause the binding to be re-evaluated when the enabled property changes.
                        return false
                    }

                    // There are no settings with any warning.
                    if (Cura.SettingInheritanceManager.settingsWithInheritanceWarning.length === 0)
                    {
                        return false
                    }

                    // This setting has a resolve value, so an inheritance warning doesn't do anything.
                    if (resolve !== "None")
                    {
                        return false
                    }

                    // If the setting does not have a limit_to_extruder property (or is -1), use the active stack.
                    if (globalPropertyProvider.properties.limit_to_extruder === null || String(globalPropertyProvider.properties.limit_to_extruder) === "-1")
                    {
                        return Cura.SettingInheritanceManager.settingsWithInheritanceWarning.indexOf(definition.key) >= 0
                    }

                    // Setting does have a limit_to_extruder property, so use that one instead.
                    if (definition.key === undefined) {
                        // Observed when loading workspace, probably when SettingItems are removed.
                        return false
                    }
                    return Cura.SettingInheritanceManager.getOverridesForExtruder(definition.key, String(globalPropertyProvider.properties.limit_to_extruder)).indexOf(definition.key) >= 0
                }

                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: height

                onClicked:
                {
                    focus = true

                    // Get the most shallow function value (eg not a number) that we can find.
                    var last_entry = propertyProvider.stackLevels[propertyProvider.stackLevels.length - 1]
                    for (var i = 1; i < base.stackLevels.length; i++)
                    {
                        var has_setting_function = typeof(propertyProvider.getPropertyValue("value", base.stackLevels[i])) == "object"
                        if(has_setting_function)
                        {
                            last_entry = propertyProvider.stackLevels[i]
                            break
                        }
                    }
                    if ((last_entry === 4 || last_entry === 11) && base.stackLevel === 0 && base.stackLevels.length === 2)
                    {
                        // Special case of the inherit reset. If only the definition (4th or 11th) container) and the first
                        // entry (user container) are set, we can simply remove the container.
                        propertyProvider.removeFromContainer(0)
                    }
                    else
                    {
                        // Put that entry into the "top" instance container.
                        // This ensures that the value in any of the deeper containers need not be removed, which is
                        // needed for the reset button (which deletes the top value) to correctly go back to profile
                        // defaults.
                        propertyProvider.setPropertyValue("value", propertyProvider.getPropertyValue("value", last_entry))
                        propertyProvider.setPropertyValue("state", "InstanceState.Calculated")

                    }
                }

                color: UM.Theme.getColor("setting_control_button")
                hoverColor: UM.Theme.getColor("setting_control_button_hover")

                iconSource: UM.Theme.getIcon("formula")

                onEntered: { hoverTimer.stop(); base.showTooltip(catalog.i18nc("@label", "This setting is normally calculated, but it currently has an absolute value set.\n\nClick to restore the calculated value.")) }
                onExited: base.showTooltip(base.createTooltipText())
            }
        }

        Item
        {
            id: controlContainer

            enabled: propertyProvider.isValueUsed

            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            width: UM.Theme.getSize("setting_control").width
            height: UM.Theme.getSize("setting_control").height
        }
    }
}
