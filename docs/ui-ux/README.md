# Naruon UI/UX Asset Repository

This directory is the single repository entry point for Naruon UI/UX visual
source material. Keep existing asset paths stable so implementation notes,
review comments, and SHA-256 evidence remain reproducible.

## Index

- `naruon-ui-ux-mapping.md`: text map for agents and reviewers. Read this
  first, then open the matching image files directly.
- `mockups/`: canonical mockup image set. These 41 images define the main
  screens, component boards, action maps, and brand assets.
- `reference-set-2026-06-18/`: durable PR-review reference set. Its
  `images/` directory contains 45 images, and `sources.tsv` records each
  stable repository path and SHA-256 digest.
- `asset-overviews-2026-06-21/`: rendered contact sheets and a manifest for
  quickly reviewing every current UI/UX asset without changing source paths.

## Agent Workflow

1. Start with `naruon-ui-ux-mapping.md` to identify the relevant screen,
   component board, or action map.
2. Open the referenced PNG files under `mockups/` or
   `reference-set-2026-06-18/images/`; the text map is an index, not a
   substitute for the original visual source.
3. Use `reference-set-2026-06-18/sources.tsv` when reference-set integrity
   matters.
4. Do not duplicate long descriptions only because filenames differ. Compare
   hashes and use the alias table in `naruon-ui-ux-mapping.md` when two assets
   represent the same UI concept.

## Storage Rules

- Keep dated reference sets immutable once review comments or PR evidence point
  at them.
- Add a new dated reference-set directory when new durable provenance is needed.
- Update `naruon-ui-ux-mapping.md` whenever new images are added, renamed, or
  semantically aliased.
- Treat rendered overviews as review aids. The original PNG files and
  `sources.tsv` remain the authority.
