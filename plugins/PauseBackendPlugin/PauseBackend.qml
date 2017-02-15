import UM 1.2 as UM
import Cura 1.0 as Cura

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

Item
{
    id: base

    Button
    {
        id: pauseResumeButton
        objectName: "pauseResumeButton"

        property bool paused: false

        height: UM.Theme.getSize("save_button_save_to_button").height
        width: height

        tooltip: paused ? catalog.i18nc("@info:tooltip", "Resume automatic slicing") : catalog.i18nc("@info:tooltip", "Pause automatic slicing")

        style: ButtonStyle {
            background: Rectangle {
                border.width: UM.Theme.getSize("default_lining").width
                border.color: !control.enabled ? UM.Theme.getColor("action_button_disabled_border") :
                                  control.pressed ? UM.Theme.getColor("action_button_active_border") :
                                  control.hovered ? UM.Theme.getColor("action_button_hovered_border") : UM.Theme.getColor("action_button_border")
                color: !control.enabled ? UM.Theme.getColor("action_button_disabled") :
                           control.pressed ? UM.Theme.getColor("action_button_active") :
                           control.hovered ? UM.Theme.getColor("action_button_hovered") : UM.Theme.getColor("action_button")
                Behavior on color { ColorAnimation { duration: 50; } }
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("save_button_text_margin").width / 2;
                width: parent.height
                height: parent.height

                UM.RecolorImage {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: parent.width / 2
                    height: parent.height / 2
                    sourceSize.width: width
                    sourceSize.height: height
                    color: !control.enabled ? UM.Theme.getColor("action_button_disabled_text") :
                               control.pressed ? UM.Theme.getColor("action_button_active_text") :
                               control.hovered ? UM.Theme.getColor("action_button_hovered_text") : UM.Theme.getColor("action_button_text");
                    source: pauseResumeButton.paused ? "play.svg" : "pause.svg"
                }
            }
            label: Label{ }
        }

        onClicked:
        {
            paused = !paused
            if(paused)
            {
                manager.pauseBackend()
            }
            else
            {
                manager.resumeBackend()
            }
        }
    }

    UM.I18nCatalog{id: catalog; name:"cura"}
}