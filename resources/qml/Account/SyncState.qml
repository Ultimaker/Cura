import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.4 as UM
import Cura 1.1 as Cura

Row // Sync state icon + message
{
    property var syncState: Cura.API.account.syncState

    id: syncRow
    width: childrenRect.width
    height: childrenRect.height
    anchors.horizontalCenter: parent.horizontalCenter
    spacing: UM.Theme.getSize("narrow_margin").height

    states: [
        State
        {
            name: "idle"
            when: syncState == Cura.AccountSyncState.IDLE
            PropertyChanges { target: icon; source: UM.Theme.getIcon("update")}
        },
        State
        {
            name: "syncing"
            when: syncState == Cura.AccountSyncState.SYNCING
            PropertyChanges { target: icon; source: UM.Theme.getIcon("update") }
            PropertyChanges { target: stateLabel; text: catalog.i18nc("@label", "Checking...")}
        },
        State
        {
            name: "up_to_date"
            when: syncState == Cura.AccountSyncState.SUCCESS
            PropertyChanges { target: icon; source: UM.Theme.getIcon("checked") }
            PropertyChanges { target: stateLabel; text: catalog.i18nc("@label", "You are in sync with your account")}
        },
        State
        {
            name: "error"
            when: syncState == Cura.AccountSyncState.ERROR
            PropertyChanges { target: icon; source: UM.Theme.getIcon("warning_light") }
            PropertyChanges { target: stateLabel; text: catalog.i18nc("@label", "Something went wrong...")}
        }
    ]

    SystemPalette
    {
        id: palette
    }


    UM.RecolorImage
    {
        id: icon
        width: 20 * screenScaleFactor
        height: width

        source: Cura.API.account.manualSyncEnabled ? UM.Theme.getIcon("update") : UM.Theme.getIcon("checked")
        color: palette.text

        RotationAnimator
        {
            id: updateAnimator
            target: icon
            from: 0
            to: 360
            duration: 1000
            loops: Animation.Infinite
            running: syncState == Cura.AccountSyncState.SYNCING

            // reset rotation when stopped
            onRunningChanged: {
                if(!running)
                {
                    icon.rotation = 0
                }
            }
        }
    }

    Column
    {
        width: childrenRect.width
        height: childrenRect.height

        Label
        {
            id: stateLabel
            text: catalog.i18nc("@state", catalog.i18nc("@label", "You are in sync with your account"))
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("medium")
            renderType: Text.NativeRendering
            visible: !Cura.API.account.manualSyncEnabled
        }

        Label
        {
            id: accountSyncButton
            text: catalog.i18nc("@button", "Check for account updates")
            color: UM.Theme.getColor("secondary_button_text")
            font: UM.Theme.getFont("medium")
            renderType: Text.NativeRendering
            visible: Cura.API.account.manualSyncEnabled

            MouseArea
            {
                anchors.fill: parent
                onClicked: Cura.API.account.sync(true)
                hoverEnabled: true
                onEntered: accountSyncButton.font.underline = true
                onExited: accountSyncButton.font.underline = false
            }
        }
    }
}