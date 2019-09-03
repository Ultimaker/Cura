// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.2 as UM
import Cura 1.6 as Cura

Popup
{
    id: popup
    implicitWidth: 400
    property var dataModel: Cura.IntentCategoryModel {}

    property int defaultMargin: UM.Theme.getSize("default_margin").width
    property color backgroundColor: UM.Theme.getColor("main_background")
    property color borderColor: UM.Theme.getColor("lining")

    padding: 0

    background: Cura.RoundedRectangle
    {
        color: backgroundColor
        border.width: UM.Theme.getSize("default_lining").width
        border.color: borderColor
        cornerSide: Cura.RoundedRectangle.Direction.Down
    }

    ButtonGroup
    {
        id: buttonGroup
        exclusive: true
        onClicked: popup.visible = false
    }

    contentItem: Column
    {
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_lining").width
        anchors.rightMargin: UM.Theme.getSize("default_lining").width
        anchors.right: parent.right
        anchors.top: parent.top

        // This repeater adds the intent labels
        Repeater
        {
            model: dataModel
            delegate: Item
            {
                // We need to set it like that, otherwise we'd have to set the sub model with model: model.qualities
                // Which obviously won't work due to naming conflicts.
                property variant subItemModel: model.qualities

                height: childrenRect.height
                anchors
                {
                    left: parent.left
                    right: parent.right
                }

                Label
                {
                    id: headerLabel
                    text: model.name
                    renderType: Text.NativeRendering
                    height: visible ? contentHeight: 0
                    enabled: false
                    visible: qualitiesList.visibleChildren.length > 0
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                }

                Column
                {
                    id: qualitiesList
                    anchors.top: headerLabel.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right

                    // We set it by means of a binding, since then we can use the when condition, which we need to
                    // prevent a binding loop.
                    Binding
                    {
                        target: parent
                        property: "height"
                        value: parent.childrenRect.height
                        when: parent.visibleChildren.length > 0
                    }

                    // Add the qualities that belong to the intent
                    Repeater
                    {
                        visible: false
                        model: subItemModel
                        MenuButton
                        {
                            id: button

                            onClicked: Cura.IntentManager.selectIntent(model.intent_category, model.quality_type)

                            width: parent.width
                            checkable: true
                            visible: model.available
                            text: model.name + " - " + model.layer_height + " mm"
                            checked:
                            {
                                if(Cura.MachineManager.hasCustomQuality)
                                {
                                    // When user created profile is active, no quality tickbox should be active.
                                    return false
                                }
                                return Cura.MachineManager.activeQualityType == model.quality_type && Cura.MachineManager.activeIntentCategory == model.intent_category
                            }
                            ButtonGroup.group: buttonGroup

                        }
                    }
                }
            }
        }

        Rectangle
        {
            height: 1
            anchors.left: parent.left
            anchors.right: parent.right
            color: borderColor
        }
        MenuButton
        {
            labelText: Cura.Actions.addProfile.text

            anchors.left: parent.left
            anchors.right: parent.right

            enabled: Cura.Actions.addProfile.enabled
            onClicked:
            {
                Cura.Actions.addProfile.trigger()
                popup.visible = false
            }
        }
        MenuButton
        {
            labelText: Cura.Actions.updateProfile.text
            anchors.left: parent.left
            anchors.right: parent.right

            enabled: Cura.Actions.updateProfile.enabled

            onClicked:
            {
                popup.visible = false
                Cura.Actions.updateProfile.trigger()
            }
        }
        MenuButton
        {
            text: catalog.i18nc("@action:button", "Discard current changes")

            anchors.left: parent.left
            anchors.right: parent.right

            enabled: Cura.MachineManager.hasUserSettings

            onClicked:
            {
                popup.visible = false
                Cura.ContainerManager.clearUserContainers()
            }
        }
        Rectangle
        {
            height: 1
            anchors.left: parent.left
            anchors.right: parent.right
            color: borderColor
        }

        MenuButton
        {
            id: manageProfilesButton
            text: Cura.Actions.manageProfiles.text
            anchors
            {
                left: parent.left
                right: parent.right
            }

            height: textLabel.contentHeight + 2 * UM.Theme.getSize("narrow_margin").height

            contentItem: Item
            {
                width: manageProfilesButton.width
                Label
                {
                    id: textLabel
                    text: manageProfilesButton.text
                    height: contentHeight
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width + UM.Theme.getSize("narrow_margin").width
                    verticalAlignment: Text.AlignVCenter
                    renderType: Text.NativeRendering
                }
                Label
                {
                    id: shortcutLabel
                    text: Cura.Actions.manageProfiles.shortcut
                    height: contentHeight
                    anchors.right: parent.right
                    anchors.rightMargin: UM.Theme.getSize("default_margin").width
                    verticalAlignment: Text.AlignVCenter
                    renderType: Text.NativeRendering
                }
            }
            onClicked:
            {
                popup.visible = false
                Cura.Actions.manageProfiles.trigger()
            }
        }
        // spacer
        Item
        {
            width: 2
            height: UM.Theme.getSize("default_radius").width 
        }
    }
}
