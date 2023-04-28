//Copyright (c) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.15

import UM 1.6 as UM
import Cura 1.6 as Cura

Cura.TableView
{
    id: profileOverview

    property var qualityItem //The quality profile to display here.
    property int extruderPosition: -1 //The extruder to display. -1 denotes the global stack.
    property bool isQualityItemCurrentlyActivated: qualityItem != null && qualityItem.name == Cura.MachineManager.activeQualityOrQualityChangesName

    // Hack to make sure that when the data of our model changes the tablemodel is also updated
    // If we directly set the rows (So without the clear being called) it doesn't seem to
    // get updated correctly.
    property var modelRows: qualitySettings.items
    onModelRowsChanged:
    {
        tableModel.clear()
        tableModel.rows = modelRows
    }

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

    model: UM.TableModel
    {
        id: tableModel
        headers: ["label", "profile_value", "user_value", "unit"]
        rows: modelRows
    }
    sectionRole: "category"
}