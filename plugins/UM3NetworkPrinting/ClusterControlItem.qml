import QtQuick 2.2
import QtQuick.Controls 1.4

import UM 1.3 as UM
import Cura 1.0 as Cura

Component
{
    Rectangle
    {
        id: base
        property var manager: Cura.MachineManager.printerOutputDevices[0]
        anchors.fill: parent
        color: UM.Theme.getColor("viewport_background")

        property var lineColor: "#DCDCDC" // TODO: Should be linked to theme.
        property var cornerRadius: 4 * screenScaleFactor // TODO: Should be linked to theme.

        visible: manager != null

        UM.I18nCatalog
        {
            id: catalog
            name: "cura"
        }

        Label
        {
            id: activePrintersLabel
            font: UM.Theme.getFont("large")
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.top: parent.top
            text: Cura.MachineManager.printerOutputDevices[0].name
        }

        Rectangle
        {
            id: printJobArea
            border.width: UM.Theme.getSize("default_lining").width
            border.color: lineColor
            anchors.top: activePrintersLabel.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.right: parent.right
            anchors.rightMargin:UM.Theme.getSize("default_margin").width
            radius: cornerRadius
            height: childrenRect.height

            Item
            {
                id: printJobTitleBar
                width: parent.width
                height: printJobTitleLabel.height + 2 * UM.Theme.getSize("default_margin").height

                Label
                {
                    id: printJobTitleLabel
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    anchors.top: parent.top
                    anchors.topMargin: UM.Theme.getSize("default_margin").height
                    text: catalog.i18nc("@title", "Print jobs")
                    font: UM.Theme.getFont("default")
                    opacity: 0.75
                }
                Rectangle
                {
                    anchors.bottom: parent.bottom
                    height: UM.Theme.getSize("default_lining").width
                    color: lineColor
                    width: parent.width
                }
            }

            Column
            {
                id: printJobColumn
                anchors.top: printJobTitleBar.bottom
                anchors.topMargin: UM.Theme.getSize("default_margin").height
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                anchors.right: parent.right
                anchors.rightMargin: UM.Theme.getSize("default_margin").width

                Item
                {
                    width: parent.width
                    height: childrenRect.height
                    opacity: 0.65
                    Label
                    {
                        text: catalog.i18nc("@label", "Printing")
                        font: UM.Theme.getFont("very_small")

                    }
                    Label
                    {
                        text: manager.numJobsPrinting
                        font: UM.Theme.getFont("small")
                        anchors.right: parent.right
                    }
                }
                Item
                {
                    width: parent.width
                    height: childrenRect.height
                    opacity: 0.65
                    Label
                    {
                        text: catalog.i18nc("@label", "Queued")
                        font: UM.Theme.getFont("very_small")
                    }
                    Label
                    {
                        text: manager.numJobsQueued
                        font: UM.Theme.getFont("small")
                        anchors.right: parent.right
                    }
                }
            }
            OpenPanelButton
            {
                anchors.top: printJobColumn.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: UM.Theme.getSize("default_margin").height
                id: configButton
                onClicked: base.manager.openPrintJobControlPanel()
                text: catalog.i18nc("@action:button", "View print jobs")
            }

            Item
            {
                // spacer
                anchors.top: configButton.bottom
                width: UM.Theme.getSize("default_margin").width
                height: UM.Theme.getSize("default_margin").height
            }
        }


        Rectangle
        {
            id: printersArea
            border.width: UM.Theme.getSize("default_lining").width
            border.color: lineColor
            anchors.top: printJobArea.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.right: parent.right
            anchors.rightMargin:UM.Theme.getSize("default_margin").width
            radius: cornerRadius
            height: childrenRect.height

            Item
            {
                id: printersTitleBar
                width: parent.width
                height: printJobTitleLabel.height + 2 * UM.Theme.getSize("default_margin").height

                Label
                {
                    id: printersTitleLabel
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    anchors.top: parent.top
                    anchors.topMargin: UM.Theme.getSize("default_margin").height
                    text: catalog.i18nc("@label:title", "Printers")
                    font: UM.Theme.getFont("default")
                    opacity: 0.75
                }
                Rectangle
                {
                    anchors.bottom: parent.bottom
                    height: UM.Theme.getSize("default_lining").width
                    color: lineColor
                    width: parent.width
                }
            }
            Column
            {
                id: printersColumn
                anchors.top: printersTitleBar.bottom
                anchors.topMargin: UM.Theme.getSize("default_margin").height
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                anchors.right: parent.right
                anchors.rightMargin: UM.Theme.getSize("default_margin").width

                Repeater
                {
                    model: manager.connectedPrintersTypeCount
                    Item
                    {
                        width: parent.width
                        height: childrenRect.height
                        opacity: 0.65
                        Label
                        {
                            text: modelData.machine_type
                            font: UM.Theme.getFont("very_small")
                        }

                        Label
                        {
                            text: modelData.count
                            font: UM.Theme.getFont("small")
                            anchors.right: parent.right
                        }
                    }
                }
            }
            OpenPanelButton
            {
                anchors.top: printersColumn.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: UM.Theme.getSize("default_margin").height
                id: printerConfigButton
                onClicked: base.manager.openPrinterControlPanel()

                text: catalog.i18nc("@action:button", "View printers")
            }

            Item
            {
                // spacer
                anchors.top: printerConfigButton.bottom
                width: UM.Theme.getSize("default_margin").width
                height: UM.Theme.getSize("default_margin").height
            }
        }
    }
}
