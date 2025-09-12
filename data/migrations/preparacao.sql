-- Fase 3 — Migração para bloco [B4] Preparação
-- Cria a tabela de preparação, caso não exista.
-- É idempotente; pode ser corrido quantas vezes quiser.
-- Diagnóstico: se der erro aqui, confirme que o ficheiro databases/ftv.db existe e é uma BD SQLite válida.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS produto_preparacao (
    produto_codigo TEXT PRIMARY KEY,
    html           TEXT NOT NULL DEFAULT '',
    CONSTRAINT fk_produto
        FOREIGN KEY (produto_codigo) REFERENCES produtos(codigo)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- Índice auxiliar (redundante com PK, mas mantido por clareza futura)
CREATE INDEX IF NOT EXISTS idx_produto_preparacao_codigo ON produto_preparacao(produto_codigo);