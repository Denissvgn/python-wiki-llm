# check_site_mirror

**Entry point:** `site_export.check_site_mirror`
**Modules involved:** [io](../modules/io.md), [site_export](../modules/site_export.md), [site_html_check](../modules/site_html_check.md), [wiki_surface](../modules/wiki_surface.md)

> Validate that an exported static-site mirror is present and linked.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `wiki_surface.collect_wiki_pages`
2. `io.read_md`
3. `site_html_check.check_built_site_links`

## Touches

- [io](../modules/io.md)
- [site_export](../modules/site_export.md)
- [site_html_check](../modules/site_html_check.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `site_export.check_site_mirror`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
