import QtQuick 2.0
import QtQuick.Controls 2.3
import Cura 1.6 as Cura

import UM 1.2 as UM
Popup
{
    id: popup
    implicitWidth: 400
    property var dataModel: Cura.IntentCategoryModel {}

    property int defaultMargin: 5
    property int checkmarkSize: 12
    property int buttonHeight: 25
    property color backgroundColor: "#f2f2f2"
    property color borderColor: "#cccccc"
    padding: 0

    background: Rectangle
    {
        color: backgroundColor
        border.width: 1
        border.color: borderColor
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
        anchors.right: parent.right
        anchors.top: parent.top

        height: childrenRect.height

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
                    leftMargin: defaultMargin
                    right: parent.right
                    rightMargin: defaultMargin
                }

                Label
                {
                    id: headerLabel
                    text: model.name
                    height: visible ? contentHeight: 0
                    enabled: false
                    visible: qualitiesList.visibleChildren.length > 0
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
                        when: parent.visibleChildren.lengt > 0
                    }

                    // Add the qualities that belong to the intent
                    Repeater
                    {
                        visible: false
                        model: subItemModel
                        Button
                        {
                            id: button

                            onClicked: Cura.IntentManager.selectIntent(model.intent_category, model.quality_type)

                            width: parent.width
                            height: buttonHeight
                            checkable: true
                            visible: model.available
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
                            background: Item {}
                            contentItem: Item
                            {
                                Rectangle
                                {
                                    id: checkmark
                                    width: checkmarkSize
                                    height: checkmarkSize
                                    anchors.verticalCenter: parent.verticalCenter
                                    color: "black"
                                    visible: button.checked
                                }

                                Label
                                {
                                    id: label
                                    text: model.name + " - " + model.layer_height + " mm"
                                    verticalAlignment: Text.AlignVCenter
                                    anchors
                                    {
                                        left: checkmark.right
                                        leftMargin: defaultMargin
                                        top: parent.top
                                        bottom: parent.bottom
                                        right: parent.right
                                    }
                                }
                            }
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
        Button
        {
            text: Cura.Actions.addProfile.text

            anchors.left: parent.left
            anchors.leftMargin: defaultMargin

            enabled: Cura.Actions.addProfile.enabled
            background: Item {}
            onClicked:
            {
                Cura.Actions.addProfile.trigger()
                popup.visible = false
            }

        }
        Button
        {
            text: Cura.Actions.updateProfile.text

            anchors.left: parent.left
            anchors.leftMargin: defaultMargin

            enabled: Cura.Actions.updateProfile.enabled
            background: Item {}
            onClicked:
            {
                popup.visible = false
                Cura.Actions.updateProfile.trigger()
            }
        }
        Button
        {
            text: catalog.i18nc("@action:button", "Discard current changes")

            anchors.left: parent.left
            anchors.leftMargin: defaultMargin

            enabled: Cura.MachineManager.hasUserSettings
            background: Item {}
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
        Button
        {
            id: manageProfilesButton
            text: Cura.Actions.manageProfiles.text
            anchors
            {
                left: parent.left
                leftMargin: defaultMargin
                right: parent.right
                rightMargin: defaultMargin
            }

            height: textLabel.contentHeight + 2 * UM.Theme.getSize("narrow_margin").height
            background: Item {}
            contentItem: Item
            {
                width: manageProfilesButton.width
                Label
                {
                    id: textLabel
                    text: manageProfilesButton.text
                    height: contentHeight
                }
                Label
                {
                    id: shortcutLabel
                    text: Cura.Actions.manageProfiles.shortcut
                    anchors.right: parent.right
                }
            }
            onClicked:
            {
                popup.visible = false
                Cura.Actions.manageProfiles.trigger()
            }
        }
    }
}
