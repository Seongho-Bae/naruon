# Naruon UI/UX Individual Assets (2026-06-22)

This directory contains deterministic crop assets derived from the unified
Naruon UI/UX visual repository.

## Source Scope

- `docs/ui-ux/mockups/mockup_01.png` through `mockup_41.png`
- `docs/ui-ux/reference-set-2026-06-18/images/ui-ux-reference-01.png`
  through `ui-ux-reference-45.png`
- `frontend/branding/naruon-ux-mockup-*.png` as exact SHA-256 aliases only

The original PNG files remain the authority. These crops are review and
implementation aids, not replacements for the source images.

## Split Rule

`build_assets.py` applies one fixed image rule to every unique source SHA:

1. Resize the source to 30% for stable component detection.
2. Mark foreground pixels that are not near-white UI background.
3. Expand nearby foreground with a `7x7` max filter.
4. Extract 4-connected components.
5. Scale each component box back to the source size, add 12px padding, and keep
   boxes at least `80x60` with area at least `30000`.
6. Sort boxes from top to bottom, then left to right.

Exact SHA aliases are not cropped again. `aliases.tsv` maps each alias path to
the canonical source SHA and the manifest selector for its assets.

## Manifest

`manifest.tsv` records one row per crop:

- `asset_id`
- `asset_kind`
- `asset_label`
- `source_group`
- `source_index`
- `source_path`
- `source_sha256`
- `source_width`
- `source_height`
- `crop_x`
- `crop_y`
- `crop_width`
- `crop_height`
- `asset_path`
- `asset_sha256`
- `source_alias_paths`
- `notes`

## Rebuild And Verify

```bash
python3 docs/ui-ux/individual-assets-2026-06-22/build_assets.py generate
python3 docs/ui-ux/individual-assets-2026-06-22/build_assets.py verify
```
