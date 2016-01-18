// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

UM.Dialog
{
    id: base

    //: About dialog title
    title: catalog.i18nc("@title:window","Load profile")
    width: 400
    height: childrenRect.height

    Label
    {
        id: body

        //: About dialog application description
        text: catalog.i18nc("@label","Selecting this profile overwrites some of your customised settings. Do you want to merge the new settings into your current profile or do you want to load a clean copy of the profile?")
        wrapMode: Text.WordWrap
        width: parent.width
        anchors.top: parent.top
        anchors.margins: UM.Theme.sizes.default_margin.height

        UM.I18nCatalog { id: catalog; name: "cura"; }
    }

    Label
    {
        id: show_details

        //: About dialog application author note
        text: catalog.i18nc("@label","Show details.")
        wrapMode: Text.WordWrap
        anchors.top: body.bottom
        anchors.topMargin: UM.Theme.sizes.default_margin.height
    }

    rightButtons: Row
    {
        spacing: UM.Theme.sizes.default_margin.width

        Button
        {
            text: catalog.i18nc("@action:button","Merge settings");
        }
        Button
        {
            text: catalog.i18nc("@action:button","Reset profile");
        }
        Button
        {
            text: catalog.i18nc("@action:button","Cancel");

            onClicked: base.visible = false;
        }
    }
}

