import QtQuick 2.0
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

// The labelBar shows a set of labels that are evenly spaced from oneother.
// The first item is aligned to the left, the last is aligned to the right.
// It's intended to be used together with RadioCheckBar. As such, it needs
// to know what the used itemSize is, so it can ensure the labels are aligned correctly.
Item
{
    id: base
    property var model: null
    property int itemSize: 14
    RowLayout
    {
        anchors.fill: parent
        spacing: 0
        Repeater
        {
            id: repeater
            model: base.model

            Item
            {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.maximumWidth: index + 1 === repeater.count ? itemSize: 200000000

                Label
                {
                    id: label
                    text: model.text

                    anchors
                    {
                        // Some magic to ensure that the items are aligned properly.
                        // We want the following:
                        // First item should be aligned to the left, no margin.
                        // Last item should be aligned to the right, no margin.
                        // The middle item(s) should be aligned to the center of the "item" it's showing (hence half the itemsize as offset).
                        // We want the center of the label to align with the center of the item, so we negatively offset by half the contentWidth
                        right: index + 1 === repeater.count ? parent.right: undefined
                        left: index + 1 === repeater.count || index === 0 ? undefined: parent.left
                        leftMargin: (0.5 * itemSize) - 0.5 * contentWidth
                    }
                }
            }
        }
    }
}
