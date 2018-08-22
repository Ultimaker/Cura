ListView
{
    id: materialListView

    model: materialsModel

    section.property: "brand"
    section.criteria: ViewSection.FullString
    section.delegate: Rectangle
    {
        width: materialScrollView.width
        height: childrenRect.height
        color: palette.light

        Label
        {
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_lining").width
            text: section
            font.bold: true
            color: palette.text
        }
    }

    delegate: Rectangle
    {
        width: materialScrollView.width
        height: childrenRect.height
        color: ListView.isCurrentItem ? palette.highlight : (model.index % 2) ? palette.base : palette.alternateBase

        Row
        {
            id: materialRow
            spacing: (UM.Theme.getSize("default_margin").width / 2) | 0
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.right: parent.right

            property bool isCurrentItem: parent.ListView.isCurrentItem

            property bool isItemActivated:
            {
                const extruder_position = Cura.ExtruderManager.activeExtruderIndex;
                const root_material_id = Cura.MachineManager.currentRootMaterialId[extruder_position];
                return model.root_material_id == root_material_id;
            }

            Rectangle
            {
                width: Math.floor(parent.height * 0.8)
                height: Math.floor(parent.height * 0.8)
                color: model.color_code
                border.color: materialRow.isCurrentItem ? palette.highlightedText : palette.text;
                anchors.verticalCenter: parent.verticalCenter
            }
            Label
            {
                width: Math.floor((parent.width * 0.3))
                text: model.material
                elide: Text.ElideRight
                font.italic: materialRow.isItemActivated
                color: materialRow.isCurrentItem ? palette.highlightedText : palette.text;
            }
            Label
            {
                text: (model.name != model.material) ? model.name : ""
                elide: Text.ElideRight
                font.italic: materialRow.isItemActivated
                color: materialRow.isCurrentItem ? palette.highlightedText : palette.text;
            }
        }

        MouseArea
        {
            anchors.fill: parent
            onClicked:
            {
                parent.ListView.view.currentIndex = model.index;
            }
        }
    }

    function activateDetailsWithIndex(index)
    {
        var model = materialsModel.getItem(index);
        base.currentItem = model;
        materialDetailsView.containerId = model.container_id;
        materialDetailsView.currentMaterialNode = model.container_node;

        detailsPanel.updateMaterialPropertiesObject();
    }

    onCurrentIndexChanged:
    {
        forceActiveFocus();  // causes the changed fields to be saved
        activateDetailsWithIndex(currentIndex);
    }
}
