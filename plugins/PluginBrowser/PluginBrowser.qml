import UM 1.1 as UM
import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.1

UM.Dialog
{
    id: base

    title: "YAY"
    width: 450
    height: 150
    ScrollView
    {
        width: parent.width
        height: parent.height - progressbar.height - UM.Theme.getSize("default_margin").height
        frameVisible: true
        ListView
        {
            id: pluginList
            model: manager.pluginsModel
            anchors.fill: parent

            delegate: pluginDelegate
        }
    }
    ProgressBar
    {
        id: progressbar
        anchors.bottom: parent.bottom
        style: UM.Theme.styles.progressbar
        minimumValue: 0;
        maximumValue: 100
        width: parent.width
        height: 20
        value: manager.downloadProgress
    }
    Item
    {
        SystemPalette { id: palette }
        Component
        {
            id: pluginDelegate
            Rectangle
            {
                width: pluginList.width;
                height: childrenRect.height;
                color: index % 2 ? palette.base : palette.alternateBase
                Row
                {
                    width: childrenRect.width
                    height: childrenRect.height;
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    Label
                    {
                        text: model.name
                        width: contentWidth
                    }

                }
                Button
                {
                    text: "Download"
                    onClicked: manager.downloadAndInstallPlugin(model.file_location)
                    anchors.right: parent.right
                }
            }

        }
    }
}