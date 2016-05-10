// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM

ScrollView
{
    id: base;

    style: UM.Theme.styles.scrollview;
    flickableItem.flickableDirection: Flickable.VerticalFlick;

    property Action configureSettings;
    signal showTooltip(Item item, point location, string text);
    signal hideTooltip();

    ListView
    {
        id: contents
        spacing: UM.Theme.getSize("default_lining").height;

        model: UM.SettingDefinitionsModel { id: definitionsModel; containerId: "fdmprinter" }

        delegate: Loader
        {
            id: delegate

            width: ListView.view.width

            property var definition: model
            property var settingDefinitionsModel: definitionsModel

            source:
            {
                switch(model.type)
                {
                    case "int":
                        return "SettingTextField.qml"
                    case "float":
                        return "SettingTextField.qml"
                    case "double":
                        return "SettingTextField.qml"
                    case "enum":
                        return "SettingComboBox.qml"
                    case "boolean":
                        return "SettingCheckBox.qml"
                    case "string":
                        return "SettingTextField.qml"
                    case "category":
                        return "SettingCategory.qml"
                    default:
                        return "SettingUnknown.qml"
                }
            }

            Connections
            {
                target: item
                onContextMenuRequested: { contextMenu.key = model.key; contextMenu.popup() }
                onShowTooltip: base.showTooltip(delegate, position, model.description)
            }
        }

        UM.I18nCatalog { id: catalog; name: "uranium"; }

        Menu
        {
            id: contextMenu;

            property string key;

            MenuItem
            {
                //: Settings context menu action
                text: catalog.i18nc("@action:menu", "Hide this setting");
                onTriggered: definitionsModel.hide(contextMenu.key);
            }
            MenuItem
            {
                //: Settings context menu action
                text: catalog.i18nc("@action:menu", "Configure setting visiblity...");

                onTriggered: if(base.configureSettings) base.configureSettings.trigger(contextMenu);
            }
        }
    }
}
