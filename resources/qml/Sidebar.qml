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
        id: header;

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

    Item
    {
        id: variantItem;

        anchors.top: header.bottom;
        height: UM.Theme.sizes.setting.height;

        visible: UM.MachineManager.hasVariants;

        Row
        {
            spacing: UM.Theme.sizes.default_margin.width;
            Label
            {
                anchors.verticalCenter: parent.verticalCenter;
                text: catalog.i18nc("@label","Variant");
            }

            ComboBox {
                anchors.verticalCenter: parent.verticalCenter;
                model: UM.MachineVariantsModel { }
                textRole: "name"
                onActivated: UM.MachineManager.setActiveMachineVariant(model.getItem(index).name);

                currentIndex:
                {
                    for(var i = 0; i < model.rowCount(); ++i)
                    {
                        if(model.getItem(i).name == UM.MachineManager.activeMachineVariant)
                        {
                            return i;
                        }
                    }

                    return 0;
                }
            }
        }
    }

    Item
    {
        id: profileItem;

        anchors.top: variantItem.bottom;
        height: UM.Theme.sizes.setting.height;

        Row
        {
            spacing: UM.Theme.sizes.default_margin.width;
            Label
            {
                anchors.verticalCenter: parent.verticalCenter;
                text: "Global Profile";
            }

            ComboBox
            {
                anchors.verticalCenter: parent.verticalCenter;
                model: UM.ProfilesModel { }
                textRole: "name"
                onActivated: UM.MachineManager.setActiveProfile(model.getItem(index).name)

                currentIndex:
                {
                    for(var i = 0; i < model.rowCount(); ++i)
                    {
                        if(model.getItem(i).name == UM.MachineManager.activeProfile)
                            return i;
                    }

                    return 0;
                }
            }

            Button
            {
                text: catalog.i18nc("@action:button", "Save");
            }
        }
    }

    Loader
    {
        id: sidebarContents;
        anchors.bottom: saveButton.top
        anchors.top: profileItem.bottom
        anchors.left: base.left
        anchors.right: base.right

        source: modesListModel.get(header.currentModeIndex).file;

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
        //: Simple configuration mode option
        ListElement { text: QT_TR_NOOP("Simple"); file: "SidebarSimple.qml" }
        //: Advanced configuration mode option
        ListElement { text: QT_TR_NOOP("Advanced"); file: "SidebarAdvanced.qml" }
    }

    Component.onCompleted:
    {
        for(var i = 0; i < modesListModel.count; ++i)
        {
            modesListModel.setProperty(i, "text", catalog.i18nc("@label", modesListModel.get(i).text));
        }
    }
}
