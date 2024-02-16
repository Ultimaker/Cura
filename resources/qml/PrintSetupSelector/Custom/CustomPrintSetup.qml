//Copyright (c) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
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

        UM.Label
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
        }

        Button
        {
            id: intentSelection
            onClicked: menu.opened ? menu.close() : menu.open()

            // Anchoring to the right makes much more sense here, but for some reason this component compresses from the right
            // and then expands from the left afterwards. This pushes it left by profileWarningReset.width
            // The solution is to anchor from the other direction so this does not happen.
            anchors.left: parent.left
            // This leftMargin gives us the same spacing as anchoring to the right on profileWarningReset
            anchors.leftMargin: parent.width - UM.Theme.getSize("print_setup_big_item").width
            width: profileWarningReset.visible ? UM.Theme.getSize("print_setup_big_item").width - profileWarningReset.width  - UM.Theme.getSize("default_margin").width : UM.Theme.getSize("print_setup_big_item").width
            height: textLabel.contentHeight + 2 * UM.Theme.getSize("narrow_margin").height
            hoverEnabled: true

            contentItem: RowLayout
            {
                spacing: 0
                anchors.left: parent.left
                anchors.right: customisedSettings.left
                anchors.leftMargin: UM.Theme.getSize("default_margin").width

                UM.Label
                {
                    id: textLabel
                    text: Cura.MachineManager.activeQualityDisplayNameMainStringParts.join(" - ")
                    Layout.margins: 0
                    Layout.maximumWidth: Math.floor(parent.width * 0.7)  // Always leave >= 30% for the rest of the row.
                    height: contentHeight
                    elide: Text.ElideRight
                    wrapMode: Text.NoWrap
                }

                UM.Label
                {
                    text:
                    {
                        const string_parts = Cura.MachineManager.activeQualityDisplayNameTailStringParts;
                        if (string_parts.length === 0)
                        {
                            return "";
                        }
                        else
                        {
                            ` - ${string_parts.join(" - ")}`
                        }
                    }

                    color: UM.Theme.getColor("text_detail")
                    Layout.margins: 0
                    Layout.fillWidth: true

                    height: contentHeight
                    elide: Text.ElideRight
                    wrapMode: Text.NoWrap
                }
            }

            background: UM.UnderlineBackground
            {
                id: backgroundItem
                liningColor: intentSelection.hovered ? UM.Theme.getColor("text_field_border_hovered") : UM.Theme.getColor("border_field_light")
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
                iconSource: UM.Theme.getIcon("StarFilled")

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
            UM.ColorImage
            {
                id: downArrow

                source: UM.Theme.getIcon("ChevronSingleDown")
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

        ProfileWarningReset
        {
            id: profileWarningReset
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            fullWarning: false
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
                checked: model.index == 0
                contentItem: Item
                {
                    Cura.ExtruderIcon
                    {
                        anchors.centerIn: parent
                        materialColor: model.color
                        extruderEnabled: model.enabled
                        iconVariant: "default"
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
            function onActiveExtruderChanged()
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
            function onModelChanged()
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
