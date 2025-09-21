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
    property string styleDevInfo: metadata && metadata.styleDevInfo ? metadata.styleDevInfo : ""
    property bool showOverlays: false
    property string metadataKey: ""
    property string overlayMetadata: {
        var values = [zoneType, widgetQtClass, widgetType, baseStyleLabel, styleDevInfo]
                .filter(function(value) {
                    return value && value.length > 0;
                });
        return values.join(" | ");
    }
    property var product: ({})
    property string overlayTooltipText: {
        var lines = [];
        lines.push("Tag: " + (tag || ""));
        lines.push("Title: " + (title || ""));
        lines.push("Zone type: " + (zoneType || ""));
        lines.push("Widget type: " + (widgetType || ""));
        lines.push("Widget Qt class: " + (widgetQtClass || ""));
        lines.push("Style dev info: " + (styleDevInfo || ""));
        lines.push("Metadata key: " + (metadataKey || ""));

        var productSummary = "";
        if (product && typeof product === "object") {
            var productKeys = Object.keys(product);
            if (productKeys.length > 0) {
                productSummary = productKeys.map(function(key) {
                    return key + ": " + product[key];
                }).join(", ");
            }
        }
        lines.push("Product: " + productSummary);
        lines.push("Show overlays: " + (showOverlays ? "true" : "false"));

        return lines.join("\n");
    }
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

    property string overlayBaseColor: metadata && metadata.overlayBaseColor ? metadata.overlayBaseColor : ""
    property string overlayMetadataColor: metadata && metadata.overlayColor ? metadata.overlayColor : ""
    property real overlayLightenStep: (typeof zoneOverlayLightenStep !== "undefined") ? zoneOverlayLightenStep : 0.18
    property real overlayLightenMax: (typeof zoneOverlayLightenMax !== "undefined") ? zoneOverlayLightenMax : 0.85
    property string overlayColor: {
        if (!overlayActive) {
            return "#ffffff";
        }
        if (overlayBaseColor && overlayBaseColor.length === 7) {
            var computed = lightenColor(overlayBaseColor, level);
            if (overlayMetadataColor && overlayMetadataColor.length === 7 && overlayMetadataColor !== computed) {
                return overlayMetadataColor;
            }
            return computed;
        }
        if (overlayMetadataColor && overlayMetadataColor.length === 7) {
            return overlayMetadataColor;
        }
        return "#ffffff";
    }

    function clamp(value, minimum, maximum) {
        if (value < minimum) {
            return minimum;
        }
        if (value > maximum) {
            return maximum;
        }
        return value;
    }

    function hexToRgb(hex) {
        var clean = hex.replace(/^#/, "");
        if (clean.length !== 6) {
            return { r: 255, g: 255, b: 255 };
        }
        return {
            r: parseInt(clean.slice(0, 2), 16),
            g: parseInt(clean.slice(2, 4), 16),
            b: parseInt(clean.slice(4, 6), 16)
        };
    }

    function rgbToHex(r, g, b) {
        function toHex(value) {
            var clamped = clamp(Math.round(value), 0, 255).toString(16);
            return clamped.length === 1 ? "0" + clamped : clamped;
        }
        return "#" + toHex(r) + toHex(g) + toHex(b);
    }

    function mixWithWhite(hex, ratio) {
        var rgb = hexToRgb(hex);
        var blend = clamp(ratio, 0.0, 1.0);
        var r = rgb.r + (255 - rgb.r) * blend;
        var g = rgb.g + (255 - rgb.g) * blend;
        var b = rgb.b + (255 - rgb.b) * blend;
        return rgbToHex(r, g, b);
    }

    function lightenColor(hex, levelValue) {
        var ratio = clamp(levelValue * overlayLightenStep, 0.0, overlayLightenMax);
        return mixWithWhite(hex, ratio);
    }

    Rectangle {
        id: background
        anchors.fill: parent
        radius: 12
        border.width: overlayActive ? 2 : 1
        border.color: overlayActive ? "#4a6fa5" : "#ccd4e0"
        color: overlayColor
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
            implicitWidth: {
                if (childrenRect.width > 0) {
                    return childrenRect.width;
                }

                var maxImplicitWidth = 0;
                for (var i = 0; i < children.length; ++i) {
                    var child = children[i];
                    if (!child || !child.visible) {
                        continue;
                    }

                    if (child.implicitWidth !== undefined && child.implicitWidth > maxImplicitWidth) {
                        maxImplicitWidth = child.implicitWidth;
                    } else if (child.contentWidth !== undefined && child.contentWidth > maxImplicitWidth) {
                        maxImplicitWidth = child.contentWidth;
                    } else if (child.width !== undefined && child.width > maxImplicitWidth) {
                        maxImplicitWidth = child.width;
                    }
                }

                return maxImplicitWidth;
            }
            implicitHeight: {
                if (childrenRect.height > 0) {
                    return childrenRect.height;
                }

                var maxImplicitHeight = 0;
                for (var i = 0; i < children.length; ++i) {
                    var child = children[i];
                    if (!child || !child.visible) {
                        continue;
                    }

                    var implicitHeight = 0;
                    if (child.implicitHeight !== undefined && child.implicitHeight > implicitHeight) {
                        implicitHeight = child.implicitHeight;
                    } else if (child.contentHeight !== undefined && child.contentHeight > implicitHeight) {
                        implicitHeight = child.contentHeight;
                    } else if (child.height !== undefined && child.height > implicitHeight) {
                        implicitHeight = child.height;
                    }

                    if (implicitHeight > maxImplicitHeight) {
                        maxImplicitHeight = implicitHeight;
                    }
                }

                return maxImplicitHeight;
            }
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

        HoverHandler {
            id: overlayHoverHandler
            acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
            enabled: overlayBadge.visible
        }

        ToolTip {
            id: overlayTooltip
            parent: overlayBadge
            visible: overlayHoverHandler.hovered && overlayBadge.visible
            text: root.overlayTooltipText
        }
    }
}
