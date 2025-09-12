"""Utilitários gerais para o projeto FTV."""

from pathlib import Path


def get_project_root() -> Path:
    """Devolve o diretório raiz do projeto.

    A raiz corresponde ao diretório que contém as pastas principais do
    repositório (por exemplo, ``databases`` e ``ftv_project``).
    Esta função é preferível a depender de ``Path.parents[3]`` espalhado
    pelos módulos, tornando o cálculo do caminho mais estável.
    """

    return Path(__file__).resolve().parents[3]


__all__ = ["get_project_root"]
