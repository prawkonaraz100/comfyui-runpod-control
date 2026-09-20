#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SCENE_ID_RE = re.compile(r"^scene-(\d{3})$")
VALID_STAGES = {"research", "style_frame", "proposal", "generation", "ready", "repair"}
VALID_STYLE_STATUSES = {"pending", "approved", "rejected"}
VALID_STYLE_REQUEST_STATUSES = {"pending", "generated", "approved", "rejected"}
VALID_SCENE_STATUSES = {"planned", "generating", "generated", "approved", "rejected"}
VALID_RENDER_STATUSES = {"not_started", "rendering", "ready", "failed"}


class ValidationError(Exception):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return data


def require(obj: dict[str, Any], key: str, expected: type, where: str) -> Any:
    if key not in obj:
        raise ValidationError(f"{where}: missing key '{key}'")
    value = obj[key]
    if not isinstance(value, expected):
        raise ValidationError(
            f"{where}.{key}: expected {expected.__name__}, got {type(value).__name__}"
        )
    return value


def require_nullable_string(obj: dict[str, Any], key: str, where: str) -> str | None:
    if key not in obj:
        raise ValidationError(f"{where}: missing key '{key}'")
    value = obj[key]
    if value is not None and not isinstance(value, str):
        raise ValidationError(f"{where}.{key}: expected string or null")
    return value


def validate_channel(channel: dict[str, Any]) -> None:
    if require(channel, "schema_version", int, "channel") != 1:
        raise ValidationError("channel.schema_version must be 1")

    channel_id = require(channel, "channel_id", str, "channel")
    if not SLUG_RE.fullmatch(channel_id):
        raise ValidationError("channel.channel_id must be a lowercase kebab-case slug")

    visual = require(channel, "visual_identity", dict, "channel")
    require(visual, "style_prompt", str, "channel.visual_identity")
    style_frame = require(visual, "style_frame", dict, "channel.visual_identity")
    style_status = require(style_frame, "status", str, "channel.visual_identity.style_frame")
    if style_status not in VALID_STYLE_STATUSES:
        raise ValidationError(
            f"channel.visual_identity.style_frame.status must be one of {sorted(VALID_STYLE_STATUSES)}"
        )
    style_path = require_nullable_string(
        style_frame, "path", "channel.visual_identity.style_frame"
    )
    if style_status == "approved" and not style_path:
        raise ValidationError("approved style frame requires a non-empty path")

    voice = require(channel, "voice", dict, "channel")
    require(voice, "tone", str, "channel.voice")
    require(voice, "provider", str, "channel.voice")
    require_nullable_string(voice, "voice_id", "channel.voice")

    defaults = require(channel, "defaults", dict, "channel")
    ratio = require(defaults, "aspect_ratio", str, "channel.defaults")
    if ratio not in {"16:9", "9:16"}:
        raise ValidationError("channel.defaults.aspect_ratio must be '16:9' or '9:16'")
    duration = require(defaults, "target_duration_seconds", int, "channel.defaults")
    if duration <= 0:
        raise ValidationError("channel.defaults.target_duration_seconds must be > 0")


def validate_project(project: dict[str, Any], channel: dict[str, Any]) -> None:
    if require(project, "schema_version", int, "project") != 1:
        raise ValidationError("project.schema_version must be 1")

    project_id = require(project, "project_id", str, "project")
    if not SLUG_RE.fullmatch(project_id):
        raise ValidationError("project.project_id must be a lowercase kebab-case slug")

    channel_id = require(project, "channel_id", str, "project")
    if channel_id != channel["channel_id"]:
        raise ValidationError("project.channel_id must match channel.channel_id")

    require(project, "topic", str, "project")
    refs = require(project, "reference_urls", list, "project")
    if not all(isinstance(item, str) and item for item in refs):
        raise ValidationError("project.reference_urls must contain only non-empty strings")

    stage = require(project, "workflow_stage", str, "project")
    if stage not in VALID_STAGES:
        raise ValidationError(f"project.workflow_stage must be one of {sorted(VALID_STAGES)}")

    approvals = require(project, "approvals", dict, "project")
    style_approved = require(approvals, "style_frame", bool, "project.approvals")
    proposal_approved = require(approvals, "production_proposal", bool, "project.approvals")

    channel_style_approved = (
        channel["visual_identity"]["style_frame"]["status"] == "approved"
    )
    if style_approved and not channel_style_approved:
        raise ValidationError(
            "project.approvals.style_frame cannot be true unless the channel style frame is approved"
        )

    if stage in {"generation", "ready", "repair"} and not (
        style_approved and proposal_approved
    ):
        raise ValidationError(
            "generation/ready/repair stages require both style_frame and production_proposal approval"
        )

    render = require(project, "render", dict, "project")
    render_status = require(render, "status", str, "project.render")
    if render_status not in VALID_RENDER_STATUSES:
        raise ValidationError(
            f"project.render.status must be one of {sorted(VALID_RENDER_STATUSES)}"
        )
    artifact = require_nullable_string(render, "final_artifact", "project.render")
    if render_status == "ready" and not artifact:
        raise ValidationError("ready render requires project.render.final_artifact")


def validate_style_frame_request(
    request: dict[str, Any], project: dict[str, Any], channel: dict[str, Any]
) -> None:
    if require(request, "schema_version", int, "style-frame-request") != 1:
        raise ValidationError("style-frame-request.schema_version must be 1")

    if require(request, "request_type", str, "style-frame-request") != "style_frame":
        raise ValidationError("style-frame-request.request_type must be 'style_frame'")

    if require(request, "project_id", str, "style-frame-request") != project["project_id"]:
        raise ValidationError("style-frame-request.project_id must match project.project_id")

    status = require(request, "status", str, "style-frame-request")
    if status not in VALID_STYLE_REQUEST_STATUSES:
        raise ValidationError(
            f"style-frame-request.status must be one of {sorted(VALID_STYLE_REQUEST_STATUSES)}"
        )

    prompt = require(request, "prompt", str, "style-frame-request")
    if not prompt.strip():
        raise ValidationError("style-frame-request.prompt must be non-empty")

    ratio = require(request, "aspect_ratio", str, "style-frame-request")
    if ratio != channel["defaults"]["aspect_ratio"]:
        raise ValidationError(
            "style-frame-request.aspect_ratio must match channel.defaults.aspect_ratio"
        )

    output_path = require(request, "output_path", str, "style-frame-request")
    if not output_path.strip():
        raise ValidationError("style-frame-request.output_path must be non-empty")


def validate_scenes(
    scenes_doc: dict[str, Any], project: dict[str, Any], channel: dict[str, Any]
) -> None:
    if require(scenes_doc, "schema_version", int, "scenes") != 1:
        raise ValidationError("scenes.schema_version must be 1")

    if require(scenes_doc, "project_id", str, "scenes") != project["project_id"]:
        raise ValidationError("scenes.project_id must match project.project_id")

    scenes = require(scenes_doc, "scenes", list, "scenes")
    if not scenes:
        if project["workflow_stage"] in {"research", "style_frame"}:
            return
        raise ValidationError(
            "scenes.scenes must contain at least one scene from proposal stage onward"
        )

    expected_order = 1
    total_duration = 0.0
    generated_states = {"generating", "generated", "approved"}

    for index, scene in enumerate(scenes, start=1):
        where = f"scenes.scenes[{index - 1}]"
        if not isinstance(scene, dict):
            raise ValidationError(f"{where} must be an object")

        scene_id = require(scene, "scene_id", str, where)
        match = SCENE_ID_RE.fullmatch(scene_id)
        if not match or int(match.group(1)) != expected_order:
            raise ValidationError(
                f"{where}.scene_id must equal scene-{expected_order:03d}"
            )

        order = require(scene, "order", int, where)
        if order != expected_order:
            raise ValidationError(f"{where}.order must equal {expected_order}")

        duration = scene.get("duration_seconds")
        if not isinstance(duration, (int, float)) or isinstance(duration, bool) or duration <= 0:
            raise ValidationError(f"{where}.duration_seconds must be a number > 0")
        total_duration += float(duration)

        narration = require(scene, "narration", str, where)
        if not narration.strip():
            raise ValidationError(f"{where}.narration must be non-empty")
        visual_prompt = require(scene, "visual_prompt", str, where)
        if not visual_prompt.strip():
            raise ValidationError(f"{where}.visual_prompt must be non-empty")

        status = require(scene, "status", str, where)
        if status not in VALID_SCENE_STATUSES:
            raise ValidationError(
                f"{where}.status must be one of {sorted(VALID_SCENE_STATUSES)}"
            )

        assets = require(scene, "assets", dict, where)
        still = require_nullable_string(assets, "still", f"{where}.assets")
        clip = require_nullable_string(assets, "clip", f"{where}.assets")

        if status in generated_states and not project["approvals"]["production_proposal"]:
            raise ValidationError(
                f"{where}: generated scene states require production proposal approval"
            )
        if status in {"generated", "approved"} and not clip:
            raise ValidationError(f"{where}: {status} scene requires assets.clip")
        if clip and not still:
            raise ValidationError(f"{where}: assets.clip requires assets.still")

        expected_order += 1

    target = float(channel["defaults"]["target_duration_seconds"])
    if total_duration > target + 2.0:
        raise ValidationError(
            f"scene duration total {total_duration:.2f}s exceeds target {target:.2f}s by more than 2s"
        )


def validate_project_dir(project_dir: Path) -> None:
    channel = load_json(project_dir / "channel.json")
    project = load_json(project_dir / "project.json")
    scenes = load_json(project_dir / "scenes.json")

    validate_channel(channel)
    validate_project(project, channel)

    request_path = project_dir / "style-frame-request.json"
    if project["workflow_stage"] == "style_frame":
        request = load_json(request_path)
        validate_style_frame_request(request, project, channel)
    elif request_path.exists():
        validate_style_frame_request(load_json(request_path), project, channel)

    validate_scenes(scenes, project, channel)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: faceless_validate.py PROJECT_DIR", file=sys.stderr)
        return 64

    project_dir = Path(argv[1])
    try:
        validate_project_dir(project_dir)
    except ValidationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    scenes = load_json(project_dir / "scenes.json")["scenes"]
    print(
        f"PASS: {project_dir} "
        f"(stage={load_json(project_dir / 'project.json')['workflow_stage']}, scenes={len(scenes)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
