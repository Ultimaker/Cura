import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
Rectangle 
{
    width: 300; height: 100
    ColumnLayout 
    {

        Text 
        {
            text: manager.progress == 0 ? "Starting firmware update, may take a while.": manager.progress > 99 ? "Firmware update completed.": "Updating firmware."
        }
        ProgressBar 
        {
            id: prog;
            value: manager.progress
            minimumValue: 0;
            maximumValue: 100;
            Layout.maximumWidth:parent.width
            Layout.preferredWidth:230
            Layout.preferredHeight:25
            Layout.minimumWidth:230
            Layout.minimumHeight:25
            width: 230
            height: 25
        }
    }
}