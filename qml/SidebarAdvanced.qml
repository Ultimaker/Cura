import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.0 as UM

ScrollView {
    id: base;

    style: UM.Theme.styles.scrollview;

    property Action configureSettings;

    Column {
        id: contents
        spacing: UM.Theme.sizes.default_margin.height;

        Repeater {
            model: UM.Models.settingCategoriesModel;

            delegate: Item {
                id: delegateItem;

                width: childrenRect.width;
                height: childrenRect.height;

                visible: model.visible;

                property variant settingsModel: model.settings;

                SidebarCategoryHeader {
                    id: categoryHeader;

                    width: base.viewport.width;
                    height: UM.Theme.sizes.section.height;

                    text: model.name;
                    iconSource: UM.Theme.icons[model.icon];
                    checkable: true;
                }

                Column {
                    id: settings;

                    anchors.top: categoryHeader.bottom;
                    anchors.topMargin: 0;

                    height: 0;
                    width: UM.Theme.sizes.setting.width;
                    spacing: UM.Theme.sizes.default_margin.height;
                    opacity: 0;

                    property real childrenHeight: {
                        var h = 0.0;
                        for(var i in children) {
                            var item = children[i];
                            h += children[i].height;

                            if(item.settingVisible) {
                                if(i - 1 > 0) {
                                    h += spacing;
                                }
                            }
                        }
                        return h;
                    }

                    Repeater {
                        model: delegateItem.settingsModel;

                        delegate: UM.SettingItem {
                            width: UM.Theme.sizes.setting.width;

                            height: model.visible ? UM.Theme.sizes.setting.height : 0;
                            Behavior on height { NumberAnimation { duration: 75; } }
                            opacity: model.visible ? 1 : 0;
                            Behavior on opacity { NumberAnimation { duration: 75; } }

                            enabled: categoryHeader.checked && model.visible;

                            property bool settingVisible: model.visible;

                            name: model.name;
                            description: model.description;
                            value: model.value;
                            unit: model.unit;
                            valid: model.valid;
                            type: model.type;
                            options: model.type == "enum" ? model.options : null;
                            key: model.key;

                            style: UM.Theme.styles.setting_item;

                            onItemValueChanged: delegateItem.settingsModel.setSettingValue(index, model.key, value);
                            onContextMenuRequested: contextMenu.popup();

                            Menu {
                                id: contextMenu;

                                MenuItem {
                                    //: Settings context menu action
                                    text: qsTr("Hide this setting");
                                    onTriggered: delegateItem.settingsModel.hideSetting(model.key);
//                                     onTriggered: settingsList.model.setVisibility(model.key, false);
                                }
                                MenuItem {
                                    //: Settings context menu action
                                    text: qsTr("Configure setting visiblity...");

                                    onTriggered: if(base.configureSettings) base.configureSettings.trigger();
                                }
                            }
                        }
                    }

                    states: State {
                        name: "expanded";
                        when: categoryHeader.checked;

                        PropertyChanges {
                            target: settings;
                            opacity: 1;
                            height: settings.childrenHeight;
                            anchors.topMargin: UM.Theme.sizes.default_margin.height;
                        }
                    }

                    transitions: Transition {
                        to: "expanded";
                        reversible: true;
                        SequentialAnimation {
                            ParallelAnimation {
                                NumberAnimation { property: "height"; duration: 75; }
                                NumberAnimation { property: "anchors.topMargin"; duration: 75; }
                            }
                            NumberAnimation { property: "opacity"; duration: 75; }
                        }
                    }
                }
            }
        }
    }
}
