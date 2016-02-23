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
                    model: UM.ProfilesModel { }
                    MenuItem
                    {
                        text: model.name
                        checkable: true;
                        checked: model.active;
                        exclusiveGroup: profileSelectionMenuGroup;
                        onTriggered:
                        {
                            UM.MachineManager.setActiveProfile(model.name);
                            if (!model.active) {
                                //Selecting a profile was canceled; undo menu selection
                                profileSelectionInstantiator.model.setProperty(index, "active", false);
                                var activeProfileName = UM.MachineManager.activeProfile;
                                var activeProfileIndex = profileSelectionInstantiator.model.find("name", activeProfileName);
                                profileSelectionInstantiator.model.setProperty(activeProfileIndex, "active", true);
                            }
                        }
                    }
                    onObjectAdded: profileSelectionMenu.insertItem(index, object)
                    onObjectRemoved: profileSelectionMenu.removeItem(object)
                }
                ExclusiveGroup { id: profileSelectionMenuGroup; }

                MenuSeparator { }
                MenuItem {
                    action: base.addProfileAction;
                }
                MenuItem {
                    action: base.manageProfilesAction;
                }
            }
        }
    }
}
