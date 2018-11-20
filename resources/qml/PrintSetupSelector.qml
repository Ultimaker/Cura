// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

import UM 1.2 as UM
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
            text: Cura.MachineManager.activeQualityOrQualityChangesName + " " + layerHeight.properties.value + "mm"

            UM.SettingPropertyProvider
            {
                id: layerHeight
                containerStackId: Cura.MachineManager.activeStackId
                key: "layer_height"
                watchedProperties: ["value"]
            }
        }

        IconWithText
        {
            source: UM.Theme.getIcon("category_infill")
            text: parseInt(infillDensity.properties.value) + "%"

            UM.SettingPropertyProvider
            {
                id: infillDensity
                containerStackId: Cura.MachineManager.activeStackId
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
        property var total_height: popupItemHeader.height + popupItemContent.height + 10 + separator_footer.height
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
                verticalAlignment: Text.AlignVCenter
                color: UM.Theme.getColor("text")
                height: parent.height
                anchors.topMargin: UM.Theme.getSize("sidebar_margin").height
                anchors.bottomMargin: UM.Theme.getSize("sidebar_margin").height
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("print_setup_selector_margin").height
            }

            Rectangle
            {
                width: parent.width
                height: UM.Theme.getSize("default_lining").height
                anchors.top: popupItemHeaderText.bottom
                color: UM.Theme.getColor("action_button_border")


            }
        }

        Rectangle
        {
            id: popupItemContent
            width: parent.width
            height: tabBar.height + sidebarContents.height
            anchors
            {
                top: popupItemHeader.bottom
                topMargin: 10
                right: parent.right
                left: parent.left
                leftMargin: 5
                rightMargin: 5
            }


            TabBar
            {
                id: tabBar
                onCurrentIndexChanged: Cura.ExtruderManager.setActiveExtruderIndex(currentIndex)
                width: parent.width
                height: UM.Theme.getSize("print_setup_tap_bar").width
                z: 1
                Repeater
                {
                    id: extruder_model_repeater
                    model: extrudersModel

                    delegate: TabButton
                    {
                        z: 2
                        width: ListView.view != null ?  Math.round(ListView.view.width / extrudersModel.rowCount()): 0
                        implicitHeight: parent.height

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
                                width: parent.width - 4
                                height: 4
                                anchors.bottom: parent.bottom
                                anchors.bottomMargin: -2
                                anchors.leftMargin: 2
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
                anchors.left: parent.left
                anchors.right: parent.right
                height: UM.Theme.getSize("print_setup_widget").height


                border.width: UM.Theme.getSize("default_lining").width * 2
                border.color: UM.Theme.getColor("action_button_border")

                SidebarSimple
                {
                    anchors.topMargin: UM.Theme.getSize("print_setup_content_top_margin").height
                    id: sidebar_simple_id
                    anchors.fill: parent
                    visible: currentModeIndex != 1
                    onShowTooltip: base.showTooltip(item, location, text)
                    onHideTooltip: base.hideTooltip()
                }

                SidebarAdvanced
                {
                    anchors.topMargin: UM.Theme.getSize("print_setup_content_top_margin").height
                    anchors.bottomMargin: 2 //does not overlap bottom border
                    anchors.fill: parent
                    visible: currentModeIndex == 1
                    onShowTooltip: base.showTooltip(item, location, text)
                    onHideTooltip: base.hideTooltip()
                }

            }
        }


        Item
        {
            id: separator_footer
            anchors.top: popupItemContent.bottom
            anchors.topMargin: 10
            width: parent.width
            height: settingControlButton.height + 4

            Rectangle
            {
                width: parent.width
                height: UM.Theme.getSize("default_lining").height
                color: UM.Theme.getColor("action_button_border")
            }

            Cura.ActionButton
            {
                id: settingControlButton

                leftPadding: UM.Theme.getSize("default_margin").width
                rightPadding: UM.Theme.getSize("default_margin").width
                height: UM.Theme.getSize("action_panel_button").height
                text: catalog.i18nc("@button", "Custom")
                color: UM.Theme.getColor("secondary")
                hoverColor: UM.Theme.getColor("secondary")
                textColor: UM.Theme.getColor("primary")
                textHoverColor: UM.Theme.getColor("text")
                iconSourceRight: UM.Theme.getIcon("arrow_right")
                width: UM.Theme.getSize("print_setup_action_button").width
                fixedWidthMode: true
                visible: currentModeIndex == 0
                anchors
                {
                    top: parent.top
                    topMargin: 10
                    bottomMargin: 10
                    right: parent.right
                    rightMargin: 5
                }

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
                    topMargin: UM.Theme.getSize("print_setup_selector_margin").height * 2
                    bottomMargin: UM.Theme.getSize("print_setup_selector_margin").height * 2
                    left: parent.left
                    leftMargin: UM.Theme.getSize("print_setup_selector_margin").height
                }

                onClicked: currentModeIndex = 0
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