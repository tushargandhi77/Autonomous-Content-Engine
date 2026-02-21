"""
Autonomous Content Engine — Streamlit App
Enhanced UI version with improved light mode, auth page, and visual polish.
All logic preserved, only UI/CSS enhanced.
"""

import sys, os, secrets
from datetime import datetime, timezone, timedelta

import bcrypt
import streamlit as st
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Content Engine",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme defaults ────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True

dark = st.session_state.dark_mode

# ── Color palette ─────────────────────────────────────────────────────────────
if dark:
    bg_main        = "#080810"
    bg_card        = "#0f0f1a"
    bg_card2       = "#131325"
    bg_sidebar     = "#0b0b16"
    text_primary   = "#ede8ff"
    text_sec       = "#8b86a8"
    text_muted     = "#4a465e"
    border_col     = "rgba(120,100,255,0.1)"
    border_input   = "rgba(120,100,255,0.18)"
    input_bg       = "#0f0f1a"
    input_text     = "#ede8ff"
    accent         = "#7c5cfc"
    accent2        = "#a855f7"
    accent_light   = "#c4a8ff"
    accent_soft    = "rgba(124,92,252,0.12)"
    hero_sub       = "#5c586e"
    hist_label     = "#2e2a40"
    md_p           = "#9e9ab8"
    md_h2          = "#c8c4e0"
    md_code_bg     = "rgba(124,92,252,0.15)"
    md_code_c      = "#c8a8f8"
    md_pre_bg      = "#07070f"
    alert_bg       = "rgba(124,92,252,0.08)"
    alert_border   = "rgba(124,92,252,0.2)"
    alert_text     = "#c8b4f8"
    mode_icon      = "☀️"
    mode_label     = "Light"
    chip_bg        = "rgba(124,92,252,0.08)"
    chip_border    = "rgba(124,92,252,0.2)"
    pipeline_run   = "#7c5cfc"
    pipeline_done  = "rgba(80,220,130,0.4)"
    auth_bg_from   = "#0a0818"
    auth_bg_to     = "#130f28"
    glow1          = "rgba(124,92,252,0.35)"
    glow2          = "rgba(168,85,247,0.2)"
    noise_opacity  = "0.03"
    card_shadow    = "0 32px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(124,92,252,0.1)"
    divider_col    = "rgba(124,92,252,0.12)"
    tab_active_bg  = "rgba(124,92,252,0.15)"
    input_shadow   = "0 0 0 3px rgba(124,92,252,0.2)"
    btn_shadow     = "0 8px 32px rgba(124,92,252,0.4)"
    eyebrow_color  = "#7c5cfc"
    tag_bg         = "rgba(124,92,252,0.1)"
else:
    bg_main        = "#f7f5ff"
    bg_card        = "#ffffff"
    bg_card2       = "#f0eeff"
    bg_sidebar     = "#f2f0ff"
    text_primary   = "#1a1535"
    text_sec       = "#5a5478"
    text_muted     = "#9490b0"
    border_col     = "rgba(98,64,232,0.1)"
    border_input   = "rgba(98,64,232,0.2)"
    input_bg       = "#ffffff"
    input_text     = "#1a1535"
    accent         = "#6240e8"
    accent2        = "#9333ea"
    accent_light   = "#7c5cf0"
    accent_soft    = "rgba(98,64,232,0.08)"
    hero_sub       = "#7a7694"
    hist_label     = "#c4c0d8"
    md_p           = "#4a4668"
    md_h2          = "#2a2448"
    md_code_bg     = "rgba(98,64,232,0.07)"
    md_code_c      = "#5a3cc8"
    md_pre_bg      = "#f5f3ff"
    alert_bg       = "rgba(98,64,232,0.05)"
    alert_border   = "rgba(98,64,232,0.15)"
    alert_text     = "#5a3cc8"
    mode_icon      = "🌙"
    mode_label     = "Dark"
    chip_bg        = "rgba(98,64,232,0.06)"
    chip_border    = "rgba(98,64,232,0.14)"
    pipeline_run   = "#6240e8"
    pipeline_done  = "rgba(40,180,90,0.35)"
    auth_bg_from   = "#f0eeff"
    auth_bg_to     = "#e8e4ff"
    glow1          = "rgba(98,64,232,0.12)"
    glow2          = "rgba(147,51,234,0.08)"
    noise_opacity  = "0.02"
    card_shadow    = "0 24px 64px rgba(98,64,232,0.12), 0 0 0 1px rgba(98,64,232,0.08)"
    divider_col    = "rgba(98,64,232,0.1)"
    tab_active_bg  = "rgba(98,64,232,0.08)"
    input_shadow   = "0 0 0 3px rgba(98,64,232,0.12)"
    btn_shadow     = "0 8px 28px rgba(98,64,232,0.35)"
    eyebrow_color  = "#6240e8"
    tag_bg         = "rgba(98,64,232,0.07)"

# ── Comprehensive CSS ─────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,500;0,9..144,600;1,9..144,300;1,9..144,400&family=DM+Mono:wght@300;400;500&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body, [data-testid="stAppViewContainer"] {{
    background: {bg_main};
    color: {text_primary};
    font-family: 'Plus Jakarta Sans', sans-serif;
    transition: background 0.4s ease, color 0.4s ease;
}}

[data-testid="stAppViewContainer"] {{
    background: {bg_main};
    background-image:
        radial-gradient(ellipse 90% 50% at 20% -5%, {glow1} 0%, transparent 65%),
        radial-gradient(ellipse 60% 40% at 85% 90%, {glow2} 0%, transparent 60%),
        radial-gradient(ellipse 40% 30% at 60% 50%, rgba(124,92,252,0.03) 0%, transparent 70%);
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: {bg_sidebar} !important;
    border-right: 1px solid {border_col} !important;
    transition: background 0.4s ease;
}}
[data-testid="stSidebar"] > div {{ padding: 1.4rem 1rem 2rem; }}

/* Hide Streamlit chrome */
#MainMenu, footer, header {{ display: none !important; }}
.block-container {{
    padding: 2rem 2.5rem 5rem;
    max-width: 1120px;
}}

/* ── Typography ── */
h1, h2, h3 {{
    font-family: 'Fraunces', serif;
    letter-spacing: -0.02em;
}}

/* ═══════════════════════════════════════════
   AUTH PAGE — Complete redesign
═══════════════════════════════════════════ */

.auth-page-wrapper {{
    min-height: 100vh;
    display: flex;
    align-items: stretch;
}}

/* Auth card */
.auth-card {{
    width: 100%;
    max-width: 480px;
    margin: 3vh auto 0;
    background: {bg_card};
    border: 1px solid {border_col};
    border-radius: 24px;
    padding: 3rem 3rem 2.5rem;
    box-shadow: {card_shadow};
    position: relative;
    overflow: hidden;
    transition: background 0.4s;
}}

.auth-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, {accent} 0%, {accent2} 50%, {accent_light} 100%);
    border-radius: 24px 24px 0 0;
}}

.auth-card::after {{
    content: '';
    position: absolute;
    top: -80px; right: -80px;
    width: 200px; height: 200px;
    border-radius: 50%;
    background: radial-gradient(circle, {glow1} 0%, transparent 70%);
    pointer-events: none;
}}

.auth-badge {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: {tag_bg};
    border: 1px solid {border_col};
    border-radius: 100px;
    padding: 0.25rem 0.75rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: {accent_light};
    margin-bottom: 1.2rem;
}}

.auth-badge .dot {{
    width: 5px; height: 5px;
    border-radius: 50%;
    background: {accent};
    box-shadow: 0 0 6px {accent};
    animation: pulse-dot 2s ease-in-out infinite;
}}

@keyframes pulse-dot {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.5; transform: scale(0.7); }}
}}

.auth-headline {{
    font-family: 'Fraunces', serif;
    font-size: 2.6rem;
    font-weight: 400;
    line-height: 1.08;
    color: {text_primary};
    margin-bottom: 0.5rem;
    letter-spacing: -0.03em;
}}

.auth-headline em {{
    font-style: italic;
    background: linear-gradient(135deg, {accent} 0%, {accent2} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.auth-sub {{
    font-size: 0.88rem;
    color: {text_muted};
    margin-bottom: 2rem;
    line-height: 1.6;
    font-weight: 400;
}}

.auth-divider {{
    height: 1px;
    background: linear-gradient(90deg, transparent, {divider_col}, transparent);
    margin: 1.5rem 0;
}}

/* Feature tags under auth */
.auth-features {{
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-top: 1.5rem;
}}
.auth-feature-tag {{
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    padding: 0.2rem 0.6rem;
    border-radius: 100px;
    background: {tag_bg};
    color: {text_muted};
    border: 1px solid {border_col};
    letter-spacing: 0.05em;
}}

/* ── Tabs (auth) ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    background: {"rgba(255,255,255,0.03)" if dark else "rgba(98,64,232,0.04)"} !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 2px !important;
    border: 1px solid {border_col} !important;
    margin-bottom: 1.2rem !important;
}}

[data-testid="stTabs"] [data-baseweb="tab"] {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    color: {text_muted} !important;
    letter-spacing: 0.02em !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.2s !important;
}}

[data-testid="stTabs"] [aria-selected="true"] {{
    color: {text_primary} !important;
    background: {tab_active_bg} !important;
    font-weight: 600 !important;
}}

/* ── Inputs (enhanced) ── */
.stTextInput input, .stTextArea textarea, .stNumberInput input {{
    background: {"rgba(255,255,255,0.03)" if dark else "#faf9ff"} !important;
    border: 1.5px solid {border_input} !important;
    border-radius: 12px !important;
    color: {input_text} !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.75rem 1rem !important;
    transition: all 0.25s !important;
    caret-color: {accent} !important;
}}

.stTextInput input:focus, .stTextArea textarea:focus {{
    border-color: {accent} !important;
    box-shadow: {input_shadow} !important;
    background: {"rgba(124,92,252,0.04)" if dark else "#fff"} !important;
    outline: none !important;
}}

.stTextInput label, .stTextArea label, .stNumberInput label {{
    color: {text_sec} !important;
    font-size: 0.72rem !important;
    font-family: 'DM Mono', monospace !important;
    letter-spacing: 0.09em !important;
    text-transform: uppercase !important;
    font-weight: 500 !important;
    margin-bottom: 0.3rem !important;
}}

/* ── Buttons (primary) ── */
.stButton > button {{
    background: linear-gradient(135deg, {accent} 0%, {accent2} 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.7rem 1.8rem !important;
    cursor: pointer !important;
    transition: all 0.25s ease !important;
    box-shadow: {btn_shadow} !important;
    letter-spacing: 0.01em !important;
    position: relative !important;
    overflow: hidden !important;
}}

.stButton > button::after {{
    content: '' !important;
    position: absolute !important;
    inset: 0 !important;
    background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, transparent 60%) !important;
    pointer-events: none !important;
}}

.stButton > button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 40px rgba(124,92,252,0.5) !important;
    filter: brightness(1.05) !important;
}}

.stButton > button:active {{
    transform: translateY(0) !important;
    box-shadow: 0 4px 16px rgba(124,92,252,0.3) !important;
}}

/* Ghost / secondary buttons */
.stButton > button[kind="secondary"] {{
    background: {"rgba(255,255,255,0.04)" if dark else "rgba(255,255,255,0.9)"} !important;
    border: 1.5px solid {border_col} !important;
    color: {text_sec} !important;
    box-shadow: none !important;
    font-weight: 500 !important;
}}

.stButton > button[kind="secondary"]:hover {{
    background: {chip_bg} !important;
    border-color: {accent} !important;
    color: {accent_light} !important;
}}

/* Download button */
.stDownloadButton > button {{
    background: {"rgba(255,255,255,0.04)" if dark else "rgba(98,64,232,0.04)"} !important;
    border: 1.5px solid {chip_border} !important;
    border-radius: 10px !important;
    color: {accent_light} !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    padding: 0.5rem 1.2rem !important;
    letter-spacing: 0.04em !important;
    transition: all 0.2s !important;
    box-shadow: none !important;
}}

.stDownloadButton > button:hover {{
    background: {accent_soft} !important;
    border-color: {accent} !important;
    transform: translateY(-1px) !important;
}}

/* ══════════════════════════════════════════
   HERO SECTION
══════════════════════════════════════════ */
.hero {{
    padding: 3.5rem 0 2.5rem;
    border-bottom: 1px solid {border_col};
    margin-bottom: 2.5rem;
    position: relative;
}}

.hero-eyebrow {{
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: {eyebrow_color};
    margin-bottom: 1rem;
    padding: 0.25rem 0.75rem;
    background: {tag_bg};
    border-radius: 100px;
    border: 1px solid {border_col};
}}

.hero-title {{
    font-family: 'Fraunces', serif;
    font-size: clamp(2.6rem, 5.5vw, 4rem);
    font-weight: 400;
    line-height: 1.08;
    color: {text_primary};
    margin: 0 0 0.75rem;
    letter-spacing: -0.03em;
}}

.hero-title em {{
    font-style: italic;
    background: linear-gradient(135deg, {accent} 0%, {accent2} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.hero-sub {{
    font-size: 0.95rem;
    color: {hero_sub};
    font-weight: 400;
    line-height: 1.6;
    max-width: 520px;
}}

/* ══════════════════════════════════════════
   PIPELINE CARDS
══════════════════════════════════════════ */
.pipeline-card {{
    background: {bg_card};
    border: 1px solid {border_col};
    border-radius: 14px;
    padding: 1rem 1.4rem;
    margin-bottom: 0.65rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: border-color 0.3s, background 0.3s, box-shadow 0.3s;
}}

.pipeline-card.active {{
    border-color: {accent};
    box-shadow: 0 0 0 1px {accent_soft}, 0 8px 24px {accent_soft};
    background: {"rgba(124,92,252,0.04)" if dark else "rgba(98,64,232,0.03)"};
}}

.pipeline-card.done {{
    border-color: {"rgba(80,220,130,0.3)" if dark else "rgba(40,180,90,0.25)"};
    background: {"rgba(80,220,130,0.03)" if dark else "rgba(40,180,90,0.02)"};
}}

.pipeline-icon {{ font-size: 1.15rem; flex-shrink: 0; }}
.pipeline-label {{
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    color: {text_muted};
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 0.1rem;
}}
.pipeline-value {{ font-size: 0.85rem; color: {text_sec}; }}

.badge {{
    margin-left: auto;
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    padding: 0.2rem 0.6rem;
    border-radius: 100px;
    letter-spacing: 0.06em;
    font-weight: 500;
}}
.badge-pending {{ background: {"rgba(255,255,255,0.05)" if dark else "rgba(0,0,0,0.05)"}; color: {text_muted}; }}
.badge-running {{
    background: rgba(124,92,252,0.2);
    color: {accent_light};
    animation: badge-pulse 1.5s ease-in-out infinite;
}}
@keyframes badge-pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.6; }}
}}
.badge-done    {{ background: {"rgba(80,220,130,0.15)" if dark else "rgba(40,180,90,0.12)"}; color: {"#60d890" if dark else "#28b45a"}; }}
.badge-skipped {{ background: {"rgba(255,180,50,0.1)" if dark else "rgba(220,140,20,0.1)"}; color: {"#e0a040" if dark else "#c07820"}; }}

/* ══════════════════════════════════════════
   OUTPUT / MARKDOWN AREA
══════════════════════════════════════════ */
.output-header {{
    display: flex;
    align-items: baseline;
    gap: 1rem;
    margin-bottom: 1.4rem;
    flex-wrap: wrap;
}}
.output-title {{
    font-family: 'Fraunces', serif;
    font-size: 1.7rem;
    color: {text_primary};
    font-weight: 400;
    letter-spacing: -0.02em;
}}
.output-meta {{
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: {text_muted};
    letter-spacing: 0.08em;
}}

.markdown-container {{
    background: {bg_card};
    border: 1px solid {border_col};
    border-radius: 16px;
    padding: 2.2rem;
    line-height: 1.8;
    transition: background 0.4s ease;
}}
.markdown-container h1 {{
    font-family: 'Fraunces', serif;
    font-size: 2rem;
    color: {text_primary};
    margin-bottom: 1.5rem;
    font-weight: 400;
    letter-spacing: -0.025em;
}}
.markdown-container h2 {{
    font-family: 'Fraunces', serif;
    font-size: 1.3rem;
    color: {md_h2};
    border-bottom: 1px solid {border_col};
    padding-bottom: 0.4rem;
    margin-top: 2.2rem;
    margin-bottom: 0.8rem;
    font-weight: 400;
}}
.markdown-container p  {{ color: {md_p}; margin-bottom: 1rem; font-size: 0.95rem; }}
.markdown-container code {{
    background: {md_code_bg};
    border-radius: 5px;
    padding: 0.12em 0.45em;
    font-family: 'DM Mono', monospace;
    font-size: 0.83em;
    color: {md_code_c};
}}
.markdown-container pre {{
    background: {md_pre_bg};
    border: 1px solid {border_col};
    border-radius: 10px;
    padding: 1.4rem;
    overflow-x: auto;
    margin: 1rem 0;
}}
.markdown-container pre code {{ background: transparent; color: {md_code_c}; }}
.markdown-container ul, .markdown-container ol {{
    color: {md_p};
    padding-left: 1.6rem;
    margin-bottom: 1rem;
}}
.markdown-container li {{ margin-bottom: 0.35rem; font-size: 0.95rem; }}
.markdown-container a {{
    color: {accent};
    text-decoration: none;
    border-bottom: 1px solid {accent_soft};
    transition: border-color 0.2s;
}}
.markdown-container a:hover {{ border-color: {accent}; }}

/* ══════════════════════════════════════════
   SIDEBAR — USER CHIP
══════════════════════════════════════════ */
.user-chip {{
    display: flex;
    align-items: center;
    gap: 0.7rem;
    background: {chip_bg};
    border: 1px solid {chip_border};
    border-radius: 14px;
    padding: 0.7rem 0.95rem;
    margin-bottom: 0.75rem;
    transition: background 0.4s;
}}
.user-avatar {{
    width: 34px; height: 34px; border-radius: 50%;
    background: linear-gradient(135deg, {accent} 0%, {accent2} 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.7rem; font-weight: 700; color: #fff;
    flex-shrink: 0;
    box-shadow: 0 4px 12px {accent_soft};
}}
.user-name  {{
    font-size: 0.85rem;
    color: {text_primary};
    font-weight: 600;
    line-height: 1.25;
    font-family: 'Plus Jakarta Sans', sans-serif;
}}
.user-email {{
    font-family: 'DM Mono', monospace;
    font-size: 0.58rem;
    color: {text_muted};
    margin-top: 0.05rem;
}}

/* ══════════════════════════════════════════
   SIDEBAR HISTORY CARDS
══════════════════════════════════════════ */
.hist-section-label {{
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {hist_label};
    margin-bottom: 0.7rem;
    padding: 0 0.1rem;
}}

.hist-card {{
    background: {bg_card};
    border: 1px solid {border_col};
    border-radius: 12px;
    padding: 0.75rem 0.9rem 0.6rem;
    margin-bottom: 0.5rem;
    transition: border-color 0.2s, background 0.2s;
}}

.hist-card.active {{
    border-color: {accent};
    background: {"rgba(124,92,252,0.05)" if dark else "rgba(98,64,232,0.04)"};
    box-shadow: 0 0 0 1px {accent_soft};
}}

/* ══════════════════════════════════════════
   SETTINGS SECTION LABEL
══════════════════════════════════════════ */
.settings-label {{
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: {hist_label};
    margin-bottom: 0.5rem;
    padding: 0 0.1rem;
}}

/* Expanders */
[data-testid="stExpander"] {{
    background: {"rgba(255,255,255,0.02)" if dark else "rgba(98,64,232,0.02)"} !important;
    border: 1px solid {border_col} !important;
    border-radius: 12px !important;
    margin-bottom: 0.5rem !important;
    transition: background 0.3s !important;
}}

[data-testid="stExpander"]:hover {{
    border-color: {chip_border} !important;
}}

[data-testid="stExpander"] summary {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    color: {text_sec} !important;
    padding: 0.6rem 0.9rem !important;
}}

/* Alerts */
[data-testid="stAlert"] {{
    background: {alert_bg} !important;
    border: 1px solid {alert_border} !important;
    border-radius: 12px !important;
    color: {alert_text} !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.88rem !important;
}}

/* HR */
hr {{
    border: none !important;
    border-top: 1px solid {divider_col} !important;
    margin: 1rem 0 !important;
}}

/* Spinner */
[data-testid="stSpinner"] > div > div {{
    border-top-color: {accent} !important;
}}

/* Radio */
[data-testid="stRadio"] label {{
    font-size: 0.88rem !important;
    color: {text_sec} !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}}

/* Sliders */
[data-testid="stSlider"] [data-baseweb="slider"] [data-testid*="StyledThumb"] {{
    background: {accent} !important;
    border-color: {accent} !important;
}}

/* Select slider */
[data-testid="stSlider"] [data-baseweb="slider"] [data-testid*="StyledTrackHighlight"] {{
    background: linear-gradient(90deg, {accent}, {accent2}) !important;
}}

/* Sidebar toggle button */
.sidebar-toggle {{
    position: fixed;
    top: 50%; left: 0;
    transform: translateY(-50%);
    z-index: 9999;
    background: linear-gradient(135deg, {accent}, {accent2});
    color: white;
    border: none;
    border-radius: 0 10px 10px 0;
    width: 22px; height: 60px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.65rem;
    transition: all 0.2s;
    box-shadow: 3px 0 16px {glow1};
}}

/* Mode pill */
.mode-closed_book {{ background: rgba(80,200,255,0.1); color: {"#60c8f8" if dark else "#0890c8"}; }}
.mode-hybrid      {{ background: rgba(255,180,50,0.1);  color: {"#e0a040" if dark else "#c07820"}; }}
.mode-open_book   {{ background: rgba(80,220,130,0.1);  color: {"#60d890" if dark else "#28b45a"}; }}
</style>
""", unsafe_allow_html=True)

# ── MongoDB ───────────────────────────────────────────────────────────────────
load_dotenv()

@st.cache_resource
def get_db():
    uri = os.getenv("MONGO_URI") or st.secrets.get("MONGO_URI", "")
    if not uri:
        st.error("MONGO_URI not set. Add it to `.streamlit/secrets.toml` or set it as an env variable.")
        st.stop()
    client = MongoClient(uri, serverSelectionTimeoutMS=6000)
    db = client["content_engine"]
    db["users"].create_index("email", unique=True)
    db["blogs"].create_index("user_id")
    db["sessions"].create_index("token", unique=True)
    db["sessions"].create_index("expires_at", expireAfterSeconds=0)
    return db

db = get_db()

# ── Auth helpers ──────────────────────────────────────────────────────────────
def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def check_pw(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())

def create_session(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    db["sessions"].insert_one({
        "token": token,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
    })
    return token

def get_user_from_token(token: str):
    if not token:
        return None
    session = db["sessions"].find_one({"token": token, "expires_at": {"$gt": datetime.now(timezone.utc)}})
    if not session:
        return None
    user = db["users"].find_one({"_id": ObjectId(session["user_id"])})
    return user

def delete_session(token: str):
    if token:
        db["sessions"].delete_one({"token": token})

def do_signup(name, email, pw):
    email = email.strip().lower()
    if db["users"].find_one({"email": email}):
        return None, "Email already registered."
    doc = {
        "name": name.strip(),
        "email": email,
        "password_hash": hash_pw(pw),
        "created_at": datetime.now(timezone.utc),
    }
    res = db["users"].insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc, None

def do_login(email, pw):
    email = email.strip().lower()
    user = db["users"].find_one({"email": email})
    if not user:
        return None, "No account found with that email."
    if not check_pw(pw, user["password_hash"]):
        return None, "Incorrect password."
    return user, None

# ── Blog DB helpers ───────────────────────────────────────────────────────────
def save_blog(user_id: str, entry: dict):
    doc = {**entry, "user_id": user_id, "saved_at": datetime.now(timezone.utc)}
    db["blogs"].insert_one(doc)

def load_blogs(user_id: str) -> list:
    out = []
    for b in db["blogs"].find({"user_id": user_id}).sort("saved_at", -1).limit(50):
        b["_id"] = str(b["_id"])
        out.append(b)
    return out

def delete_blog(blog_id: str):
    db["blogs"].delete_one({"_id": ObjectId(blog_id)})

# ── User settings DB helpers ──────────────────────────────────────────────────
DEFAULT_SETTINGS = {
    "gemini_api_key":    "",
    "tavily_api_key":    "",
    "output_type":       "Study Guide",
    "section_count":     5,
    "words_per_section": 300,
    "depth_level":       "Balanced",
    "tone":              "Educational",
    "extra_instruction": "",
}

def load_settings(user_id: str) -> dict:
    doc = db["user_settings"].find_one({"user_id": user_id})
    if not doc:
        return DEFAULT_SETTINGS.copy()
    return {k: doc.get(k, v) for k, v in DEFAULT_SETTINGS.items()}

def save_settings(user_id: str, cfg: dict):
    db["user_settings"].update_one(
        {"user_id": user_id},
        {"$set": {**cfg, "user_id": user_id, "updated_at": datetime.now(timezone.utc)}},
        upsert=True,
    )

# ── Session defaults ──────────────────────────────────────────────────────────
_defaults = {
    "user":           None,
    "session_token":  None,
    "history":        [],
    "history_loaded": False,
    "viewing_id":     None,
    "current_result": None,
    "settings":       None,
    "settings_open":  False,
    "confirm_delete": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Auto-login from token in query params ─────────────────────────────────────
if st.session_state.user is None:
    token_from_url = st.query_params.get("_token", "")
    if token_from_url:
        auto_user = get_user_from_token(token_from_url)
        if auto_user:
            st.session_state.user = {
                "id": str(auto_user["_id"]),
                "name": auto_user["name"],
                "email": auto_user["email"],
            }
            st.session_state.session_token = token_from_url
            st.session_state.history_loaded = False
            st.session_state.settings = load_settings(str(auto_user["_id"]))

# ══════════════════════════════════════════════════════════════════════════════
# AUTH WALL
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.user is None:
    # JS: read localStorage token and redirect
    st.components.v1.html("""
    <script>
    (function() {
        if (sessionStorage.getItem('ce_redirect_tried')) return;
        sessionStorage.setItem('ce_redirect_tried', '1');
        const token = localStorage.getItem('content_engine_token');
        if (!token) return;
        try {
            const parentParams = new URLSearchParams(window.parent.location.search);
            if (!parentParams.has('_token')) {
                parentParams.set('_token', token);
                window.parent.location.replace(
                    window.parent.location.pathname + '?' + parentParams.toString()
                );
            }
        } catch(e) { console.warn('CE: could not access parent location', e); }
    })();
    </script>
    """, height=0)

    # Theme toggle — top right
    _, col_theme = st.columns([5, 1])
    with col_theme:
        if st.button(f"{mode_icon} {mode_label}", key="auth_theme"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

    # ── Auth card markup ──────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="auth-card">
        <div class="auth-badge">
            <span class="dot"></span>
            Study &amp; Content Engine
        </div>
        <h1 class="auth-headline">Learn deeper.<br><em>Study smarter.</em></h1>
        <p class="auth-sub">
            Generate detailed study guides, deep-dive research, and structured content 
            — from any subject, instantly.
        </p>
        <div class="auth-divider"></div>
    </div>
    """, unsafe_allow_html=True)

    # Streamlit inputs rendered inside the card visually via CSS proximity
    tab_in, tab_up = st.tabs(["✦  Sign In", "Create Account"])

    with tab_in:
        li_email = st.text_input("Email address", key="li_email", placeholder="you@example.com")
        li_pw    = st.text_input("Password", key="li_pw", type="password", placeholder="Your password")
        if st.button("Sign In →", key="do_login_btn", use_container_width=True):
            if not li_email or not li_pw:
                st.error("Please fill in both fields.")
            else:
                u, err = do_login(li_email, li_pw)
                if err:
                    st.error(err)
                else:
                    token = create_session(str(u["_id"]))
                    st.session_state.user = {"id": str(u["_id"]), "name": u["name"], "email": u["email"]}
                    st.session_state.session_token = token
                    st.session_state.history_loaded = False
                    st.session_state.settings = load_settings(str(u["_id"]))
                    st.query_params["_token"] = token
                    st.components.v1.html(f"""
                    <script>localStorage.setItem('content_engine_token', '{token}');</script>
                    """, height=0)
                    st.rerun()

    with tab_up:
        su_name  = st.text_input("Full Name", key="su_name", placeholder="Jane Doe")
        su_email = st.text_input("Email address", key="su_email", placeholder="you@example.com")
        su_pw    = st.text_input("Password", key="su_pw", type="password", placeholder="Min 8 characters")
        su_pw2   = st.text_input("Confirm Password", key="su_pw2", type="password", placeholder="Repeat password")
        if st.button("Create Account →", key="do_signup_btn", use_container_width=True):
            if not su_name or not su_email or not su_pw:
                st.error("All fields are required.")
            elif len(su_pw) < 8:
                st.error("Password must be at least 8 characters.")
            elif su_pw != su_pw2:
                st.error("Passwords don't match.")
            else:
                u, err = do_signup(su_name, su_email, su_pw)
                if err:
                    st.error(err)
                else:
                    token = create_session(str(u["_id"]))
                    st.session_state.user = {"id": str(u["_id"]), "name": u["name"], "email": u["email"]}
                    st.session_state.session_token = token
                    st.session_state.history_loaded = False
                    st.session_state.settings = load_settings(str(u["_id"]))
                    st.query_params["_token"] = token
                    st.components.v1.html(f"""
                    <script>localStorage.setItem('content_engine_token', '{token}');</script>
                    """, height=0)
                    st.rerun()

    # Feature tags at the bottom
    st.markdown(f"""
    <div class="auth-features">
        <span class="auth-feature-tag">✦ AI-Powered Research</span>
        <span class="auth-feature-tag">📖 Study Guides</span>
        <span class="auth-feature-tag">🔬 Deep Analysis</span>
        <span class="auth-feature-tag">💾 Cloud Saved</span>
        <span class="auth-feature-tag">⚡ Instant Generate</span>
    </div>
    """, unsafe_allow_html=True)

    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# LOGGED IN — refresh token
# ══════════════════════════════════════════════════════════════════════════════
user  = st.session_state.user
token = st.session_state.get("session_token", "")

if token:
    st.query_params["_token"] = token
    st.components.v1.html(f"""
    <script>
    (function() {{
        localStorage.setItem('content_engine_token', '{token}');
        sessionStorage.removeItem('ce_redirect_tried');
    }})();
    </script>
    """, height=0)

if not st.session_state.history_loaded:
    st.session_state.history = load_blogs(user["id"])
    st.session_state.history_loaded = True

history = st.session_state.history

# Sidebar knob: simple, robust implementation.
# Shows a hamburger button when sidebar is collapsed. Polls every 300ms — lightweight.
def _build_sidebar_js(accent_color, accent2_color):
    return (
        "<script>(function(){"
        "var p=window.parent,pd=p.document;"
        "var KNOB='ce-sidebar-knob';"

        # ---- create knob once ----
        "if(!pd.getElementById(KNOB)){"
        "var b=pd.createElement('button');"
        "b.id=KNOB;"
        "b.innerHTML='&#9776;';"
        "b.title='Open sidebar';"
        "b.style.cssText='"
        "position:fixed;top:50%;left:0;transform:translateY(-50%);"
        "z-index:2147483647;"
        "background:linear-gradient(135deg," + accent_color + "," + accent2_color + ");"
        "color:#fff;border:none;border-radius:0 10px 10px 0;"
        "width:26px;height:60px;cursor:pointer;"
        "display:none;align-items:center;justify-content:center;"
        "font-size:1rem;padding:0;line-height:1;"
        "box-shadow:3px 0 16px rgba(124,92,252,.45);"
        "transition:width .15s;"
        "';"
        "b.onmouseenter=function(){b.style.width='34px';};"
        "b.onmouseleave=function(){b.style.width='26px';};"
        "pd.body.appendChild(b);}"

        # ---- always update gradient (theme may have changed) ----
        "var knob=pd.getElementById(KNOB);"
        "knob.style.background='linear-gradient(135deg," + accent_color + "," + accent2_color + ")';"

        # ---- click: find & click Streamlit's own toggle ----
        "knob.onclick=function(){"
        "var found=false;"
        "var tries=["
        "'button[data-testid=\"collapsedControl\"]',"
        "'[data-testid=\"stSidebarCollapsedControl\"] button',"
        "'button[aria-label=\"open sidebar\"]',"
        "'button[aria-label=\"Open sidebar\"]',"
        "'button[aria-label=\"close sidebar\"]',"
        "'button[aria-label=\"Close sidebar\"]'"
        "];"
        "for(var i=0;i<tries.length;i++){"
        "var el=pd.querySelector(tries[i]);"
        "if(el){el.click();found=true;break;}}"
        # fallback: find button adjacent to sidebar in DOM
        "if(!found){"
        "var sb=pd.querySelector('[data-testid=\"stSidebar\"]');"
        "if(sb&&sb.nextElementSibling){"
        "var fbtn=sb.nextElementSibling.querySelector('button');"
        "if(fbtn)fbtn.click();}}"
        "};"

        # ---- poll every 300ms to show/hide knob ----
        # clear old interval stored on window.parent
        "if(p.__ce_iv__)clearInterval(p.__ce_iv__);"
        "p.__ce_iv__=setInterval(function(){"
        "var sb=pd.querySelector('[data-testid=\"stSidebar\"]');"
        "if(!sb)return;"
        "var w=sb.getBoundingClientRect().width;"
        "knob.style.display=w<50?'flex':'none';"
        "},300);"

        # ---- run once immediately ----
        "(function(){"
        "var sb=pd.querySelector('[data-testid=\"stSidebar\"]');"
        "if(!sb)return;"
        "knob.style.display=sb.getBoundingClientRect().width<50?'flex':'none';"
        "})();"

        "})();</script>"
    )

st.components.v1.html(_build_sidebar_js(accent, accent2), height=0)
if st.session_state.settings is None:
    st.session_state.settings = load_settings(user["id"])

cfg = st.session_state.settings

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    initials = "".join(w[0].upper() for w in user["name"].split()[:2])
    st.markdown(
        f'<div class="user-chip">'
        f'<div class="user-avatar">{initials}</div>'
        f'<div><div class="user-name">{user["name"]}</div>'
        f'<div class="user-email">{user["email"]}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    col_theme, col_out = st.columns(2)
    with col_theme:
        if st.button(f"{mode_icon} {mode_label}", key="theme_toggle", use_container_width=True):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    with col_out:
        if st.button("⎋ Sign Out", key="signout_btn", use_container_width=True):
            delete_session(st.session_state.get("session_token", ""))
            st.components.v1.html("<script>localStorage.removeItem('content_engine_token');</script>", height=0)
            st.query_params.clear()
            for k in _defaults:
                st.session_state[k] = _defaults[k]
            st.rerun()

    st.markdown("---")

    # ── Settings ──────────────────────────────────────────────────────────────
    st.markdown(
        f'<div class="settings-label">⚙ Settings</div>',
        unsafe_allow_html=True,
    )

    with st.expander("🔑 API Keys", expanded=st.session_state.settings_open):
        st.markdown(
            f'<div style="font-family:\'DM Mono\',monospace;font-size:0.62rem;'
            f'color:{accent_light};letter-spacing:0.07em;margin-bottom:0.2rem;">GEMINI API KEY</div>'
            f'<div style="font-size:0.72rem;color:{text_muted};margin-bottom:0.4rem;">'
            f'Overrides server default · <a href="https://aistudio.google.com/app/apikey" target="_blank" '
            f'style="color:{accent};text-decoration:none;">Get key ↗</a></div>',
            unsafe_allow_html=True,
        )
        new_key = st.text_input(
            "Gemini API Key",
            value=cfg["gemini_api_key"],
            type="password",
            placeholder="AIzaSy...",
            key="s_api_key",
            label_visibility="collapsed",
        )
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-family:\'DM Mono\',monospace;font-size:0.62rem;'
            f'color:{accent_light};letter-spacing:0.07em;margin-bottom:0.2rem;">TAVILY API KEY</div>'
            f'<div style="font-size:0.72rem;color:{text_muted};margin-bottom:0.4rem;">'
            f'For web research · Free 1,000/mo · <a href="https://app.tavily.com/home" target="_blank" '
            f'style="color:{accent};text-decoration:none;">Get key ↗</a></div>',
            unsafe_allow_html=True,
        )
        new_tavily_key = st.text_input(
            "Tavily API Key",
            value=cfg.get("tavily_api_key", ""),
            type="password",
            placeholder="tvly-...",
            key="s_tavily_key",
            label_visibility="collapsed",
        )
        st.markdown(
            f'<div style="font-size:0.68rem;color:{text_muted};margin-top:0.4rem;">'
            f'🔒 Keys stored securely in your account</div>',
            unsafe_allow_html=True,
        )

    with st.expander("📄 Output Type", expanded=False):
        new_output_type = st.radio(
            "Output Type",
            options=["Study Guide", "Blog Post", "Deep Research", "Quick Summary"],
            index=["Study Guide", "Blog Post", "Deep Research", "Quick Summary"].index(cfg["output_type"]),
            key="s_output_type",
            label_visibility="collapsed",
        )
        desc_map = {
            "Study Guide":   "📖 Structured for learning — definitions, examples, key concepts",
            "Blog Post":     "✍️ Engaging narrative with introduction and conclusion",
            "Deep Research": "🔬 Exhaustive analysis with citations and multiple perspectives",
            "Quick Summary": "⚡ Concise overview, key takeaways only",
        }
        st.markdown(
            f'<div style="font-size:0.72rem;color:{text_muted};margin-top:0.3rem;line-height:1.5;">'
            f'{desc_map.get(new_output_type, "")}</div>',
            unsafe_allow_html=True,
        )

    with st.expander("📏 Length & Depth", expanded=False):
        new_section_count = st.slider(
            "Number of Sections",
            min_value=3, max_value=10,
            value=int(cfg.get("section_count", 5)),
            step=1, key="s_section_count",
        )
        st.markdown(
            f'<div style="font-family:\'DM Mono\',monospace;font-size:0.62rem;color:{text_muted};margin-bottom:0.6rem;">'
            f'📑 {new_section_count} sections</div>',
            unsafe_allow_html=True,
        )
        new_words_per_section = st.slider(
            "Words per Section",
            min_value=100, max_value=1000,
            value=int(cfg.get("words_per_section", 300)),
            step=50, key="s_words_per_section",
        )
        total_words = new_section_count * new_words_per_section
        st.markdown(
            f'<div style="font-family:\'DM Mono\',monospace;font-size:0.62rem;color:{text_muted};margin-bottom:0.6rem;">'
            f'📝 {new_words_per_section}w/section · ~{total_words:,} total · ≈{total_words // 200} min read</div>',
            unsafe_allow_html=True,
        )
        new_depth = st.select_slider(
            "Research Depth",
            options=["Quick", "Balanced", "Deep", "Exhaustive"],
            value=cfg.get("depth_level", "Balanced"),
            key="s_depth",
        )
        depth_desc = {
            "Quick":      "⚡ Fast — uses model knowledge only",
            "Balanced":   "⚖️ Model knowledge + targeted web research",
            "Deep":       "🔬 Full research pipeline with multiple sources",
            "Exhaustive": "🌐 Maximum sources, multi-angle analysis",
        }
        st.markdown(
            f'<div style="font-size:0.72rem;color:{text_muted};">{depth_desc[new_depth]}</div>',
            unsafe_allow_html=True,
        )

    with st.expander("🎨 Tone & Style", expanded=False):
        new_tone = st.radio(
            "Tone",
            options=["Educational", "Academic", "Casual", "Professional", "Socratic"],
            index=["Educational", "Academic", "Casual", "Professional", "Socratic"].index(cfg["tone"]),
            key="s_tone",
            label_visibility="collapsed",
        )
        tone_desc = {
            "Educational":  "📚 Clear explanations, examples, student-friendly",
            "Academic":     "🎓 Formal, citations, technical terminology",
            "Casual":       "😊 Conversational, relatable, plain language",
            "Professional": "💼 Precise, structured, business-ready",
            "Socratic":     "❓ Question-driven, encourages critical thinking",
        }
        st.markdown(
            f'<div style="font-size:0.72rem;color:{text_muted};">{tone_desc[new_tone]}</div>',
            unsafe_allow_html=True,
        )

    with st.expander("💬 Custom Instructions", expanded=False):
        new_extra = st.text_area(
            "Extra Instructions",
            value=cfg["extra_instruction"],
            placeholder=(
                "e.g. 'Always include a worked example at the end'\n"
                "'Focus on Indian curriculum standards'\n"
                "'Add a glossary section for technical terms'"
            ),
            height=100,
            key="s_extra",
            label_visibility="collapsed",
        )
        st.markdown(
            f'<div style="font-size:0.68rem;color:{text_muted};">'
            f'Injected directly into the AI system prompt.</div>',
            unsafe_allow_html=True,
        )

    if st.button("💾  Save Settings", key="save_settings_btn", use_container_width=True):
        updated = {
            "gemini_api_key":    new_key.strip(),
            "tavily_api_key":    new_tavily_key.strip(),
            "output_type":       new_output_type,
            "section_count":     new_section_count,
            "words_per_section": new_words_per_section,
            "depth_level":       new_depth,
            "tone":              new_tone,
            "extra_instruction": new_extra.strip(),
        }
        save_settings(user["id"], updated)
        st.session_state.settings = updated
        cfg = updated
        st.success("✓ Settings saved!")

    st.markdown("---")

    # ── History ───────────────────────────────────────────────────────────────
    st.markdown(
        f'<div class="hist-section-label">Study History ({len(history)})</div>',
        unsafe_allow_html=True,
    )

    if not history:
        st.markdown(
            f'<div style="font-family:\'DM Mono\',monospace;font-size:0.72rem;'
            f'color:{text_muted};padding:0.4rem 0.1rem;">No guides yet — generate your first!</div>',
            unsafe_allow_html=True,
        )
    else:
        for entry in history:
            title   = entry.get("blog_title", "Untitled")
            ts      = entry.get("created_at", "")
            bid     = entry["_id"]
            otype   = entry.get("output_type", "")
            nsec    = entry.get("section_count", "")
            wps     = entry.get("words_per_section", "")
            size_info = f"{nsec}×{wps}w" if nsec and wps else ""
            is_active = st.session_state.viewing_id == bid

            card_cls = "hist-card active" if is_active else "hist-card"
            st.markdown(f'<div class="{card_cls}">', unsafe_allow_html=True)

            confirming = st.session_state.confirm_delete == bid

            if not confirming:
                col_b, col_d = st.columns([7, 1])
                with col_b:
                    if st.button(
                        f"{'▶ ' if is_active else ''}{title[:26]}{'…' if len(title) > 26 else ''}",
                        key=f"v_{bid}", use_container_width=True,
                    ):
                        st.session_state.viewing_id = bid
                        st.session_state.current_result = None
                        st.rerun()
                with col_d:
                    if st.button("🗑", key=f"d_{bid}", help="Delete"):
                        st.session_state.confirm_delete = bid
                        st.rerun()
            else:
                st.markdown(
                    f'<div style="font-size:0.72rem;color:#f08080;margin-bottom:0.4rem;font-weight:500;">'
                    f'Delete this entry?</div>',
                    unsafe_allow_html=True,
                )
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✓ Yes", key=f"yes_{bid}", use_container_width=True):
                        delete_blog(bid)
                        st.session_state.history = [h for h in history if h["_id"] != bid]
                        st.session_state.confirm_delete = None
                        if st.session_state.viewing_id == bid:
                            st.session_state.viewing_id = None
                        st.rerun()
                with col_no:
                    if st.button("✗ No", key=f"no_{bid}", use_container_width=True):
                        st.session_state.confirm_delete = None
                        st.rerun()

            # Type pill colors
            type_color = {
                "Study Guide":   ("#1a1035", "#b89cfa") if dark else ("#ede8ff", "#6240e8"),
                "Blog Post":     ("#0d1f12", "#60d890") if dark else ("#e6fff0", "#28a85a"),
                "Deep Research": ("#1a1210", "#f0a060") if dark else ("#fff3e6", "#c07020"),
                "Quick Summary": ("#0d1828", "#60c8f8") if dark else ("#e6f4ff", "#0878c8"),
            }.get(otype, ("#1a1a2e", "#9a96c0") if dark else ("#f0eeff", "#6240e8"))

            pill_html = f'<span style="background:{type_color[0]};color:{type_color[1]};font-family:\'DM Mono\',monospace;font-size:0.55rem;padding:0.12rem 0.5rem;border-radius:100px;font-weight:500;">{otype}</span>' if otype else ""
            size_html = f'<span style="color:{text_muted};font-size:0.58rem;font-family:\'DM Mono\',monospace;">{size_info}</span>' if size_info else ""

            st.markdown(
                f'<div style="font-family:\'DM Mono\',monospace;font-size:0.58rem;color:{text_muted};'
                f'margin-top:0.2rem;display:flex;align-items:center;gap:0.4rem;flex-wrap:wrap;">'
                f'{ts} {pill_html} {size_html}</div>',
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
    <div class="hero-eyebrow">✦ Study &amp; Content Engine</div>
    <h1 class="hero-title">Learn deeper.<br><em>Study smarter.</em></h1>
    <p class="hero-sub">Generate detailed study guides, topic deep-dives &amp; structured content — from any subject, instantly.</p>
</div>
""", unsafe_allow_html=True)

# ── Blog renderer ─────────────────────────────────────────────────────────────
def render_blog(entry: dict, label: str = ""):
    title       = entry.get("blog_title", "Untitled")
    mode        = entry.get("mode", "").replace("_", " ")
    output_type = entry.get("output_type", "")
    ts          = entry.get("created_at", "")
    md          = entry.get("markdown", "")
    fn          = entry.get("filename", "blog.md")
    depth       = entry.get("depth_level", "")
    nsec        = entry.get("section_count", "")
    wps         = entry.get("words_per_section", "")
    size_str    = f"{nsec}×{wps}w" if nsec and wps else ""
    tone        = entry.get("tone", "")
    meta_parts  = [p for p in [ts, output_type or mode, size_str, depth, tone, label] if p]
    meta        = " · ".join(meta_parts)

    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(
            f'<div class="output-header">'
            f'<span class="output-title">{title}</span>'
            f'<span class="output-meta">{meta}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.download_button(
            "↓ Download", data=md, file_name=fn,
            mime="text/markdown", use_container_width=True,
        )
    st.markdown('<div class="markdown-container">', unsafe_allow_html=True)
    st.markdown(md)
    st.markdown('</div>', unsafe_allow_html=True)

# ── Routing ───────────────────────────────────────────────────────────────────
viewing_history = (
    st.session_state.viewing_id is not None
    and st.session_state.current_result is None
)

if viewing_history:
    entry = next((h for h in history if h["_id"] == st.session_state.viewing_id), None)
    if entry:
        render_blog(entry, label="from history")
    else:
        st.warning("Blog not found — it may have been deleted.")
    st.markdown("---")
    if st.button("← Back to Generator"):
        st.session_state.viewing_id = None
        st.rerun()

elif st.session_state.current_result:
    render_blog(st.session_state.current_result, label="just generated")
    st.markdown("---")
    if st.button("← Generate another"):
        st.session_state.current_result = None
        st.rerun()

else:
    # ── Generator view ────────────────────────────────────────────────────────
    topic = st.text_area(
        "TOPIC / SUBJECT",
        placeholder=(
            '"Explain Quantum Entanglement for a physics exam"\n'
            '"Deep dive: French Revolution causes and consequences"\n'
            '"Study guide: Machine Learning fundamentals with examples"'
        ),
        height=120,
    )

    col_btn, col_hint = st.columns([2, 5])
    with col_btn:
        btn_labels = {
            "Study Guide":   "✦ Generate Study Guide",
            "Blog Post":     "✦ Generate Blog Post",
            "Deep Research": "✦ Deep Research",
            "Quick Summary": "✦ Quick Summary",
        }
        generate = st.button(
            btn_labels.get(cfg.get("output_type", "Study Guide"), "✦ Generate"),
            use_container_width=True,
        )
    with col_hint:
        st.markdown(
            f'<div style="font-family:\'DM Mono\',monospace;font-size:0.65rem;color:{text_muted};padding-top:0.9rem;">'
            f'Research → Outline → Deep content → Structured Markdown</div>',
            unsafe_allow_html=True,
        )

    if generate:
        if not topic.strip():
            st.warning("Please enter a topic before generating.")
        else:
            active_key = cfg.get("gemini_api_key", "").strip() or os.getenv("GOOGLE_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
            if not active_key:
                st.error("⚠️ No Google API key found. Add your Gemini key in ⚙️ Settings → 🔑 API Keys (sidebar).")
                st.stop()

            os.environ["GOOGLE_API_KEY"]        = active_key
            os.environ["GEMINI_API_KEY"]        = active_key
            tavily_key = cfg.get("tavily_api_key", "").strip() or os.getenv("TAVILY_API_KEY", "")
            if tavily_key:
                os.environ["TAVILY_API_KEY"]    = tavily_key
            os.environ["ACE_OUTPUT_TYPE"]       = cfg.get("output_type", "Study Guide")
            os.environ["ACE_SECTION_COUNT"]     = str(cfg.get("section_count", 5))
            os.environ["ACE_WORDS_PER_SECTION"] = str(cfg.get("words_per_section", 300))
            os.environ["ACE_DEPTH_LEVEL"]       = cfg.get("depth_level", "Balanced")
            os.environ["ACE_TONE"]              = cfg.get("tone", "Educational")
            os.environ["ACE_EXTRA_INSTRUCTION"] = cfg.get("extra_instruction", "")

            try:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                if "ACE_backend" in sys.modules:
                    del sys.modules["ACE_backend"]
                from ACE_backend import app as engine_app  # type: ignore
            except ImportError:
                st.error("**ACE_backend.py not found.** Place it in the same folder as app.py.")
                st.stop()

            otype   = cfg.get("output_type", "Study Guide")
            nsec    = cfg.get("section_count", 5)
            wps     = cfg.get("words_per_section", 300)
            depth   = cfg.get("depth_level", "Balanced")
            tone    = cfg.get("tone", "Educational")
            total_w = nsec * wps

            st.markdown(
                f'<div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:1.2rem;">'
                f'<span class="badge badge-done" style="margin:0;">📄 {otype}</span>'
                f'<span class="badge badge-done" style="margin:0;">📑 {nsec} sections</span>'
                f'<span class="badge badge-done" style="margin:0;">📝 {wps}w/section</span>'
                f'<span class="badge badge-running" style="margin:0;">🔬 {depth}</span>'
                f'<span class="badge badge-skipped" style="margin:0;">🎨 {tone}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.markdown("### Pipeline")
            stages = [
                ("router",       "🔀", "Router",    "Deciding research strategy…"),
                ("research",     "🔍", "Research",  "Fetching live evidence…"),
                ("orchestrator", "📐", "Planner",   "Creating structured outline…"),
                ("worker",       "✍️",  "Writer",    "Generating sections in parallel…"),
                ("reducer",      "🗜️", "Assembler", "Merging & saving Markdown…"),
            ]
            phs = {}
            for key, icon, label, desc in stages:
                ph = st.empty()
                phs[key] = ph
                ph.markdown(
                    f'<div class="pipeline-card"><span class="pipeline-icon">{icon}</span>'
                    f'<div><div class="pipeline-label">{label}</div>'
                    f'<div class="pipeline-value">{desc}</div></div>'
                    f'<span class="badge badge-pending">pending</span></div>',
                    unsafe_allow_html=True,
                )

            def upd(key, icon, label, desc, status):
                cc = "active" if status == "running" else ("done" if status == "done" else "")
                phs[key].markdown(
                    f'<div class="pipeline-card {cc}"><span class="pipeline-icon">{icon}</span>'
                    f'<div><div class="pipeline-label">{label}</div>'
                    f'<div class="pipeline-value">{desc}</div></div>'
                    f'<span class="badge badge-{status}">{status}</span></div>',
                    unsafe_allow_html=True,
                )

            result_md = None
            plan_obj  = None
            mode_used = "closed_book"

            with st.spinner(""):
                try:
                    upd("router", "🔀", "Router", "Routing topic…", "running")
                    for event in engine_app.stream({"topic": topic.strip()}, stream_mode="updates"):
                        if "router" in event:
                            r = event["router"]
                            mode_used = r.get("mode", "closed_book")
                            needs_res = r.get("needs_research", False)
                            upd("router", "🔀", "Router", f"Mode: {mode_used.replace('_',' ')}", "done")
                            if needs_res:
                                upd("research", "🔍", "Research", "Fetching live evidence…", "running")
                            else:
                                upd("research", "🔍", "Research", "Skipped (closed-book)", "skipped")
                        if "research" in event:
                            ev = event["research"].get("evidence", [])
                            upd("research", "🔍", "Research", f"Retrieved {len(ev)} evidence items", "done")
                            upd("orchestrator", "📐", "Planner", "Creating outline…", "running")
                        if "orchestrator" in event:
                            plan_obj = event["orchestrator"].get("plan")
                            n = len(plan_obj.tasks) if plan_obj else "?"
                            upd("orchestrator", "📐", "Planner", f"Plan ready · {n} sections", "done")
                            upd("worker", "✍️", "Writer", f"Writing {n} sections in parallel…", "running")
                        if "reducer" in event:
                            upd("worker",  "✍️",  "Writer",    "All sections written", "done")
                            upd("reducer", "🗜️", "Assembler", "Merging Markdown…", "running")
                            result_md = event["reducer"].get("final")
                            upd("reducer", "🗜️", "Assembler", "Blog assembled ✓", "done")
                except Exception as e:
                    st.error(f"Pipeline error: {e}")
                    st.stop()

            if result_md and plan_obj:
                blog_title = plan_obj.blog_title
                filename = (
                    "".join(c if c.isalnum() or c in (" ", "_", "-") else "" for c in blog_title)
                    .strip().lower().replace(" ", "_") + ".md"
                )
                entry = {
                    "blog_title":        blog_title,
                    "markdown":          result_md,
                    "filename":          filename,
                    "mode":              mode_used,
                    "output_type":       cfg.get("output_type", "Study Guide"),
                    "section_count":     cfg.get("section_count", 5),
                    "words_per_section": cfg.get("words_per_section", 300),
                    "depth_level":       cfg.get("depth_level", "Balanced"),
                    "tone":              cfg.get("tone", "Educational"),
                    "topic":             topic.strip(),
                    "created_at":        datetime.now().strftime("%b %d %Y, %H:%M"),
                }
                save_blog(user["id"], entry)
                refreshed = load_blogs(user["id"])
                st.session_state.history = refreshed
                st.session_state.current_result = refreshed[0]
                st.rerun()
            else:
                st.error("No output produced. Check your API keys and backend.")