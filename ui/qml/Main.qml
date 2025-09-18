import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "components"

ApplicationWindow {
    id: root
    visible: true
    width: 1180
    height: 860
    title: qsTr("Ficha Técnica (Qt Quick)")

    property var product: productModel ? productModel : ({})
    property bool showDevOverlays: overlayController ? overlayController.showOverlays : false

    background: Rectangle {
        color: "#f3f6fb"
    }

    ColumnLayout {
        id: layoutRoot
        anchors.fill: parent
        anchors.margins: 24
        spacing: 24

        Block {
            id: identificationBlock
            objectName: "block_identificacao"
            Layout.fillWidth: true
            title: qsTr("Identificação do Produto")
            product: root.product
            showOverlays: root.showDevOverlays

            Zone {
                tag: "B1.C1"
                title: qsTr("Código")
                zoneType: "bloco-dados-gerais"
                widgetType: "campo"
                widgetQtClass: "QLineEdits"
                metadataKey: "code"
                product: identificationBlock.product
                showOverlays: identificationBlock.showOverlays
            }

            Zone {
                tag: "B1.C2"
                title: qsTr("Designação")
                zoneType: "bloco-dados-gerais"
                widgetType: "campo"
                widgetQtClass: "QLineEdits"
                metadataKey: "name"
                product: identificationBlock.product
                showOverlays: identificationBlock.showOverlays
            }
        }

        Block {
            id: technicalBlock
            objectName: "block_dados_tecnicos"
            Layout.fillWidth: true
            title: qsTr("Dados Técnicos")
            product: root.product
            showOverlays: root.showDevOverlays

            Zone {
                tag: "B2.C1"
                title: qsTr("Estado")
                zoneType: "bloco-ingredientes"
                widgetType: "tabela"
                widgetQtClass: "QTableViews"
                metadataKey: "estado"
                product: technicalBlock.product
                showOverlays: technicalBlock.showOverlays
            }

            Zone {
                tag: "B2.C2"
                title: qsTr("Validade")
                zoneType: "bloco-ingredientes"
                widgetType: "tabela"
                widgetQtClass: "QTableViews"
                metadataKey: "validade"
                product: technicalBlock.product
                showOverlays: technicalBlock.showOverlays
            }
        }

        Block {
            id: overlayBlock
            objectName: "block_overlays"
            Layout.fillWidth: true
            title: qsTr("Informação Complementar")
            product: root.product
            showOverlays: root.showDevOverlays

            Zone {
                tag: "B3.C1"
                title: qsTr("Observações")
                zoneType: "bloco-food-cost"
                widgetType: "campo"
                widgetQtClass: "QLineEdits"
                metadataKey: "observacoes"
                product: overlayBlock.product
                showOverlays: overlayBlock.showOverlays
            }
        }

        Item {
            Layout.fillHeight: true
            Layout.fillWidth: true
        }
    }
}
