# SlotSmith UX research

Accessed 11 Oct 2026 (IST). Scope: targeted, not exhaustive. Method: fetched public pages with a page-summariser, plus local reading of Emerson PDFs already in `reference/emerson/` (retrieved 10 Oct). Summaries were produced by a fetch tool, so exact wording was not independently re-read on the live pages. Where a claim comes from a vendor blog rather than a standard, it is flagged. No authenticated interface was inspected. No product UI was reproduced.

## 1. Domain terminology (official sources)

| Fact | Source | Evidence |
|---|---|---|
| A CHARM is a single-channel module that characterises one field signal; 12 CHARMs sit on one baseplate; up to 8 baseplates hang below one CIOC carrier = 96 channels. | Emerson DeltaV Electronic Marshalling PDS (Aug 2026), pp. 1–3, 10 (local copy `reference/emerson/deltav-electronic-marshalling.pdf`) | Directly read |
| Home-run multi-core cables are "landed in order" on CHARM terminal blocks; "core #1 → CHARM 1-1" | same PDS p.1; CHARMs Commissioning white paper p.7 | Directly read |
| Six terminal-block types; Standard fits all CHARMs; Fused-Injected-Power for isolated DO; Relay Output needs the DO high-side CHARM | PDS pp. 4–5 | Directly read |
| 4 CIOCs per cabinet is a **hackathon project rule**, not an Emerson hardware limit | PS #02 p.5 vs PDS (no cabinet limit stated) | Directly compared |
| Non-HART signals are allocated to channels manually (drag-and-drop or Bulk Edit) | Smart Commissioning white paper p.5 | Directly read |

Consequence for UI wording: use "marshalling cabinet → CIOC → baseplate → CHARM slot" exactly as the PS and PDS do. Never present "4 CIOCs/cabinet" as an Emerson limit. Do not use "DeltaV-compliant" or "certified".

## 2. Reference matrix

| Reference | URL | Type | Transferable principle | Why it applies | Do not copy | Evidence |
|---|---|---|---|---|---|---|
| ISA-101 committee page | isa.org/…/isa101 | Standards body page | Scope lists menu hierarchy and screen navigation, graphics and colour conventions, popups and help. The page states no principles (the standard text is paywalled). | Confirms that navigation and colour conventions are first-class concerns for industrial interfaces. | Don't claim ISA-101 compliance: SlotSmith is an engineering workstation, not an operator HMI. | Direct (page) |
| High-performance HMI summaries (ifactoryapp, LADX, Emerson Automation Experts white paper) | via web search; several vendor/consultancy blogs | Vendor/secondary | Neutral grey as the normal state; colour reserved for abnormal; overview → detail hierarchy; flat schematic graphics. Exact hex values are rules of thumb, not the standard. | SlotSmith's cabinet map shows hundreds of "normal" slots; colour should signal attention (TQs, held slots, stale data), not decorate. | Specific shades or "90% grey" figures; operator-HMI alarm conventions. | Interpretation (secondary sources) |
| AVEVA Unified Engineering | aveva.com/…/unified-engineering | Official product page | Change propagation and tracked revisions/approvals are central to engineering software; page gives no detail on UI. | Validates "revision impact" as a headline workflow. | Cloud collaboration, 3D, AI assistant claims: not SlotSmith features. | Direct (page); UI details not available |
| Carbon Design System: Data table | carbondesignsystem.com/components/data-table/usage | Design-system docs | Row densities 24/32/40/48/64 px; search and filters in a toolbar above the table; single-select with an action area; skeleton over spinner for slow loads; header row height matches body rows. | TQ list, impact list and mapping review are dense tables with filters. | Component code or visuals. | Direct (summarised) |
| Carbon: Status indicator pattern | carbondesignsystem.com/patterns/status-indicator-pattern | Design-system docs | Pair at least two of colour/shape/symbol/type; ≥ 3:1 contrast; place the indicator next to the element it describes; use the highest-attention colour for consolidated status; skip indicators when no action is needed. | Verification PASS/FAIL, TQ severity, stale-result banner. | Their palette. | Direct (summarised) |
| GitHub Primer: DataTable | primer.style/product/components/data-table | Design-system docs | Title and subtitle linked via aria attributes; right-align numeric columns; default sort; one primary row action. | Tables of counts and addresses. | — | Direct (page truncated: loading/empty/keyboard not covered) |
| Linear: "How we redesigned the Linear UI" | linear.app/now/how-we-redesigned-the-linear-ui | Product design case study | Reduce visual noise; keep alignment; perceptual colour space for themes; few theme inputs (base, accent, contrast) generate the full palette; neutral palette over brand-saturated surfaces. | Supports a token system with few inputs, a restrained accent, and neutral surfaces. | Their layout and branding. | Direct (summarised) |
| WCAG 2.2 SC 2.5.8 Target Size (Minimum) | w3.org/WAI/WCAG22/Understanding/target-size-minimum | Standard | Pointer targets ≥ 24×24 CSS px, with spacing/inline/equivalent exceptions. | Cabinet slots are pointer targets. They must be ≥ 24 px or have an equivalent control (search + slot list). | — | Direct |
| Okabe–Ito palette (jfly.uni-koeln.de/color) | Research page | Colour-universal-design guidance | Don't encode by colour alone; add shape, symbol, position; label directly instead of a key; avoid red on dark backgrounds. | Six signal types must stay distinguishable. | The page does not list the palette numerically; the standard Okabe–Ito hex values used in `design.md` come from the published palette, not from this fetch (unverified in this session). | Mixed |
| Streamlit docs (`st.html`, theming, `st.context`) | docs.streamlit.io (v1.65.0) | Framework docs | (a) `st.html` is DOMPurify-sanitised, not in an iframe, scripts ignored unless `unsafe_allow_javascript`; style-only HTML goes to the event container and takes no layout space. (b) `[theme.light]` / `[theme.dark]` are supported; users switch in the Settings menu. (c) `st.context.theme.type` is inferred from background colour and "may be wrong on first load and when the user changes the theme". | Dictates the theme architecture (§4). | — | Direct |

## 3. Empirical findings (this repository, 11 Oct 2026)

1. **Streamlit sets `color-scheme` on `.stApp`.** In headless Chromium, `getComputedStyle(.stApp).colorScheme` was `light` or `dark` according to the emulated system theme; `light-dark()` colours resolved correctly inside `.stApp`. Consequence: CSS custom properties defined with `light-dark()` follow Streamlit's native theme instantly, without a rerun, without server-side theme detection, and without a second theme state.
2. **AppTest supports `st.navigation`, `st.Page` and `st.switch_page`** in Streamlit 1.65 (verified with a 10-line spike). Native multipage routing is therefore testable.
3. **The previous Stage 3 crashed in a real browser** with `StreamlitDuplicateElementKey` (the rules toggles were rendered twice with the same key), although 77 AppTests passed. Browser verification is not optional.
4. The previous landing page embedded ≈1.6 MB of JPEGs as base64 on every run and used anchor links with query parameters for navigation (see `docs/ux_review_log.md` for measurements).

## 4. Patterns to adopt

1. **Neutral-first colour.** Grey surfaces; colour carries meaning (exceptions, selection, status). The cabinet map uses tinted, low-chroma type colours *plus two-letter codes*, and reserves saturated colour for held/TQ slots and selection. (ISA-101-style principle; interpretation from secondary sources.)
2. **Status = colour + symbol + text.** Every status (pass, fail, stale, blocking, warning) has an icon and a label. (Carbon status pattern; Okabe–Ito guidance.)
3. **Toolbar-over-table.** Search, severity filter and count sit directly above each table; numeric columns right-aligned. (Carbon, Primer.)
4. **One navigation system.** A single stage rail, with step status, is the only workbench navigation. (Own finding on the previous UI; Linear's emphasis on hierarchy.)
5. **Overview → detail.** Results summary → cabinet → CIOC → baseplate → slot detail. (High-performance HMI hierarchy; interpretation.)
6. **Skeleton/inline progress for solver runs** instead of a blank screen; show elapsed work and the solver's reported status. (Carbon.)
7. **Tokens with few inputs, `light-dark()` pairs, native theme.** (Linear; empirical finding 1.)
8. **Real output as the product preview.** The landing page's signal-flow figure and examples are computed by the real engine at load, labelled synthetic. (Honesty requirement.)

## 5. Patterns rejected

- Operator-HMI conventions (alarm colours for equipment state; ISA-101 compliance claims).
- Marketing-grade hero photography, stock plant images, device-frame mock-ups with fake UI.
- Fake telemetry, "live" indicators, counters that tick, invented customer outcomes.
- Glassmorphism, glow, gradient washes, emoji as icons.
- Custom JavaScript theme toggle (would create a second theme state conflicting with Streamlit's).
- Web fonts from a CDN (extra network dependency; no offline demo).
- A 3D or physics visualisation: costly, not comprehensible faster than a 2D schematic.

## 6. Signature visualisation: options and decision

| Criterion (0–3) | A. Signal-flow schematic: MDB rows → Validate → Allocate → Verify → slot | B. Static-to-interactive cabinet/slot grid hero | C. Revision "ghost slots" diff animation |
|---|---|---|---|
| Relevance to electronic marshalling | 3 | 3 | 2 |
| Comprehensible in seconds | 3 | 2 (grid alone has no story) | 2 |
| Distinctiveness | 3 | 2 | 3 |
| Implementation cost (3 = cheap) | 2 | 3 | 1 |
| Performance (3 = best) | 3 (CSS/SVG) | 3 | 2 |
| Accessibility / reduced motion | 3 | 3 | 2 |
| Compatibility with Streamlit | 3 (`st.html` SVG + native pills) | 3 | 2 |
| Risk of implying live data | 2: mitigated by a visible "computed from synthetic data" label | 2 | 2 |
| **Total** | **22** | **21** | **16** |

**Decision: A, with B embedded as its endpoint.** The figure shows three real MDB rows entering a pipeline and landing on a real slot of a real allocated baseplate. The viewer picks a signal with native pills; its path and slot highlight, with the actual CHARM address. Motion is a single slow dash-flow along the active path (CSS), disabled under `prefers-reduced-motion`, and the static state is fully meaningful. It is labelled as computed by SlotSmith from a seeded synthetic MDB.

## 7. Evidence-backed recommendations (feed `design.md`)

R1. Replace the dual navigation (radio + sidebar + landing anchors) with `st.navigation` pages and one stage rail.
R2. Use native Streamlit theming (`[theme.light]`, `[theme.dark]`) plus CSS `light-dark()` tokens. No JS, no `st.context.theme` dependency.
R3. Keep all session data in `st.session_state`; derive status from fingerprints (existing, tested); show *Current / Stale* beside every result.
R4. Make the cabinet map a 24 px-target grid with a searchable slot list and detail panel; encode type with letter + tint.
R5. Show TQs as a filterable table with the rule ID, source rows and suggested action.
R6. Render the rules as a first-class setup panel with a computed implication line (e.g. "4 of 32 baseplates kept empty per cabinet"), never static text.
R7. Show solver status honestly: window repairs "proven exact" vs "best found within the time limit"; fallback shown as a warning.
R8. Provide a Rev B workbook download (the previous UI exposed none).
R9. Remove all invented preview content.

## 8. Open questions and confidence

| Question | Confidence | Note |
|---|---|---|
| Do judges/engineers prefer light or dark by default? | Low | Follow the user's system/Streamlit setting. |
| Exact Okabe–Ito hex values | Medium-high | Standard published values; not re-fetched. |
| ISA-101 normative colour rules | Low | Standard text is paywalled; secondary sources only. |
| Whether `light-dark()` is supported by all judges' browsers | Medium | Supported in Chrome ≥ 123, Safari ≥ 17.5, Firefox ≥ 120. A fixed fallback token is declared before each pair. |
| Whether Emerson engineers would map "CHARM slot" naming the same way (`001-CBP-1-01`) | Low | Naming is a user-defined project rule in the PS. |
