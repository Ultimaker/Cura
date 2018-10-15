import QtQuick 2.7

import QtQuick.Controls 1.4

import UM 1.3 as UM
import Cura 1.1 as Cura


Row
{
    spacing: UM.Theme.getSize("default_margin").width

    // This widget doesn't show tooltips by itself. Instead it emits signals so others can do something with it.
    signal showTooltip(Item item, point location, string text)
    signal hideTooltip()

    UM.I18nCatalog
    {
        id: catalog
        name:"cura"
    }

    Button
    {
        id: openFileButton
        text: catalog.i18nc("@action:button", "Open File")
        iconSource: UM.Theme.getIcon("load")
        style: UM.Theme.styles.tool_button
        tooltip: ""
        action: Cura.Actions.open
    }

    Cura.MachineAndConfigurationSelector
    {
    }

    Cura.MaterialAndVariantSelector
    {
        width: UM.Theme.getSize("sidebar").width
    }

    Cura.ProfileAndSettingComponent
    {
        width: UM.Theme.getSize("sidebar").width
        onShowTooltip: parent.showTooltip(item, location, text)
        onHideTooltip: parent.hideTooltip()
    }
}