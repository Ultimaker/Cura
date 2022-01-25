//Copyright (c) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4 as OldControls
import QtQuick.Controls 2.15

import UM 1.5 as UM
import Cura 1.6 as Cura

OldControls.TableView
{
    id: profileOverview

    property var qualityItem //The quality profile to display here.
    property int extruderPosition: -1 //The extruder to display. -1 denotes the global stack.

    property bool isQualityItemCurrentlyActivated:
    {
        if (qualityItem == null)
        {
            return false;
        }
        return qualityItem.name == Cura.MachineManager.activeQualityOrQualityChangesName;
    }

    Component
    {
        id: itemDelegate

        UM.TooltipArea
        {
            property var setting: qualitySettings.getItem(styleData.row)
            height: childrenRect.height
            width: (parent != null) ? parent.width : 0
            text:
            {
                if (styleData.value === undefined)
                {
                    return ""
                }
                return (styleData.value.substr(0,1) == "=") ? styleData.value : ""
            }

            Label
            {
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                anchors.right: parent.right
                text:
                {
                    if (styleData.value === undefined)
                    {
                        return ""
                    }
                    return (styleData.value.substr(0,1) == "=") ? catalog.i18nc("@info:status", "Calculated") : styleData.value
                }
                font.strikeout: styleData.column == 1 && setting.user_value != "" && profileOverview.isQualityItemCurrentlyActivated
                font.italic: setting.profile_value_source == "quality_changes" || (setting.user_value != "" && profileOverview.isQualityItemCurrentlyActivated)
                opacity: font.strikeout ? 0.5 : 1
                color: styleData.textColor
                elide: Text.ElideRight
            }
        }
    }

    OldControls.TableViewColumn
    {
        role: "label"
        title: catalog.i18nc("@title:column", "Setting")
        width: (parent.width * 0.4) | 0
        delegate: itemDelegate
    }
    OldControls.TableViewColumn
    {
        role: "profile_value"
        title: catalog.i18nc("@title:column", "Profile")
        width: (parent.width * 0.18) | 0
        delegate: itemDelegate
    }
    OldControls.TableViewColumn
    {
        role: "user_value"
        title: catalog.i18nc("@title:column", "Current");
        visible: profileOverview.isQualityItemCurrentlyActivated
        width: (parent.width * 0.18) | 0
        delegate: itemDelegate
    }
    OldControls.TableViewColumn
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
        selectedPosition: profileOverview.extruderPosition
        selectedQualityItem: profileOverview.qualityItem == null ? {} : profileOverview.qualityItem
    }
}