"""SlotSmith design tokens and stylesheet (design.md sections C and D).

Colours are CSS custom properties declared on `.stApp` with `light-dark()`. Streamlit sets `color-scheme`
on `.stApp` for its active theme, so these flip with the native Settings switch (or the system setting) with no
rerun, no JavaScript and no server-side theme state. A hex fallback precedes each pair for older browsers.
"""
from __future__ import annotations

from functools import lru_cache

# name: (light, dark)
TOKENS: dict[str, tuple[str, str]] = {
    "bg": ("#EEF0F3", "#12161B"),
    "surface": ("#FFFFFF", "#1A1F26"),
    "surface-2": ("#F6F7F9", "#222831"),
    "border": ("#D3D8DF", "#303846"),
    "border-strong": ("#A9B1BC", "#4A5565"),
    "text": ("#16202B", "#E8ECF1"),
    "text-2": ("#46525F", "#AAB4C1"),
    "text-3": ("#5F6B78", "#8F9AA8"),
    "accent": ("#0A6C7A", "#4FC3CF"),
    "accent-fg": ("#FFFFFF", "#062329"),
    "accent-soft": ("#DCEFF1", "#173840"),
    "ok": ("#187233", "#4CC775"),
    "ok-soft": ("#E1F2E6", "#173A24"),
    "warn": ("#8A5A00", "#F0B64A"),
    "warn-soft": ("#FBEFD2", "#41330F"),
    "bad": ("#B3261E", "#FF8F86"),
    "bad-soft": ("#FBE4E2", "#472220"),
    "info": ("#2B5DB8", "#86AEF5"),
    "info-soft": ("#E3ECFA", "#1C2D4C"),
    # signal types: fill, text
    "t-ai": ("#CFE6F5", "#1E3F57"), "t-ai-fg": ("#0B4A72", "#9FD3F5"),
    "t-ao": ("#F0D3E3", "#4A2A3D"), "t-ao-fg": ("#6B2146", "#F1B4D2"),
    "t-di": ("#C8EBDD", "#1B4636"), "t-di-fg": ("#0A5640", "#8FE0C0"),
    "t-do": ("#F8E3B0", "#4D3A12"), "t-do-fg": ("#6B4700", "#F5CF75"),
    "t-df": ("#F7D3BB", "#55301A"), "t-df-fg": ("#7A3200", "#F5B188"),
    "t-rl": ("#CDD6F6", "#2A3566"), "t-rl-fg": ("#1F3A8A", "#B8C6FF"),
}

FONT_SANS = 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
FONT_MONO = 'ui-monospace, "SF Mono", "Cascadia Mono", Menlo, Consolas, monospace'


def _token_block() -> str:
    lines = []
    for name, (light, dark) in TOKENS.items():
        lines.append(f"--ss-{name}:{light};--ss-{name}:light-dark({light},{dark});")
    return "".join(lines)


_CSS = """
.stApp{@@TOKENS@@
--ss-font:@@SANS@@;--ss-mono:@@MONO@@;--ss-maxw:1360px;
--ss-r-sm:4px;--ss-r-md:6px;--ss-r-lg:10px;
--ss-focus:2px solid var(--ss-accent);
background:var(--ss-bg);color:var(--ss-text);font-family:var(--ss-font);}
.stApp, .stApp p, .stApp label, .stApp li, .stApp input, .stApp textarea, .stApp button{font-family:var(--ss-font);}
[data-testid="stMainBlockContainer"]{max-width:var(--ss-maxw);padding:1.25rem 2rem 4rem;}
[data-testid="stHeader"]{background:transparent;}
h1,h2,h3,h4{font-family:var(--ss-font);letter-spacing:-0.01em;color:var(--ss-text);}
.stApp h2{font-size:1.75rem;line-height:1.2;margin:0 0 .25rem;padding:0;font-weight:700;}
.stApp h3{font-size:1.25rem;line-height:1.3;font-weight:650;}
.stApp h4{font-size:1.05rem;line-height:1.35;font-weight:650;margin:0 0 .25rem;padding:0;}
a{color:var(--ss-accent);}
code,.ss-mono{font-family:var(--ss-mono);font-variant-numeric:tabular-nums;}
.ss-skip{position:absolute;left:-999px;top:0;background:var(--ss-surface);color:var(--ss-text);padding:8px 12px;z-index:100;border:1px solid var(--ss-border-strong);border-radius:var(--ss-r-md);}
.ss-skip:focus{left:8px;top:8px;}

/* ---- focus (native widgets included) ---- */
.stApp button:focus-visible,.stApp a:focus-visible,.stApp [role="tab"]:focus-visible,.stApp [role="radio"]:focus-visible,
.stApp .ss-cabwrap:focus-visible,.stApp input:focus-visible,.stApp [data-baseweb="select"]:focus-within,.stApp [role="switch"]:focus-visible,.stApp summary:focus-visible{
 outline:var(--ss-focus);outline-offset:2px;box-shadow:0 0 0 4px var(--ss-accent-soft);}

/* ---- buttons ---- */
.stApp [data-testid="stBaseButton-primary"],.stApp [data-testid="stBaseButton-primaryFormSubmit"]{background:var(--ss-accent);color:var(--ss-accent-fg);border:1px solid var(--ss-accent);font-weight:600;min-height:2.5rem;}
.stApp [data-testid="stBaseButton-primary"]:hover{filter:brightness(1.08);}
.stApp [data-testid="stBaseButton-primary"] p,.stApp [data-testid="stBaseButton-primary"] span{color:var(--ss-accent-fg);}
.stApp [data-testid="stBaseButton-secondary"],.stApp [data-testid="stBaseButton-secondaryFormSubmit"],.stApp [data-testid="stDownloadButton"] button{background:var(--ss-surface);color:var(--ss-text);border:1px solid var(--ss-border-strong);min-height:2.5rem;font-weight:550;}
.stApp [data-testid="stBaseButton-secondary"]:hover,.stApp [data-testid="stDownloadButton"] button:hover{border-color:var(--ss-accent);color:var(--ss-accent);}
.stApp [data-testid="stBaseButton-tertiary"]{color:var(--ss-accent);min-height:2.25rem;}
.stApp button:disabled{opacity:.45;cursor:not-allowed;}
.stApp [data-testid="stDownloadButton"] button[kind="primary"],.stApp [data-testid="stDownloadButton"] [data-testid="stBaseButton-primary"]{background:var(--ss-accent);color:var(--ss-accent-fg);}

/* ---- page links ---- */
.stApp [data-testid="stPageLink-NavLink"]{border-radius:var(--ss-r-md);min-height:2.5rem;color:var(--ss-text);}
.stApp [data-testid="stPageLink-NavLink"]:hover{background:var(--ss-accent-soft);}
.stApp [data-testid="stPageLink-NavLink"][aria-current="page"]{background:var(--ss-accent-soft);font-weight:650;box-shadow:inset 3px 0 0 var(--ss-accent);}
.stApp [data-testid="stPageLink-NavLink"][disabled],.stApp [data-testid="stPageLink-NavLink"][aria-disabled="true"]{opacity:.5;}

/* ---- sidebar rail ---- */
[data-testid="stSidebar"]{background:var(--ss-surface);border-right:1px solid var(--ss-border);}
[data-testid="stSidebarContent"]{padding-top:.5rem;}
.ss-rail-group{font-size:12px;font-weight:600;color:var(--ss-text-3);letter-spacing:.02em;margin:14px 0 4px 10px;}
.ss-rail-meta{border:1px solid var(--ss-border);background:var(--ss-surface-2);border-radius:var(--ss-r-md);padding:10px 12px;margin:8px 0 12px;font-size:13px;line-height:1.45;}
.ss-rail-meta b{font-weight:650;}

/* ---- tabs, tables, expanders, alerts ---- */
.stApp [data-baseweb="tab-list"]{gap:4px;border-bottom:1px solid var(--ss-border);}
.stApp [data-baseweb="tab"]{min-height:40px;font-weight:550;color:var(--ss-text-2);}
.stApp [aria-selected="true"][data-baseweb="tab"]{color:var(--ss-accent);}
.stApp [data-baseweb="tab-highlight"]{background:var(--ss-accent);}
[data-testid="stDataFrame"]{border:1px solid var(--ss-border);border-radius:var(--ss-r-md);overflow:hidden;}
[data-testid="stExpander"] details{border:1px solid var(--ss-border);border-radius:var(--ss-r-md);background:var(--ss-surface);}
[data-testid="stExpander"] summary{min-height:2.5rem;}
.stApp [data-testid="stAlert"]{border-radius:var(--ss-r-md);}
.stApp [data-testid="stFileUploaderDropzone"]{background:var(--ss-surface);border:1px dashed var(--ss-border-strong);border-radius:var(--ss-r-lg);}
.stApp [data-testid="stCaptionContainer"],.stApp [data-testid="stCaptionContainer"] p,.stApp small{color:var(--ss-text-3) !important;opacity:1 !important;}
.stApp [data-testid="stWidgetLabel"] p{font-weight:600;font-size:14px;color:var(--ss-text);}
[data-testid="stToolbar"]{right:.75rem;}

/* ---- header ---- */
.ss-header{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;padding:6px 0 18px;min-height:48px;}
.ss-brand{display:inline-flex;align-items:center;gap:10px;font-weight:750;font-size:18px;letter-spacing:-.01em;color:var(--ss-text);text-decoration:none;}
.ss-mark{display:grid;grid-template-columns:repeat(4,6px);gap:2px;}
.ss-mark i{width:6px;height:6px;border-radius:1px;background:var(--ss-accent);display:block;}
.ss-mark i:nth-child(3n){background:var(--ss-text-3);opacity:.55;}
.ss-mark i:nth-child(5){background:var(--ss-t-ai-fg);}
.ss-nav{display:flex;gap:6px;margin-left:12px;}
.ss-nav a{color:var(--ss-text-2);text-decoration:none;font-size:14px;font-weight:550;padding:8px 10px;border-radius:var(--ss-r-md);min-height:24px;}
.ss-nav a:hover{background:var(--ss-accent-soft);color:var(--ss-text);}
.ss-spacer{flex:1;}

/* ---- chips and banners ---- */
.ss-chip{display:inline-flex;align-items:center;gap:6px;font-size:13px;font-weight:600;line-height:1;padding:6px 10px;border-radius:999px;border:1px solid transparent;white-space:nowrap;}
.ss-chip svg{width:14px;height:14px;flex:none;}
.ss-chip.ok{background:var(--ss-ok-soft);color:var(--ss-ok);border-color:color-mix(in srgb,var(--ss-ok) 35%,transparent);}
.ss-chip.warn{background:var(--ss-warn-soft);color:var(--ss-warn);border-color:color-mix(in srgb,var(--ss-warn) 35%,transparent);}
.ss-chip.bad{background:var(--ss-bad-soft);color:var(--ss-bad);border-color:color-mix(in srgb,var(--ss-bad) 35%,transparent);}
.ss-chip.info{background:var(--ss-info-soft);color:var(--ss-info);border-color:color-mix(in srgb,var(--ss-info) 35%,transparent);}
.ss-chip.neutral{background:var(--ss-surface-2);color:var(--ss-text-2);border-color:var(--ss-border);}
.ss-banner{display:flex;gap:12px;align-items:flex-start;padding:14px 16px;border-radius:var(--ss-r-md);border:1px solid var(--ss-border);background:var(--ss-surface);margin:8px 0 16px;}
.ss-banner svg{width:20px;height:20px;flex:none;margin-top:1px;}
.ss-banner b{display:block;font-weight:650;margin-bottom:2px;}
.ss-banner p{margin:0;color:var(--ss-text-2);font-size:14px;line-height:1.45;}
.ss-banner.ok{background:var(--ss-ok-soft);border-color:color-mix(in srgb,var(--ss-ok) 40%,transparent);} .ss-banner.ok svg{color:var(--ss-ok);}
.ss-banner.warn{background:var(--ss-warn-soft);border-color:color-mix(in srgb,var(--ss-warn) 45%,transparent);} .ss-banner.warn svg{color:var(--ss-warn);}
.ss-banner.bad{background:var(--ss-bad-soft);border-color:color-mix(in srgb,var(--ss-bad) 45%,transparent);} .ss-banner.bad svg{color:var(--ss-bad);}
.ss-banner.info{background:var(--ss-info-soft);border-color:color-mix(in srgb,var(--ss-info) 40%,transparent);} .ss-banner.info svg{color:var(--ss-info);}

/* ---- tiles, panels ---- */
.ss-tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:8px 0 18px;}
.ss-tile{background:var(--ss-surface);border:1px solid var(--ss-border);border-radius:var(--ss-r-md);padding:14px 16px;min-width:0;}
.ss-tile .l{font-size:13px;color:var(--ss-text-2);font-weight:550;}
.ss-tile .v{font-size:28px;line-height:1.15;font-weight:700;letter-spacing:-.01em;margin-top:2px;font-variant-numeric:tabular-nums;}
.ss-tile .q{font-size:12px;color:var(--ss-text-3);margin-top:2px;line-height:1.35;}
.ss-tile.stale{opacity:.6;} .ss-tile.attn .v{color:var(--ss-warn);} .ss-tile.bad .v{color:var(--ss-bad);} .ss-tile.good .v{color:var(--ss-ok);}
.ss-panel{background:var(--ss-surface);border:1px solid var(--ss-border);border-radius:var(--ss-r-lg);padding:18px 20px;}
.ss-panel h4{margin:0 0 6px;font-size:16px;font-weight:650;}
.ss-panel p,.ss-panel li{color:var(--ss-text-2);font-size:14px;line-height:1.5;}
.stApp .ss-kv{display:grid;grid-template-columns:max-content 1fr;gap:6px 16px;font-size:14px;margin:0;padding:0;}
.stApp .ss-kv dt{color:var(--ss-text-3);margin:0;padding:0;} .stApp .ss-kv dd{margin:0;padding:0;word-break:break-word;}
.ss-page-sub{color:var(--ss-text-2);font-size:15px;margin:0 0 18px;max-width:70ch;line-height:1.5;}
.ss-ledger{width:100%;border-collapse:collapse;font-size:14px;}
.ss-ledger th{text-align:left;font-weight:600;color:var(--ss-text-2);background:var(--ss-surface-2);padding:8px 12px;border-bottom:1px solid var(--ss-border);}
.ss-ledger td{padding:9px 12px;border-bottom:1px solid var(--ss-border);vertical-align:top;}
.ss-ledger td:first-child{white-space:nowrap;font-family:var(--ss-mono);font-size:13px;}
.ss-ledger td.n,.ss-ledger th.n{text-align:right;font-variant-numeric:tabular-nums;}
.ss-ledger tr:last-child td{border-bottom:0;}
.ss-ledger-wrap{border:1px solid var(--ss-border);border-radius:var(--ss-r-md);overflow:auto;background:var(--ss-surface);}

/* ---- stage list (landing) ---- */
.ss-panel .ss-tiles{grid-template-columns:repeat(2,minmax(0,1fr));}
.ss-panel ul{margin:8px 0 0;padding-left:20px;}
.ss-steps{margin:0 !important;padding:0 !important;display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;counter-reset:s;margin:0;padding:0;list-style:none;}
.ss-steps li{counter-increment:s;background:var(--ss-surface);border:1px solid var(--ss-border);border-radius:var(--ss-r-lg);padding:16px 18px;}
.ss-steps li::before{content:counter(s);display:inline-grid;place-items:center;width:24px;height:24px;border-radius:50%;background:var(--ss-accent-soft);color:var(--ss-accent);font-weight:700;font-size:13px;margin-bottom:8px;}
.ss-steps h4{margin:0 0 4px;font-size:16px;} .ss-steps p{margin:0;font-size:14px;color:var(--ss-text-2);line-height:1.45;}

/* ---- landing hero ---- */
.ss-hero h1{font-size:clamp(2rem,1.2rem + 2.6vw,2.9rem);line-height:1.08;letter-spacing:-.025em;font-weight:760;margin:12px 0 14px;max-width:21ch;}
.ss-hero p.lead{font-size:18px;line-height:1.55;color:var(--ss-text-2);max-width:62ch;margin:0 0 20px;}
.ss-section{margin:56px 0 12px;} .ss-section h2{font-size:1.6rem;margin-bottom:6px;} .ss-section .sub{color:var(--ss-text-2);max-width:68ch;margin:0 0 18px;line-height:1.5;}
.ss-foot{margin-top:64px;padding-top:20px;border-top:1px solid var(--ss-border);color:var(--ss-text-3);font-size:13px;line-height:1.6;}

/* ---- signal-flow figure ---- */
.ss-flow{background:var(--ss-surface);border:1px solid var(--ss-border);border-radius:var(--ss-r-lg);padding:20px;margin:6px 0 0;}
.ss-flow ol{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:1fr 1fr 1.1fr 1fr 1.55fr;gap:34px;}
.ss-fstep{position:relative;background:var(--ss-surface-2);border:1px solid var(--ss-border);border-radius:var(--ss-r-md);padding:12px 12px 14px;min-width:0;font-size:13px;line-height:1.45;}
.ss-fstep h4{margin:0 0 6px;font-size:14px;font-weight:700;color:var(--ss-text);display:flex;gap:8px;align-items:center;}
.ss-fstep h4 span{font-weight:500;color:var(--ss-text-3);font-size:12px;}
.ss-fstep .mono{font-family:var(--ss-mono);font-size:12px;word-break:break-all;}
.ss-fstep .row{display:flex;justify-content:space-between;gap:8px;border-top:1px dashed var(--ss-border);padding-top:4px;margin-top:4px;}
.ss-fstep .row span:first-child{color:var(--ss-text-3);}
.ss-fstep::after{content:"";position:absolute;top:50%;right:-34px;width:34px;height:2px;
 background:repeating-linear-gradient(90deg,var(--ss-accent) 0 6px,transparent 6px 12px);background-size:24px 2px;animation:ss-flow 2.4s linear infinite;}
.ss-fstep:last-child::after{display:none;}
.ss-fstep.act{border-color:var(--ss-accent);box-shadow:0 0 0 3px var(--ss-accent-soft);}
.ss-bp{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:2px;margin-top:8px;}
.ss-bp i{display:grid;place-items:center;aspect-ratio:1;font-style:normal;font-size:9px;font-weight:700;border-radius:2px;background:var(--ss-surface);border:1px dashed var(--ss-border);color:var(--ss-text-3);min-width:0;}
.ss-bp i.sel{outline:2px solid var(--ss-accent);outline-offset:1px;box-shadow:0 0 0 4px var(--ss-accent-soft);}
.ss-cap{font-size:12px;color:var(--ss-text-3);margin-top:12px;line-height:1.5;}
@keyframes ss-flow{from{background-position:0 0}to{background-position:24px 0}}
@media (max-width:1099px){.ss-flow ol{grid-template-columns:1fr;gap:30px;}.ss-fstep::after{top:auto;bottom:-30px;right:auto;left:24px;width:2px;height:30px;background:repeating-linear-gradient(180deg,var(--ss-accent) 0 6px,transparent 6px 12px);background-size:2px 24px;animation-name:ss-flow-v;}}
@keyframes ss-flow-v{from{background-position:0 0}to{background-position:0 24px}}

/* ---- signal-type cells (selectors carry .ss-bp i / .ss-slot so they outrank the base cell rules) ---- */
.ss-bp i.t-ai,.ss-slot.t-ai{background:var(--ss-t-ai);color:var(--ss-t-ai-fg);border:1px solid transparent;}
.ss-bp i.t-ao,.ss-slot.t-ao{background:var(--ss-t-ao);color:var(--ss-t-ao-fg);border:1px solid transparent;}
.ss-bp i.t-di,.ss-slot.t-di{background:var(--ss-t-di);color:var(--ss-t-di-fg);border:1px solid transparent;}
.ss-bp i.t-do,.ss-slot.t-do{background:var(--ss-t-do);color:var(--ss-t-do-fg);border:1px solid transparent;}
.ss-bp i.t-df,.ss-slot.t-df{background:var(--ss-t-df);color:var(--ss-t-df-fg);border:1px solid transparent;}
.ss-bp i.t-rl,.ss-slot.t-rl{background:var(--ss-t-rl);color:var(--ss-t-rl-fg);border:1px solid transparent;}
.ss-bp i.spare,.ss-slot.spare{background:repeating-linear-gradient(135deg,var(--ss-surface-2) 0 3px,var(--ss-border) 3px 4px);border:1px solid var(--ss-border);color:var(--ss-text-3);}
.ss-bp i.held,.ss-slot.held{background:var(--ss-warn-soft);border:1px solid var(--ss-warn);color:var(--ss-warn);}

/* ---- cabinet grid ---- */
.ss-cabwrap{display:flex;gap:22px;overflow-x:auto;padding:16px;background:var(--ss-surface);border:1px solid var(--ss-border);border-radius:var(--ss-r-lg);}
.ss-cioc{flex:none;min-width:0;}
.ss-cioc-h{font-size:13px;font-weight:650;margin:0 0 2px;font-family:var(--ss-mono);}
.ss-cioc-s{font-size:12px;color:var(--ss-text-3);margin:0 0 8px;}
.ss-bprow{display:flex;align-items:center;gap:3px;margin-bottom:4px;}
.ss-bpn{width:20px;font-size:11px;color:var(--ss-text-3);text-align:right;margin-right:3px;font-variant-numeric:tabular-nums;}
.ss-slot{width:24px;height:24px;display:grid;place-items:center;border-radius:var(--ss-r-sm);font-size:10px;font-weight:700;border:1px solid transparent;flex:none;font-family:var(--ss-font);}
.ss-slot.free{background:transparent;border:1px dashed var(--ss-border);color:transparent;}
.ss-slot.sel{outline:2px solid var(--ss-accent);outline-offset:1px;box-shadow:0 0 0 4px var(--ss-accent-soft);z-index:1;}
.ss-slot.dim{opacity:.22;}
.ss-legend{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:13px;margin:10px 0 14px;color:var(--ss-text-2);}
.ss-legend span{display:inline-flex;align-items:center;gap:6px;}
.ss-legend .ss-slot{width:22px;height:22px;font-size:9px;}

/* ---- bars ---- */
.ss-bar{height:8px;border-radius:4px;background:var(--ss-surface-2);border:1px solid var(--ss-border);overflow:hidden;min-width:80px;}
.ss-bar i{display:block;height:100%;background:var(--ss-accent);}

/* ---- responsive ---- */
@media (min-width:769px){.st-key-stages_menu{display:none;}}
@media (max-width:768px){.ss-header{padding-left:34px;}}
@media (max-width:1099px){[data-testid="stMainBlockContainer"]{padding:1rem 1.25rem 3rem;}}
@media (max-width:699px){
 [data-testid="stMainBlockContainer"]{padding:.75rem .9rem 3rem;}
 .ss-nav{display:none;} .ss-header{gap:10px;flex-wrap:wrap;}
 .ss-tiles{grid-template-columns:repeat(2,minmax(0,1fr));}
 .ss-hero p.lead{font-size:16px;}
 .ss-section{margin-top:40px;}
}
@media (prefers-reduced-motion:reduce){
 .stApp *,.stApp *::before,.stApp *::after{animation:none !important;transition:none !important;scroll-behavior:auto !important;}
}
"""


@lru_cache(maxsize=1)
def stylesheet() -> str:
    return _CSS.replace("@@TOKENS@@", _token_block()).replace("@@SANS@@", FONT_SANS).replace("@@MONO@@", FONT_MONO)


def maxw_override(px: int) -> str:
    """Per-page content width (landing 1200, workbench 1360)."""
    return f".stApp{{--ss-maxw:{int(px)}px;}}"
