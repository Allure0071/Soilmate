---
name: soilmate-ui-style
description: Keep the Soilmate / 壤脉天玑 website visually consistent when editing its Vue pages, account pages, charts, or interface copy in E:\soil-frontend. Excludes backend-only work and unrelated websites.
---

# 壤脉天玑网站风格

Preserve the current fused website design: a field-photo editorial homepage leading into a restrained soil-data workspace. Do not replace the established hero layout or redesign the navigation merely to change a color or font. The user chose to return to this earlier layout after seeing a light split-hero experiment.

For full-page or cross-page UI work, read `product/04-Soilmate全站UI参考库与设计蓝图.md`. It maps official product references to Soilmate's own workflows and records what is already built versus planned. Use reference products for layout and interaction ideas, never as a source of SoilHUB data or scientific claims.

## Character

- Agricultural imagery, earthy green, pale neutral surfaces, precise data presentation, and generous editorial spacing.
- The homepage has one immersive field photograph with a readable localized shade and a floating white navigation bar. The workspaces use light panels, fine borders, and compact controls.
- All working modules continue the cover with a field-green outer frame (`#28513B`), a softly shadowed light work surface, and restrained serif titles. The map also reuses the rounded white navigation and a short crop of the cover image in its location panel. The green frame is interface styling, not a soil data layer.
- In analysis and evidence views, match the explorer's navigation, type scale, green accents, rounded controls, and soft card shadows. Use a quiet contour-textured title panel as the research counterpart to the explorer's field-photo location panel.
- The live `/account/` page uses the same green frame, with no top navigation bar. The cover photo forms a darkened left story panel; the legible, softly elevated form card contains a small return-home link. Keep its login and registration behavior intact.
- The data explorer's tool rail contains only layer, search, and map-location controls. Data resources belong in the main navigation; assessment starts from its own task entry.
- Give each surface its own focal point: photo on the homepage, map in exploration, metadata in data resources, one evidence-bounded finding in analysis, lineage in trace, and a readable narrative in reports. Avoid an equal-weight dashboard card grid across the site.
- Keep marketing language expressive and research language exact. Clearly label measured data, estimates, previews, and planned features. Do not present synthetic or predicted values as observations.

## Typography

- All interface text, headings, controls and numerals use the locally bundled `HarmonyOS Sans SC` family via `--font-ui`. `--font-display` aliases the same family. Keep true code/sequence fields monospace. Use `frontend/public/assets/design-system/typography.css`; preserve the upstream type scale.
- Use medium weight for titles and spacing/scale for hierarchy. Do not reintroduce per-page serif or hardcoded system font overrides.
- Avoid the generic all-sans, extra-wide-tracking look. Do not add remote font dependencies solely for this style.
- Keep workspace descriptions around 13–14 px and compact step/field labels at least 11–12 px. Use dark botanical secondary text (`#4D6253` range) on light panels; do not fade disabled buttons to illegible opacity.

## Color and components

- Existing page background is a pale botanical neutral (`#F4F6F1`); cards are white. Existing forest green and field imagery give the homepage its depth, while interface surfaces remain light.
- Use green as a purposeful accent for actions, selection, maps, and status. Keep text contrast clear, especially on the hero photograph. If the user requests color tuning, adjust the green itself without changing the established page composition.
- Use softly rounded cards and buttons, subtle shadows, visible focus states, and responsive layouts. Avoid generic gradients, decorative glass effects throughout the product, and repeated photo heroes on data pages.

Before changing UI, inspect the relevant existing component and shared CSS. Reuse current patterns and semantic variables where possible, then verify the build and the affected viewport. The user's latest instruction takes precedence over this style guide.

## Shared navigation, motion and copy

- Preserve the upstream `SiteHeader.vue`, navigation entries, routes and shared frame. Home, data, research, assistant and tools use that same component. A workspace or legacy tool must not cover or disable the primary navigation; keep module-specific tools inside their work surface.
- Use `frontend/public/assets/design-system/motion.css` for explicit Bezier tokens, page arrival and UI feedback, and `frontend/src/design-system/motion.js` for scroll reveal and the small scroll response. Pages enter with one gentle overshoot and settle exactly. Drawers use the shared pop/exit curves.
- Keep native scrolling. Scroll-linked movement is a bounded visual offset on the marked content, with one damped settle; do not intercept wheel/touch, accumulate scrolling, move the navigation or animate data tables on every scroll.
- Support `prefers-reduced-motion`, stop RAF when settled/hidden/unmounted, and preserve real content/focus in the static state. Inspect actual intermediate frames, final geometry, fast repeated opening and native scrolling; source/build checks alone do not establish visible motion.
- Remove duplicate overlines, instruction lists and filler copy. Retain units, missing-data states, source/quality constraints and required notices. Longer reference material belongs in labeled details.
- The local iGEM Wiki motion/art references supply behavioral principles only. Do not copy their artwork, palette, water/glass scenes or project assets into Soilmate.
- Desktop is the primary review target under the user's current scope.
