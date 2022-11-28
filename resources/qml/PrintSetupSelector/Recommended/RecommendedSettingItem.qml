// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 2.10

import UM 1.5 as UM
import Cura 1.7 as Cura


Item
{
    width: parent.width
    height: UM.Theme.getSize("section_header").height
    Layout.fillWidth: true

    property alias settingControl: settingContainer.children
    property alias settingName: settingLabel.text
    property int leftColumnWidth: width / 2

    UM.Label
    {
        id: settingLabel
        width: leftColumnWidth
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        // These numbers come from the IconWithText in RecommendedSettingSection
        anchors.leftMargin: UM.Theme.getSize("medium_button_icon").width + UM.Theme.getSize("thick_margin").width - UM.Theme.getSize("thick_lining").width
    }


    Loader
    {
        id: settingContainer
        height: childrenRect.height
        anchors.left: settingLabel.right
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
    }
}