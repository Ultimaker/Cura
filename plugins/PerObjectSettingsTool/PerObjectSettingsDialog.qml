// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Controls.Styles 1.2
import QtQuick.Window 2.2

import UM 1.1 as UM

UM.Dialog {
    id: settingPickDialog
    title: catalog.i18nc("@title:window", "Pick a Setting to Customize")
    property var settingCategoriesModel

    TextField {
        id: filter;

        anchors {
            top: parent.top;
            left: parent.left;
            right: parent.right;
        }

        placeholderText: catalog.i18nc("@label:textbox", "Filter...");

        onTextChanged: settingCategoriesModel.filter(text);
    }

    ScrollView {
        id: view;
        anchors {
            top: filter.bottom;
            left: parent.left;
            right: parent.right;
            bottom: parent.bottom;
        }

        Column {
            width: view.width - UM.Theme.sizes.default_margin.width * 2;
            height: childrenRect.height;

            Repeater {
                id: settingList;

                model: settingPickDialog.settingCategoriesModel

                delegate: Item {
                    id: delegateItem;

                    width: parent.width;
                    height: childrenRect.height;

                    ToolButton {
                        id: categoryHeader;
                        text: model.name;
                        checkable: true;
                        width: parent.width;
                        onCheckedChanged: settingsColumn.state != "" ? settingsColumn.state = "" : settingsColumn.state = "collapsed";

                        style: ButtonStyle {
                            background: Rectangle
                            {
                                width: control.width;
                                height: control.height;
                                color: control.hovered ? palette.highlight : "transparent";
                            }
                            label: Row
                            {
                                spacing: UM.Theme.sizes.default_margin.width;
                                Image
                                {
                                    anchors.verticalCenter: parent.verticalCenter;
                                    source: control.checked ? UM.Theme.icons.arrow_right : UM.Theme.icons.arrow_bottom;
                                }
                                Label
                                {
                                    text: control.text;
                                    font.bold: true;
                                    color: control.hovered ? palette.highlightedText : palette.text;
                                }
                            }
                        }
                    }

                    property variant settingsModel: model.settings;

                    visible: model.visible;

                    Column {
                        id: settingsColumn;

                        anchors.top: categoryHeader.bottom;

                        property real childrenHeight:
                        {
                            var h = 0.0;
                            for(var i in children)
                            {
                                var item = children[i];
                                h += children[i].height;
                                if(item.settingVisible)
                                {
                                    if(i > 0)
                                    {
                                        h += spacing;
                                    }
                                }
                            }
                            return h;
                        }

                        width: childrenRect.width;
                        height: childrenHeight;
                        Repeater {
                            model: delegateItem.settingsModel;

                            delegate: ToolButton {
                                id: button;
                                x: model.depth * UM.Theme.sizes.default_margin.width;
                                text: model.name
                                tooltip: model.description;

                                onClicked: {
                                    var object_id = UM.ActiveTool.properties.Model.getItem(base.currentIndex).id;
                                    UM.ActiveTool.properties.Model.addSettingOverride(object_id, model.key);
                                    settingPickDialog.visible = false;
                                }

                                states: State {
                                    name: "filtered"
                                    when: model.filtered || !model.visible || !model.enabled || model.global_only
                                    PropertyChanges { target: button; height: 0; opacity: 0; }
                                }
                            }
                        }

                        states: State {
                            name: "collapsed";

                            PropertyChanges { target: settingsColumn; opacity: 0; height: 0; }
                        }
                    }
                }
            }
        }
    }

    rightButtons: [
        Button {
            text: catalog.i18nc("@action:button", "Cancel");
            onClicked: {
                settingPickDialog.visible = false;
            }
        }
    ]
}