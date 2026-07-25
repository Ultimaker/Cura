// Copyright (c) 2026 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

// Minimal (non-collapsible) category row delegate for the tabbed settings view.
// Used instead of SettingCategory when showing a single category's settings.

import QtQuick
import QtQuick.Controls

import UM 1.5 as UM

CategoryHeader
{
    id: base
    anchors.left: parent ? parent.left : undefined
    anchors.right: parent ? parent.right : undefined

    categoryIcon: definition ? UM.Theme.getIcon(definition.icon) : ""
    expanded: true
    labelText: definition ? definition.label : ""

    signal showTooltip(string text)
    signal hideTooltip()
    signal contextMenuRequested()
    signal showAllHiddenInheritedSettings(string category_id)
    signal focusReceived()
    signal setActiveFocusToNextSetting(bool forward)
}
