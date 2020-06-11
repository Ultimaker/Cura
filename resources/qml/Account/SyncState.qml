import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.4 as UM
import Cura 1.1 as Cura

Row // sync state icon + message
{

    id: syncRow
    width: childrenRect.width
    height: childrenRect.height
    anchors.horizontalCenter: parent.horizontalCenter
    spacing: UM.Theme.getSize("narrow_margin").height

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
            running: true

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
            height: visible ? accountSyncButton.intrinsicHeight : 0

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

    signal syncStateChanged(string newState)

    onSyncStateChanged: {
        if(newState == Cura.AccountSyncState.IDLE){
            icon.source = UM.Theme.getIcon("update")
        } else if(newState == Cura.AccountSyncState.SYNCING){
            icon.source = UM.Theme.getIcon("update")
            stateLabel.text = catalog.i18nc("@label", "Checking...")
        } else if (newState == Cura.AccountSyncState.SUCCESS) {
            icon.source = UM.Theme.getIcon("checked")
            stateLabel.text = catalog.i18nc("@label", "You are in sync with your account")
        } else if (newState == Cura.AccountSyncState.ERROR) {
            icon.source = UM.Theme.getIcon("warning_light")
            stateLabel.text = catalog.i18nc("@label", "Something went wrong...")
        } else {
            print("Error: unexpected sync state: " + newState)
        }

        if(newState == Cura.AccountSyncState.SYNCING){
            updateAnimator.running = true
        } else {
            updateAnimator.running = false
        }
    }

    Component.onCompleted: Cura.API.account.syncStateChanged.connect(syncStateChanged)


}