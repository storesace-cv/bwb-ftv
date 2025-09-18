import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    objectName: tag.length > 0 ? "zone_" + tag.replace(/\./g, "_") : "zone"
    implicitWidth: Math.max(zoneBody.implicitWidth + 24, overlayBadge.visible ? overlayBadge.width + 12 : 0)
    implicitHeight: Math.max(zoneBody.implicitHeight + 24, overlayBadge.visible ? overlayBadge.height + 12 : 0)
    Layout.fillWidth: true
    Layout.preferredHeight: implicitHeight

    property string tag: ""
    property var metadataMap: (typeof zonesMetadata !== "undefined") ? zonesMetadata : null
    property var metadata: metadataMap && tag.length > 0 && metadataMap[tag] !== undefined ? metadataMap[tag] : null
    property int level: metadata && metadata.level !== undefined ? metadata.level : 0
    property string title: ""
    property string zoneType: metadata && metadata.zoneType ? metadata.zoneType : ""
    property string widgetType: metadata && metadata.widgetType ? metadata.widgetType : ""
    property string widgetQtClass: metadata && metadata.widgetQtClass ? metadata.widgetQtClass : ""
    property string baseStyleLabel: metadata && metadata.baseStyleLabel ? metadata.baseStyleLabel : ""
    property bool showOverlays: false
    property string metadataKey: ""
    property string overlayMetadata: {
        var values = [zoneType, widgetQtClass, widgetType, baseStyleLabel]
                .filter(function(value) {
                    return value && value.length > 0;
                });
        return values.join(" | ");
    }
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

    ColumnLayout {
        id: zoneBody
        anchors.fill: parent
        anchors.margins: 12
        spacing: 8
        implicitWidth: contentWidth
        implicitHeight: contentHeight

        Label {
            id: titleLabel
            text: root.title
            font.bold: true
            font.pixelSize: 16
            color: "#253858"
            visible: text.length > 0
            Layout.fillWidth: true
        }

        Label {
            id: valueLabel
            objectName: root.objectName + "_value"
            text: root.displayValue
            color: "#42526e"
            wrapMode: Text.WordWrap
            visible: text.length > 0
            Layout.fillWidth: true
        }

        Item {
            id: contentSlot
            implicitWidth: childrenRect.width
            implicitHeight: childrenRect.height
            Layout.fillWidth: true
        }
    }

    Rectangle {
        id: overlayBadge
        visible: overlayActive && root.tag.length > 0
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 6
        radius: 4
        border.width: 1
        border.color: "#4a6fa5"
        color: "#ffffff"
        width: overlayContent.implicitWidth + 8
        height: overlayContent.implicitHeight + 8

        Column {
            id: overlayContent
            anchors.fill: parent
            anchors.margins: 4
            spacing: root.overlayMetadata.length > 0 ? 2 : 0

            Label {
                id: overlayTag
                text: root.tag
                font.pixelSize: 12
                color: "#1f4a8a"
                wrapMode: Text.NoWrap
                verticalAlignment: Text.AlignVCenter
            }

            Label {
                id: overlayMetadataLabel
                text: root.overlayMetadata
                visible: text.length > 0
                font.pixelSize: 11
                color: "#1f4a8a"
                wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                verticalAlignment: Text.AlignVCenter
            }
        }
    }
}
