// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.2 as UM
import Cura 1.0 as Cura

Cura.ExpandableComponent
{
    id: viewSelector

    iconSource: expanded ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_left")

    property var viewModel: UM.ViewModel { }

    property var activeView:
    {
        for (var i = 0; i < viewModel.rowCount(); i++)
        {
            if (viewModel.items[i].active)
            {
                return viewModel.items[i]
            }
        }
        return null
    }

    Component.onCompleted:
    {
        // Nothing was active, so just return the first one (the list is sorted by priority, so the most
        // important one should be returned)
        if (activeView == null)
        {
            UM.Controller.setActiveView(viewModel.getItem(0).id)
        }
    }

    headerItem: Label
    {
        text: viewSelector.activeView ? viewSelector.activeView.name : ""
        verticalAlignment: Text.AlignVCenter
        height: parent.height
        elide: Text.ElideRight
        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
        renderType: Text.NativeRendering
    }

    popupItem: Column
    {
        id: viewSelectorPopup
        width: viewSelector.width - 2 * UM.Theme.getSize("default_margin").width

        // For some reason the height/width of the column gets set to 0 if this is not set...
        Component.onCompleted:
        {
            height = implicitHeight
            width = viewSelector.width - 2 * UM.Theme.getSize("default_margin").width
        }

        Repeater
        {
            id: viewsList
            model: viewSelector.viewModel
            RoundButton
            {
                text: name
                radius: UM.Theme.getSize("default_radius").width
                checkable: true
                checked: viewSelector.activeView != null ? viewSelector.activeView.id == id : false
                onClicked:
                {
                    viewSelector.togglePopup()
                    UM.Controller.setActiveView(id)
                }
            }
        }

    }
}