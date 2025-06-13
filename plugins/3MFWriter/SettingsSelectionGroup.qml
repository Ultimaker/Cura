// Copyright (c) 2024 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtQuick.Window 2.2

import UM 1.5 as UM
import Cura 1.1 as Cura
import ThreeMFWriter 1.0 as ThreeMFWriter

ColumnLayout
{
    id: settingsGroup
    spacing: UM.Theme.getSize("narrow_margin").width

    RowLayout
    {
        id: settingsGroupTitleRow
        spacing: UM.Theme.getSize("default_margin").width

        Item
        {
            id: icon
            height: UM.Theme.getSize("medium_button_icon").height
            width: height

            UM.ColorImage
            {
                id: settingsMainImage
                anchors.fill: parent
                source:
                {
                    switch(modelData.category)
                    {
                        case ThreeMFWriter.SettingsExportGroup.Global:
                            return UM.Theme.getIcon("Sliders")
                        case ThreeMFWriter.SettingsExportGroup.Model:
                            return UM.Theme.getIcon("View3D")
                        default:
                            return ""
                    }
                }

                color: UM.Theme.getColor("text")
            }

            Cura.ExtruderIcon
            {
                id: settingsExtruderIcon
                anchors.fill: parent
                visible: modelData.category === ThreeMFWriter.SettingsExportGroup.Extruder
                text: (modelData.extruder_index + 1).toString()
                font: UM.Theme.getFont("tiny_emphasis")
                materialColor: modelData.extruder_color
            }
        }

        UM.Label
        {
            id: settingsTitle
            text: modelData.name + (modelData.category_details ? ' (%1)'.arg(modelData.category_details) : '')
            font: UM.Theme.getFont("default_bold")
        }
    }

    ListView
    {
        id: settingsExportList
        Layout.fillWidth: true
        Layout.preferredHeight: contentHeight
        spacing: 0
        model: modelData.visibleSettings
        visible: modelData.visibleSettings.length > 0

        delegate: SettingSelection { }
    }

    UM.Label
    {
        UM.I18nCatalog { id: catalog; name: "cura" }
        text: catalog.i18nc("@label", "No specific value has been set")
        visible: modelData.visibleSettings.length === 0
    }
}
