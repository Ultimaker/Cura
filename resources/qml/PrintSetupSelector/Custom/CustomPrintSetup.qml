// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Controls 1.4 as OldControls
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.6 as Cura
import ".."

Item
{
    id: customPrintSetup

    property real padding: UM.Theme.getSize("default_margin").width
    property bool multipleExtruders: extrudersModel.count > 1

    property var extrudersModel: CuraApplication.getExtrudersModel()

    Item
    {
        id: intent
        height: childrenRect.height

        anchors
        {
            top: parent.top
            topMargin: UM.Theme.getSize("default_margin").height
            left: parent.left
            leftMargin: parent.padding
            right: parent.right
            rightMargin: parent.padding
        }

        Label
        {
            id: profileLabel
            anchors
            {
                top: parent.top
                bottom: parent.bottom
                left: parent.left
                right: intentSelection.left
            }
            text: catalog.i18nc("@label", "Profile")
            font: UM.Theme.getFont("medium")
            renderType: Text.NativeRendering
            color: UM.Theme.getColor("text")
            verticalAlignment: Text.AlignVCenter
        }

        NoIntentIcon
        {
            affected_extruders: Cura.MachineManager.extruderPositionsWithNonActiveIntent
            intent_type: Cura.MachineManager.activeIntentCategory
            anchors.right: intentSelection.left
            anchors.rightMargin: UM.Theme.getSize("narrow_margin").width
            width: Math.round(profileLabel.height * 0.5)
            anchors.verticalCenter: parent.verticalCenter
            height: width
            visible: affected_extruders.length
        }

        Button
        {
            id: intentSelection
            onClicked: menu.opened ? menu.close() : menu.open()

            anchors.right: parent.right
            width: UM.Theme.getSize("print_setup_big_item").width
            height: textLabel.contentHeight + 2 * UM.Theme.getSize("narrow_margin").height
            hoverEnabled: true

            baselineOffset: null // If we don't do this, there is a binding loop. WHich is a bit weird, since we override the contentItem anyway...


            contentItem: RowLayout
            {
                spacing: 0
                anchors.left: parent.left
                anchors.right: customisedSettings.left
                anchors.leftMargin: UM.Theme.getSize("default_margin").width



                Label
                {
                    id: textLabel
                    text: qualityName()
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                    anchors.verticalCenter: intentSelection.verticalCenter
                    Layout.margins: 0
                    Layout.maximumWidth: parent.width * 0.7
                    height: contentHeight
                    verticalAlignment: Text.AlignVCenter
                    renderType: Text.NativeRendering
                    elide: Text.ElideRight

                    function qualityName() {
                        var resultMap = Cura.MachineManager.activeQualityDisplayNameMap
                        return resultMap["main"]
                    }
                }

                Label
                {
                    text: activeQualityDetailText()
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text_detail")
                    anchors.verticalCenter: intentSelection.verticalCenter
                    Layout.margins: 0
                    Layout.fillWidth: true

                    height: contentHeight
                    verticalAlignment: Text.AlignVCenter
                    renderType: Text.NativeRendering
                    elide: Text.ElideRight

                    function activeQualityDetailText()
                    {
                        var resultMap = Cura.MachineManager.activeQualityDisplayNameMap
                        var resultSuffix = resultMap["suffix"]
                        var result = ""

                        if (Cura.MachineManager.isActiveQualityExperimental)
                        {
                            resultSuffix += " (Experimental)"
                        }

                        if (Cura.MachineManager.isActiveQualitySupported)
                        {
                            if (Cura.MachineManager.activeQualityLayerHeight > 0)
                            {
                                if (resultSuffix)
                                {
                                    result += " - "
                                }
                                if (resultSuffix)
                                {
                                    result +=  resultSuffix
                                }
                                result += " - "
                                result += Cura.MachineManager.activeQualityLayerHeight + "mm"
                            }
                        }

                        return result
                    }
                }




            }

            background: Rectangle
            {
                id: backgroundItem
                border.color: intentSelection.hovered ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_border")
                border.width: UM.Theme.getSize("default_lining").width
                radius: UM.Theme.getSize("default_radius").width
                color: UM.Theme.getColor("main_background")
            }

            UM.SimpleButton
            {
                id: customisedSettings

                visible: Cura.MachineManager.hasUserSettings
                width: UM.Theme.getSize("print_setup_icon").width
                height: UM.Theme.getSize("print_setup_icon").height

                anchors.verticalCenter: parent.verticalCenter
                anchors.right: downArrow.left
                anchors.rightMargin: UM.Theme.getSize("default_margin").width

                color: hovered ? UM.Theme.getColor("setting_control_button_hover") : UM.Theme.getColor("setting_control_button");
                iconSource: UM.Theme.getIcon("star")

                onClicked:
                {
                    forceActiveFocus();
                    Cura.Actions.manageProfiles.trigger()
                }
                onEntered:
                {
                    var content = catalog.i18nc("@tooltip", "Some setting/override values are different from the values stored in the profile.\n\nClick to open the profile manager.")
                    base.showTooltip(intent, Qt.point(-UM.Theme.getSize("default_margin").width, 0), content)
                }
                onExited: base.hideTooltip()
            }
            UM.RecolorImage
            {
                id: downArrow


                source: UM.Theme.getIcon("arrow_bottom")
                width: UM.Theme.getSize("standard_arrow").width
                height: UM.Theme.getSize("standard_arrow").height

                anchors
                {
                    right: parent.right
                    verticalCenter: parent.verticalCenter
                    rightMargin: UM.Theme.getSize("default_margin").width
                }

                color: UM.Theme.getColor("setting_control_button")
            }
        }

        QualitiesWithIntentMenu
        {
            id: menu
            y: intentSelection.y + intentSelection.height
            x: intentSelection.x
            width: intentSelection.width
        }
    }

    UM.TabRow
    {
        id: tabBar

        visible: multipleExtruders  // The tab row is only visible when there are more than 1 extruder

        anchors
        {
            top: intent.bottom
            topMargin: UM.Theme.getSize("default_margin").height
            left: parent.left
            leftMargin: parent.padding
            right: parent.right
            rightMargin: parent.padding
        }

        Repeater
        {
            id: repeater
            model: extrudersModel
            delegate: UM.TabRowButton
            {
                contentItem: Item
                {
                    Cura.ExtruderIcon
                    {
                        anchors.horizontalCenter: parent.horizontalCenter
                        materialColor: model.color
                        extruderEnabled: model.enabled
                    }
                }
                onClicked:
                {
                    Cura.ExtruderManager.setActiveExtruderIndex(tabBar.currentIndex)
                }
            }
        }

        //When active extruder changes for some other reason, switch tabs.
        //Don't directly link currentIndex to Cura.ExtruderManager.activeExtruderIndex!
        //This causes a segfault in Qt 5.11. Something with VisualItemModel removing index -1. We have to use setCurrentIndex instead.
        Connections
        {
            target: Cura.ExtruderManager
            onActiveExtruderChanged:
            {
                tabBar.setCurrentIndex(Cura.ExtruderManager.activeExtruderIndex);
            }
        }

        //When the model of the extruders is rebuilt, the list of extruders is briefly emptied and rebuilt.
        //This causes the currentIndex of the tab to be in an invalid position which resets it to 0.
        //Therefore we need to change it back to what it was: The active extruder index.
        Connections
        {
            target: repeater.model
            onModelChanged:
            {
                tabBar.setCurrentIndex(Cura.ExtruderManager.activeExtruderIndex)
            }
        }
    }

    Rectangle
    {
        anchors
        {
            top: tabBar.visible ? tabBar.bottom : intent.bottom
            topMargin: -UM.Theme.getSize("default_lining").width
            left: parent.left
            leftMargin: parent.padding
            right: parent.right
            rightMargin: parent.padding
            bottom: parent.bottom
        }
        z: tabBar.z - 1
        // Don't show the border when only one extruder

        border.color: tabBar.visible ? UM.Theme.getColor("lining") : "transparent"
        border.width: UM.Theme.getSize("default_lining").width

        color: UM.Theme.getColor("main_background")
        Cura.SettingView
        {
            anchors
            {
                fill: parent
                topMargin: UM.Theme.getSize("default_margin").height
                leftMargin: UM.Theme.getSize("default_margin").width
                // Small space for the scrollbar
                rightMargin: UM.Theme.getSize("narrow_margin").width
                // Compensate for the negative margin in the parent
                bottomMargin: UM.Theme.getSize("default_lining").width
            }
        }
    }
}
