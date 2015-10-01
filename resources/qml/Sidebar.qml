// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM

Rectangle
{
    id: base;

    property Action addMachineAction;
    property Action configureMachinesAction;
    property Action manageProfilesAction;

    color: UM.Theme.colors.sidebar;
    UM.I18nCatalog { id: catalog; name:"cura"}

    function showTooltip(item, position, text)
    {
        tooltip.text = text;
        position = item.mapToItem(base, position.x, position.y / 2);
        tooltip.show(position);
    }

    function hideTooltip()
    {
        tooltip.hide();
    }

    MouseArea
    {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons;

        onWheel:
        {
            wheel.accepted = true;
        }
    }

    SidebarHeader {
        id: header
        width: parent.width
        height: totalHeightHeader

        addMachineAction: base.addMachineAction;
        configureMachinesAction: base.configureMachinesAction;
        modesModel: modesListModel;

        currentModeIndex:
        {
            var index = parseInt(UM.Preferences.getValue("cura/active_mode"))
            if(index)
            {
                return index;
            }
            return 0;
        }
        onCurrentModeIndexChanged: UM.Preferences.setValue("cura/active_mode", currentModeIndex);
    }

    ProfileSetup {
        id: profileItem
        manageProfilesAction: base.manageProfilesAction
        anchors.top: header.bottom
        width: parent.width
        height: totalHeightProfileSetup
    }

    Loader
    {
        id: sidebarContents;
        anchors.bottom: saveButton.top
        anchors.top: profileItem.bottom
        anchors.topMargin: UM.Theme.sizes.default_margin.height
        anchors.left: base.left
        anchors.right: base.right

        source: modesListModel.count > header.currentModeIndex ? modesListModel.get(header.currentModeIndex).file : "";

        property Item sidebar: base;

        onLoaded:
        {
            if(item)
            {
                item.configureSettings = base.configureMachinesAction;
                if(item.onShowTooltip != undefined)
                {
                    item.showTooltip.connect(base.showTooltip)
                }
                if(item.onHideTooltip != undefined)
                {
                    item.hideTooltip.connect(base.hideTooltip)
                }
            }
        }
    }

    SaveButton
    {
        id: saveButton;
        implicitWidth: base.width
        implicitHeight: totalHeight
        anchors.bottom: parent.bottom
    }

    SidebarTooltip
    {
        id: tooltip;
    }

    ListModel
    {
        id: modesListModel;
    }

    Component.onCompleted:
    {
        modesListModel.append({ text: catalog.i18nc("@title:tab", "Simple"), file: "SidebarSimple.qml" })
        modesListModel.append({ text: catalog.i18nc("@title:tab", "Advanced"), file: "SidebarAdvanced.qml" })
        sidebarContents.setSource(modesListModel.get(header.currentModeIndex).file)
    }
}
