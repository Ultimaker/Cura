import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
Rectangle 
{
    width: 300; height: 100
    ColumnLayout 
    {
        RowLayout 
        {
            Text 
            {
                text: "extruder temperature " + manager.extruderTemperature
            }
            Text 
            {
                text: "bed temperature " + manager.bedTemperature
            }
            Text 
            {
                text: "" + manager.error
            }
        
        }
        RowLayout 
        {
            Button 
            {
                text: "Print"  
                onClicked: { manager.startPrint() }
                enabled: manager.progress == 0 ? true : false
            }
            Button
            {
                text: "Cancel" 
                onClicked: { manager.cancelPrint() }
                enabled: manager.progress == 0 ? false:  true
            }
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