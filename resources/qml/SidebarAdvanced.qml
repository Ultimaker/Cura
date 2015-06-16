// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.0

import QtQuick.Controls 1.2

import UM 1.0 as UM

UM.SettingView {
    expandedCategories: Printer.expandedCategories;
    onExpandedCategoriesChanged: Printer.setExpandedCategories(expandedCategories);
}
