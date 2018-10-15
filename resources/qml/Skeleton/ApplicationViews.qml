// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.4 as UM
import Cura 1.0 as Cura


// This item contains the views selector, a combobox that is dynamically created from
// the list of available Views (packages that create different visualizations of the
// scene). Aside from the selector, there is a row of buttons that change the orientation of the view.
Item
{
    id: applicationViewsSelector

    height: UM.Theme.getSize("views_selector").height


    ComboBox
    {
        id: viewModeButton

        anchors
        {
            verticalCenter: parent.verticalCenter
            right: parent.right
            rightMargin: UM.Theme.getSize("default_margin").width
        }

        style: UM.Theme.styles.combobox

        model: UM.ViewModel { }
        textRole: "name"

        // update the model's active index
        function updateItemActiveFlags ()
        {
            currentIndex = getActiveIndex()
            for (var i = 0; i < model.rowCount(); i++)
            {
                model.getItem(i).active = (i == currentIndex)
            }
        }

        // get the index of the active model item on start
        function getActiveIndex ()
        {
            for (var i = 0; i < model.rowCount(); i++)
            {
                if (model.getItem(i).active)
                {
                    return i;
                }
            }
            return 0
        }

        // set the active index
        function setActiveIndex(index)
        {
            UM.Controller.setActiveView(index)
            // the connection to UM.ActiveView will trigger update so there is no reason to call it manually here
        }

        onCurrentIndexChanged:
        {
            if (model.getItem(currentIndex).id != undefined)
            {
                viewModeButton.setActiveIndex(model.getItem(currentIndex).id)
            }
        }
        currentIndex: getActiveIndex()

        // watch the active view proxy for changes made from the menu item
        Connections
        {
            target: UM.ActiveView
            onActiveViewChanged: viewModeButton.updateItemActiveFlags()
        }
    }

    Loader
    {
        id: viewPanel

        anchors.top: viewModeButton.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.right: viewModeButton.right

        property var buttonTarget: Qt.point(viewModeButton.x + Math.round(viewModeButton.width / 2), viewModeButton.y + Math.round(viewModeButton.height / 2))

        height: childrenRect.height
        width: childrenRect.width

        source: UM.ActiveView.valid ? UM.ActiveView.activeViewPanel : ""
    }
}
