// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Tab
{
    id: base

    property string extruderId: "";
    property string extruderDefinition: "";
    property string quality: "";
    property string material: "";

    TableView
    {
        anchors.fill: parent
        anchors.margins: UM.Theme.getSize("default_margin").width

        TableViewColumn
        {
            role: "label"
            title: catalog.i18nc("@title:column", "Setting")
            width: parent.width * 0.4
        }
        TableViewColumn
        {
            role: "profile_value"
            title: catalog.i18nc("@title:column", "Profile")
            width: parent.width * 0.18
            delegate: Rectangle
            {
                property var setting: qualitySettings.getItem(styleData.row)
                height: childrenRect.height
                color: "transparent"
                width: (parent != null) ? parent.width : 0
                Label
                {
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    anchors.right: parent.right
                    text: styleData.value
                    font.weight: (setting.profile_value_source == "quality_changes") ? Font.Bold : Font.Normal
                    font.strikeout: quality == Cura.MachineManager.activeQualityId && setting.user_value != ""
                    opacity: font.strikeout ? 0.5 : 1
                    color: styleData.textColor
                    elide: Text.ElideRight
                }
            }

        }
        TableViewColumn
        {
            role: "user_value"
            title: catalog.i18nc("@title:column", "Current");
            visible: quality == Cura.MachineManager.activeQualityId
            width: parent.width * 0.18
        }
        TableViewColumn
        {
            role: "unit"
            title: catalog.i18nc("@title:column", "Unit")
            width: parent.width * 0.14
        }

        section.property: "category"
        section.delegate: Label
        {
            text: section
            font.bold: true
        }

        model: Cura.QualitySettingsModel
        {
            id: qualitySettings
            extruderId: base.extruderId
            extruderDefinition: base.extruderDefinition
            quality: base.quality != null ? base.quality : ""
            material: base.material != null ? base.material : ""
        }

        SystemPalette { id: palette }
    }
}
