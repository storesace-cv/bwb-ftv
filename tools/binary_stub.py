#!/usr/bin/env python3
"""Ferramenta auxiliar para preparar ficheiros binários antes do commit.

Esta "stub" cria uma representação textual ou um pacote comprimido de um
ficheiro binário, permitindo contornar políticas que bloqueiem o envio
direto desses binários para o repositório. O conteúdo convertido pode ser
incluído no controlo de versões e, mais tarde, reconstruído no destino.
"""
from __future__ import annotations

import argparse
import base64
from pathlib import Path
import textwrap
import zipfile


def prepare_binary_stub(path: Path, strategy: str = "base64") -> Path:
    """Transforma ``path`` segundo ``strategy`` e devolve o caminho resultante.

    Parameters
    ----------
    path:
        Caminho para o ficheiro binário original.
    strategy:
        Estratégia de preparação. As opções disponíveis são:

        ``"base64"``
            Gera um ficheiro ``.b64`` com o conteúdo codificado em Base64
            (texto puro), apto para commit em repositórios que rejeitam
            binários.
        ``"zip"``
            Cria um arquivo ``.zip`` com compressão ``ZIP_DEFLATED``. Útil
            quando a política apenas bloqueia extensões específicas.

    Returns
    -------
    Path
        Caminho para o ficheiro convertido.
    """

    if not path.exists() or not path.is_file():
        msg = f"ficheiro inexistente ou inválido: {path}"
        raise FileNotFoundError(msg)

    strategy = strategy.lower()

    if strategy == "base64":
        output_path = path.with_suffix(path.suffix + ".b64")
        output_path.write_bytes(base64.b64encode(path.read_bytes()))
        return output_path

    if strategy == "zip":
        output_path = path.with_suffix(path.suffix + ".zip")
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(path, arcname=path.name)
        return output_path

    msg = "estratégia desconhecida: {} (use 'base64' ou 'zip')".format(strategy)
    raise ValueError(msg)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stub para preparar ficheiros binários antes do commit"
    )
    parser.add_argument(
        "ficheiro",
        type=Path,
        help="caminho para o ficheiro binário que precisa de ser transformado",
    )
    parser.add_argument(
        "--estrategia",
        "-e",
        choices=("base64", "zip"),
        default="base64",
        help="método a aplicar (base64 cria texto, zip comprime)",
    )
    return parser


def _format_instructions(output_path: Path, strategy: str) -> str:
    if strategy == "base64":
        return textwrap.dedent(
            f"""
            Ficheiro preparado: {output_path}
            Para restaurar o binário original:
              base64 --decode {output_path} > {output_path.with_suffix('')}
            (em Windows pode usar `certutil -decode`).
            """
        ).strip()

    return textwrap.dedent(
        f"""
        Ficheiro preparado: {output_path}
        Para restaurar o binário original:
          unzip {output_path}
        """
    ).strip()


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    output_path = prepare_binary_stub(args.ficheiro, args.estrategia)
    print(_format_instructions(output_path, args.estrategia))


if __name__ == "__main__":
    main()
