import QtQuick 2.7

import QtQuick.Controls 1.4

import UM 1.3 as UM
import Cura 1.1 as Cura

Item
{
    id: previewMenu
    // This widget doesn't show tooltips by itself. Instead it emits signals so others can do something with it.
    signal showTooltip(Item item, point location, string text)
    signal hideTooltip()

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    Row
    {
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: UM.Theme.getSize("default_margin").width

        ComboBox
        {
            // This item contains the views selector, a combobox that is dynamically created from
            // the list of available Views (packages that create different visualizations of the
            // scene).
            id: viewModeButton

            style: UM.Theme.styles.combobox

            model: UM.ViewModel { }
            textRole: "name"

            // update the model's active index
            function updateItemActiveFlags()
            {
                currentIndex = getActiveIndex()
                for (var i = 0; i < model.rowCount(); i++)
                {
                    model.getItem(i).active = (i == currentIndex)
                }
            }

            // get the index of the active model item on start
            function getActiveIndex()
            {
                for (var i = 0; i < model.rowCount(); i++)
                {
                    if (model.getItem(i).active)
                    {
                        return i;
                    }
                }
                return 0
            }

            onCurrentIndexChanged:
            {
                if (model.getItem(currentIndex).id != undefined)
                {
                    UM.Controller.setActiveView(model.getItem(currentIndex).id)
                }
            }
            currentIndex: getActiveIndex()
        }

        Loader
        {
            // TODO: Make this panel collapsable and ensure it has a standardised background.
            id: viewPanel

            property var buttonTarget: Qt.point(viewModeButton.x + Math.round(viewModeButton.width / 2), viewModeButton.y + Math.round(viewModeButton.height / 2))

            height: childrenRect.height
            width: childrenRect.width

            source: UM.ActiveView.valid ? UM.ActiveView.activeViewPanel : ""
        }

        Cura.PrintSetupSelector
        {
            width: UM.Theme.getSize("print_setup_widget").width
            onShowTooltip: previewMenu.showTooltip(item, location, text)
            onHideTooltip: previewMenu.hideTooltip()
        }
    }
}