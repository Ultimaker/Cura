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
        anchors.fill: parent
        frameVisible: true
        ListView
        {
            id: pluginList
            model: manager.pluginsModel
            anchors.fill: parent

            delegate: pluginDelegate
        }
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
                    width: parent.width
                    height: childrenRect.height;
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    Label
                    {

                        text: model.name
                        width: contentWidth
                    }
                    Button
                    {
                        text: "Download"
                        onClicked: manager.downloadAndInstallPlugin(model.file_location)
                    }
                }
            }
        }
    }
}