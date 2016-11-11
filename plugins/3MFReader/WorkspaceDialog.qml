// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

UM.Dialog
{
    title: catalog.i18nc("@title:window", "Conflict")

    width: 350 * Screen.devicePixelRatio;
    minimumWidth: 350 * Screen.devicePixelRatio;
    maximumWidth: 350 * Screen.devicePixelRatio;

    height: 250 * Screen.devicePixelRatio;
    minimumHeight: 250 * Screen.devicePixelRatio;
    maximumHeight: 250 * Screen.devicePixelRatio;

    onClosing: manager.notifyClosed()

    Item
    {
        UM.I18nCatalog { id: catalog; name: "cura"; }
    }
    rightButtons: [
        Button
        {
            id: override_button
            text: catalog.i18nc("@action:button","Override");
            onClicked: { manager.onOverrideButtonClicked() }
            enabled: true
        },
        Button
        {
            id: create_new
            text: catalog.i18nc("@action:button","Create new");
            onClicked: { manager.onNewButtonClicked() }
            enabled: true
        },
        Button
        {
            id: cancel_button
            text: catalog.i18nc("@action:button","Cancel");
            onClicked: { manager.onCancelButtonClicked() }
            enabled: true
        }
    ]
}