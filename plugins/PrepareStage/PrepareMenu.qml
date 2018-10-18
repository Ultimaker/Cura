import QtQuick 2.7

import QtQuick.Controls 1.4

import UM 1.3 as UM
import Cura 1.1 as Cura


Item
{
    id: prepareMenu
    // This widget doesn't show tooltips by itself. Instead it emits signals so others can do something with it.
    signal showTooltip(Item item, point location, string text)
    signal hideTooltip()

    property bool isNetworkPrinter: Cura.MachineManager.activeMachineNetworkKey != ""
    property bool printerConnected: Cura.MachineManager.printerConnected

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    Row
    {
        anchors.horizontalCenter: parent.horizontalCenter

        Button
        {
            id: openFileButton
            text: catalog.i18nc("@action:button", "Open File")
            iconSource: UM.Theme.getIcon("load")
            style: UM.Theme.styles.tool_button
            tooltip: ""
            action: Cura.Actions.open
        }

        Item
        {
            id: spacing
            width: UM.Theme.getSize("default_margin").width
            height: prepareMenu.height
        }

        Cura.MachineSelector
        {
            id: machineSelection
            width: UM.Theme.getSize("sidebar").width
            height: prepareMenu.height
        }

        Cura.QuickConfigurationSelector
        {
            id: configSelection
            visible: isNetworkPrinter && printerConnected
            width: visible ? Math.round(machineSelection.width * 0.15) : 0
            panelWidth: machineSelection.width
            height: prepareMenu.height
        }

        Cura.CustomConfigurationSelector
        {
            width: UM.Theme.getSize("sidebar").width
        }

        Cura.PrintSetupSelector
        {
            width: UM.Theme.getSize("sidebar").width
            onShowTooltip: prepareMenu.showTooltip(item, location, text)
            onHideTooltip: prepareMenu.hideTooltip()
        }
    }
}