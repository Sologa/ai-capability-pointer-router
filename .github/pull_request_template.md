## Summary

-

## Checks

- [ ] `python3 validation/validate_router_tree.py .`
- [ ] `python3 -m unittest discover -s tests`
- [ ] Upstream anchors checked if `references/route-registry.yaml` changed
- [ ] Local refresh checked if materialization or graph scope changed

## Boundary Confirmation

- [ ] This change keeps source cards, route indexes, manifests, and graph outputs locator-only.
- [ ] This change does not commit local clones, cache manifests, route indexes, or graph outputs.
