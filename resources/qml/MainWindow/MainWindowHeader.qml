// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.4

import UM 1.5 as UM
import Cura 1.0 as Cura

import "../Account"
import "../ApplicationSwitcher"

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
    ButtonGroup
    {
        buttons: stagesListContainer.children
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
                //style: UM.Theme.styles.main_window_header_tab
                height: Math.round(0.5 * UM.Theme.getSize("main_window_header").height)
                // This id is required to find the stage buttons through Squish
                property string stageId: model.id
                hoverEnabled: true
                leftPadding: 2 * UM.Theme.getSize("default_margin").width
                rightPadding: 2 * UM.Theme.getSize("default_margin").width

                // Set top & bottom padding to whatever space is left from height and the size of the text.
                bottomPadding: Math.round((height - buttonLabel.contentHeight) / 2)
                topPadding: bottomPadding

                background: Rectangle
                {
                    radius: UM.Theme.getSize("action_button_radius").width
                    color:
                    {
                        if (stageSelectorButton.checked)
                        {
                            return UM.Theme.getColor("main_window_header_button_background_active")
                        }
                        else
                        {
                            if (stageSelectorButton.hovered)
                            {
                                return UM.Theme.getColor("main_window_header_button_background_hovered")
                            }
                            return UM.Theme.getColor("main_window_header_button_background_inactive")
                        }
                    }
                }

                contentItem: UM.Label
                {
                    id: buttonLabel
                    text: stageSelectorButton.text
                    anchors.centerIn: stageSelectorButton
                    font: UM.Theme.getFont("medium")
                    color:
                    {
                        if (stageSelectorButton.checked)
                        {
                            return UM.Theme.getColor("main_window_header_button_text_active")
                        }
                        else
                        {
                            if (stageSelectorButton.hovered)
                            {
                                return UM.Theme.getColor("main_window_header_button_text_hovered")
                            }
                            return UM.Theme.getColor("main_window_header_button_text_inactive")
                        }
                    }
                }

                // This is a trick to assure the activeStage is correctly changed. It doesn't work properly if done in the onClicked (see CURA-6028)
                MouseArea
                {
                    anchors.fill: parent
                    onClicked: UM.Controller.setActiveStage(model.id)
                }
            }
        }
    }

    ApplicationSwitcher
    {
        id: applicationSwitcher
        anchors
        {
            verticalCenter: parent.verticalCenter
            right: accountWidget.left
            rightMargin: UM.Theme.getSize("default_margin").width
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
