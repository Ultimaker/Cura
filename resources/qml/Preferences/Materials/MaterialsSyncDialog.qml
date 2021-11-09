//Copyright (c) 2021 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.15
import QtQuick.Window 2.1
import Cura 1.1 as Cura
import UM 1.4 as UM

Window
{
    id: materialsSyncDialog
    property variant catalog: UM.I18nCatalog { name: "cura" }

    title: catalog.i18nc("@title:window", "Sync materials with printers")
    minimumWidth: UM.Theme.getSize("modal_window_minimum").width
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height
    width: minimumWidth
    height: minimumHeight
    modality: Qt.ApplicationModal

    property variant syncModel
    property alias pageIndex: swipeView.currentIndex
    property alias syncStatusText: syncStatusLabel.text
    property bool hasExportedUsb: false

    SwipeView
    {
        id: swipeView
        anchors.fill: parent
        interactive: false

        Rectangle
        {
            id: introPage
            color: UM.Theme.getColor("main_background")
            Column
            {
                spacing: UM.Theme.getSize("default_margin").height
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_margin").width

                Label
                {
                    text: catalog.i18nc("@title:header", "Sync materials with printers")
                    font: UM.Theme.getFont("large_bold")
                    color: UM.Theme.getColor("text")
                }
                Label
                {
                    text: catalog.i18nc("@text", "Following a few simple steps, you will be able to synchronize all your material profiles with your printers.")
                    font: UM.Theme.getFont("medium")
                    color: UM.Theme.getColor("text")
                    wrapMode: Text.Wrap
                    width: parent.width
                }
                Image
                {
                    source: UM.Theme.getImage("material_ecosystem")
                    width: parent.width
                    sourceSize.width: width
                }
            }

            Cura.PrimaryButton
            {
                id: startButton
                anchors
                {
                    right: parent.right
                    rightMargin: UM.Theme.getSize("default_margin").width
                    bottom: parent.bottom
                    bottomMargin: UM.Theme.getSize("default_margin").height
                }
                text: catalog.i18nc("@button", "Start")
                onClicked:
                {
                    if(Cura.API.account.isLoggedIn)
                    {
                        swipeView.currentIndex += 2; //Skip sign in page.
                    }
                    else
                    {
                        swipeView.currentIndex += 1;
                    }
                }
            }
            Cura.TertiaryButton
            {
                anchors
                {
                    left: parent.left
                    leftMargin: UM.Theme.getSize("default_margin").width
                    verticalCenter: startButton.verticalCenter
                }
                text: catalog.i18nc("@button", "Why do I need to sync material profiles?")
                iconSource: UM.Theme.getIcon("LinkExternal")
                isIconOnRightSide: true
                onClicked: Qt.openUrlExternally("https://support.ultimaker.com/hc/en-us/articles/360013137919?utm_source=cura&utm_medium=software&utm_campaign=sync-material-printer-why")
            }
        }

        Rectangle
        {
            id: signinPage
            color: UM.Theme.getColor("main_background")

            Connections //While this page is active, continue to the next page if the user logs in.
            {
                target: Cura.API.account
                function onLoginStateChanged(is_logged_in)
                {
                    if(is_logged_in && signinPage.SwipeView.isCurrentItem)
                    {
                        swipeView.currentIndex += 1;
                    }
                }
            }

            ColumnLayout
            {
                spacing: UM.Theme.getSize("default_margin").height
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_margin").width

                Label
                {
                    text: catalog.i18nc("@title:header", "Sign in")
                    font: UM.Theme.getFont("large_bold")
                    color: UM.Theme.getColor("text")
                    Layout.preferredHeight: height
                }
                Label
                {
                    text: catalog.i18nc("@text", "To automatically sync the material profiles with all your printers connected to Digital Factory you need to be signed in in Cura.")
                    font: UM.Theme.getFont("medium")
                    color: UM.Theme.getColor("text")
                    wrapMode: Text.Wrap
                    width: parent.width
                    Layout.maximumWidth: width
                    Layout.preferredHeight: height
                }
                Item
                {
                    Layout.preferredWidth: parent.width
                    Layout.fillHeight: true
                    Image
                    {
                        source: UM.Theme.getImage("first_run_ultimaker_cloud")
                        width: parent.width / 2
                        sourceSize.width: width
                        anchors.centerIn: parent
                    }
                }
                Item
                {
                    width: parent.width
                    height: childrenRect.height
                    Layout.preferredHeight: height
                    Cura.SecondaryButton
                    {
                        anchors.left: parent.left
                        text: catalog.i18nc("@button", "Sync materials with USB")
                        onClicked: swipeView.currentIndex = removableDriveSyncPage.SwipeView.index
                    }
                    Cura.PrimaryButton
                    {
                        anchors.right: parent.right
                        text: catalog.i18nc("@button", "Sign in")
                        onClicked: Cura.API.account.login()
                    }
                }
            }
        }

        Rectangle
        {
            id: printerListPage
            color: UM.Theme.getColor("main_background")

            ColumnLayout
            {
                spacing: UM.Theme.getSize("default_margin").height
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_margin").width
                visible: cloudPrinterList.count > 0

                Row
                {
                    Layout.preferredHeight: childrenRect.height
                    spacing: UM.Theme.getSize("default_margin").width

                    states: [
                        State
                        {
                            name: "idle"
                            when: typeof syncModel === "undefined" || syncModel.exportUploadStatus == "idle" || syncModel.exportUploadStatus == "uploading"
                            PropertyChanges { target: printerListHeader; text: catalog.i18nc("@title:header", "The following printers will receive the new material profiles:") }
                            PropertyChanges { target: printerListHeaderIcon; status: UM.StatusIcon.Status.NEUTRAL; width: 0 }
                        },
                        State
                        {
                            name: "error"
                            when: typeof syncModel !== "undefined" && syncModel.exportUploadStatus == "error"
                            PropertyChanges { target: printerListHeader; text: catalog.i18nc("@title:header", "Something went wrong when sending the materials to the printers.") }
                            PropertyChanges { target: printerListHeaderIcon; status: UM.StatusIcon.Status.ERROR }
                        },
                        State
                        {
                            name: "success"
                            when: typeof syncModel !== "undefined" && syncModel.exportUploadStatus == "success"
                            PropertyChanges { target: printerListHeader; text: catalog.i18nc("@title:header", "Material profiles successfully synced with the following printers:") }
                            PropertyChanges { target: printerListHeaderIcon; status: UM.StatusIcon.Status.POSITIVE }
                        }
                    ]

                    UM.StatusIcon
                    {
                        id: printerListHeaderIcon
                        width: UM.Theme.getSize("section_icon").width
                        height: width
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Label
                    {
                        id: printerListHeader
                        anchors.verticalCenter: parent.verticalCenter
                        //Text is always defined by the states above.
                        font: UM.Theme.getFont("large_bold")
                        color: UM.Theme.getColor("text")
                    }
                }
                Row
                {
                    Layout.preferredWidth: parent.width
                    Layout.preferredHeight: childrenRect.height

                    Label
                    {
                        id: syncStatusLabel

                        width: parent.width - UM.Theme.getSize("default_margin").width - troubleshootingLink.width

                        wrapMode: Text.Wrap
                        elide: Text.ElideRight
                        visible: text !== ""
                        text: ""
                        color: UM.Theme.getColor("text")
                        font: UM.Theme.getFont("medium")
                    }
                    Cura.TertiaryButton
                    {
                        id: troubleshootingLink
                        text: catalog.i18nc("@button", "Troubleshooting")
                        visible: typeof syncModel !== "undefined" && syncModel.exportUploadStatus == "error"
                        iconSource: UM.Theme.getIcon("LinkExternal")
                        onClicked: Qt.openUrlExternally("https://support.ultimaker.com/hc/en-us/articles/360012019239?utm_source=cura&utm_medium=software&utm_campaign=sync-material-wizard-troubleshoot-cloud-printer")
                    }
                }
                ScrollView
                {
                    id: printerListScrollView
                    width: parent.width
                    Layout.preferredWidth: width
                    Layout.fillHeight: true
                    clip: true
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                    ListView
                    {
                        id: printerList
                        width: parent.width
                        spacing: UM.Theme.getSize("default_margin").height

                        model: cloudPrinterList
                        delegate: Rectangle
                        {
                            id: delegateContainer
                            color: "transparent"
                            border.color: UM.Theme.getColor("lining")
                            border.width: UM.Theme.getSize("default_lining").width
                            width: printerListScrollView.width
                            height: UM.Theme.getSize("card").height

                            property string syncStatus:
                            {
                                var printer_id = model.metadata["host_guid"]
                                if(syncModel.printerStatus[printer_id] === undefined) //No status information available. Could be added after we started syncing.
                                {
                                    return "idle";
                                }
                                return syncModel.printerStatus[printer_id];
                            }

                            Cura.IconWithText
                            {
                                anchors
                                {
                                    verticalCenter: parent.verticalCenter
                                    left: parent.left
                                    leftMargin: Math.round(parent.height - height) / 2 //Equal margin on the left as above and below.
                                    right: parent.right
                                    rightMargin: Math.round(parent.height - height) / 2
                                }

                                text: model.name
                                font: UM.Theme.getFont("medium")

                                source: UM.Theme.getIcon("Printer", "medium")
                                iconColor: UM.Theme.getColor("machine_selector_printer_icon")
                                iconSize: UM.Theme.getSize("machine_selector_icon").width

                                //Printer status badge (always cloud, but whether it's online or offline).
                                UM.RecolorImage
                                {
                                    width: UM.Theme.getSize("printer_status_icon").width
                                    height: UM.Theme.getSize("printer_status_icon").height
                                    anchors
                                    {
                                        bottom: parent.bottom
                                        bottomMargin: -Math.round(height / 6)
                                        left: parent.left
                                        leftMargin: parent.iconSize - Math.round(width * 5 / 6)
                                    }

                                    source: UM.Theme.getIcon("CloudBadge", "low")
                                    color: UM.Theme.getColor("primary")

                                    //Make a themeable circle in the background so we can change it in other themes.
                                    Rectangle
                                    {
                                        anchors.centerIn: parent
                                        width: parent.width - 1.5 //1.5 pixels smaller (at least sqrt(2), regardless of pixel scale) so that the circle doesn't show up behind the icon due to anti-aliasing.
                                        height: parent.height - 1.5
                                        radius: width / 2
                                        color: UM.Theme.getColor("connection_badge_background")
                                        z: parent.z - 1
                                    }
                                }
                            }

                            UM.RecolorImage
                            {
                                id: printerSpinner
                                width: UM.Theme.getSize("section_icon").width
                                height: width
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.right: parent.right
                                anchors.rightMargin: Math.round((parent.height - height) / 2) //Same margin on the right as above and below.

                                visible: delegateContainer.syncStatus === "uploading"
                                source: UM.Theme.getIcon("ArrowDoubleCircleRight")
                                color: UM.Theme.getColor("primary")

                                RotationAnimator
                                {
                                    target: printerSpinner
                                    from: 0
                                    to: 360
                                    duration: 1000
                                    loops: Animation.Infinite
                                    running: true
                                }
                            }
                            UM.StatusIcon
                            {
                                width: UM.Theme.getSize("section_icon").width
                                height: width
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.right: parent.right
                                anchors.rightMargin: Math.round((parent.height - height) / 2) //Same margin on the right as above and below.

                                visible: delegateContainer.syncStatus === "failed" || delegateContainer.syncStatus === "success"
                                status: delegateContainer.syncStatus === "success" ? UM.StatusIcon.Status.POSITIVE : UM.StatusIcon.Status.ERROR
                            }
                        }

                        footer: Item
                        {
                            width: printerListScrollView.width
                            height: {
                                if(!visible)
                                {
                                    return 0;
                                }
                                let h = UM.Theme.getSize("card").height + printerListTroubleshooting.height + UM.Theme.getSize("default_margin").height * 2; //1 margin between content and footer, 1 for troubleshooting link.
                                return h;
                            }
                            visible: includeOfflinePrinterList.count - cloudPrinterList.count > 0 && typeof syncModel !== "undefined" && syncModel.exportUploadStatus === "idle"
                            Rectangle
                            {
                                anchors.fill: parent
                                anchors.topMargin: UM.Theme.getSize("default_margin").height

                                border.color: UM.Theme.getColor("lining")
                                border.width: UM.Theme.getSize("default_lining").width
                                color: "transparent"

                                Row
                                {
                                    anchors
                                    {
                                        fill: parent
                                        margins: Math.round(UM.Theme.getSize("card").height - UM.Theme.getSize("machine_selector_icon").width) / 2 //Same margin as in other cards.
                                    }
                                    spacing: UM.Theme.getSize("default_margin").width

                                    UM.StatusIcon
                                    {
                                        id: infoIcon
                                        width: UM.Theme.getSize("section_icon").width
                                        height: width
                                        //Fake anchor.verticalCenter: printersMissingText.verticalCenter, since we can't anchor to things that aren't siblings.
                                        anchors.top: parent.top
                                        anchors.topMargin: Math.round(printersMissingText.height / 2 - height / 2)

                                        status: UM.StatusIcon.Status.WARNING
                                    }

                                    Column
                                    {
                                        //Fill the total width. Can't use layouts because we need the anchors for vertical alignment.
                                        width: parent.width - infoIcon.width - refreshListButton.width - parent.spacing * 2

                                        spacing: UM.Theme.getSize("default_margin").height

                                        Label
                                        {
                                            id: printersMissingText
                                            text: catalog.i18nc("@text Asking the user whether printers are missing in a list.", "Printers missing?")
                                              + "\n"
                                              + catalog.i18nc("@text", "Make sure all your printers are turned ON and connected to Digital Factory.")
                                            font: UM.Theme.getFont("medium")
                                            color: UM.Theme.getColor("text")
                                            elide: Text.ElideRight
                                        }
                                        Cura.TertiaryButton
                                        {
                                            id: printerListTroubleshooting
                                            leftPadding: 0  //Want to visually align this to the text.

                                            text: catalog.i18nc("@button", "Troubleshooting")
                                            iconSource: UM.Theme.getIcon("LinkExternal")
                                            onClicked: Qt.openUrlExternally("https://support.ultimaker.com/hc/en-us/articles/360012019239?utm_source=cura&utm_medium=software&utm_campaign=sync-material-wizard-troubleshoot-cloud-printer")
                                        }
                                    }

                                    Cura.SecondaryButton
                                    {
                                        id: refreshListButton
                                        //Fake anchor.verticalCenter: printersMissingText.verticalCenter, since we can't anchor to things that aren't siblings.
                                        anchors.top: parent.top
                                        anchors.topMargin: Math.round(printersMissingText.height / 2 - height / 2)

                                        text: catalog.i18nc("@button", "Refresh List")
                                        iconSource: UM.Theme.getIcon("ArrowDoubleCircleRight")
                                        onClicked: Cura.API.account.sync(true)
                                    }
                                }
                            }
                        }
                    }
                }
                Item
                {
                    width: parent.width
                    height: childrenRect.height
                    Layout.preferredWidth: width
                    Layout.preferredHeight: height

                    Cura.SecondaryButton
                    {
                        anchors.left: parent.left
                        text: catalog.i18nc("@button", "Sync materials with USB")
                        onClicked: swipeView.currentIndex = removableDriveSyncPage.SwipeView.index
                    }
                    Cura.PrimaryButton
                    {
                        id: syncButton
                        anchors.right: parent.right
                        text:
                        {
                            if(typeof syncModel !== "undefined" && syncModel.exportUploadStatus == "error")
                            {
                                return catalog.i18nc("@button", "Try again");
                            }
                            if(typeof syncModel !== "undefined" && syncModel.exportUploadStatus == "success")
                            {
                                return catalog.i18nc("@button", "Done");
                            }
                            return catalog.i18nc("@button", "Sync");
                        }
                        onClicked:
                        {
                            if(typeof syncModel !== "undefined" && syncModel.exportUploadStatus == "success")
                            {
                                materialsSyncDialog.close();
                            }
                            else
                            {
                                syncModel.exportUpload();
                            }
                        }
                        visible:
                        {
                            if(!syncModel) //When the dialog is created, this is not set yet.
                            {
                                return true;
                            }
                            return syncModel.exportUploadStatus != "uploading";
                        }
                    }
                    Item
                    {
                        anchors.right: parent.right
                        width: childrenRect.width
                        height: syncButton.height

                        visible: !syncButton.visible

                        UM.RecolorImage
                        {
                            id: syncingIcon
                            height: UM.Theme.getSize("action_button_icon").height
                            width: height
                            anchors.verticalCenter: syncingLabel.verticalCenter

                            source: UM.Theme.getIcon("ArrowDoubleCircleRight")
                            color: UM.Theme.getColor("primary")

                            RotationAnimator
                            {
                                target: syncingIcon
                                from: 0
                                to: 360
                                duration: 1000
                                loops: Animation.Infinite
                                running: true
                            }
                        }
                        Label
                        {
                            id: syncingLabel
                            anchors.left: syncingIcon.right
                            anchors.leftMargin: UM.Theme.getSize("narrow_margin").width

                            text: catalog.i18nc("@button", "Syncing")
                            color: UM.Theme.getColor("primary")
                            font: UM.Theme.getFont("medium")
                        }
                    }
                }
            }

            ColumnLayout //Placeholder for when the user has no cloud printers.
            {
                spacing: UM.Theme.getSize("default_margin").height
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_margin").width
                visible: cloudPrinterList.count == 0

                Label
                {
                    text: catalog.i18nc("@title:header", "No printers found")
                    font: UM.Theme.getFont("large_bold")
                    color: UM.Theme.getColor("text")
                    Layout.preferredWidth: width
                    Layout.preferredHeight: height
                }
                Image
                {
                    source: UM.Theme.getImage("3d_printer_faded")
                    sourceSize.width: width
                    fillMode: Image.PreserveAspectFit
                    Layout.alignment: Qt.AlignHCenter
                    Layout.preferredWidth: parent.width / 3
                }
                Label
                {
                    text: catalog.i18nc("@text", "It seems like you don't have access to any printers connected to Digital Factory.")
                    width: parent.width
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                    Layout.preferredWidth: width
                    Layout.preferredHeight: height
                }
                Item
                {
                    Layout.preferredWidth: parent.width
                    Layout.fillHeight: true
                    Cura.TertiaryButton
                    {
                        text: catalog.i18nc("@button", "Learn how to connect your printer to Digital Factory")
                        iconSource: UM.Theme.getIcon("LinkExternal")
                        onClicked: Qt.openUrlExternally("https://support.ultimaker.com/hc/en-us/articles/360012019239?utm_source=cura&utm_medium=software&utm_campaign=sync-material-wizard-add-cloud-printer")
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                }
                Item
                {
                    width: parent.width
                    height: childrenRect.height
                    Layout.preferredWidth: width
                    Layout.preferredHeight: height

                    Cura.SecondaryButton
                    {
                        anchors.left: parent.left
                        text: catalog.i18nc("@button", "Sync materials with USB")
                        onClicked: swipeView.currentIndex = removableDriveSyncPage.SwipeView.index
                    }
                    Cura.PrimaryButton
                    {
                        id: disabledSyncButton
                        anchors.right: parent.right
                        text: catalog.i18nc("@button", "Sync")
                        enabled: false //If there are no printers, always disable this button.
                    }
                    Cura.SecondaryButton
                    {
                        anchors.right: disabledSyncButton.left
                        anchors.rightMargin: UM.Theme.getSize("default_margin").width
                        text: catalog.i18nc("@button", "Refresh")
                        iconSource: UM.Theme.getIcon("ArrowDoubleCircleRight")
                        outlineColor: "transparent"
                        onClicked: Cura.API.account.sync(true)
                    }
                }
            }
        }

        Rectangle
        {
            id: removableDriveSyncPage
            color: UM.Theme.getColor("main_background")

            ColumnLayout
            {
                spacing: UM.Theme.getSize("default_margin").height
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_margin").width

                Label
                {
                    text: catalog.i18nc("@title:header", "Sync material profiles via USB")
                    font: UM.Theme.getFont("large_bold")
                    color: UM.Theme.getColor("text")
                    Layout.preferredHeight: height
                }
                Label
                {
                    text: catalog.i18nc("@text In the UI this is followed by a list of steps the user needs to take.", "Follow the following steps to load the new material profiles to your printer.")
                    font: UM.Theme.getFont("medium")
                    color: UM.Theme.getColor("text")
                    wrapMode: Text.Wrap
                    width: parent.width
                    Layout.maximumWidth: width
                    Layout.preferredHeight: height
                }
                Row
                {
                    width: parent.width
                    Layout.preferredWidth: width
                    Layout.fillHeight: true
                    spacing: UM.Theme.getSize("default_margin").width

                    Image
                    {
                        source: UM.Theme.getImage("insert_usb")
                        width: parent.width / 3
                        height: width
                        anchors.verticalCenter: parent.verticalCenter
                        sourceSize.width: width
                    }
                    Label
                    {
                        text: "1. " + catalog.i18nc("@text", "Click the export material archive button.")
                          + "\n2. " + catalog.i18nc("@text", "Save the .umm file on a USB stick.")
                          + "\n3. " + catalog.i18nc("@text", "Insert the USB stick into your printer and launch the procedure to load new material profiles.")
                        font: UM.Theme.getFont("medium")
                        color: UM.Theme.getColor("text")
                        wrapMode: Text.Wrap
                        width: parent.width * 2 / 3 - UM.Theme.getSize("default_margin").width
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                Cura.TertiaryButton
                {
                    text: catalog.i18nc("@button", "How to load new material profiles to my printer")
                    iconSource: UM.Theme.getIcon("LinkExternal")
                    onClicked: Qt.openUrlExternally("https://support.ultimaker.com/hc/en-us/articles/360013137919?utm_source=cura&utm_medium=software&utm_campaign=sync-material-wizard-how-usb")
                }

                Item
                {
                    width: parent.width
                    height: childrenRect.height
                    Layout.preferredWidth: width
                    Layout.preferredHeight: height

                    Cura.SecondaryButton
                    {
                        anchors.left: parent.left
                        text: catalog.i18nc("@button", "Back")
                        onClicked: swipeView.currentIndex = 0 //Reset to first page.
                    }
                    Cura.PrimaryButton
                    {
                        id: exportUsbButton
                        anchors.right: parent.right

                        property bool hasExported: false
                        text: materialsSyncDialog.hasExportedUsb ? catalog.i18nc("@button", "Done") : catalog.i18nc("@button", "Export material archive")
                        onClicked:
                        {
                            if(!materialsSyncDialog.hasExportedUsb)
                            {
                                exportUsbDialog.folder = syncModel.getPreferredExportAllPath();
                                exportUsbDialog.open();
                            }
                            else
                            {
                                materialsSyncDialog.close();
                            }
                        }
                    }
                }
            }
        }
    }

    Cura.GlobalStacksModel
    {
        id: cloudPrinterList
        filterConnectionType: 3 //Only show cloud connections.
        filterOnlineOnly: true //Only show printers that are online.
    }
    Cura.GlobalStacksModel
    {
        //In order to show a refresh button only when there are offline cloud printers, we need to know if there are any offline printers.
        //A global stacks model without the filter for online-only printers allows this.
        id: includeOfflinePrinterList
        filterConnectionType: 3 //Still only show cloud connections.
    }

    FileDialog
    {
        id: exportUsbDialog
        title: catalog.i18nc("@title:window", "Export All Materials")
        selectExisting: false
        nameFilters: ["Material archives (*.umm)", "All files (*)"]
        onAccepted:
        {
            syncModel.exportAll(fileUrl);
            CuraApplication.setDefaultPath("dialog_material_path", folder);
            materialsSyncDialog.hasExportedUsb = true;
        }
    }
}