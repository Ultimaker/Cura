// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

import UM 1.2 as UM
import Cura 1.0 as Cura
import "Menus"
import "Menus/ConfigurationMenu"

Rectangle
{
    id: base

    height: childrenRect.height

    property int currentModeIndex: -1
    property bool hideSettings: PrintInformation.preSliced

    property variant printDuration: PrintInformation.currentPrintTime
    property variant printMaterialLengths: PrintInformation.materialLengths
    property variant printMaterialWeights: PrintInformation.materialWeights
    property variant printMaterialCosts: PrintInformation.materialCosts
    property variant printMaterialNames: PrintInformation.materialNames

    color: UM.Theme.getColor("sidebar")
    UM.I18nCatalog { id: catalog; name:"cura"}

    // This widget doesn't show tooltips by itself. Instead it emits signals so others can do something with it.
    signal showTooltip(Item item, point location, string text)
    signal hideTooltip()

    Timer
    {
        id: tooltipDelayTimer
        interval: 500
        repeat: false
        property var item
        property string text

        onTriggered:
        {
            base.showTooltip(base, {x: 0, y: item.y}, text);
        }
    }

    function strPadLeft(string, pad, length)
    {
        return (new Array(length + 1).join(pad) + string).slice(-length);
    }

    function getPrettyTime(time)
    {
        var hours = Math.floor(time / 3600)
        time -= hours * 3600
        var minutes = Math.floor(time / 60);
        time -= minutes * 60
        var seconds = Math.floor(time);

        var finalTime = strPadLeft(hours, "0", 2) + ':' + strPadLeft(minutes,'0',2)+ ':' + strPadLeft(seconds,'0',2);
        return finalTime;
    }

    MouseArea
    {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons

        onWheel:
        {
            wheel.accepted = true;
        }
    }

    onCurrentModeIndexChanged:
    {
        UM.Preferences.setValue("cura/active_mode", currentModeIndex);
    }

    Label
    {
        id: settingsModeLabel
        text: !hideSettings ? catalog.i18nc("@label:listbox", "Print Setup") : catalog.i18nc("@label:listbox", "Print Setup disabled\nG-code files cannot be modified")
        renderType: Text.NativeRendering

        anchors
        {
            left: parent.left
            top: parent.top
            margins: UM.Theme.getSize("sidebar_margin").width
        }

        width: Math.round(parent.width * 0.45)
        height: contentHeight
        font: UM.Theme.getFont("large")
        color: UM.Theme.getColor("text")
    }


    ListView
    {
        // Settings mode selection toggle
        id: settingsModeSelection
        model: modesListModel
        width: Math.round(parent.width * 0.55)
        height: UM.Theme.getSize("sidebar_header_mode_toggle").height

        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.getSize("sidebar_margin").width

        anchors.top: settingsModeLabel.top

        ButtonGroup
        {
            id: modeMenuGroup
        }

        delegate: Button
        {
            id: control

            height: settingsModeSelection.height
            width: Math.round(parent.width / 2)

            anchors.left: parent.left
            anchors.leftMargin: model.index * Math.round(settingsModeSelection.width / 2)
            anchors.verticalCenter: parent.verticalCenter

            ButtonGroup.group: modeMenuGroup

            checkable: true
            checked: base.currentModeIndex == index
            onClicked: base.currentModeIndex = index

            onHoveredChanged:
            {
                if (hovered)
                {
                    tooltipDelayTimer.item = settingsModeSelection
                    tooltipDelayTimer.text = model.tooltipText
                    tooltipDelayTimer.start()
                }
                else
                {
                    tooltipDelayTimer.stop()
                    base.hideTooltip()
                }
            }

            background: Rectangle
            {
                border.width: control.checked ? UM.Theme.getSize("default_lining").width * 2 : UM.Theme.getSize("default_lining").width
                border.color: (control.checked || control.pressed) ? UM.Theme.getColor("action_button_active_border") : control.hovered ? UM.Theme.getColor("action_button_hovered_border"): UM.Theme.getColor("action_button_border")

                // for some reason, QtQuick decided to use the color of the background property as text color for the contentItem, so here it is
                color: (control.checked || control.pressed) ? UM.Theme.getColor("action_button_active") : control.hovered ? UM.Theme.getColor("action_button_hovered") : UM.Theme.getColor("action_button")
            }

            contentItem: Label
            {
                text: model.text
                font: UM.Theme.getFont("default")
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                renderType: Text.NativeRendering
                elide: Text.ElideRight
                color:
                {
                    if(control.pressed)
                    {
                        return UM.Theme.getColor("action_button_active_text");
                    }
                    else if(control.hovered)
                    {
                        return UM.Theme.getColor("action_button_hovered_text");
                    }
                    return UM.Theme.getColor("action_button_text");
                }
            }
        }
    }

    Item
    {
        id: sidebarContents
        anchors.top: settingsModeSelection.bottom
        anchors.topMargin: UM.Theme.getSize("sidebar_margin").height
        anchors.left: parent.left
        anchors.right: parent.right
        height: 500

        // We load both of them at once (instead of using a loader) because the advanced sidebar can take
        // quite some time to load. So in this case we sacrifice memory for speed.
        SidebarAdvanced
        {
            anchors.fill: parent
            visible: currentModeIndex == 1
            onShowTooltip: base.showTooltip(item, location, text)
            onHideTooltip: base.hideTooltip()
        }

        SidebarSimple
        {
            anchors.fill: parent
            visible: currentModeIndex != 1
            onShowTooltip: base.showTooltip(item, location, text)
            onHideTooltip: base.hideTooltip()
        }
    }

    // Setting mode: Recommended or Custom
    ListModel
    {
        id: modesListModel
    }

    Component.onCompleted:
    {
        modesListModel.append({
            text: catalog.i18nc("@title:tab", "Recommended"),
            tooltipText: catalog.i18nc("@tooltip", "<b>Recommended Print Setup</b><br/><br/>Print with the recommended settings for the selected printer, material and quality.")
        })
        modesListModel.append({
            text: catalog.i18nc("@title:tab", "Custom"),
            tooltipText: catalog.i18nc("@tooltip", "<b>Custom Print Setup</b><br/><br/>Print with finegrained control over every last bit of the slicing process.")
        })

        var index = Math.round(UM.Preferences.getValue("cura/active_mode"))

        if(index != null && !isNaN(index))
        {
            currentModeIndex = index;
        }
        else
        {
            currentModeIndex = 0;
        }
    }
}
