import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

UM.AngledCornerRectangle {
    id: base;

    property Action addMachineAction;
    property Action configureMachinesAction;
    property alias saveAction: saveButton.saveAction;

    cornerSize: UM.Theme.sizes.default_margin.width;
    
    function showTooltip(item, position, text) {
        tooltip.text = text;
        position = item.mapToItem(base, position.x, position.y);
        tooltip.show(position);
    }

    function hideTooltip() {
        tooltip.hide();
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons;

        onWheel: {
            wheel.accepted = true;
        }
    }

    ColumnLayout {
        anchors.fill: parent;
        anchors.topMargin: UM.Theme.sizes.default_margin.height;
        anchors.bottomMargin: UM.Theme.sizes.window_margin.height;

        spacing: UM.Theme.sizes.default_margin.height;

        SidebarHeader {
            id: header;

            Layout.fillWidth: true;

            addMachineAction: base.addMachineAction;
            configureMachinesAction: base.configureMachinesAction;
            modesModel: modesListModel;

            currentModeIndex: {
                var index = parseInt(UM.Preferences.getValue("cura/active_mode"))
                if(index) {
                    return index;
                }
                return 0;
            }
            onCurrentModeIndexChanged: UM.Preferences.setValue("cura/active_mode", currentModeIndex);
        }

        Loader {
            id: sidebarContents;

            Layout.fillWidth: true;
            Layout.fillHeight: true;

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

        SaveButton {
            id: saveButton;
            Layout.preferredWidth: base.width - UM.Theme.sizes.default_margin.width * 2;
            Layout.preferredHeight: UM.Theme.sizes.button.height;
            Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter;
        }
        
    }
    
    SidebarTooltip {
        id: tooltip;
    }

    ListModel {
        id: modesListModel;
        //: Simple configuration mode option
        ListElement { text: QT_TR_NOOP("Simple"); file: "SidebarSimple.qml" }
        //: Advanced configuration mode option
        ListElement { text: QT_TR_NOOP("Advanced"); file: "SidebarAdvanced.qml" }
    }
}
