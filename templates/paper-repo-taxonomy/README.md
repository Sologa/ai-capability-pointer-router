# Paper + Repo Taxonomy Router Template

These files are scaffolds for turning this staged Codex router into a new paper + repo taxonomy router.

They are templates, not evidence. Replace every `<placeholder>` before review and then run the validator and tests.

## Files

- `route-registry-profile.yaml.tmpl`: replacement `profile` block.
- `route-registry-route.yaml.tmpl`: one route block for `references/route-registry.yaml`.
- `route-registry-source.yaml.tmpl`: one source block for `references/route-registry.yaml`.
- `category-router.md.tmpl`: category router file for `references/category-routers/<route_id>.md`.
- `source-card.md.tmpl`: source card file for `references/source-cards/<source_id>.md`.
- `skill-category-section.md.tmpl`: `SKILL.md` category section shape that the validator expects.

## Minimal Use

1. Copy the profile block and replace the seed `profile`.
2. Add route blocks under `routes`.
3. Add source blocks under `sources`.
4. Create one category router per route.
5. Create one source card per source.
6. Update `SKILL.md` so the category bullets match registry routes exactly.
7. Run:

```sh
python3 validation/validate_router_tree.py .
python3 -m unittest discover -s tests
```

## Current Limits

The current scripts materialize GitHub repositories only. Paper PDFs, arXiv pages, Zenodo records, Hugging Face repos, GitLab repos, and local folders need schema and script changes before they become first-class materialized sources.

The source template includes optional paper-facing metadata such as `paper`, `artifact_role`, `topic_tags`, `question_types`, `claim_scope`, `preferred_evidence_order`, and `paired_assets`. These fields document the paper/repo relationship, but only the GitHub repo anchors are materialized by the current refresh script. When present, the fields are schema-checked: paper metadata needs the full id/title/citation/URI set, materialized repo assets must point to GitHub display URLs, and paper assets cannot be marked as materialized sources.
