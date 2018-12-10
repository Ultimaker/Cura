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

    // If the widget was used to vote, but the vote isn't sent to remote yet, we do want to fake some things.
    property int _numRatings: _localRating != 0 ? numRatings + 1 : numRatings
    property int _localRating: 0
    onVisibleChanged: _localRating = 0 // Reset the _localRating

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
                        if(ratingWidget._localRating > 0)
                        {
                            return _localRating >= index +1
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
                            if((ratingWidget.indexHovered >= 0 || ratingWidget.userRating > 0 || ratingWidget._localRating > 0) && isStarFilled)
                            {
                                return UM.Theme.getColor("primary")
                            }
                            return "#5a5a5a"
                        }
                    }
                    onClicked:
                    {
                        // Ensure that the local rating is updated (even though it's not on the server just yet)
                        _localRating = index + 1
                        toolbox.ratePackage(ratingWidget.packageId, index + 1)
                    }
                }
            }
            Label
            {
                text: "(" + _numRatings + ")"
                verticalAlignment: Text.AlignVCenter
                height: parent.height
                color: "#5a5a5a"
                font: UM.Theme.getFont("small")
            }
        }
    }
}