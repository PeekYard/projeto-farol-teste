#!/usr/bin/env python3
"""Guarda de autoria: executada exclusivamente a partir da main confiável do projeto."""
import json
import os
import re
import sys
from pathlib import Path


def is_authorized(pr, config):
    actor = pr.get("user") or {}
    if (pr.get("base") or {}).get("ref") != "main":
        return False
    if actor.get("id") == config.get("authorized_author_id"):
        return True
    head = pr.get("head") or {}
    head_repo = head.get("repo") or {}
    branch = head.get("ref", "")
    bot = config.get("provisioner_bot_login", "")
    if (actor.get("login") == bot
            and actor.get("type") == "Bot"
            and head_repo.get("full_name", "").lower() == os.environ.get("GITHUB_REPOSITORY", "").lower()
            and re.fullmatch(r"submission/issue-[0-9]+-[0-9a-f]{8}", branch)):
        return True
    return False


def main():
    if os.environ.get("GITHUB_EVENT_NAME") != "pull_request":
        raise RuntimeError("PR Guard executa somente em evento pull_request")
    data = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    pr = data.get("pull_request")
    if not isinstance(pr, dict):
        raise ValueError("Evento sem PR")
    config = json.loads(Path(".peekyard/author.json").read_text())
    if not isinstance(config.get("authorized_author_id"), int):
        raise ValueError("Identificador de proprietário inválido")
    if not re.fullmatch(r"[a-z0-9-]+\[bot\]", config.get("provisioner_bot_login", "")):
        raise ValueError("Identificação do bot inválida")
    if is_authorized(pr, config):
        print("PR de autor autorizado. Ainda exige aprovação de PeekYardMaster.")
    else:
        raise PermissionError("PR não admitido: o autor não está autorizado neste projeto")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, PermissionError, KeyError) as exc:
        print("PR GUARD REPROVADO:", str(exc), file=sys.stderr)
        sys.exit(1)
