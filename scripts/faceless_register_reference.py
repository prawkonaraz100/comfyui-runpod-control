#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

IMAGE_EXTENSIONS = {
    "png": ".png",
    "jpeg": ".jpg",
    "webp": ".webp",
}


class RegistrationError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RegistrationError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RegistrationError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RegistrationError(f"{path} must contain a JSON object")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def detect_image_type(path: Path) -> str:
    with path.open("rb") as handle:
        header = handle.read(16)
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if header.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp"
    raise RegistrationError("source must be a PNG, JPEG, or WEBP image")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_destination_available(path: Path, replace: bool) -> None:
    if path.exists() and not replace:
        raise RegistrationError(
            f"destination already exists: {path}; pass --replace to overwrite it"
        )


def relative_asset_path(project_dir: Path, path: Path) -> str:
    return path.relative_to(project_dir).as_posix()


def register_reference(
    project_dir: Path,
    source: Path,
    kind: str,
    *,
    approve: bool,
    replace: bool,
) -> dict[str, Any]:
    project_dir = project_dir.resolve()
    source = source.resolve()

    if not project_dir.is_dir():
        raise RegistrationError(f"project directory does not exist: {project_dir}")
    if not source.is_file():
        raise RegistrationError(f"source image does not exist: {source}")

    image_type = detect_image_type(source)
    extension = IMAGE_EXTENSIONS[image_type]

    channel_path = project_dir / "channel.json"
    project_path = project_dir / "project.json"
    continuity_path = project_dir / "continuity.json"
    request_path = project_dir / "style-frame-request.json"

    channel = load_json(channel_path)
    project = load_json(project_path)
    continuity = load_json(continuity_path)

    if continuity.get("project_id") != project.get("project_id"):
        raise RegistrationError("continuity.project_id must match project.project_id")

    if kind == "style-frame":
        style_lock = continuity["style_lock"]
        destination = project_dir / "assets" / "style" / f"style-frame-v1{extension}"
        ensure_destination_available(destination, replace)

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        rel = relative_asset_path(project_dir, destination)

        channel["visual_identity"]["style_frame"]["path"] = rel
        channel["visual_identity"]["style_frame"]["status"] = (
            "approved" if approve else "pending"
        )
        project["approvals"]["style_frame"] = bool(approve)
        style_lock["canonical_reference"] = rel
        style_lock["status"] = "approved" if approve else "pending"

        if request_path.exists():
            request = load_json(request_path)
            request["output_path"] = rel
            request["status"] = "approved" if approve else "generated"
            write_json(request_path, request)

        write_json(channel_path, channel)
        write_json(project_path, project)
        write_json(continuity_path, continuity)

    elif kind == "character":
        if approve and not project["approvals"]["style_frame"]:
            raise RegistrationError(
                "cannot approve a canonical character before the style frame is approved"
            )

        character_lock = continuity["character_lock"]
        character_id = character_lock["character_id"]
        destination = (
            project_dir / "assets" / "characters" / f"{character_id}{extension}"
        )
        ensure_destination_available(destination, replace)

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        rel = relative_asset_path(project_dir, destination)

        character_lock["canonical_reference"] = rel
        character_lock["status"] = "approved" if approve else "pending"
        write_json(continuity_path, continuity)

    elif kind == "character-sheet":
        if approve:
            raise RegistrationError(
                "a character sheet cannot approve the canonical character lock; "
                "register a canonical character image with --kind character --approve"
            )

        character_lock = continuity["character_lock"]
        character_id = character_lock["character_id"]
        destination = (
            project_dir
            / "assets"
            / "characters"
            / f"{character_id}-sheet{extension}"
        )
        ensure_destination_available(destination, replace)

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        rel = relative_asset_path(project_dir, destination)

        character_lock["character_sheet"] = rel
        write_json(continuity_path, continuity)

    else:
        raise RegistrationError(f"unsupported reference kind: {kind}")

    return {
        "kind": kind,
        "path": rel,
        "sha256": sha256_file(destination),
        "approved": bool(approve),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize an approved faceless reference image into a project."
    )
    parser.add_argument("project_dir", type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument(
        "--kind",
        required=True,
        choices=("style-frame", "character", "character-sheet"),
    )
    parser.add_argument(
        "--approve",
        action="store_true",
        help="Mark the registered style frame or canonical character as approved.",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace an existing reference asset at the canonical destination.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        result = register_reference(
            args.project_dir,
            args.source,
            args.kind,
            approve=args.approve,
            replace=args.replace,
        )
    except (KeyError, RegistrationError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
