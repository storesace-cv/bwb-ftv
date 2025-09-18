import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: root
    objectName: tag.length > 0 ? "zone_" + tag.replace(/\./g, "_") : "zone"
    width: 320
    height: 160
    implicitWidth: 320
    implicitHeight: 160

    property string tag: ""
    property int level: 0
    property string title: ""
    property string zoneType: ""
    property string widgetType: ""
    property string widgetQtClass: ""
    property string baseStyleLabel: ""
    property bool showOverlays: false
    property string metadataKey: ""
    property var product: ({})
    property string displayValue: {
        if (!metadataKey || !product) {
            return "";
        }
        var value = product[metadataKey];
        if (value === undefined || value === null) {
            return "";
        }
        return String(value);
    }
    property bool overlayActive: showOverlays
    default property alias content: contentSlot.children

    readonly property var overlayPalette: [
        "#eafbf1",
        "#eef5ff",
        "#fff5e8",
        "#f7f0ff",
        "#fff0f0"
    ]

    Rectangle {
        id: background
        anchors.fill: parent
        radius: 12
        border.width: overlayActive ? 2 : 1
        border.color: overlayActive ? "#4a6fa5" : "#ccd4e0"
        color: overlayActive ? overlayPalette[level % overlayPalette.length] : "#ffffff"
    }

    Column {
        id: zoneBody
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8

        Label {
            id: titleLabel
            text: root.title
            font.bold: true
            font.pixelSize: 16
            color: "#253858"
            visible: text.length > 0
        }

        Label {
            id: valueLabel
            objectName: root.objectName + "_value"
            text: root.displayValue
            color: "#42526e"
            wrapMode: Text.WordWrap
            visible: text.length > 0
        }

        Item {
            id: contentSlot
            anchors.left: parent.left
            anchors.right: parent.right
            height: childrenRect.height
        }
    }

    Label {
        id: overlayTag
        text: root.tag
        visible: overlayActive && text.length > 0
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 6
        font.pixelSize: 12
        color: "#1f4a8a"
        background: Rectangle {
            radius: 4
            border.width: 1
            border.color: "#4a6fa5"
            color: "#ffffff"
        }
        padding: 4
    }
}
