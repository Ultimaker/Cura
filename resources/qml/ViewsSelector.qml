// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.0 as Cura

Cura.ExpandablePopup
{
    id: viewSelector

    contentPadding: UM.Theme.getSize("default_lining").width
    contentAlignment: Cura.ExpandablePopup.ContentAlignment.AlignLeft

    property var viewModel: UM.ViewModel
    {
        onDataChanged: updateActiveView()
    }

    property var activeView: null

    function updateActiveView()
    {
        for (var index in viewModel.items)
        {
            if (viewModel.items[index].active)
            {
                activeView = viewModel.items[index]
                return
            }
        }
        activeView = null
    }

    Component.onCompleted:
    {
        if (activeView == null)
        {
            UM.Controller.setActiveView(viewModel.getItem(0).id)
        }
    }

    headerItem: Item
    {
        UM.Label
        {
            id: title
            text: catalog.i18nc("@label", "View type")
            height: parent.height
            elide: Text.ElideRight
            font: UM.Theme.getFont("medium")
            color: UM.Theme.getColor("text_medium")
        }

        UM.Label
        {
            text: viewSelector.activeView ? viewSelector.activeView.name : ""
            anchors
            {
                left: title.right
                leftMargin: UM.Theme.getSize("default_margin").width
                right: parent.right
            }
            height: parent.height
            elide: Text.ElideRight
            font: UM.Theme.getFont("medium")
        }
    }

    contentWidth: viewSelector.width - 2 * viewSelector.contentPadding
    contentItem: Column
    {
        id: viewSelectorPopup

        Repeater
        {
            id: viewsList
            model: viewSelector.viewModel

            delegate: Button
            {
                id: viewsSelectorButton
                text: model.name
                width: parent.width - viewSelectorPopup.leftPadding - viewSelectorPopup.rightPadding
                height: UM.Theme.getSize("action_button").height
                leftPadding: UM.Theme.getSize("default_margin").width
                rightPadding: UM.Theme.getSize("default_margin").width
                checkable: true
                checked: viewSelector.activeView != null ? viewSelector.activeView.id == id : false

                contentItem: UM.Label
                {
                    id: buttonText
                    text: viewsSelectorButton.text
                    font: UM.Theme.getFont("medium")
                    elide: Text.ElideRight
                }

                background: Rectangle
                {
                    id: backgroundRect
                    color: viewsSelectorButton.hovered ? UM.Theme.getColor("action_button_hovered") : "transparent"
                    radius: UM.Theme.getSize("action_button_radius").width
                    border.width: UM.Theme.getSize("default_lining").width
                    border.color: viewsSelectorButton.checked ? UM.Theme.getColor("primary") : "transparent"
                }

                onClicked:
                {
                    toggleContent()
                    UM.Controller.setActiveView(id)
                }
            }
        }
    }
}