---
name: soilmate-ui-style
description: Keep the Soilmate / 沃壤知行 website visually consistent when editing its Vue pages, account pages, charts, or interface copy. Excludes backend-only work and unrelated websites.
---

# 沃壤知行网站风格

Preserve the current fused website design: a field-photo editorial homepage leading into a restrained soil-data workspace. Do not replace the established hero layout or redesign the navigation merely to change a color or font. The user chose to return to this earlier layout after seeing a light split-hero experiment.

For full-page or cross-page UI work, read `product/04-Soilmate全站UI参考库与设计蓝图.md`. It maps official product references to Soilmate's own workflows and records what is already built versus planned. Use reference products for layout and interaction ideas, never as a source of SoilHUB data or scientific claims.

## Character

- Agricultural imagery, earthy green, pale neutral surfaces, precise data presentation, and generous editorial spacing.
- The homepage has one immersive field photograph with a readable localized shade and a floating white navigation bar. The workspaces use light panels, fine borders, and compact controls.
- All working modules continue the cover with a field-green outer frame (`#28513B`), a softly shadowed light work surface, and restrained titles in the shared HarmonyOS family. The map also reuses the rounded white navigation and a short crop of the cover image in its location panel. The green frame is interface styling, not a soil data layer.
- In analysis and evidence views, match the explorer's navigation, type scale, green accents, rounded controls, and soft card shadows. Use a quiet contour-textured title panel as the research counterpart to the explorer's field-photo location panel.
- The live `/account/` page uses the same green frame, with no top navigation bar. The cover photo forms a darkened left story panel; the legible, softly elevated form card contains a small return-home link. Keep its login and registration behavior intact.
- The data explorer's tool rail contains only layer, search, and map-location controls. Data resources belong in the main navigation; assessment starts from its own task entry.
- Give each surface its own focal point: photo on the homepage, map in exploration, metadata in data resources, one evidence-bounded finding in analysis, lineage in trace, and a readable narrative in reports. Avoid an equal-weight dashboard card grid across the site.
- Keep marketing language expressive and research language exact. Clearly label measured data, estimates, previews, and planned features. Do not present synthetic or predicted values as observations.

## Typography

- All interface text, headings, controls and numerals use the locally bundled `HarmonyOS Sans SC` family via `--font-ui`. `--font-display` aliases the same family. Keep true code/sequence fields monospace. Use `frontend/public/assets/design-system/typography.css`; preserve the upstream type scale.
- Use medium weight for titles and spacing/scale for hierarchy. Do not reintroduce per-page serif or hardcoded system font overrides.
- Use weight, scale and spacing for hierarchy; avoid extra-wide tracking. Do not add remote font dependencies solely for this style.
- Keep workspace descriptions around 13–14 px and compact step/field labels at least 11–12 px. Use dark botanical secondary text (`#4D6253` range) on light panels; do not fade disabled buttons to illegible opacity.

## Color and components

- Existing page background is a pale botanical neutral (`#F4F6F1`); cards are white. Existing forest green and field imagery give the homepage its depth, while interface surfaces remain light.
- Use green as a purposeful accent for actions, selection, maps, and status. Keep text contrast clear, especially on the hero photograph. If the user requests color tuning, adjust the green itself without changing the established page composition.
- Use rounded rectangular cards and controls, quiet layered shadows and visible focus states. Apple-inspired frosted glass belongs on the shared navigation, floating controls, drawers and selected call-to-action surfaces. Use translucent backing, a coherent bright edge and background blur; keep data canvases, long text and tables clear. Do not spread blur across the whole workspace or add repeated photo heroes on data pages.
- Reuse `frontend/public/assets/design-system/surfaces.css` for surface, radius and glass rules, including the standalone account page. CSS glass is a visual approximation without optical refraction. Keep readable fallback surfaces when blur or transparency is unavailable or reduced by user preference.

Before changing UI, inspect the relevant existing component and shared CSS. Reuse current patterns and semantic variables where possible, then verify the build and the affected viewport. The user's latest instruction takes precedence over this style guide.

## Shared navigation, motion and copy

- Preserve the upstream `SiteHeader.vue`, navigation entries, routes and shared frame. Home, data, research, assistant and tools use that same component. A workspace or legacy tool must not cover or disable the primary navigation; keep module-specific tools inside their work surface.
- Use `frontend/public/assets/design-system/motion.css` for explicit Bezier tokens and UI feedback, and `frontend/src/design-system/motion.js` for page transitions, scroll reveal and the small scroll response. Pages blend in place with a stable shared header; never slide or bounce the whole workspace upward. Local panels can scale with one gentle overshoot. Drawers retain directional pop/exit curves. Home titles do not replay an entrance on every navigation.
- Use the latest target for rapid navigation and the same transition boundary for browser history. Preserve existing authentication and route behavior. Unsupported browsers and reduced motion update directly. Current implementation details belong in `frontend/DESIGN_SYSTEM.md`; reusable cross-page lessons are in the local `$datiao-wiki` skill.
- Keep native scrolling. Scroll-linked movement is a bounded visual offset on the marked content, with one damped settle; do not intercept wheel/touch, accumulate scrolling, move the navigation or animate data tables on every scroll.
- Support `prefers-reduced-motion`, stop RAF when settled/hidden/unmounted, and preserve real content/focus in the static state. Inspect actual intermediate frames, final geometry, fast repeated opening and native scrolling; source/build checks alone do not establish visible motion.
- Remove duplicate overlines, instruction lists and filler copy. Retain units, missing-data states, source/quality constraints and required notices. Longer reference material belongs in labeled details.
- The local iGEM Wiki motion/art references supply behavioral principles only. Do not copy their artwork, palette, water/glass scenes or project assets into Soilmate.
- Desktop is the primary review target under the user's current scope.
