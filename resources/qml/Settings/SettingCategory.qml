// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM

import ".."

Button {
    id: base;

    style: UM.Theme.styles.sidebar_category;

    signal showTooltip(string text);
    signal hideTooltip();
    signal contextMenuRequested()

    text: definition.label
    iconSource: UM.Theme.getIcon(definition.icon)

    checkable: true
    checked: definition.expanded

    onClicked: definition.expanded ? settingDefinitionsModel.collapse(definition.key) : settingDefinitionsModel.expandAll(definition.key)

    UM.SimpleButton {
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
            Actions.configureSettingVisibility.trigger(definition)
        }
    }

    UM.SimpleButton
    {
        id: inheritButton;

        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.getSize("setting_preferences_button_margin").width

        visible: hiddenValuesCount > 0
        height: parent.height / 2;
        width: height;

        onClicked: {
            base.showAllHiddenInheritedSettings()
        }

        color: UM.Theme.getColor("setting_control_button")
        hoverColor: UM.Theme.getColor("setting_control_button_hover")
        iconSource: UM.Theme.getIcon("notice")

        onEntered: {
            base.showTooltip(catalog.i18nc("@label","Some hidden settings use values different from their normal calculated value.\n\nClick to make these settings visible."))
        }

        onExited: {
            base.hideTooltip();
        }

        UM.I18nCatalog { id: catalog; name: "cura" }
    }
}
