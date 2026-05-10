---
name: Source update
about: Request a registry, source-card, or upstream anchor update
title: ""
labels: source-update
assignees: ""
---

## Source


## Requested change


## Upstream evidence


## Checks

- [ ] Exact raw-file anchors identified
- [ ] `last_verified.checked_paths` updated when anchors changed
- [ ] `python3 validation/check_upstream_anchors.py references/route-registry.yaml --ref main`
- [ ] `python3 validation/validate_router_tree.py .`
