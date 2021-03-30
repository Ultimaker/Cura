// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0 as Controls2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.1

import UM 1.4 as UM
import Cura 1.0 as Cura
import QtGraphicalEffects 1.0

import "../Account"

Item
{
    id: base

    implicitHeight: UM.Theme.getSize("main_window_header").height
    implicitWidth: UM.Theme.getSize("main_window_header").width

    Image
    {
        id: logo
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        anchors.verticalCenter: parent.verticalCenter

        source: UM.Theme.getImage("logo")
        width: UM.Theme.getSize("logo").width
        height: UM.Theme.getSize("logo").height
        fillMode: Image.PreserveAspectFit
        sourceSize.width: width
        sourceSize.height: height
    }

    Row
    {
        id: stagesListContainer
        spacing: Math.round(UM.Theme.getSize("default_margin").width / 2)

        anchors
        {
            horizontalCenter: parent.horizontalCenter
            verticalCenter: parent.verticalCenter
            leftMargin: UM.Theme.getSize("default_margin").width
        }

        // The main window header is dynamically filled with all available stages
        Repeater
        {
            id: stagesHeader

            model: UM.StageModel { }

            delegate: Button
            {
                id: stageSelectorButton
                text: model.name.toUpperCase()
                checkable: true
                checked: UM.Controller.activeStage !== null && model.id == UM.Controller.activeStage.stageId

                anchors.verticalCenter: parent.verticalCenter
                exclusiveGroup: mainWindowHeaderMenuGroup
                style: UM.Theme.styles.main_window_header_tab
                height: UM.Theme.getSize("main_window_header_button").height
                iconSource: model.stage.iconSource

                property color overlayColor: "transparent"
                property string overlayIconSource: ""
                // This id is required to find the stage buttons through Squish
                property string stageId: model.id

                // This is a trick to assure the activeStage is correctly changed. It doesn't work propertly if done in the onClicked (see CURA-6028)
                MouseArea
                {
                    anchors.fill: parent
                    onClicked: UM.Controller.setActiveStage(model.id)
                }
            }
        }

        ExclusiveGroup { id: mainWindowHeaderMenuGroup }
    }

    // Shortcut button to quick access the Toolbox
    Controls2.Button
    {
        id: marketplaceButton
        text: catalog.i18nc("@action:button", "Marketplace")
        height: Math.round(0.5 * UM.Theme.getSize("main_window_header").height)
        onClicked: Cura.Actions.browsePackages.trigger()

        hoverEnabled: true

        background: Rectangle
        {
            radius: UM.Theme.getSize("action_button_radius").width
            color: marketplaceButton.hovered ? UM.Theme.getColor("primary_text") : UM.Theme.getColor("main_window_header_background")
            border.width: UM.Theme.getSize("default_lining").width
            border.color: UM.Theme.getColor("primary_text")
        }

        contentItem: Label
        {
            id: label
            text: marketplaceButton.text
            font: UM.Theme.getFont("default")
            color: marketplaceButton.hovered ? UM.Theme.getColor("main_window_header_background") : UM.Theme.getColor("primary_text")
            width: contentWidth
            verticalAlignment: Text.AlignVCenter
            renderType: Text.NativeRendering
        }

        anchors
        {
            right: accountWidget.left
            rightMargin: UM.Theme.getSize("default_margin").width
            verticalCenter: parent.verticalCenter
        }

        Cura.NotificationIcon
        {
            id: marketplaceNotificationIcon
            anchors
            {
                top: parent.top
                right: parent.right
                rightMargin: (-0.5 * width) | 0
                topMargin: (-0.5 * height) | 0
            }
            visible: CuraApplication.getPackageManager().packagesWithUpdate.length > 0

            labelText:
            {
                const itemCount = CuraApplication.getPackageManager().packagesWithUpdate.length
                return itemCount > 9 ? "9+" : itemCount
            }
        }
    }

    AccountWidget
    {
        id: accountWidget
        anchors
        {
            verticalCenter: parent.verticalCenter
            right: parent.right
            rightMargin: UM.Theme.getSize("default_margin").width
        }
    }
}
