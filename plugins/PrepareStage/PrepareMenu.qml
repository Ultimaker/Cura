import QtQuick 2.7
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.4

import UM 1.3 as UM
import Cura 1.1 as Cura


Item
{
    id: prepareMenu
    // This widget doesn't show tooltips by itself. Instead it emits signals so others can do something with it.
    signal showTooltip(Item item, point location, string text)
    signal hideTooltip()


    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    // Item to ensure that all of the buttons are nicely centered.
    Item
    {
        anchors.horizontalCenter: parent.horizontalCenter
        width: openFileButtonBackground.width + itemRow.width + UM.Theme.getSize("default_margin").width
        height: parent.height

        RowLayout
        {
            id: itemRow

            anchors.left: openFileButtonBackground.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width

            width: 0.9 * prepareMenu.width
            height: parent.height
            spacing: 0

            Cura.MachineSelector
            {
                id: machineSelection
                z: openFileButtonBackground.z - 1 //Ensure that the tooltip of the open file button stays above the item row.
                headerCornerSide: Cura.RoundedRectangle.Direction.Left
                Layout.minimumWidth: UM.Theme.getSize("machine_selector_widget").width
                Layout.maximumWidth: UM.Theme.getSize("machine_selector_widget").width
                Layout.fillWidth: true
                Layout.fillHeight: true
            }

            // Separator line
            Rectangle
            {
                height: parent.height
                width: UM.Theme.getSize("default_lining").width
                color: UM.Theme.getColor("lining")
            }

            Cura.QuickConfigurationSelector
            {
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.preferredWidth: itemRow.width - machineSelection.width - printSetupSelectorItem.width - 2 * UM.Theme.getSize("default_lining").width
            }

            // Separator line
            Rectangle
            {
                height: parent.height
                width: UM.Theme.getSize("default_lining").width
                color: UM.Theme.getColor("lining")
            }

            Item
            {
                id: printSetupSelectorItem
                // This is a work around to prevent the printSetupSelector from having to be re-loaded every time
                // a stage switch is done.
                children: [printSetupSelector]
                height: childrenRect.height
                width: childrenRect.width
            }
        }


        Rectangle
        {
            id: openFileButtonBackground
            height: UM.Theme.getSize("stage_menu").height
            width: UM.Theme.getSize("stage_menu").height

            radius: UM.Theme.getSize("default_radius").width
            color: UM.Theme.getColor("toolbar_background")
            Button
            {
                id: openFileButton
                text: catalog.i18nc("@action:button", "Open File")
                iconSource: UM.Theme.getIcon("load")
                style: UM.Theme.styles.toolbar_button
                tooltip: ""
                action: Cura.Actions.open
                anchors.centerIn: parent
            }
        }
    }
}
