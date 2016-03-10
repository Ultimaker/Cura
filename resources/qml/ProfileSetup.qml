// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM

Item{
    id: base;
    UM.I18nCatalog { id: catalog; name:"cura"}
    property int totalHeightProfileSetup: childrenRect.height
    property Action manageProfilesAction
    property Action addProfileAction

    Rectangle{
        id: globalProfileRow
        anchors.top: base.top
        height: UM.Theme.getSize("sidebar_setup").height
        width: base.width

        Label{
            id: globalProfileLabel
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width;
            anchors.verticalCenter: parent.verticalCenter
            text: catalog.i18nc("@label","Profile:");
            width: parent.width/100*45
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
        }

        ToolButton {
            property int rightMargin: customisedSettings.visible ? customisedSettings.width + UM.Theme.getSize("default_margin").width / 2 : 0

            id: globalProfileSelection
            text: UM.MachineManager.activeProfile
            width: parent.width/100*55
            height: UM.Theme.getSize("setting_control").height
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: parent.verticalCenter
            tooltip: UM.MachineManager.activeProfile
            style: UM.Theme.styles.sidebar_header_button

            menu: Menu
            {
                id: profileSelectionMenu
                Instantiator
                {
                    id: profileSelectionInstantiator
                    model: UM.ProfilesModel { addSeparators: true }
                    Loader {
                        property QtObject model_data: model
                        property int model_index: index
                        sourceComponent: model.separator ? menuSeparatorDelegate : menuItemDelegate
                    }
                    onObjectAdded: profileSelectionMenu.insertItem(index, object.item)
                    onObjectRemoved: profileSelectionMenu.removeItem(object.item)
                }
                ExclusiveGroup { id: profileSelectionMenuGroup; }
                Component
                {
                    id: menuSeparatorDelegate
                    MenuSeparator {
                        id: item
                    }
                }
                Component
                {
                    id: menuItemDelegate
                    MenuItem
                    {
                        id: item
                        text: model_data.name
                        checkable: true;
                        checked: model_data.active;
                        exclusiveGroup: profileSelectionMenuGroup;
                        onTriggered:
                        {
                            UM.MachineManager.setActiveProfile(model_data.name);
                            if (!model_data.active) {
                                //Selecting a profile was canceled; undo menu selection
                                profileSelectionInstantiator.model.setProperty(model_index, "active", false);
                                var activeProfileName = UM.MachineManager.activeProfile;
                                var activeProfileIndex = profileSelectionInstantiator.model.find("name", activeProfileName);
                                profileSelectionInstantiator.model.setProperty(activeProfileIndex, "active", true);
                            }
                        }
                    }
                }


                MenuSeparator { }
                MenuItem {
                    action: base.addProfileAction;
                }
                MenuItem {
                    action: base.manageProfilesAction;
                }
            }
        }
        UM.SimpleButton {
            id: customisedSettings

            visible: UM.ActiveProfile.hasCustomisedValues
            height: parent.height * 0.6
            width: parent.height * 0.6

            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("setting_preferences_button_margin").width

            color: hovered ? UM.Theme.getColor("setting_control_button_hover") : UM.Theme.getColor("setting_control_button");
            iconSource: UM.Theme.getIcon("star");

            onClicked: base.manageProfilesAction.trigger()
        }
    }
}
