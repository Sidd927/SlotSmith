# SlotSmith Frontend Design Specification

## `design.md` --- Landing Page (Page 01) and Extensible Design System

**Status:** Initial visual specification\
**Product:** SlotSmith --- rule-driven, independently checked,
revision-aware DeltaV I/O allocation\
**Primary reference:** User-provided SlotSmith landing-page screenshot\
**Implementation context:** Existing SlotSmith Streamlit prototype.
Preserve the current application architecture and working flows; do not
assume a framework migration.

------------------------------------------------------------------------

## 1. Purpose and use

This document translates the supplied landing-page reference into
implementation-ready design guidance for Antigravity. It defines the
visual language, page hierarchy, layout, reusable components, responsive
behavior, interaction expectations, accessibility requirements, and
acceptance criteria.

Treat the reference image as the visual source of truth for the
**landing-page composition and aesthetic**, not as proof that every
visible product claim or interaction already exists. Reproduce the
design intent with real application components and existing product
functionality. Do not use a static screenshot as the page itself.

This document is intentionally structured to grow. Future pages should
be appended as separate page specifications while continuing to use the
shared design tokens and components defined here.

### Product design objective

Present SlotSmith as a credible industrial engineering application:
calm, precise, technical, readable, and trustworthy. The interface
should feel like professional engineering software rather than a generic
SaaS template or a marketing-only website.

### Source-of-truth order

When implementation details conflict, follow this order:

1.  Existing product behavior, business logic, and validated application
    routes.
2.  Current project requirements and approved evidence/claim
    constraints.
3.  This design specification.
4.  The reference screenshot's visual styling.
5.  Antigravity's assumptions.

Do not invent backend capabilities to match a visual element. If a
visual element implies functionality that is not implemented, label it
as illustrative or omit the interaction until it exists.

------------------------------------------------------------------------

## 2. Reference image analysis

The reference is a full-width, desktop-first landing page captured at
approximately **1024 × 1536 px**. It uses a white/light-gray interface,
deep navy typography, saturated industrial blue accents, pale blue
surfaces, fine borders, restrained shadows, and large engineering
imagery.

The page contains these sections, in order:

1.  White top navigation.
2.  Hero with left-aligned copy and CTAs; industrial background image
    and floating product screenshot on the right.
3.  Four compact value propositions.
4.  Five-step workflow.
5.  Four capability cards.
6.  Hardware inspection feature with a photograph, hotspot/callout, and
    explanatory text.
7.  Closing proof/impact section with a text block and three metrics.

The page alternates between near-white and very pale cool-gray section
backgrounds. There are no dark full-bleed sections in the supplied
reference. Blue is used consistently for actions, icons, selected
states, and emphasis.

### Overall visual impression

-   **Tone:** Professional, technical, confident, restrained.
-   **Density:** Moderate. Content is information-rich but not crowded.
-   **Geometry:** Mostly rectangular cards with medium rounded corners;
    large imagery and strong horizontal section alignment.
-   **Typography:** Modern sans-serif; bold, tightly composed headings;
    comfortable body line-height.
-   **Contrast:** Navy text on pale surfaces; blue buttons with white
    text.
-   **Visual hierarchy:** Navigation → hero headline → hero visual →
    workflow → capabilities → hardware inspection → proof/impact.
-   **Avoid:** Excessive gradients, neon accents, glassmorphism,
    oversized empty panels, ornamental animations, dense dashboard
    widgets on the landing page, and generic template-like card grids
    without product-specific content.

------------------------------------------------------------------------

## 3. Shared design foundations

### 3.1 Color tokens

Use these as initial implementation tokens. If the repository already
has an established palette that closely matches the reference,
consolidate rather than introducing duplicate variables.

  --------------------------------------------------------------------------
  Token                      Suggested value         Use
  -------------------------- ----------------------- -----------------------
  `--color-brand-700`        `#0756A6`               Primary actions,
                                                     emphasized heading
                                                     text, active links

  `--color-brand-600`        `#0968C8`               Primary buttons, icons,
                                                     links

  `--color-brand-500`        `#1677D2`               Hover/focus accents and
                                                     selected indicators

  `--color-brand-100`        `#E5F1FC`               Icon discs, selected
                                                     backgrounds, soft
                                                     highlights

  `--color-brand-050`        `#F2F7FC`               Subtle blue-tinted
                                                     surfaces

  `--color-ink-900`          `#142235`               Main headings and
                                                     primary text

  `--color-ink-700`          `#35465B`               Body text and secondary
                                                     headings

  `--color-ink-600`          `#526176`               Supporting copy,
                                                     descriptions

  `--color-ink-500`          `#718096`               Captions and tertiary
                                                     text

  `--color-surface`          `#FFFFFF`               Cards, navigation,
                                                     primary page surface

  `--color-surface-subtle`   `#F6F8FB`               Alternating section
                                                     backgrounds

  `--color-border`           `#DFE6EE`               Card and input outlines

  `--color-border-strong`    `#C8D3E0`               Stronger input borders
                                                     and separators

  `--color-success`          `#14804A`               Genuine success states
                                                     only

  `--color-warning`          `#A65A00`               Warnings and
                                                     review-required states

  `--color-danger`           `#B42318`               Errors and blocking
                                                     validation states
  --------------------------------------------------------------------------

**Rules** - Use blue for primary emphasis; do not make every element
blue. - Use navy for most text, not pure black. - Use pale blue
backgrounds sparingly to distinguish related elements. - Reserve green,
amber, and red for semantic status in product interfaces; do not use
them decoratively on the marketing page. - Maintain readable text
contrast. Do not reduce opacity on body text to imitate a low-contrast
mockup.

### 3.2 Typography

Preferred stack: the existing system sans-serif stack, such as
`Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`.
Do not add a remote font dependency unless the project already uses one.

  ---------------------------------------------------------------------------------------
  Role                             Desktop guidance             Weight        Line-height
  -------------- ---------------------------------- ------------------ ------------------
  Hero heading     `clamp(2.25rem, 3.5vw, 3.35rem)`           700--750         1.08--1.16

  Section           `clamp(1.8rem, 2.4vw, 2.45rem)`                700          1.12--1.2
  heading                                                              

  Card heading                      `1rem–1.125rem`           650--700          1.25--1.4

  Body lead                       `1.05rem–1.15rem`           400--450          1.55--1.7

  Body standard                      `0.92rem–1rem`                400          1.5--1.65

  Eyebrow /                       `0.68rem–0.76rem`           650--750                1.3
  label                                                                

  Navigation                      `0.88rem–0.95rem`           500--600                1.2

  Caption /                       `0.75rem–0.82rem`           450--550                1.4
  metadata                                                             
  ---------------------------------------------------------------------------------------

The screenshot's body text is compact but readable. Do not reduce font
size merely to fit more copy. Reflow the layout or shorten nonessential
copy instead.

### 3.3 Spacing system

Use a consistent spacing scale based on 4 px:

`4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96 px`

Guidance: - Main page gutters: `clamp(24px, 4.2vw, 68px)`. - Standard
section vertical padding: `64–88px` desktop. - Hero vertical padding:
`48–72px` desktop. - Card internal padding: `20–24px`. - Card grid gap:
`16–20px`. - Heading-to-description gap: `12–18px`. - Section
heading-to-content gap: `28–36px`.

Avoid arbitrarily different margins for each section. Align section
content to a shared container.

### 3.4 Container and grid

-   Maximum main content width: approximately `1440px`; use a centered
    container.
-   Standard desktop content: 12-column conceptual grid, or CSS Grid
    with equivalent behavior.
-   Hero: approximately 50/50 or 48/52 split, adjusted to fit the
    product visual.
-   Four capability cards: four equal columns on wide desktop.
-   Workflow: five equal steps across desktop.
-   Hardware inspection: approximately 58% image / 42% explanatory text.
-   Closing impact section: approximately 54% explanatory text / 46%
    metrics.
-   Use `min-width: 0` on grid children to prevent long content from
    forcing overflow.

### 3.5 Borders, radius, and elevation

-   Standard card radius: `12–16px`.
-   Button radius: `7–10px`.
-   Inputs: `7–9px`.
-   Standard border: `1px solid var(--color-border)`.
-   Card shadow: very subtle, e.g. `0 2px 10px rgba(20, 34, 53, 0.035)`.
-   Hover elevation should be subtle and must not cause surrounding
    layout shifts.
-   Do not apply heavy shadows to every element. The hero product image
    may have a more pronounced shadow because it is the main visual
    anchor.

### 3.6 Iconography

Use one consistent icon family already available in the project. If none
exists, prefer simple line icons with consistent stroke width. Do not
mix emoji, filled clip-art, and multiple unrelated icon styles.

Icons are generally blue line icons: - Shield/check: rule-checked
allocation. - Database/layers: hardware mapping or data ingestion. -
Grid/cabinet: cabinet visualization. - Circular arrows: revision
management. - Document: upload/ingest. - Check-circle: validation. -
Gear: allocation. - Download: export. - Table/grid: structured
engineering data.

Icons should support text, not replace it. Decorative icons should be
hidden from screen readers; actionable icons require accessible names.

------------------------------------------------------------------------

## 4. Page 01 --- Landing page

### 4.1 Navigation header

**Reference appearance** - White horizontal bar spanning the viewport. -
Approximate desktop height: `60–72px`. - Brand mark and wordmark on the
left. - Navigation links centered across the available space. -
Utility/theme control and secondary/primary actions on the right. - Fine
bottom border or very subtle shadow. - Header content vertically
centered and aligned to the main container.

**Structure** 1. Brand lockup: SlotSmith logo/mark, wordmark, compact
descriptor "ELECTRONIC MARSHALLING". 2. Navigation links: Product, How
It Works, Capabilities, About. 3. Utility control: theme icon only if
theme switching is implemented and tested. 4. Secondary action: "Sign
In" only if authentication exists. If not, remove it or label the real
destination accurately. 5. Primary action: "Open Workbench →".

**Behavior** - Logo returns to the landing page. - In-page links scroll
to their actual sections with a sensible scroll offset. - "Open
Workbench" routes through the application's existing navigation handler
to the appropriate starting stage. - Avoid dead `href="#"` links,
non-functional buttons, or `postMessage` calls without a real
receiver. - On narrow screens, collapse the navigation into an
accessible menu or a compact, tested arrangement. - Keyboard focus must
be clearly visible.

**Do not** - Implement fake sign-in. - Add a theme toggle that changes
only the icon but not the theme. - Duplicate the primary CTA in the
header without a clear reason.

### 4.2 Hero section

**Composition** - Full-width, pale cool-gray / near-white hero
section. - Two main columns. - Left: eyebrow, headline, descriptive
paragraph, two CTAs, four compact proof points. - Right: large
industrial facility image with a floating or overlaid SlotSmith product
screenshot. - Background imagery may fade toward the left to preserve
headline readability. - Hero content should be vertically balanced and
not compressed into a narrow strip.

**Suggested content hierarchy** 1. Eyebrow pill: "BUILT FOR DELTAV
ENGINEERING TEAMS". 2. Headline on two or three lines: - "From I/O
workbook to" - "verified marshalling allocation." Use the brand blue for
the second line or key phrase. 3. Description: "SlotSmith helps
engineers ingest I/O workbooks, validate signal grouping against project
constraints, generate an allocation, inspect cabinet layouts, and export
traceable engineering outputs." 4. Primary CTA: "Open Workbench →". 5.
Secondary CTA: "Explore Demo Dataset". 6. Four value propositions
beneath the CTAs: - Rule-checked allocations - DeltaV-aware hardware
mapping - Cabinet visualization - Revision-aware change management

**Hero background** - Use a relevant industrial/process-plant
photograph, preferably a licensed or project-owned asset. - Apply a
light overlay or gradient so the left-side copy remains readable. -
Avoid high-contrast pipework directly behind body copy. - If a suitable
asset is not available, use a clean light background rather than a
random stock image.

**Product visual** - Use a genuine screenshot from the current SlotSmith
application, not a fabricated dashboard that implies non-existent
features. - Crop and scale it to show the most relevant product
experience: cabinet map, allocation status, or workflow. - The product
image can sit inside a frame with rounded corners and a soft shadow. -
It may overlap the background image, but must not overlap or obscure the
main text/CTAs. - Ensure the screenshot is sharp enough to be understood
at normal desktop scale. - If the product screenshot is too dense to
read, create a deliberately simplified *illustrative mockup* and label
it as illustrative; do not present it as a live application screenshot.

**Hero responsive behavior** - At widths below roughly 900px, stack the
copy above the product visual. - Keep the main headline first in reading
order. - Place CTAs close to the description. - Move the proof-point row
below the visual or wrap it into two columns. - At 375px, buttons must
wrap or stack without horizontal overflow. - Do not keep a desktop-sized
product screenshot clipped off-screen.

### 4.3 Four hero value propositions

A horizontal row of four concise items directly beneath the hero CTAs.

Each item includes: - Small blue line icon. - Short title, one or two
lines. - No enclosing card unless required by responsive behavior. -
Consistent horizontal spacing and baseline alignment.

Recommended wording: - "Rule-checked allocations" - "DeltaV-aware
hardware mapping" - "Cabinet visualization" - "Revision-aware change
management"

Avoid unsupported guarantees such as "zero violations guaranteed". The
application can report the checks it actually performs; it must not
imply that all possible engineering errors are impossible.

### 4.4 Workflow section

**Background:** white or near-white, with generous top and bottom
padding.

**Header row** - Left: eyebrow "A CLEAR, GUIDED ENGINEERING WORKFLOW". -
Left below: heading "From input to deliverables in five steps." - Right:
short explanatory paragraph aligned toward the heading baseline.

**Five steps, in order** 1. **Input & Ingest** --- "Upload I/O workbook
or use a demo dataset." 2. **Review & Validate** --- "Check mappings,
findings and TQs." 3. **Allocate** --- "Apply constraints and generate
allocation." 4. **Inspect & Verify** --- "Review cabinet layouts and
rule-check results." 5. **Export Deliverables** --- "Download allocation
workbook and reports."

**Step visual** - Circular pale-blue icon disc. - Blue line icon
centered inside. - Step title below. - Two-line supporting text. - Light
chevron between steps on desktop, vertically centered between icon
groups. - Chevrons are decorative and hidden from assistive
technology. - Use equal-width columns and consistent card-free spacing.

**Interaction** - If steps are clickable, the entire step should have a
clear focus/hover state and navigate to the corresponding existing
application stage. - If the route is not implemented, present the step
as informational rather than as a dead link. - The visual sequence must
not suggest that the app automatically completes steps without user
review.

**Responsive** - Desktop: five columns. - Medium width: consider a
wrapped layout such as 3 + 2. - Mobile: vertical numbered sequence or
two-column grid. Preserve the step order and readable descriptions. - Do
not squeeze all five steps into unreadable narrow columns.

### 4.5 Capabilities section

**Background:** pale cool-gray surface, visually distinct from the
workflow section.

**Header** - Eyebrow: "ENGINEERED FOR INDUSTRIAL REALITY". - Heading:
"Purpose-built for DeltaV marshalling." - Supporting sentence aligned to
the right on desktop: "Combining domain rules, hardware constraints, and
deterministic allocation for more reliable engineering outcomes." Ensure
any wording about determinism is technically accurate for the relevant
workflow. Revision repair may be solver-time-limited and
non-deterministic; do not describe the entire product as deterministic
if that would mislead.

**Four cards** Each card uses a white surface, thin border, medium
radius, subtle shadow, and consistent padding.

1.  **Flexible Data Ingestion**
    -   Icon: table/grid or database.
    -   Description: "Import customer I/O workbooks (.xlsx, .xls, .csv)
        with automatic column mapping and validation."
    -   Only list formats actually supported by the current application.
        If a format is not supported, remove it or mark it as planned.
2.  **Rule-Checked Allocation**
    -   Icon: shield/check.
    -   Description: "Apply configured project constraints, capacity,
        segregation, hardware compatibility, and cable-grouping rules."
    -   Avoid implying that unimplemented rule interpretations have been
        approved by the sponsor.
3.  **Interactive Cabinet Map**
    -   Icon: cabinet/grid.
    -   Description: "Visualize CIOCs, baseplates, and CHARM slots with
        allocation data. Inspect signal assignments and hardware usage."
4.  **Revision Repair (Rev B)**
    -   Icon: circular arrows.
    -   Description: "Compare revised designs and limit disruption using
        window-local CP-SAT constraint repair."
    -   Do not promise globally minimum moves or guaranteed optimality.

**Card consistency** - Icons align at the top. - Titles align
consistently. - Descriptions have a readable line length. - Cards in the
same row should visually align without forcing awkward fixed heights. -
Cards may be clickable only if each has a real destination. - On hover,
use a slight border-color change or small elevation increase. Avoid
large motion effects.

**Responsive** - Wide desktop: four columns. - Tablet: two columns. -
Mobile: one column, or two only if each card remains comfortably
readable.

### 4.6 Hardware inspection feature

**Layout** - Two-column section with a large photograph on the left and
explanatory content on the right. - Approximate desktop ratio: 58% /
42%. - The photograph has a medium radius and crops intentionally. - A
small interactive callout panel may overlay the image. - The text column
includes eyebrow, heading, paragraph, and a four-item checklist.

**Reference copy direction** - Eyebrow: "VISUAL INSPECTION MADE
SIMPLE". - Heading: "See the allocation. Understand the detail." -
Paragraph: "Explore marshalling cabinets, inspect CHARM assignments,
view signal details, and identify unplaced or conflicted signals in one
interface."

**Checklist** - "Per-cabinet and per-CIOC visualization" - "Select a
slot to inspect signal details" - "Clear hardware type colouring and
legend" - "Identify free slots, spares, and conflicts at a glance"

Use the exact terms and levels supported by the application. If the
interface does not yet support hover selection, do not claim hover
behavior; say "Select a slot" instead.

**Image and callout** - Use a project-owned or properly licensed
cabinet/hardware image. - Keep the callout visually attached to a
meaningful point on the image. - The callout should show only fields
that are actually available, such as: - CIOC identifier - Baseplate and
slot - Signal/tag - Cable identifier or pair, if available - Allocation
state - Rule-check result, if genuinely computed - Never fabricate a tag
or PASS state and present it as live product data. - For synthetic
examples, visibly label the panel "Illustrative synthetic data". -
Position overlays relative to the image container and ensure they remain
within the image bounds. - At small viewports, move the detail panel
below the image rather than letting it cover most of the photograph.

**Interaction** - If hotspots are implemented, make them
keyboard-operable buttons with accessible names. - Selecting a hotspot
updates the details panel. - Clearly distinguish the selected hotspot. -
Provide an accessible fallback selector or list so the feature is usable
without pointer hover. - Do not use hover as the only means of revealing
important data.

### 4.7 Closing impact / proof section

**Background:** white or near-white, with a subtle top divider if
needed.

**Left block** - Eyebrow: "BUILT FOR REAL ENGINEERING CHALLENGES". -
Heading: "Built for real engineering challenges." - Body copy should
describe expected benefits without implying that time savings or
accuracy improvements have been measured when they have not.

Suggested copy: "SlotSmith is designed to reduce manual coordination,
improve consistency, and make allocation decisions easier to inspect and
trace."

**Right block** - Three metrics or proof points separated by fine
vertical dividers. - Each item: large blue value, small explanatory
label. - On mobile, stack or wrap metrics with sufficient separation.

**Critical evidence constraint** The reference screenshot contains "90%+
Rule compliance accuracy", "10x Faster allocation turnaround", and "100%
Traceable engineering outputs". These are visual examples in the
reference, **not approved factual claims**. Do not reproduce them as
product achievements without new evidence.

Preferred replacement: - "11" --- "rule families checked" (only while
this remains accurate in the current verifier). - "20,033" ---
"synthetic signals processed in the audited benchmark" (only if the
benchmark is current and the synthetic qualifier is visible). - "100%"
must not be used for allocation coverage unless its meaning is
explicitly "allocated or covered by a TQ", and the context clearly says
it is a synthetic test result. Prefer not to use a headline percentage
on a marketing landing page.

Alternative: use non-numeric capability statements rather than
metrics: - "Traceable findings" --- "TQs linked to source rows" -
"Independent checks" --- "Exported workbook re-verified" -
"Revision-aware" --- "Unchanged assignments can be preserved"

The best choice is to avoid unsupported percentages and multipliers
altogether. If evidence-backed metrics are used, label the dataset and
conditions directly beside the numbers, not only in a footer.

### 4.8 Footer and CTA continuity

The provided image ends after the impact section, but the implemented
page should include a restrained footer if the product currently has one
or if navigation requires it.

Potential footer elements: - SlotSmith logo/wordmark. - One-line product
descriptor. - Links to the page sections and actual workbench. -
Version/status information only if available and useful.

Do not add fictional customer logos, endorsements, customer counts,
compliance badges, or social links.

If adding a closing CTA, avoid duplicating the header, hero, and footer
actions in a way that feels repetitive. One clear primary action is
sufficient.

------------------------------------------------------------------------

## 5. Interaction and navigation contract

The landing page is an entry point into the existing SlotSmith
application, not a separate prototype with invented destinations.

### Required actions

-   Header "Open Workbench" opens the existing workbench at the intended
    initial stage.
-   Hero "Open Workbench" uses the same route/handler as the header
    action.
-   "Explore Demo Dataset" invokes the existing demo-data path and moves
    to the correct review stage.
-   Workflow items navigate to their actual existing stages, if
    implemented.
-   Capability cards navigate to the correct existing workspace only if
    they are genuinely actionable.
-   Hardware hotspots update the selected item and its detail panel if
    this interaction exists.
-   All navigation must preserve relevant session state and avoid
    duplicate or stale query parameters.

### Implementation rules

-   Reuse current route names, navigation constants, and handlers;
    inspect them before wiring links.
-   Do not infer route names from display labels.
-   Avoid hard-coded navigation logic duplicated in multiple components.
-   Avoid dead fragment anchors, placeholder URLs, and fake button
    behavior.
-   Use native buttons for actions and links for navigation where the
    current architecture supports them.
-   Preserve the Streamlit application architecture unless a separate
    approved migration is underway.
-   If Streamlit's rendering model imposes limitations, implement a
    reliable accessible fallback rather than a visual-only control.

------------------------------------------------------------------------

## 6. Responsive design specification

Test the real rendered page at these target viewports:

  -----------------------------------------------------------------------
  Target                  Purpose                 Expected behavior
  ----------------------- ----------------------- -----------------------
  1440 × 900              Primary desktop         Full navigation;
                                                  two-column hero; four
                                                  capability cards; five
                                                  workflow steps

  1280 × 800              Standard laptop         Same structure with
                                                  adjusted spacing; no
                                                  clipped hero visual

  768 px wide             Tablet                  Navigation adapts; hero
                                                  and hardware section
                                                  may stack; card grids
                                                  become two columns

  375 px wide             Mobile                  Compact navigation;
                                                  stacked hero;
                                                  full-width/stacked
                                                  CTAs; one-column cards;
                                                  no horizontal overflow
  -----------------------------------------------------------------------

At every width: - No horizontal page scrolling caused by layout bugs. -
No text clipped by fixed heights. - No overlapping CTAs or section
headings. - No inaccessible or off-screen popovers. - No images
distorted by forced width/height. - No critical information available
only on hover. - Maintain an appropriate tap target, ideally at least 44
× 44 CSS px for primary touch controls. - Respect reduced-motion
preferences.

Responsive behavior must be verified in a real browser. The presence of
media queries alone is not sufficient evidence.

------------------------------------------------------------------------

## 7. Accessibility and semantics

-   Use semantic landmarks: `header`, `nav`, `main`, `section`, and
    `footer` where the framework allows.
-   Use one clear page-level `h1`; section headings should follow a
    logical hierarchy.
-   Buttons and links must have descriptive accessible names.
-   Every interactive hotspot must be keyboard-operable and visibly
    focused.
-   Decorative icons should not produce redundant screen-reader
    announcements.
-   Do not use colour alone to communicate success, warning, selection,
    or error.
-   Ensure adequate contrast for small body text and controls.
-   Provide meaningful alt text for informative images; use empty alt
    text for purely decorative backgrounds.
-   Do not encode important text into a background image.
-   Preserve browser zoom and avoid fixed text sizes that become
    unusable when zoomed.
-   Avoid animations that flash, distract, or cause layout shifts.

------------------------------------------------------------------------

## 8. Content integrity and engineering credibility

SlotSmith is engineering software. Its design must communicate clarity
and traceability without exaggerating its guarantees.

### Use accurate descriptions

-   Describe the allocator and verifier in terms supported by the
    current implementation.
-   Keep the distinction between baseline allocation and revision repair
    clear.
-   Describe revision repair as window-local where applicable.
-   Do not claim globally minimal moves or guaranteed optimality.
-   Do not claim that all possible violations are impossible.
-   Do not claim official template compatibility or official-data
    validation unless it has actually been verified.
-   Do not imply live plant connectivity, live hardware telemetry, or a
    real-time cabinet connection unless implemented.
-   Label synthetic examples and benchmark results as synthetic.
-   Describe AI-assisted features as planned if they are not
    implemented. AI must not be presented as placing signals if it does
    not.
-   Do not claim certification without a genuine certification basis.
-   Do not use unsupported accuracy percentages, time-saving
    multipliers, customer counts, or performance improvements.

### Content tone

Prefer: - "Rule-checked" - "Independently verified" - "Traceable" -
"Revision-aware" - "Designed to reduce manual effort" - "Synthetic
benchmark" - "Window-local repair"

Avoid unsupported: - "Certified" - "Guaranteed zero violations" - "10×
faster" - "90%+ accuracy" - "Globally optimal" - "Minimum moves
guaranteed" - "Live plant status"

------------------------------------------------------------------------

## 9. Implementation notes for Antigravity

1.  Inspect the repository before changing code. Identify the current
    landing-page entry point, component builders, style definitions,
    assets, and navigation handlers.
2.  Preserve unrelated user changes and existing application behavior.
3.  Keep this design specification as the design reference for the
    landing page.
4.  Reuse the current architecture. Do not migrate frameworks or rewrite
    the backend as part of a visual task.
5.  Build real HTML/UI components. Never display HTML source as visible
    page text.
6.  Keep trusted application-generated markup separate from
    user-provided workbook values. Escape or safely render externally
    supplied values to prevent HTML injection.
7.  Prefer shared components and design tokens over repeated ad hoc
    styling.
8.  Use actual local assets where available. Do not fabricate
    screenshots, customer logos, benchmark claims, or hardware states.
9.  After implementation, inspect the page in a real browser at all
    target viewport widths.
10. Capture screenshots of the hero, workflow, capability cards,
    hardware inspection, and closing section.
11. Run the relevant existing tests and verify the header, hero,
    demo-data, card, slot, and hotspot interactions.
12. Review the Git diff. Do not reset, clean, commit, or push unless
    separately requested.

### Important rendering requirement

If this landing page is rendered through Streamlit, inspect the actual
rendering API and HTML string assembly. HTML must be passed through an
HTML-capable renderer rather than a text/code display path. Do not hide
raw markup with CSS. Verify the real browser output.

------------------------------------------------------------------------

## 10. Acceptance criteria

The landing page is accepted when all of the following are true:

-   [ ] The page hierarchy matches the reference: navigation, hero,
    workflow, capabilities, hardware inspection, impact/proof, footer if
    applicable.
-   [ ] The page uses the light, blue-accented industrial-software
    visual language.
-   [ ] The hero has a readable headline, concise description, two
    meaningful actions, value propositions, and a product visual.
-   [ ] Navigation and all visible actions lead somewhere real or are
    presented as non-interactive information.
-   [ ] Five workflow steps appear in the correct order and remain
    readable responsively.
-   [ ] Four capability cards have consistent spacing, typography, and
    visual treatment.
-   [ ] Hardware imagery and detail callouts are correctly positioned
    and do not obscure key content.
-   [ ] No unsupported metrics, certification, guarantees, or fake
    live-status claims appear.
-   [ ] Synthetic data is clearly labelled where shown.
-   [ ] No raw HTML source appears anywhere in the rendered page.
-   [ ] The page works at 1440 × 900, 1280 × 800, 768 px wide, and 375
    px wide.
-   [ ] Keyboard navigation, focus states, contrast, and accessible
    labels are acceptable.
-   [ ] The existing workbench, demo-data, and relevant inspection
    interactions still work.
-   [ ] The implementation does not alter business logic or unrelated
    files.
-   [ ] Actual browser screenshots and test results are reported
    honestly.

------------------------------------------------------------------------

## 11. Future-page extension template

Append a new page section to this file for each subsequent page. Do not
redefine the global tokens unless a deliberate design-system change is
approved.

Use this template:

``` md
# Page NN — [Page Name]

## Purpose
What task does this page help the user complete?

## Primary user and context
Who uses it, and at what point in the workflow?

## Entry and exit points
Which existing route/stage opens it? Where can the user go next?

## Information hierarchy
List the page title, summary, primary panel, supporting panels, and secondary information.

## Layout
Describe container width, grid, panel order, alignment, density, and responsive behavior.

## Components
For each component: purpose, content, state, interactions, and accessibility.

## Data and state
Identify actual application fields and states. Do not invent backend capabilities.

## Loading, empty, error, and success states
Define the visible behavior for each real state.

## Interaction contract
Document the exact controls and their expected outcomes.

## Visual treatment
Reference existing tokens and shared components. Only document page-specific differences.

## Responsive behavior
Specify desktop, tablet, and mobile layouts.

## Accessibility
Keyboard, focus, labels, semantics, contrast, and screen-reader behavior.

## Acceptance criteria
A testable checklist of expected outcomes.

## Open questions
List unresolved product or engineering decisions rather than silently guessing.
```

### Future-page design principle

Each page should look like part of the same SlotSmith product. Reuse the
same typography, spacing, colours, controls, card language, borders,
focus states, and navigation conventions. Page-specific complexity may
change, but the product should not look as if each screen came from a
different template.
