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
}
