import QtQuick 2.2

Item
{
    id: contentItem

    // Point to the dialog containing the displayItem
    property var dialog

    // Connect the finished property change to completed signal.
    property var finished: manager.finished
    onFinishedChanged: if(manager.finished) {completed()}
    signal completed()

    function reset()
    {
        manager.reset()
    }
}