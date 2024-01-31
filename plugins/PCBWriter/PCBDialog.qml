// Copyright (c) 2024 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtQuick.Window 2.2

import UM 1.5 as UM
import Cura 1.1 as Cura
import PCBWriter 1.0 as PCBWriter

UM.Dialog
{
    id: workspaceDialog
    title: catalog.i18nc("@title:window", "Export pre-configured build batch")

    margin: UM.Theme.getSize("default_margin").width
    minimumWidth: UM.Theme.getSize("modal_window_minimum").width
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height

    backgroundColor: UM.Theme.getColor("detail_background")

    headerComponent: Rectangle
    {
        UM.I18nCatalog { id: catalog; name: "cura" }

        height: childrenRect.height + 2 * UM.Theme.getSize("default_margin").height
        color: UM.Theme.getColor("main_background")

        ColumnLayout
        {
            id: headerColumn

            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.rightMargin: anchors.leftMargin

            UM.Label
            {
                id: titleLabel
                text: catalog.i18nc("@action:title", "Summary - Pre-configured build batch")
                font: UM.Theme.getFont("large")
            }

            UM.Label
            {
                id: descriptionLabel
                text: catalog.i18nc("@action:description", "When exporting a build batch, all the models present on the build plate will be included with their current position, orientation and scale. You can also select which per-extruder or per-model settings should be included to ensure a proper printing of the batch, even on different printers.")
                font: UM.Theme.getFont("default")
                wrapMode: Text.Wrap
                Layout.maximumWidth: headerColumn.width
            }
        }
    }

    Rectangle
    {
        anchors.fill: parent
        color: UM.Theme.getColor("main_background")

        PCBWriter.SettingsExportModel{ id: settingsExportModel }

        ListView
        {
            id: settingsExportList
            anchors.fill: parent
            anchors.margins: UM.Theme.getSize("default_margin").width
            spacing: UM.Theme.getSize("thick_margin").height
            model: settingsExportModel.settingsGroups
            clip: true

            ScrollBar.vertical: UM.ScrollBar { id: verticalScrollBar }

            delegate: SettingsSelectionGroup { Layout.margins: 0 }
        }
    }

    footerComponent: Rectangle
    {
        color: warning ? UM.Theme.getColor("warning") : "transparent"
        anchors.bottom: parent.bottom
        width: parent.width
        height: childrenRect.height + (warning ? 2 * workspaceDialog.margin : workspaceDialog.margin)

        Column
        {
            height: childrenRect.height
            spacing: workspaceDialog.margin

            anchors.leftMargin: workspaceDialog.margin
            anchors.rightMargin: workspaceDialog.margin
            anchors.bottomMargin: workspaceDialog.margin
            anchors.topMargin: warning ? workspaceDialog.margin : 0

            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top

            RowLayout
            {
                id: warningRow
                height: childrenRect.height
                visible: warning
                spacing: workspaceDialog.margin
                UM.ColorImage
                {
                    width: UM.Theme.getSize("extruder_icon").width
                    height: UM.Theme.getSize("extruder_icon").height
                    source: UM.Theme.getIcon("Warning")
                }

                UM.Label
                {
                    id: warningText
                    text: catalog.i18nc("@label", "This project contains materials or plugins that are currently not installed in Cura.<br/>Install the missing packages and reopen the project.")
                }
            }

            Loader
            {
                width: parent.width
                height: childrenRect.height
                sourceComponent: buttonRow
            }
        }
    }

    buttonSpacing: UM.Theme.getSize("wide_margin").width

    onClosing: manager.notifyClosed()
}
