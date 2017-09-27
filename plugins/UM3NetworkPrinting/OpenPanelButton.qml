import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.1 as UM

Button {
    objectName: "openPanelSaveAreaButton"
    id: openPanelSaveAreaButton

    UM.I18nCatalog { id: catalog; name: "cura"; }

    height: UM.Theme.getSize("save_button_save_to_button").height
    tooltip: catalog.i18nc("@info:tooltip", "Opens the print jobs page with your default web browser.")
    text: catalog.i18nc("@action:button", "View print jobs")

    style: UM.Theme.styles.sidebar_action_button
}
