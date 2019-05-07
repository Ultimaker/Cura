// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This component contains the content for the "Help us to improve Ultimaker Cura" page of the welcome on-boarding process.
//
Item
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: catalog.i18nc("@label", "Help us to improve Ultimaker Cura")
        color: UM.Theme.getColor("primary_button")
        font: UM.Theme.getFont("huge")
        renderType: Text.NativeRendering
    }

    // Area where the cloud contents can be put. Pictures, texts and such.
    Item
    {
        id: contentsArea

        anchors
        {
            top: titleLabel.bottom
            bottom: getStartedButton.top
            left: parent.left
            right: parent.right
            topMargin: UM.Theme.getSize("default_margin").width
        }

        Column
        {
            anchors.centerIn: parent
            width: parent.width

            spacing: UM.Theme.getSize("wide_margin").height

            Label
            {
                id: topLabel
                width: parent.width
                anchors.horizontalCenter: parent.horizontalCenter
                horizontalAlignment: Text.AlignHCenter
                text: catalog.i18nc("@text", "Ultimaker Cura collects anonymous data to improve print quality and user experience, including:")
                wrapMode: Text.WordWrap
                font: UM.Theme.getFont("medium")
                color: UM.Theme.getColor("text")
                renderType: Text.NativeRendering
            }

            Grid {
                columns: 2
                spacing: UM.Theme.getSize("wide_margin").height
                anchors.horizontalCenter: parent.horizontalCenter

                ImageTile
                {
                    text: catalog.i18nc("@text", "Machine types")
                    imageSource: UM.Theme.getImage("first_run_machine_types")
                }

                ImageTile
                {
                    text: catalog.i18nc("@text", "Material usage")
                    imageSource: UM.Theme.getImage("first_run_material_usage")
                }

                ImageTile
                {
                    text: catalog.i18nc("@text", "Number of slices")
                    imageSource: UM.Theme.getImage("first_run_number_slices")
                }

                ImageTile
                {
                    text: catalog.i18nc("@text", "Print settings")
                    imageSource: UM.Theme.getImage("first_run_print_settings")
                }
            }

            Label
            {
                id: bottomLabel
                width: parent.width
                anchors.horizontalCenter: parent.horizontalCenter
                horizontalAlignment: Text.AlignHCenter
                text:
                {
                    var t = catalog.i18nc("@text", "Data collected by Ultimaker Cura will not contain any personal information.")
                    var t2 = catalog.i18nc("@text", "More information")
                    t += " <a href='https://notusedref'>" + t2 + "</a>"
                    return t
                }
                textFormat: Text.RichText
                wrapMode: Text.WordWrap
                font: UM.Theme.getFont("medium")
                color: UM.Theme.getColor("text")
                linkColor: UM.Theme.getColor("text_link")
                onLinkActivated: CuraApplication.showMoreInformationDialogForAnonymousDataCollection()
                renderType: Text.NativeRendering
            }
        }
    }

    Cura.PrimaryButton
    {
        id: getStartedButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        text: catalog.i18nc("@button", "Next")
        onClicked: base.showNextPage()
    }
}
