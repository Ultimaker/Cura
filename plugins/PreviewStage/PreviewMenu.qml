// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7

import QtQuick.Controls 2.4

import UM 1.3 as UM
import Cura 1.1 as Cura

Item
{
    id: previewMenu
    // This widget doesn't show tooltips by itself. Instead it emits signals so others can do something with it.
    signal showTooltip(Item item, point location, string text)
    signal hideTooltip()

    property real itemHeight: height - 2 * UM.Theme.getSize("default_lining").width

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    Rectangle
    {
        anchors.fill: stageMenu
        anchors.leftMargin: -radius
        radius: UM.Theme.getSize("default_radius").width
        color: UM.Theme.getColor("toolbar_background")
    }

    Item
    {
        id: stageMenu
        height: parent.height
        width: childrenRect.width + UM.Theme.getSize("default_margin").width
        anchors.horizontalCenter: parent.horizontalCenter
        Row
        {
            anchors.centerIn: parent
            //spacing: UM.Theme.getSize("default_margin").width
            height: parent.height

            Cura.ExpandableComponent
            {
                id: viewSelector
                iconSource: expanded ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_left")
                height: parent.height

                property var viewModel: UM.ViewModel { }

                property var activeView:
                {
                    for (var i = 0; i < viewModel.rowCount(); i++)
                    {
                        if(viewModel.getItem(i).active)
                        {
                            return viewModel.getItem(i)
                        }
                    }
                    // Nothing was active, so just return the first one (the list is sorted by priority, so the most
                    // important one sshould be returned)
                    return viewModel.getItem(0)
                }

                // Ensure that the controller is synced with whatever happend here.
                onActiveViewChanged: UM.Controller.setActiveView(activeView.id)

                headerItem: Label
                {
                    text: viewSelector.activeView.name
                    verticalAlignment: Text.AlignVCenter
                    height: parent.height
                    elide: Text.ElideRight
                    font: UM.Theme.getFont("default")
                }

                popupItem: Column
                {
                    id: column
                    width: viewSelector.width - 2 * UM.Theme.getSize("default_margin").width

                    // For some reason the height of the column gets set to 0 if this is not set...
                    Component.onCompleted: height = implicitHeight

                    Repeater
                    {
                        id: networkedPrinters
                        model: viewSelector.viewModel
                        RoundButton
                        {
                            text: name
                            radius: UM.Theme.getSize("default_radius").width
                            checkable: true
                            checked: active
                            onClicked: UM.Controller.setActiveView(id)
                        }
                    }

                }
            }

            // Separator line
            Rectangle
            {
                height: parent.height
                // If there is no viewPanel, we only need a single spacer, so hide this one.
                visible: viewPanel.source != ""
                width: visible ? UM.Theme.getSize("default_lining").width : 0

                color: UM.Theme.getColor("lining")
            }

            Loader
            {
                // TODO: Make this panel collapsable and ensure it has a standardised background.
                id: viewPanel

                //property var buttonTarget: Qt.point(viewModeButton.x + Math.round(viewModeButton.width / 2), viewModeButton.y + Math.round(viewModeButton.height / 2))

                height: parent.height
                width: childrenRect.width

                source: UM.Controller.activeView != null && UM.Controller.activeView.stageMenuComponent != null ? UM.Controller.activeView.stageMenuComponent : ""
            }

            // Separator line
            Rectangle
            {
                height: parent.height
                width: UM.Theme.getSize("default_lining").width
                color: UM.Theme.getColor("lining")
            }

            Cura.PrintSetupSelector
            {
                width: UM.Theme.getSize("print_setup_widget").width
                height: parent.height
                onShowTooltip: previewMenu.showTooltip(item, location, text)
                onHideTooltip: previewMenu.hideTooltip()
            }
        }
    }
}