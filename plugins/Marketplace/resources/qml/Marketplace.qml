// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.2

import UM 1.2 as UM

Window
{
    id: marketplaceDialog
    property variant catalog: UM.I18nCatalog { name: "cura" }

    minimumWidth: UM.Theme.getSize("modal_window_minimum").width
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height
    width: minimumWidth
    height: minimumHeight

    title: "Marketplace" //Seen by Ultimaker as a brand name, so this doesn't get translated.
    modality: Qt.NonModal

    Rectangle //Background color.
    {
        anchors.fill: parent
        color: UM.Theme.getColor("main_background")

        ColumnLayout
        {
            anchors.fill: parent
            anchors.margins: UM.Theme.getSize("default_margin").width

            spacing: UM.Theme.getSize("default_margin").height

            Label //Page title.
            {
                Layout.preferredWidth: parent.width
                Layout.preferredHeight: contentHeight

                font: UM.Theme.getFont("large")
                color: UM.Theme.getColor("text")
                text: catalog.i18nc("@header", "Install Plugins")
            }
            Loader //Page contents.
            {
                Layout.preferredWidth: parent.width
                Layout.fillHeight: true

                source: "Plugins.qml"
            }
        }
    }
}