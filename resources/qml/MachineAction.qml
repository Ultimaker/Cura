import QtQuick 2.2

Item
{
    id: contentItem
    // Connect the finished property change to completed signal.
    property var finished: manager.finished
    onFinishedChanged: if(manager.finished) {completed()}
    signal completed()
}