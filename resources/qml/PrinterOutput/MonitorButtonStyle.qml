import QtQuick 2.10
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.3

import UM 1.2 as UM
import Cura 1.0 as Cura


Component
{
    ButtonStyle
    {
        background: Rectangle
        {
            border.width: UM.Theme.getSize("default_lining").width
            border.color:
            {
                if(!control.enabled)
                {
                    return UM.Theme.getColor("action_button_disabled_border");
                }
                else if(control.pressed)
                {
                    return UM.Theme.getColor("action_button_active_border");
                }
                else if(control.hovered)
                {
                    return UM.Theme.getColor("action_button_hovered_border");
                }
                return UM.Theme.getColor("action_button_border");
            }
            color:
            {
                if(!control.enabled)
                {
                    return UM.Theme.getColor("action_button_disabled");
                }
                else if(control.pressed)
                {
                    return UM.Theme.getColor("action_button_active");
                }
                else if(control.hovered)
                {
                    return UM.Theme.getColor("action_button_hovered");
                }
                return UM.Theme.getColor("action_button");
            }
            Behavior on color
            {
                ColorAnimation
                {
                    duration: 50
                }
            }
        }

        label: Item
        {
            UM.RecolorImage
            {
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenter: parent.horizontalCenter
                width: Math.floor(control.width / 2)
                height: Math.floor(control.height / 2)
                sourceSize.width: width
                sourceSize.height: width
                color:
                {
                    if(!control.enabled)
                    {
                        return UM.Theme.getColor("action_button_disabled_text");
                    }
                    else if(control.pressed)
                    {
                        return UM.Theme.getColor("action_button_active_text");
                    }
                    else if(control.hovered)
                    {
                        return UM.Theme.getColor("action_button_hovered_text");
                    }
                    return UM.Theme.getColor("action_button_text");
                }
                source: control.iconSource
            }
        }
    }
}
