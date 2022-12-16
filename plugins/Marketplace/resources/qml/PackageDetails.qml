// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.3

import Cura 1.0 as Cura
import UM 1.5 as UM

Item
{
    id: detailPage
    property var packageData: packages.selectedPackage
    property string title: catalog.i18nc("@header", "Package details")

    RowLayout
    {
        id: header
        anchors
        {
            top: parent.top
            topMargin: UM.Theme.getSize("default_margin").height
            left: parent.left
            leftMargin: UM.Theme.getSize("default_margin").width
            right: parent.right
            rightMargin: anchors.leftMargin
        }

        spacing: UM.Theme.getSize("default_margin").width

        Cura.SecondaryButton
        {
            Layout.alignment: Qt.AlignVCenter
            Layout.preferredHeight: UM.Theme.getSize("action_button").height
            Layout.preferredWidth: height

            onClicked: contextStack.pop() //Remove this page, returning to the main package list or whichever thing is beneath it.

            tooltip: catalog.i18nc("@button:tooltip", "Back")
            toolTipContentAlignment: UM.Enums.ContentAlignment.AlignRight
            leftPadding: UM.Theme.getSize("narrow_margin").width
            rightPadding: leftPadding
            iconSource: UM.Theme.getIcon("ArrowLeft")
            iconSize: height - leftPadding * 2
        }

        UM.Label
        {
            Layout.alignment: Qt.AlignVCenter
            Layout.fillWidth: true

            text: detailPage.title
            font: UM.Theme.getFont("large")
        }
    }

    Rectangle
    {
        anchors
        {
            top: header.bottom
            topMargin: UM.Theme.getSize("default_margin").height
            left: parent.left
            right: parent.right
            bottom: parent.bottom
        }
        color: UM.Theme.getColor("detail_background")

        ScrollView
        {
            anchors.fill: parent

            clip: true //Need to clip, not for the bottom (which is off the window) but for the top (which would overlap the header).
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            contentHeight: packagePage.height + UM.Theme.getSize("default_margin").height * 2

            PackagePage
            {
                id: packagePage
                anchors
                {
                    left: parent.left
                    leftMargin: UM.Theme.getSize("default_margin").width
                    right: parent.right
                    rightMargin: anchors.leftMargin
                    top: parent.top
                    topMargin: UM.Theme.getSize("default_margin").height
                }

                packageData: detailPage.packageData
            }
        }
    }
}
