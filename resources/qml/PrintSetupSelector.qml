// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.0 as Cura
import "Menus"
import "Menus/ConfigurationMenu"

Cura.ExpandableComponent
{
    id: base

    property int currentModeIndex: -1
    property bool hideSettings: PrintInformation.preSliced

    property string enabledText: catalog.i18nc("@label:Should be short", "On")
    property string disabledText: catalog.i18nc("@label:Should be short", "Off")

    // This widget doesn't show tooltips by itself. Instead it emits signals so others can do something with it.
    signal showTooltip(Item item, point location, string text)
    signal hideTooltip()

    implicitWidth: 200 * screenScaleFactor
    height: childrenRect.height
    iconSource: UM.Theme.getIcon("pencil")

    popupPadding : 0
    popupSpacingY: UM.Theme.getSize("narrow_margin").width

    popupClosePolicy: Popup.CloseOnEscape

    onCurrentModeIndexChanged: UM.Preferences.setValue("cura/active_mode", currentModeIndex)

    Component.onCompleted:
    {
        popupItemWrapper.width = base.width
    }

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    Timer
    {
        id: tooltipDelayTimer
        interval: 500
        repeat: false
        property var item
        property string text

        onTriggered: base.showTooltip(base, {x: 0, y: item.y}, text)
    }

    headerItem: RowLayout
    {
        anchors.fill: parent

        IconWithText
        {
            source: UM.Theme.getIcon("category_layer_height")
            text: Cura.MachineManager.activeStack ? Cura.MachineManager.activeQualityOrQualityChangesName + " " + layerHeight.properties.value + "mm" : ""

            UM.SettingPropertyProvider
            {
                id: layerHeight
                containerStack: Cura.MachineManager.activeStack
                key: "layer_height"
                watchedProperties: ["value"]
            }
        }

        IconWithText
        {
            source: UM.Theme.getIcon("category_infill")
            text: Cura.MachineManager.activeStack ? parseInt(infillDensity.properties.value) + "%" : "0%"

            UM.SettingPropertyProvider
            {
                id: infillDensity
                containerStack: Cura.MachineManager.activeStack
                key: "infill_sparse_density"
                watchedProperties: ["value"]
            }
        }

        IconWithText
        {
            source: UM.Theme.getIcon("category_support")
            text: supportEnabled.properties.value == "True" ? enabledText : disabledText


            UM.SettingPropertyProvider
            {
                id: supportEnabled
                containerStack: Cura.MachineManager.activeMachine
                key: "support_enable"
                watchedProperties: ["value"]
            }
        }

        IconWithText
        {
            source: UM.Theme.getIcon("category_adhesion")
            text: platformAdhesionType.properties.value != "skirt" && platformAdhesionType.properties.value != "none" ? enabledText : disabledText

            UM.SettingPropertyProvider
            {
                id: platformAdhesionType
                containerStack: Cura.MachineManager.activeMachine
                key: "adhesion_type"
                watchedProperties: [ "value"]
            }
        }
    }

    Cura.ExtrudersModel
    {
        id: extrudersModel
    }

    popupItem: Rectangle
    {

        property var totalMargins: UM.Theme.getSize("narrow_margin").height * 11
        property var total_height: popupItemHeader.height + popupItemContent.height + totalMargins
        id: popupItemWrapper
        height: total_height

        border.width: UM.Theme.getSize("default_lining").width
        border.color: UM.Theme.getColor("lining")

        Item
        {
            id: popupItemHeader
            height: 36

            anchors
            {
                top: parent.top
                right: parent.right
                left: parent.left
            }

            Label
            {
                id: popupItemHeaderText
                text: catalog.i18nc("@label", "Print settings");
                font: UM.Theme.getFont("default")
                renderType: Text.NativeRendering
                verticalAlignment: Text.AlignVCenter
                color: UM.Theme.getColor("text")
                height: parent.height

                anchors
                {
                    //topMargin: UM.Theme.getSize("sidebar_margin").height
                    left: parent.left
                    leftMargin: UM.Theme.getSize("narrow_margin").height * 2
                }
            }

            Rectangle
            {
                width: parent.width
                height: UM.Theme.getSize("default_lining").height
                anchors.top: popupItemHeaderText.bottom
                color: UM.Theme.getColor("action_button_border")
            }

            Button
            {
                id: closeButton;
                width: UM.Theme.getSize("message_close").width;
                height: UM.Theme.getSize("message_close").height;

                anchors
                {
                    right: parent.right;
                    rightMargin: UM.Theme.getSize("default_margin").width;
                    top: parent.top;
                    topMargin: 10
                }

                UM.RecolorImage
                {
                    anchors.fill: parent;
                    sourceSize.width: width
                    sourceSize.height: width
                    color: UM.Theme.getColor("message_text")
                    source: UM.Theme.getIcon("cross1")
                }

                onClicked: base.togglePopup() // Will hide the popup item

                background: Rectangle
                {
                    color: UM.Theme.getColor("message_background")
                }
            }
        }

        Rectangle
        {
            id: popupItemContent
            width: parent.width
            height:  globalProfileRow.height  + tabBar.height + UM.Theme.getSize("print_setup_widget").height - UM.Theme.getSize("print_setup_item").height
            anchors
            {
                top: popupItemHeader.bottom
                topMargin: UM.Theme.getSize("default_margin").height * 1.5
                right: parent.right
                left: parent.left
                leftMargin: UM.Theme.getSize("default_margin").width
                rightMargin: UM.Theme.getSize("default_margin").width
            }

            GlobalProfileButton
            {
                id: globalProfileRow
                anchors
                {
                    top: parent.top
                    left: parent.left
                    right: parent.right
                }
            }

            UM.TabRow
            {
                id: tabBar
                anchors.top: globalProfileRow.bottom
                anchors.topMargin: UM.Theme.getSize("default_margin").height * 1.5
                onCurrentIndexChanged: Cura.ExtruderManager.setActiveExtruderIndex(currentIndex)
                z: 1
                Repeater
                {
                    model: extrudersModel
                    delegate: UM.TabRowButton
                    {
                        contentItem: Rectangle
                        {
                            z: 2
                            Cura.ExtruderIcon
                            {
                                anchors.horizontalCenter: parent.horizontalCenter
                                materialColor: model.color
                                extruderEnabled: model.enabled
                                width: parent.height
                                height: parent.height
                            }
                        }

                        background: Rectangle
                        {

                            width: parent.width
                            z: 1
                            border.width: UM.Theme.getSize("default_lining").width * 2
                            border.color: UM.Theme.getColor("action_button_border")

                            visible:
                            {
                                return index == tabBar.currentIndex
                            }

                            // overlap bottom border
                            Rectangle
                            {
                                width: parent.width - UM.Theme.getSize("default_lining").width * 4
                                height: UM.Theme.getSize("default_lining").width * 4
                                anchors.bottom: parent.bottom
                                anchors.bottomMargin: - (UM.Theme.getSize("default_lining").width * 2)
                                anchors.leftMargin: UM.Theme.getSize("default_lining").width * 2
                                anchors.left: parent.left

                            }
                        }
                    }
                }
            }

            Rectangle
            {
                id: sidebarContents
                anchors.top: tabBar.bottom
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                border.width: UM.Theme.getSize("default_lining").width * 2
                border.color: UM.Theme.getColor("action_button_border")

                SidebarSimple
                {
                    anchors.topMargin: UM.Theme.getSize("print_setup_content_top_margin").height
                    anchors.fill: parent
                    visible: currentModeIndex != 1
                    onShowTooltip: base.showTooltip(item, location, text)
                    onHideTooltip: base.hideTooltip()
                }

                SidebarAdvanced
                {
                    anchors.topMargin: Math.round(UM.Theme.getSize("wide_margin").height / 1.7)
                    anchors.bottomMargin: 2 //prevent bottom line overlapping
                    anchors.fill: parent
                    visible: currentModeIndex == 1
                    onShowTooltip: base.showTooltip(item, location, text)
                    onHideTooltip: base.hideTooltip()
                }
            }
        }

        Item
        {
            id: footerControll
            anchors.top: popupItemContent.bottom
            anchors.topMargin: UM.Theme.getSize("narrow_margin").height * 2
            width: parent.width
            Rectangle
            {
                width: parent.width
                height: UM.Theme.getSize("default_lining").height
                color: UM.Theme.getColor("action_button_border")
            }

            Cura.ActionButton
            {
                id: settingControlButton
                visible: currentModeIndex == 0
                text: catalog.i18nc("@button", "Custom")
                width: UM.Theme.getSize("print_setup_action_button").width
                anchors
                {
                    top: parent.top
                    topMargin: UM.Theme.getSize("narrow_margin").height * 2
                    right: parent.right
                    rightMargin: UM.Theme.getSize("narrow_margin").height * 2
                }

                color: UM.Theme.getColor("secondary")
                hoverColor: UM.Theme.getColor("secondary")
                textColor: UM.Theme.getColor("primary")
                textHoverColor: UM.Theme.getColor("text")
                iconSource: UM.Theme.getIcon("arrow_right")
                iconOnRightSide: true

                onClicked: currentModeIndex = 1
            }

            Cura.ActionButton
            {
                height: UM.Theme.getSize("action_panel_button").height
                text: catalog.i18nc("@button", "Recommended")
                color: UM.Theme.getColor("secondary")
                hoverColor: UM.Theme.getColor("secondary")
                textColor: UM.Theme.getColor("primary")
                textHoverColor: UM.Theme.getColor("text")
                iconSource: UM.Theme.getIcon("arrow_left")
                width: UM.Theme.getSize("print_setup_action_button").width
                fixedWidthMode: true

                visible: currentModeIndex == 1
                anchors
                {
                    top: parent.top
                    topMargin: UM.Theme.getSize("narrow_margin").height * 2
                    left: parent.left
                    leftMargin: UM.Theme.getSize("narrow_margin").height * 2
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: currentModeIndex = 0
                }
            }
        }

        Component.onCompleted:
        {
            var index = Math.round(UM.Preferences.getValue("cura/active_mode"))

            if(index != null && !isNaN(index))
            {
                currentModeIndex = index
            }
            else
            {
                currentModeIndex = 0
            }
        }
    }
}