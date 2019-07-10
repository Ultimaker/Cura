// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura

Tab
{
    id: base

    property int extruderPosition: -1 //Denotes the global stack.
    property var qualityItem: null

    property bool isQualityItemCurrentlyActivated:
    {
        if (qualityItem == null)
        {
            return false;
        }
        return qualityItem.name == Cura.MachineManager.activeQualityOrQualityChangesName;
    }

    TableView
    {
        anchors.fill: parent
        anchors.margins: UM.Theme.getSize("default_margin").width
        id: profileSettingsView

        Component
        {
            id: itemDelegate

            UM.TooltipArea
            {
                property var setting: qualitySettings.getItem(styleData.row)
                height: childrenRect.height
                width: (parent != null) ? parent.width : 0
                text: (styleData.value.substr(0,1) == "=") ? styleData.value : ""

                Label
                {
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    anchors.right: parent.right
                    text: (styleData.value.substr(0,1) == "=") ? catalog.i18nc("@info:status", "Calculated") : styleData.value
                    font.strikeout: styleData.column == 1 && setting.user_value != "" && base.isQualityItemCurrentlyActivated
                    font.italic: setting.profile_value_source == "quality_changes" || (setting.user_value != "" && base.isQualityItemCurrentlyActivated)
                    opacity: font.strikeout ? 0.5 : 1
                    color: styleData.textColor
                    elide: Text.ElideRight
                }
            }
        }

        TableViewColumn
        {
            role: "label"
            title: catalog.i18nc("@title:column", "Setting")
            width: (parent.width * 0.4) | 0
            delegate: itemDelegate
        }
        TableViewColumn
        {
            role: "profile_value"
            title: catalog.i18nc("@title:column", "Profile")
            width: (parent.width * 0.18) | 0
            delegate: itemDelegate
        }
        TableViewColumn
        {
            role: "user_value"
            title: catalog.i18nc("@title:column", "Current");
            visible: base.isQualityItemCurrentlyActivated
            width: (parent.width * 0.18) | 0
            delegate: itemDelegate
        }
        TableViewColumn
        {
            role: "unit"
            title: catalog.i18nc("@title:column", "Unit")
            width: (parent.width * 0.14) | 0
            delegate: itemDelegate
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
            selectedPosition: base.extruderPosition
            selectedQualityItem: base.qualityItem == null ? {} : base.qualityItem
        }

        SystemPalette { id: palette }
    }
}
