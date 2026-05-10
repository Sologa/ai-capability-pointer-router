# Contributing

This repository is a staged Codex skill draft. Contributions should keep the router lazy, locator-only, and reviewable.

## Local Checks

Run these before proposing a change:

```sh
python3 -m pip install -r requirements.txt
python3 validation/validate_router_tree.py .
python3 -m unittest discover -s tests
```

For review-time upstream anchor checks:

```sh
python3 validation/check_upstream_anchors.py references/route-registry.yaml --ref main
```

For local cache / graph refresh checks:

```sh
python3 scripts/local_refresh_repos.py --registry references/route-registry.yaml --category <route_id>
```

## Add a Source

1. Start from `templates/paper-repo-taxonomy/route-registry-source.yaml.tmpl` and `templates/paper-repo-taxonomy/source-card.md.tmpl` when creating a paper + repo taxonomy source.
2. Add the source to `references/route-registry.yaml`.
3. Add it to exactly one category route.
4. Add `references/source-cards/<source_id>.md`.
5. Use exact raw-file anchors where possible.
6. Keep route-index keys namespaced as `<source_id>/<local_route>`.
7. Add optional paper/repo metadata only when it describes real source identity or evidence order.
8. Add or update local graph scope for the source.
9. Update `last_verified` only after running an upstream anchor check.

## Boundaries

- Do not claim source cards, route indexes, manifests, or graph outputs are evidence.
- Do not add another automatic clone/fetch/write-cache path; use and harden `scripts/local_refresh_repos.py`.
- Do not add generated artifacts to the repository.
- The repository license is Apache-2.0. Do not change licensing without an explicit owner decision.
