//Copyright (c) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import Qt.labs.qmlmodels 1.0
import QtQuick 2.7
import QtQuick.Controls 1.4 as OldControls
import QtQuick.Controls 2.15

import UM 1.5 as UM
import Cura 1.6 as Cura

Cura.TableView
{
    id: profileOverview

    property var qualityItem //The quality profile to display here.
    property int extruderPosition: -1 //The extruder to display. -1 denotes the global stack.
    property bool isQualityItemCurrentlyActivated: qualityItem != null && qualityItem.name == Cura.MachineManager.activeQualityOrQualityChangesName

    Cura.QualitySettingsModel
    {
        id: qualitySettings
        selectedPosition: profileOverview.extruderPosition
        selectedQualityItem: profileOverview.qualityItem == null ? {} : profileOverview.qualityItem
    }

    columnHeaders: [
        catalog.i18nc("@title:column", "Setting"),
        catalog.i18nc("@title:column", "Profile"),
        catalog.i18nc("@title:column", "Current"),
        catalog.i18nc("@title:column Unit of measurement", "Unit")
    ]
    model: TableModel
    {
        TableModelColumn { display: "label" }
        TableModelColumn { display: "profile_value" }
        TableModelColumn { display: "user_value" }
        TableModelColumn { display: "unit" }
        rows: qualitySettings.items
    }
    sectionRole: "category"
}