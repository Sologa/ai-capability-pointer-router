## Summary

-

## Checks

- [ ] `python validation/validate_router_tree.py .`
- [ ] `python -m unittest discover -s tests`
- [ ] Upstream anchors checked if `references/route-registry.yaml` changed

## Boundary Confirmation

- [ ] This change keeps source cards, route indexes, manifests, and graph outputs locator-only.
- [ ] This change does not add clone/fetch/write-cache behavior.
