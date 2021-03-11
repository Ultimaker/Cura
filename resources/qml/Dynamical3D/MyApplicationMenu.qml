import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.4
import UM 1.3 as UM


Rectangle {
    id: menuBackground;

    property QtObject window;
    Binding {
        target: menu.__contentItem
        property: "width"
        value: window.width
        when: !menu.__isNative
    }

    default property alias menus: menu.menus

    property alias estilo: menu.style

    width: menu.__isNative ? 0 : menu.__contentItem.width
    height: menu.__isNative ? 0 : menu.__contentItem.height

    color: palette.window;

    Keys.forwardTo: menu.__contentItem;

    property color menuBackgroundColor: UM.Theme.getColor("viewport_overlay")
    
    MenuBar
    {
        id: menu

        Component.onCompleted:
        {
            __contentItem.parent = menuBackground;
        }
        style: MenuBarStyle {

            padding {
                left: 0
                right: 20
                top: 3
                bottom: 3
            }
            background: Rectangle {
                id: rect
                color: menuBackgroundColor
            }

            itemDelegate: Rectangle {            // the menus
                implicitWidth: lab.contentWidth + 15          // adjust width the way you prefer it
                implicitHeight: lab.contentHeight            // adjust height the way you prefer it
                color: styleData.selected || styleData.open ? UM.Theme.getColor("xray") : menuBackgroundColor
                Label {
                    id: lab
                    //anchors.horizontalCenter: parent.horizontalCenter
                    text: styleData.text.replace("&","")
                }
            }



            menuStyle: MenuStyle {               // the menus items
                id: menuStyle

                frame: Rectangle {
                    color: menuBackgroundColor
                }

                itemDelegate {
                    background: Rectangle {
                        color:  styleData.selected || styleData.open ? UM.Theme.getColor("xray") : menuBackgroundColor
                        radius: styleData.selected ? 3 : 0
                    }

                    label: Label {
                        //color: styleData.selected ? menuBackgroundColor : UM.Theme.getColor("xray")
                        text: styleData.text.replace("&","")
                    }



                    shortcut: Label {
                        //color: styleData.selected ? menuBackgroundColor : UM.Theme.getColor("xray")
                        text: styleData.shortcut
                    }

                }


            }
        }
    }

            // delegate: MenuBarItem {
        //     id: menuBarItem

        //     contentItem: Text {
        //         text: menuBarItem.text
        //         font: menuBarItem.font
        //         opacity: enabled ? 1.0 : 0.3
        //         color: menuBarItem.highlighted ? "#ffffff" : "#21be2b"
        //         horizontalAlignment: Text.AlignLeft
        //         verticalAlignment: Text.AlignVCenter
        //         elide: Text.ElideRight
        //     }

        //     background: Rectangle {
        //         implicitWidth: 40
        //         implicitHeight: 40
        //         opacity: enabled ? 1 : 0.3
        //         color: menuBarItem.highlighted ? "#21be2b" : "transparent"
        //     }
        // }

    SystemPalette {
        id: palette
        colorGroup: SystemPalette.Active
    }
}
