// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Dialogs 1.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.3
import QtGraphicalEffects 1.0

import QtQuick.Controls 2.0 as Controls2

import UM 1.3 as UM
import Cura 1.0 as Cura


Component
{
    Rectangle
    {
        id: base
        property var lineColor: "#DCDCDC" // TODO: Should be linked to theme.
        property var shadowRadius: 5 * screenScaleFactor
        property var cornerRadius: 4 * screenScaleFactor // TODO: Should be linked to theme.
        visible: OutputDevice != null
        anchors.fill: parent
        color: "white"

        UM.I18nCatalog
        {
            id: catalog
            name: "cura"
        }

        Label
        {
            id: printingLabel
            font: UM.Theme.getFont("large")
            anchors
            {
                margins: 2 * UM.Theme.getSize("default_margin").width
                leftMargin: 4 * UM.Theme.getSize("default_margin").width
                top: parent.top
                left: parent.left
                right: parent.right
            }

            text: catalog.i18nc("@label", "Printing")
            elide: Text.ElideRight
        }

        Label
        {
            id: managePrintersLabel
            anchors.rightMargin: 4 * UM.Theme.getSize("default_margin").width
            anchors.right: printerScrollView.right
            anchors.bottom: printingLabel.bottom
            text: catalog.i18nc("@label link to connect manager", "Manage printers")
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("primary")
            linkColor: UM.Theme.getColor("primary")
        }

        MouseArea
        {
            anchors.fill: managePrintersLabel
            hoverEnabled: true
            onClicked: Cura.MachineManager.printerOutputDevices[0].openPrinterControlPanel()
            onEntered: managePrintersLabel.font.underline = true
            onExited: managePrintersLabel.font.underline = false
        }

        // Skeleton loading
        Column
        {
            id: skeletonLoader
            visible: printerList.count === 0;
            anchors
            {
                top: printingLabel.bottom
                topMargin: UM.Theme.getSize("default_margin").height
                left: parent.left
                leftMargin: UM.Theme.getSize("wide_margin").width
                right: parent.right
                rightMargin: UM.Theme.getSize("wide_margin").width
            }
            spacing: UM.Theme.getSize("default_margin").height - 10

            PrinterCard
            {
                printer: null
            }
            PrinterCard
            {
                printer: null
            }
        }

        // Actual content
        ScrollView
        {
            id: printerScrollView
            anchors
            {
                top: printingLabel.bottom
                topMargin: UM.Theme.getSize("default_margin").height
                left: parent.left
                right: parent.right
                bottom: parent.bottom;
            }

            style: UM.Theme.styles.scrollview

            ListView
            {
                id: printerList
                property var currentIndex: -1
                anchors
                {
                    fill: parent
                    leftMargin: UM.Theme.getSize("wide_margin").width
                    rightMargin: UM.Theme.getSize("wide_margin").width
                }
                spacing: UM.Theme.getSize("default_margin").height - 10
                model: OutputDevice.printers
                delegate: PrinterCard
                {
                    printer: modelData
                }
            }
        }
    }
}
