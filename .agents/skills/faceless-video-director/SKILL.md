---
name: faceless-video-director
description: Build or continue a faceless-video production in this repository. Use when the user asks for a faceless script, research package, style frame, character lock, style lock, scene plan, scene generation, continuity-safe scene repair, voiceover plan, storyboard, or final faceless-video package. Supports SHORT (20-60s) and LONG (5-10m) explainers/documentaries/true-crime. Do not use for unrelated coding or generic image requests that are not part of a faceless-video workflow.
---

# Faceless Video Director

Use this skill as the production director for faceless-video work in this repository.

The repository workflow target is `docs/FACELESS_WORKFLOW_V1.md`. Until V1 parity is demonstrated, do not redesign that workflow or add unrelated production features.

## Non-negotiable operating rules

1. Do not introduce OpenAI API calls or paid token usage. Use the Codex session itself and the generation/render tools already available to the project unless the user explicitly approves another paid backend.
2. Treat approved visual references as production assets, not as inspiration.
3. Never rely on a text prompt alone for character continuity once a character reference exists.
4. Never use the previous generated scene as the only character reference. Always anchor a new scene to the canonical character reference and canonical style reference. This prevents cumulative visual drift.
5. Do not silently change a locked character, wardrobe, palette, illustration language, aspect ratio, voice identity, or pacing rule.
6. A storyboard contact sheet is a planning artifact only. Do not use a multi-panel storyboard as the final image asset for multiple scenes.
7. If one scene fails continuity or content QA, reject and regenerate only that scene. Preserve unaffected scenes, narration timing, and approved assets.
8. Keep generated text out of base artwork when practical. Prefer deterministic/programmatic overlays for titles, labels, captions, numbers, and Polish text.
9. When a generation tool supports reference images, provide both the canonical character reference and canonical style reference. When it supports IDs, seeds, or generation metadata, preserve them, but never treat a seed alone as a continuity lock.
10. Do not claim a stage is complete until its required artifact exists and the relevant validation/quality checks pass.

## Sources of truth

Before producing or repairing a project, inspect in this order:

1. `docs/FACELESS_WORKFLOW_V1.md`
2. the current project `channel.json`
3. the current project `project.json`
4. the current project `style-frame-request.json`, if present
5. the current project `scenes.json`
6. the project's canonical reference assets and continuity manifest
7. `references/script-writer-source.md` when writing or rewriting the script

If code, manifests, and documentation disagree, report the discrepancy. Do not silently change architectural assumptions.

## Modes

### SHORT

Use for approximately 20-60 seconds.

Default production rhythm:
- 5-10 visual beats,
- usually 3-6 seconds per beat,
- a direct hook in the opening seconds,
- no long trailer,
- no filler intro,
- one clear idea per spoken sentence,
- visual change normally no slower than every 5 seconds unless a deliberate hold is justified.

### LONG

Use for approximately 5-10 minutes unless the user specifies otherwise.

Follow the niche blueprints, research requirements, retention rules, title rules, and fact-check rules in `references/script-writer-source.md`.

## Production workflow

Follow these stages in order unless the project is resuming from a later confirmed stage.

### 1. Research

Given a channel, video, niche, reference, or topic:

- research the subject,
- identify reusable topic/title/story patterns without copying creator wording or identity,
- verify factual claims before scripting,
- record source URLs or source notes in the project research material,
- propose the production direction before spending generation/render resources.

For factual scripts, verify core facts against at least two independent reliable sources when research tools are available. If a key fact cannot be verified, remove it or mark the uncertainty explicitly.

### 2. Script

For writing rules, read `references/script-writer-source.md`.

For SHORT mode, adapt the source rules rather than using its default 5-8 minute length:
- write the body first when useful, then sharpen the hook,
- keep the hook immediate,
- use concrete nouns, actions, dates, amounts, places, and objects,
- remove filler transitions,
- keep narration easy to speak,
- map every sentence or clause to a visual beat.

Output a timecoded script with:
- `VO`
- `VISUAL`
- duration estimate
- fact-check notes for factual claims

### 3. Create one style frame

Before full scene generation, create exactly one representative image for the proposed visual language.

The style frame establishes:
- illustration/rendering language,
- palette,
- lighting,
- background detail level,
- icon language,
- line/shading treatment,
- composition density.

Do not treat a style frame as approved until the user approves it.

Store its exact asset path/reference and generation metadata when available.

### 4. Create the canonical character lock

After style approval, create or select a canonical character asset.

Minimum character lock:

```yaml
character_id: driver-01
canonical_reference: assets/characters/driver-01.png
faceless: true
locked_traits:
  hair:
  head_shape:
  skin_tone:
  body_proportions:
  outerwear:
  shirt:
  trousers:
  shoes:
  backpack:
  hand_style:
forbidden_changes:
  - facial features
  - hair restyle
  - wardrobe replacement
  - body-proportion drift
```

For a recurring character, create a character sheet when possible:
- front,
- 3/4,
- side,
- back,
- neutral standing,
- walking,
- sitting,
- holding a common prop.

A character sheet supplements the canonical reference; it does not replace the canonical identity asset.

### 5. Create the canonical style lock

Create a style manifest that points to the approved style-frame asset.

Minimum style lock:

```yaml
style_id: channel-style-v1
canonical_reference: assets/style/style-frame-v1.png
palette:
line_language:
shading:
lighting:
background_density:
icon_language:
composition_rules:
typography_overlay_rules:
forbidden_changes:
```

For PrawkoNaRaz work, the project may intentionally use the house brand. The source script-writer rule against brand names does not prohibit the user's own approved brand identity.

### 6. Build scene manifests

Every scene must reference the canonical locks explicitly.

Minimum scene shape:

```json
{
  "scene_id": "scene-002",
  "start_seconds": 4.0,
  "duration_seconds": 5.0,
  "narration": "Po zdanym egzaminie wynik trafia do systemu.",
  "visual_goal": "Show the exam result moving into the official digital process.",
  "character_id": "driver-01",
  "style_id": "channel-style-v1",
  "references": {
    "character": "assets/characters/driver-01.png",
    "style": "assets/style/style-frame-v1.png"
  },
  "locked_traits": [
    "hair",
    "head shape",
    "dark grey jacket",
    "white t-shirt",
    "black backpack",
    "faceless appearance"
  ],
  "allowed_changes": [
    "pose",
    "camera framing",
    "location",
    "scene props"
  ],
  "forbidden_changes": [
    "new face",
    "new haircut",
    "new wardrobe",
    "different illustration style"
  ]
}
```

Do not generate a scene until required canonical references exist.

### 7. Generate scene assets

For each scene:

1. Load the canonical character reference.
2. Load the canonical style reference.
3. Apply only the scene's allowed changes.
4. Generate one candidate at a time when continuity is still being established.
5. Save the output and generation metadata.
6. Run continuity QA before moving to the next scene.

Do not create all remaining scenes in one unreviewed batch until the first consecutive scenes prove the lock is stable.

### 8. Continuity QA

Check each generated scene against the canonical locks.

At minimum verify:

- same character identity,
- same faceless treatment,
- same hair shape/color,
- same wardrobe and backpack unless explicitly changed,
- same body proportions,
- same illustration/render style,
- same palette and shading family,
- same vehicle/environment design language where recurring,
- correct aspect ratio,
- no unwanted AI text baked into the image,
- no extra limbs or malformed hands that materially harm the scene.

Record a simple result:

```json
{
  "scene_id": "scene-002",
  "continuity": "pass",
  "content": "pass",
  "notes": []
}
```

If continuity fails, do not accept the scene just because the subject matter is correct.

### 9. Voice and timing

Use the approved channel voice/tone.

- Narration is the timing authority.
- Scene duration should serve the spoken line.
- Do not rewrite approved narration merely to fit a failed visual.
- Preserve pronunciations and timing when repairing a visual scene.

### 10. Animate and assemble

When animation/video tools are available:

- animate scenes independently,
- preserve scene boundaries,
- keep narration as the master timeline,
- add deterministic overlays separately when practical,
- assemble the final timeline,
- render a review version before final output.

### 11. Scene-level repair

When the user says a specific scene is wrong:

1. Identify the exact scene.
2. Keep narration and duration unchanged unless the user asks otherwise.
3. Reload canonical character and style references.
4. Change only the rejected property.
5. Regenerate only that scene.
6. Re-run continuity QA.
7. Replace only that scene in the timeline.
8. Re-render the final output.

Never regenerate the full film merely because one scene failed.

## Continuity file

From `proposal` onward, `continuity.json` is required and both locks must have `status: "approved"`. The validator treats the manifest as the canonical source for scene identity/style references.

Current schema:

```json
{
  "schema_version": 1,
  "project_id": "demo-episode-001",
  "character_lock": {
    "status": "approved",
    "character_id": "driver-01",
    "canonical_reference": "assets/characters/driver-01.png",
    "character_sheet": "assets/characters/driver-01-sheet.png",
    "locked_traits": {
      "faceless": true,
      "hair": "short wavy brown hair",
      "outerwear": "dark grey overshirt jacket"
    },
    "forbidden_changes": [
      "facial features",
      "hair restyle",
      "wardrobe replacement",
      "body-proportion drift"
    ]
  },
  "style_lock": {
    "status": "approved",
    "style_id": "channel-style-v1",
    "canonical_reference": "assets/style/style-frame-v1.png",
    "rules": {
      "palette": "approved channel palette",
      "rendering": "approved illustration language"
    },
    "forbidden_changes": [
      "different illustration language",
      "unapproved palette shift"
    ]
  }
}
```

Rules enforced by `scripts/faceless_validate.py`:
- `project_id` must match `project.json`,
- lock IDs are lowercase kebab-case,
- approved locks require non-empty canonical references,
- the approved style reference must exactly match `channel.visual_identity.style_frame.path`,
- approved character/style locks require non-empty traits/rules and forbidden-change lists,
- every scene from `proposal` onward must match the canonical IDs and reference paths and must declare explicit lock/allowed/forbidden change lists.

The exact schema may evolve only through an explicit repository change with tests and documentation. Do not invent incompatible per-project formats ad hoc.

## What to do when tools are missing

If the current Codex environment cannot generate an image, voice, or video:

- complete all upstream artifacts that are possible,
- produce the exact generation manifest/prompt/reference list required by the missing step,
- identify the missing tool boundary precisely,
- do not pretend the media asset was created.

## Completion criteria

A faceless project is not complete merely because a script or storyboard exists.

For V1, completion remains governed by `docs/FACELESS_WORKFLOW_V1.md`, including:
- approved style frame,
- stable reusable channel identity,
- generated scenes,
- final MP4,
- scene-level repair,
- reuse of the same identity in a second episode.
