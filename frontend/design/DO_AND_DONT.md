# Do and don’t

## Do

- Use black/white base + dusk **horizon** accent only where documented
- Put code-shaped data in **IBM Plex Mono**
- Pair every status/confidence color with a **label or number**
- Prefer list shells for triage; tables for multi-column explorers
- Keep primary CTA as **white button**
- Match `frontend-lab` when unsure — then update these docs if you intentionally diverge
- Update **TOKENS.md** + lab accents in the same PR when changing the horizon

## Don’t

- Don’t use indigo/purple as the brand accent (retired)
- Don’t use Inter or Geist as the UI font
- Don’t paint full-bleed rainbow backgrounds or gradient text on body UI
- Don’t use vertical rainbow rails for selection (use horizontal horizon underlines)
- Don’t encode meaning in color alone
- Don’t nest cards inside cards with heavy shadows
- Don’t add a second brand accent “just for this screen”
- Don’t ship illustrations/empty-state mascots in v1
- Don’t wrap paths or diffs — scroll horizontally
- Don’t write dense marketing paragraphs in the product UI
- Don’t clone Linear pixel-for-pixel; don’t invent a new aesthetic every PR

## Agent checklist

Before merging frontend UI work, confirm:

- [ ] Tokens match [TOKENS.md](./TOKENS.md)
- [ ] Horizon only on mark / underlines / optional wash
- [ ] Jakarta + Plex Mono in use (or explicitly migrating toward them)
- [ ] Status + confidence remain readable without color
- [ ] Change Detail still prioritizes trust (sites + PR), not decoration
- [ ] Docs updated if you changed the system
