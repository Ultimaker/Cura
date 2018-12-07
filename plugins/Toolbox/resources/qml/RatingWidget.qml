import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.0 as UM

Item
{
    id: ratingWidget

    property real rating: 0
    property int indexHovered: -1
    property string packageId: ""
    property int numRatings: 0
    property int userRating: 0
    width: contentRow.width
    height: contentRow.height
    MouseArea
    {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: ratingWidget.enabled
        acceptedButtons: Qt.NoButton
        onExited:
        {
            ratingWidget.indexHovered = -1
        }

        Row
        {
            id: contentRow
            height: childrenRect.height
            Repeater
            {
                model: 5 // We need to get 5 stars
                Button
                {
                    id: control
                    hoverEnabled: true
                    onHoveredChanged:
                    {
                        if(hovered)
                        {
                            indexHovered = index
                        }
                    }

                    property bool isStarFilled:
                    {
                        // If the entire widget is hovered, override the actual rating.
                        if(ratingWidget.indexHovered >= 0)
                        {
                            return indexHovered >= index
                        }

                        if(ratingWidget.userRating > 0)
                        {
                            return userRating >= index +1
                        }

                        return rating >= index + 1
                    }

                    contentItem: Item {}
                    height: UM.Theme.getSize("rating_star").height
                    width: UM.Theme.getSize("rating_star").width
                    background: UM.RecolorImage
                    {
                        source: UM.Theme.getIcon(control.isStarFilled ? "star_filled" : "star_empty")

                        // Unfilled stars should always have the default color. Only filled stars should change on hover
                        color:
                        {
                            if(!enabled)
                            {
                                return "#5a5a5a"
                            }
                            if((ratingWidget.indexHovered >= 0 || ratingWidget.userRating > 0) && isStarFilled)
                            {
                                return UM.Theme.getColor("primary")
                            }
                            return "#5a5a5a"
                        }
                    }
                    onClicked:
                    {
                        if(userRating == 0)
                        {
                            //User didn't vote yet, locally fake it
                            numRatings += 1
                        }
                        userRating = index + 1 // Fake local data
                        toolbox.ratePackage(ratingWidget.packageId, index + 1)
                    }
                }
            }
            Label
            {
                text: "(" + numRatings + ")"
            }
        }
    }
}