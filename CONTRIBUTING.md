# Contributing

This repository is a staged Codex skill draft. Contributions should keep the router lazy, locator-only, and reviewable.

## Local Checks

Run these before proposing a change:

```sh
python -m pip install -r requirements.txt
python validation/validate_router_tree.py .
python -m unittest discover -s tests
```

For review-time upstream anchor checks:

```sh
python validation/check_upstream_anchors.py references/route-registry.yaml --ref main
```

## Add a Source

1. Add the source to `references/route-registry.yaml`.
2. Add it to exactly one category route.
3. Add `references/source-cards/<source_id>.md`.
4. Use exact raw-file anchors where possible.
5. Keep route-index keys namespaced as `<source_id>/<local_route>`.
6. Update `last_verified` only after running an upstream anchor check.

## Boundaries

- Do not claim source cards, route indexes, manifests, or graph outputs are evidence.
- Do not add automatic clone/fetch/write-cache behavior without a separate security review.
- Do not add generated artifacts to the repository.
- Do not add a license file unless the repository owner has chosen the license.
