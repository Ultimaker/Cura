// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM


Item
{
    id: base

    property var active: false
    property var complete: false

    property var readyLabel: catalog.i18nc("@action:button", "Install")
    property var activeLabel: catalog.i18nc("@action:button", "Cancel")
    property var completeLabel: catalog.i18nc("@action:button", "Installed")

    property var readyAction: null          // Action when button is ready and clicked (likely install)
    property var activeAction: null         // Action when button is active and clicked (likely cancel)
    property var completeAction: null       // Action when button is complete and clicked (likely go to installed)

    width: UM.Theme.getSize("toolbox_action_button").width
    height: UM.Theme.getSize("toolbox_action_button").height

    Button
    {
        id: button
        text:
        {
            if (complete)
            {
                return completeLabel
            }
            else if (active)
            {
                return activeLabel
            }
            else
            {
                return readyLabel
            }
        }
        onClicked:
        {
            if (complete)
            {
                return completeAction()
            }
            else if (active)
            {
                return activeAction()
            }
            else
            {
                return readyAction()
            }
        }
        style: ButtonStyle
        {
            background: Rectangle
            {
                implicitWidth: UM.Theme.getSize("toolbox_action_button").width
                implicitHeight: UM.Theme.getSize("toolbox_action_button").height
                color:
                {
                    if (base.complete)
                    {
                        return UM.Theme.getColor("action_button_disabled")
                    }
                    else
                    {
                        if (control.hovered)
                        {
                            return UM.Theme.getColor("primary_hover")
                        }
                        else
                        {
                            return UM.Theme.getColor("primary")
                        }
                    }
                }
            }
            label: Label
            {
                text: control.text
                color:
                {
                    if (base.complete)
                    {
                        return UM.Theme.getColor("action_button_disabled_text")
                    }
                    else
                    {
                        if (control.hovered)
                        {
                            return UM.Theme.getColor("button_text_hover")
                        }
                        else
                        {
                            return UM.Theme.getColor("button_text")
                        }
                    }
                }
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font: UM.Theme.getFont("default_bold")
            }
        }
    }

    AnimatedImage
    {
        id: loader
        visible: active
        source: "../images/loading.gif"
        width: UM.Theme.getSize("toolbox_loader").width
        height: UM.Theme.getSize("toolbox_loader").height
        anchors.right: button.left
        anchors.rightMargin: UM.Theme.getSize("default_margin").width
        anchors.verticalCenter: button.verticalCenter
    }
}
