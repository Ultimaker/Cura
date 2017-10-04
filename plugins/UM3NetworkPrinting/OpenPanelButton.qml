import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.1 as UM

Button {
    objectName: "openPanelSaveAreaButton"
    id: openPanelSaveAreaButton

    UM.I18nCatalog { id: catalog; name: "cura"; }

    height: UM.Theme.getSize("save_button_save_to_button").height
    tooltip: catalog.i18nc("@info:tooltip", "Opens the print jobs page with your default web browser.")
    text: catalog.i18nc("@action:button", "View print jobs")

    // FIXME: This button style is copied and duplicated from SaveButton.qml
    style: ButtonStyle {
        background: Rectangle
        {
            border.width: UM.Theme.getSize("default_lining").width
            border.color:
            {
                if(!control.enabled)
                    return UM.Theme.getColor("action_button_disabled_border");
                else if(control.pressed)
                    return UM.Theme.getColor("print_button_ready_pressed_border");
                else if(control.hovered)
                    return UM.Theme.getColor("print_button_ready_hovered_border");
                else
                    return UM.Theme.getColor("print_button_ready_border");
            }
            color:
            {
                if(!control.enabled)
                    return UM.Theme.getColor("action_button_disabled");
                else if(control.pressed)
                    return UM.Theme.getColor("print_button_ready_pressed");
                else if(control.hovered)
                    return UM.Theme.getColor("print_button_ready_hovered");
                else
                    return UM.Theme.getColor("print_button_ready");
            }

            Behavior on color { ColorAnimation { duration: 50; } }

            implicitWidth: actualLabel.contentWidth + (UM.Theme.getSize("sidebar_margin").width * 2)

            Label {
                id: actualLabel
                anchors.centerIn: parent
                color:
                {
                    if(!control.enabled)
                        return UM.Theme.getColor("action_button_disabled_text");
                    else if(control.pressed)
                        return UM.Theme.getColor("print_button_ready_text");
                    else if(control.hovered)
                        return UM.Theme.getColor("print_button_ready_text");
                    else
                        return UM.Theme.getColor("print_button_ready_text");
                }
                font: UM.Theme.getFont("action_button")
                text: control.text;
            }
        }
        label: Item { }
    }


}
