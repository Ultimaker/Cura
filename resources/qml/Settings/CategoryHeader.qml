// Copyright (c) 2026 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

// Non-collapsible category header used in the tabbed settings view.

import QtQuick
import QtQuick.Controls

import UM 1.5 as UM
import Cura 1.5 as Cura

Cura.CategoryButton
{
    id: base
    anchors.left: parent.left
    anchors.right: parent.right

    categoryIcon: definition ? UM.Theme.getIcon(definition.icon) : ""
    labelText: definition ? definition.label : ""

    expanded: true
    showArrow: false
    interactive: false

    signal showTooltip(string text)
    signal hideTooltip()
    signal contextMenuRequested()
    signal showAllHiddenInheritedSettings(string category_id)
    signal focusReceived()
    signal setActiveFocusToNextSetting(bool forward)
}

