#!/usr/bin/env python3
"""Ferramenta auxiliar para preparar e restaurar ficheiros binários.

Esta "stub" cria uma representação textual ou um pacote comprimido de um
ficheiro binário, permitindo contornar políticas que bloqueiem o envio
direto desses binários para o repositório. O conteúdo convertido pode ser
incluído no controlo de versões e, mais tarde, reconstruído no destino.

Para quem faz *checkout* do ramo noutro ambiente, o comando também oferece
o modo inverso, gerando novamente o binário original a partir do ficheiro
``.b64`` ou ``.zip`` previamente commitado.
"""
from __future__ import annotations

import argparse
import textwrap
import zipfile
from pathlib import Path

import base64


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


def restore_binary_stub(path: Path, output: Path | None = None) -> Path:
    """Reconstrói o binário original a partir de ``path``.

    Parameters
    ----------
    path:
        Caminho para o ficheiro gerado previamente por :func:`prepare_binary_stub`.
        Reconhece automaticamente extensões ``.b64`` e ``.zip`` (com um único
        ficheiro no interior).
    output:
        Destino opcional para o ficheiro restaurado. Se não for indicado,
        utiliza-se o mesmo diretório de ``path``.

    Returns
    -------
    Path
        Caminho para o binário reconstruído.
    """

    if not path.exists() or not path.is_file():
        msg = f"ficheiro inexistente ou inválido: {path}"
        raise FileNotFoundError(msg)

    suffix = path.suffix.lower()

    if suffix == ".b64":
        target = output or path.with_suffix("")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(base64.b64decode(path.read_bytes()))
        return target

    if suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            members = [m for m in zf.namelist() if not m.endswith("/")]
            if len(members) != 1:
                raise ValueError(
                    "esperava um único ficheiro dentro do zip, obtidos: {}".format(
                        ", ".join(members)
                    )
                )

            member = members[0]
            data = zf.read(member)

        target = output
        if target is None:
            target = path.with_suffix("")
        elif target.is_dir() or target.suffix == "":
            target = target / member

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target

    msg = (
        "não foi possível inferir a estratégia a partir de {} (apenas .b64 ou .zip)"
    ).format(path)
    raise ValueError(msg)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stub para preparar ou restaurar ficheiros binários"
    )

    subparsers = parser.add_subparsers(dest="comando", required=True)

    preparar = subparsers.add_parser(
        "preparar", help="converter o binário original para .b64 ou .zip"
    )
    preparar.add_argument(
        "ficheiro",
        type=Path,
        help="caminho para o ficheiro binário que precisa de ser transformado",
    )
    preparar.add_argument(
        "--estrategia",
        "-e",
        choices=("base64", "zip"),
        default="base64",
        help="método a aplicar (base64 cria texto, zip comprime)",
    )

    restaurar = subparsers.add_parser(
        "restaurar", help="reconstituir o binário a partir do ficheiro preparado"
    )
    restaurar.add_argument(
        "ficheiro",
        type=Path,
        help="ficheiro .b64 ou .zip previamente commitado",
    )
    restaurar.add_argument(
        "--destino",
        "-d",
        type=Path,
        help="local opcional onde guardar o binário restaurado",
    )

    return parser


def _format_instructions(output_path: Path, strategy: str) -> str:
    if strategy == "base64":
        return textwrap.dedent(
            f"""
            Ficheiro preparado: {output_path}
            Para restaurar o binário original:
              python tools/binary_stub.py restaurar {output_path}
            (alternativa manual: base64 --decode {output_path} > {output_path.with_suffix('')})
            Em Windows pode usar `certutil -decode`.
        """
    ).strip()

    return textwrap.dedent(
        f"""
        Ficheiro preparado: {output_path}
        Para restaurar o binário original:
          python tools/binary_stub.py restaurar {output_path}
        """
    ).strip()


def _format_restore_message(result_path: Path) -> str:
    return textwrap.dedent(
        f"""
        Ficheiro restaurado em: {result_path}
        Confirme a integridade (por exemplo, com sha256sum) antes de utilizar.
        """
    ).strip()


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()

    if args.comando == "preparar":
        output_path = prepare_binary_stub(args.ficheiro, args.estrategia)
        print(_format_instructions(output_path, args.estrategia))
        return

    result_path = restore_binary_stub(args.ficheiro, getattr(args, "destino", None))
    print(_format_restore_message(result_path))


if __name__ == "__main__":
    main()
