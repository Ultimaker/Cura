// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.2 as UM

// The labelBar shows a set of labels that are evenly spaced from oneother.
// The first item is aligned to the left, the last is aligned to the right.
// It's intended to be used together with RadioCheckBar. As such, it needs
// to know what the used itemSize is, so it can ensure the labels are aligned correctly.
Item
{
    id: base
    property var model: null
    property string modelKey: ""
    property int itemSize: 14
    height: childrenRect.height
    RowLayout
    {
        anchors.left: parent.left
        anchors.right: parent.right
        height: label.height
        spacing: 0
        Repeater
        {
            id: repeater
            model: base.model

            Item
            {
                Layout.fillWidth: true
                Layout.maximumWidth: Math.round(index + 1 === repeater.count || repeater.count <= 1 ? itemSize : base.width / (repeater.count - 1))
                height: label.height

                Label
                {
                    id: label
                    text: model[modelKey]
                    color: UM.Theme.getColor("text")
                    font: UM.Theme.getFont("default")
                    renderType: Text.NativeRendering
                    height: contentHeight
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
                        leftMargin: Math.round((itemSize - contentWidth) * 0.5)
                    }
                }
            }
        }
    }
}
