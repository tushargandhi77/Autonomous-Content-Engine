"""
Autonomous Content Engine — Streamlit App
Fixes:
  1. Persistent login via session token stored in MongoDB + browser localStorage (JS injection)
  2. Sidebar always accessible via custom toggle button
  3. Light / Dark mode toggle with enhanced UI

Requires:
  pip install streamlit pymongo bcrypt python-dotenv
  ACE_backend.py in the same folder
  .streamlit/secrets.toml  →  MONGO_URI = "mongodb+srv://..."
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

# ── CSS ───────────────────────────────────────────────────────────────────────
if dark:
    bg_main      = "#0a0a0f"
    bg_card      = "#13131e"
    bg_sidebar   = "#0e0e16"
    text_primary = "#f0ece4"
    text_sec     = "#9a96a0"
    text_muted   = "#5a5660"
    border_col   = "rgba(255,255,255,0.07)"
    border_input = "rgba(255,255,255,0.1)"
    input_bg     = "#13131e"
    input_text   = "#e8e4dc"
    accent       = "#7c5cfc"
    accent_light = "#b89cfa"
    accent_soft  = "rgba(124,92,252,0.12)"
    hero_sub     = "#7a7870"
    hist_label   = "#3a3640"
    radial1      = "radial-gradient(ellipse 80% 40% at 50% -10%, rgba(120,80,255,0.12) 0%, transparent 70%)"
    radial2      = "radial-gradient(ellipse 40% 30% at 90% 80%, rgba(255,120,60,0.06) 0%, transparent 60%)"
    md_p         = "#b8b4ac"
    md_h2        = "#d4d0cc"
    md_code_bg   = "rgba(124,92,252,0.15)"
    md_code_c    = "#c8b4f8"
    md_pre_bg    = "#0a0a12"
    alert_bg     = "rgba(124,92,252,0.08)"
    alert_border = "rgba(124,92,252,0.2)"
    alert_text   = "#c8b4f8"
    mode_icon    = "☀️"
    mode_label   = "Light Mode"
    chip_bg      = "rgba(124,92,252,0.08)"
    chip_border  = "rgba(124,92,252,0.18)"
    pipeline_run = "#7c5cfc"
    pipeline_done= "rgba(80,220,130,0.4)"
else:
    bg_main      = "#f4f2ee"
    bg_card      = "#ffffff"
    bg_sidebar   = "#eeecea"
    text_primary = "#1a1520"
    text_sec     = "#5a5560"
    text_muted   = "#9a96a8"
    border_col   = "rgba(0,0,0,0.08)"
    border_input = "rgba(0,0,0,0.14)"
    input_bg     = "#ffffff"
    input_text   = "#1a1520"
    accent       = "#6240e8"
    accent_light = "#8a6cf0"
    accent_soft  = "rgba(98,64,232,0.08)"
    hero_sub     = "#7a7680"
    hist_label   = "#b0aab8"
    radial1      = "radial-gradient(ellipse 80% 40% at 50% -10%, rgba(120,80,255,0.06) 0%, transparent 70%)"
    radial2      = "radial-gradient(ellipse 40% 30% at 90% 80%, rgba(255,120,60,0.04) 0%, transparent 60%)"
    md_p         = "#4a4660"
    md_h2        = "#2a2438"
    md_code_bg   = "rgba(98,64,232,0.08)"
    md_code_c    = "#5a3cc8"
    md_pre_bg    = "#f0eef8"
    alert_bg     = "rgba(98,64,232,0.06)"
    alert_border = "rgba(98,64,232,0.18)"
    alert_text   = "#5a3cc8"
    mode_icon    = "🌙"
    mode_label   = "Dark Mode"
    chip_bg      = "rgba(98,64,232,0.06)"
    chip_border  = "rgba(98,64,232,0.16)"
    pipeline_run = "#6240e8"
    pipeline_done= "rgba(40,180,90,0.4)"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Mono:wght@300;400;500&family=Cabinet+Grotesk:wght@400;500;700;800&display=swap');

*, *::before, *::after {{ box-sizing: border-box; }}

html, body, [data-testid="stAppViewContainer"] {{
    background: {bg_main};
    color: {text_primary};
    font-family: 'Cabinet Grotesk', sans-serif;
    transition: background 0.3s ease, color 0.3s ease;
}}
[data-testid="stAppViewContainer"] {{
    background: {bg_main};
    background-image: {radial1}, {radial2};
}}
[data-testid="stSidebar"] {{
    background: {bg_sidebar} !important;
    border-right: 1px solid {border_col} !important;
    transition: background 0.3s ease;
}}
[data-testid="stSidebar"] > div {{ padding: 1.5rem 1rem; }}
#MainMenu, footer, header {{ display: none !important; }}
.block-container {{ padding: 2rem 2.5rem 4rem; max-width: 1100px; }}
h1, h2, h3 {{ font-family: 'Instrument Serif', serif; letter-spacing: -0.02em; }}

/* ── Auth card ── */
.auth-wrap {{
    max-width: 460px;
    margin: 6vh auto 0;
    background: {bg_card};
    border: 1px solid {border_col};
    border-radius: 20px;
    padding: 2.8rem 2.8rem 2.2rem;
    box-shadow: 0 24px 80px rgba(0,0,0,{0.25 if dark else 0.08});
    transition: background 0.3s ease;
}}
.auth-logo {{
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: {accent};
    margin-bottom: 1rem;
}}
.auth-title {{
    font-family: 'Instrument Serif', serif;
    font-size: 2.4rem;
    color: {text_primary};
    margin: 0 0 0.3rem;
    line-height: 1.1;
}}
.auth-title em {{ font-style: italic; color: {accent_light}; }}
.auth-sub {{ font-size: 0.88rem; color: {text_muted}; margin-bottom: 2rem; }}

/* ── Hero ── */
.hero {{
    padding: 3rem 0 2rem;
    border-bottom: 1px solid {border_col};
    margin-bottom: 2.5rem;
}}
.hero-eyebrow {{
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: {accent};
    margin-bottom: 0.75rem;
}}
.hero-title {{
    font-family: 'Instrument Serif', serif;
    font-size: clamp(2.4rem,5vw,3.8rem);
    font-weight: 400;
    line-height: 1.1;
    color: {text_primary};
    margin: 0 0 0.5rem;
}}
.hero-title em {{ font-style: italic; color: {accent_light}; }}
.hero-sub {{ font-size: 0.95rem; color: {hero_sub}; }}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea {{
    background: {input_bg} !important;
    border: 1px solid {border_input} !important;
    border-radius: 10px !important;
    color: {input_text} !important;
    font-family: 'Cabinet Grotesk', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.2s !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
    border-color: {accent} !important;
    box-shadow: 0 0 0 3px {accent_soft} !important;
    outline: none !important;
}}
.stTextInput label, .stTextArea label {{
    color: {text_sec} !important;
    font-size: 0.75rem !important;
    font-family: 'DM Mono', monospace !important;
    letter-spacing: 0.08em !important;
}}

/* ── Buttons ── */
.stButton > button {{
    background: linear-gradient(135deg, {accent} 0%, {accent_light} 100%) !important;
    border: none !important;
    border-radius: 8px !important;
    color: #fff !important;
    font-family: 'Cabinet Grotesk', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 1.8rem !important;
    cursor: pointer !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 20px {accent_soft} !important;
}}
.stButton > button:hover {{
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 28px rgba(124,92,252,0.45) !important;
}}
/* Ghost buttons (logout, back, delete) */
.stButton > button[kind="secondary"] {{
    background: transparent !important;
    border: 1px solid {border_col} !important;
    color: {text_sec} !important;
    box-shadow: none !important;
}}

.stDownloadButton > button {{
    background: transparent !important;
    border: 1px solid rgba(124,92,252,0.5) !important;
    border-radius: 8px !important;
    color: {accent_light} !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.78rem !important;
    padding: 0.5rem 1.2rem !important;
    letter-spacing: 0.04em !important;
    transition: all 0.2s !important;
}}
.stDownloadButton > button:hover {{
    background: {accent_soft} !important;
    border-color: {accent} !important;
}}

/* ── Pipeline cards ── */
.pipeline-card {{
    background: {bg_card};
    border: 1px solid {border_col};
    border-radius: 12px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: border-color 0.3s, background 0.3s;
}}
.pipeline-card.active {{ border-color: {pipeline_run}; }}
.pipeline-card.done   {{ border-color: {pipeline_done}; }}
.pipeline-icon {{ font-size: 1.2rem; flex-shrink: 0; }}
.pipeline-label {{
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: {text_muted};
    letter-spacing: 0.06em;
    text-transform: uppercase;
}}
.pipeline-value {{ font-size: 0.88rem; color: {text_sec}; margin-top: 0.1rem; }}
.badge {{
    margin-left: auto;
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    padding: 0.18rem 0.55rem;
    border-radius: 100px;
    letter-spacing: 0.06em;
}}
.badge-pending {{ background: rgba(128,128,128,0.1); color: {text_muted}; }}
.badge-running {{ background: rgba(124,92,252,0.2); color: {accent_light}; }}
.badge-done    {{ background: rgba(80,220,130,0.15); color: #60d890; }}
.badge-skipped {{ background: rgba(255,180,50,0.1); color: #e0a040; }}

/* ── Markdown output ── */
.output-header {{
    display: flex;
    align-items: baseline;
    gap: 1rem;
    margin-bottom: 1.2rem;
    flex-wrap: wrap;
}}
.output-title  {{ font-family: 'Instrument Serif', serif; font-size: 1.5rem; color: {text_primary}; }}
.output-meta   {{ font-family: 'DM Mono', monospace; font-size: 0.68rem; color: {text_muted}; letter-spacing: 0.08em; }}
.markdown-container {{
    background: {bg_card};
    border: 1px solid {border_col};
    border-radius: 12px;
    padding: 2rem;
    line-height: 1.75;
    transition: background 0.3s ease;
}}
.markdown-container h1 {{ font-size: 1.9rem; color: {text_primary}; margin-bottom: 1.5rem; }}
.markdown-container h2 {{ font-size: 1.25rem; color: {md_h2}; border-bottom: 1px solid {border_col}; padding-bottom: 0.35rem; margin-top: 2rem; }}
.markdown-container p  {{ color: {md_p}; margin-bottom: 1rem; }}
.markdown-container code {{ background: {md_code_bg}; border-radius: 4px; padding: 0.1em 0.4em; font-family: 'DM Mono', monospace; font-size: 0.84em; color: {md_code_c}; }}
.markdown-container pre {{ background: {md_pre_bg}; border: 1px solid {border_col}; border-radius: 8px; padding: 1.2rem; overflow-x: auto; }}
.markdown-container pre code {{ background: transparent; color: {md_code_c}; }}
.markdown-container ul, .markdown-container ol {{ color: {md_p}; padding-left: 1.5rem; }}
.markdown-container li {{ margin-bottom: 0.3rem; }}
.markdown-container a {{ color: {accent}; text-decoration: none; border-bottom: 1px solid {accent_soft}; }}

/* ── Sidebar history ── */
.hist-meta {{
    font-family: 'DM Mono', monospace;
    font-size: 0.62rem;
    color: {hist_label};
    margin: -0.3rem 0 0.7rem 0;
    padding: 0 0.1rem;
}}
.mode-pill {{
    display: inline-block;
    font-family: 'DM Mono', monospace;
    font-size: 0.58rem;
    padding: 0.08rem 0.4rem;
    border-radius: 100px;
}}
.mode-closed_book {{ background: rgba(80,200,255,0.1); color: #60c8f8; }}
.mode-hybrid      {{ background: rgba(255,180,50,0.1);  color: #e0a040; }}
.mode-open_book   {{ background: rgba(80,220,130,0.1);  color: #60d890; }}

/* ── User chip ── */
.user-chip {{
    display: flex;
    align-items: center;
    gap: 0.65rem;
    background: {chip_bg};
    border: 1px solid {chip_border};
    border-radius: 10px;
    padding: 0.65rem 0.9rem;
    margin-bottom: 1rem;
    transition: background 0.3s;
}}
.user-avatar {{
    width: 30px; height: 30px; border-radius: 50%;
    background: linear-gradient(135deg, {accent}, {accent_light});
    display: flex; align-items: center; justify-content: center;
    font-size: 0.72rem; font-weight: 700; color: #fff; flex-shrink: 0;
}}
.user-name  {{ font-size: 0.85rem; color: {text_primary}; font-weight: 600; line-height: 1.2; }}
.user-email {{ font-family: 'DM Mono', monospace; font-size: 0.6rem; color: {text_muted}; }}

/* ── Sidebar toggle button ── */
.sidebar-toggle {{
    position: fixed;
    top: 50%;
    left: 0;
    transform: translateY(-50%);
    z-index: 9999;
    background: {accent};
    color: white;
    border: none;
    border-radius: 0 8px 8px 0;
    width: 22px;
    height: 56px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.65rem;
    transition: all 0.2s;
    box-shadow: 2px 0 12px rgba(124,92,252,0.3);
}}
.sidebar-toggle:hover {{ width: 28px; box-shadow: 4px 0 20px rgba(124,92,252,0.5); }}

/* ── Theme toggle ── */
.theme-btn {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: {chip_bg};
    border: 1px solid {chip_border};
    border-radius: 8px;
    padding: 0.45rem 0.9rem;
    cursor: pointer;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: {text_sec};
    transition: all 0.2s;
    width: 100%;
    margin-bottom: 0.5rem;
}}
.theme-btn:hover {{ border-color: {accent}; color: {accent_light}; }}

hr {{ border-color: {border_col} !important; margin: 1.2rem 0 !important; }}

[data-testid="stAlert"] {{
    background: {alert_bg} !important;
    border: 1px solid {alert_border} !important;
    border-radius: 8px !important;
    color: {alert_text} !important;
}}

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab"] {{
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: {text_muted};
    letter-spacing: 0.06em;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    color: {accent} !important;
}}

/* Spinner */
[data-testid="stSpinner"] > div > div {{
    border-top-color: {accent} !important;
}}
</style>
""", unsafe_allow_html=True)

# ── Persistent login via localStorage (JS injection) ──────────────────────────
# We inject a small JS snippet to:
# 1. On page load: read token from localStorage → send to Streamlit via query_params
# 2. On login: write token to localStorage

def inject_local_storage_reader():
    """On page load, read token from localStorage and put it in URL param if present."""
    st.components.v1.html("""
    <script>
    (function() {
        const token = localStorage.getItem('content_engine_token');
        const params = new URLSearchParams(window.location.search);
        if (token && !params.has('_token')) {
            params.set('_token', token);
            // Replace URL without reload to let Streamlit pick up query_params
            const newUrl = window.location.pathname + '?' + params.toString();
            window.history.replaceState({}, '', newUrl);
            // Trigger a rerun by navigating — but we use postMessage to parent instead
            window.parent.postMessage({type: 'streamlit:setQueryParam', key: '_token', value: token}, '*');
        }
    })();
    </script>
    """, height=0)

def set_local_storage_token(token: str):
    """Write token to localStorage after login."""
    st.components.v1.html(f"""
    <script>
        localStorage.setItem('content_engine_token', '{token}');
    </script>
    """, height=0)

def clear_local_storage_token():
    """Clear token from localStorage on logout."""
    st.components.v1.html("""
    <script>
        localStorage.removeItem('content_engine_token');
    </script>
    """, height=0)

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
    db["sessions"].create_index("expires_at", expireAfterSeconds=0)  # TTL index
    return db

db = get_db()

# ── Auth helpers ──────────────────────────────────────────────────────────────
def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def check_pw(pw: str, hashed: str) -> bool:
    return bcrypt.checkpw(pw.encode(), hashed.encode())

def create_session(user_id: str) -> str:
    """Create a session token in MongoDB with 30-day expiry."""
    token = secrets.token_urlsafe(32)
    db["sessions"].insert_one({
        "token": token,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(days=30),
    })
    return token

def get_user_from_token(token: str):
    """Look up a user from their session token."""
    if not token:
        return None
    session = db["sessions"].find_one({"token": token, "expires_at": {"$gt": datetime.now(timezone.utc)}})
    if not session:
        return None
    user = db["users"].find_one({"_id": ObjectId(session["user_id"])})
    return user

def delete_session(token: str):
    """Invalidate a session token."""
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
    "user":          None,
    "session_token": None,
    "history":       [],
    "history_loaded": False,
    "viewing_id":    None,
    "current_result": None,
    "settings":        None,
    "settings_open":   False,
    "confirm_delete":  None,   # bid of entry pending delete confirmation
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
            # Also load settings immediately so sidebar has them
            st.session_state.settings = load_settings(str(auto_user["_id"]))

# ══════════════════════════════════════════════════════════════════════════════
# AUTH WALL
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.user is None:
    # Inject JS to read localStorage token and redirect parent (not iframe) ONCE using sessionStorage guard
    st.components.v1.html("""
    <script>
    (function() {
        // Only attempt redirect if we haven't already tried this session
        if (sessionStorage.getItem('ce_redirect_tried')) return;
        sessionStorage.setItem('ce_redirect_tried', '1');

        const token = localStorage.getItem('content_engine_token');
        if (!token) return;

        // Check parent URL (the real Streamlit page, not the iframe)
        try {
            const parentParams = new URLSearchParams(window.parent.location.search);
            if (!parentParams.has('_token')) {
                parentParams.set('_token', token);
                window.parent.location.replace(
                    window.parent.location.pathname + '?' + parentParams.toString()
                );
            }
        } catch(e) {
            // Cross-origin fallback — shouldn't happen on same-origin Streamlit
            console.warn('CE: could not access parent location', e);
        }
    })();
    </script>
    """, height=0)

    # Theme toggle on auth page
    auth_col1, auth_col2 = st.columns([4, 1])
    with auth_col2:
        if st.button(f"{mode_icon} {mode_label}", key="auth_theme"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()

    st.markdown('<div class="auth-wrap">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="auth-logo">✦ Study Engine</div>'
        f'<h1 class="auth-title">Study deeper.<br><em>Learn smarter.</em></h1>'
        f'<p class="auth-sub">Sign in to save your study guides and access your full learning history.</p>',
        unsafe_allow_html=True,
    )

    tab_in, tab_up = st.tabs(["Sign In", "Create Account"])

    with tab_in:
        li_email = st.text_input("Email", key="li_email", placeholder="you@example.com")
        li_pw    = st.text_input("Password", key="li_pw", type="password", placeholder="••••••••")
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
                    # Store token in localStorage via JS, also set in URL for immediate use
                    st.query_params["_token"] = token
                    st.components.v1.html(f"""
                    <script>localStorage.setItem('content_engine_token', '{token}');</script>
                    """, height=0)
                    st.rerun()

    with tab_up:
        su_name  = st.text_input("Full Name", key="su_name", placeholder="Jane Doe")
        su_email = st.text_input("Email", key="su_email", placeholder="you@example.com")
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

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# LOGGED IN — keep token in URL and localStorage fresh
# ══════════════════════════════════════════════════════════════════════════════
user = st.session_state.user
token = st.session_state.get("session_token", "")

# Keep token alive in localStorage on every rerun
if token:
    st.query_params["_token"] = token
    st.components.v1.html(f"""
    <script>
    (function() {{
        localStorage.setItem('content_engine_token', '{token}');
        // Clear the redirect-tried flag so logout + re-login works cleanly
        sessionStorage.removeItem('ce_redirect_tried');
    }})();
    </script>
    """, height=0)

# Load history once per session
if not st.session_state.history_loaded:
    st.session_state.history = load_blogs(user["id"])
    st.session_state.history_loaded = True

history = st.session_state.history

# ── Sidebar toggle injection ──────────────────────────────────────────────────
st.components.v1.html(f"""
<script>
(function() {{
    var BTN_ID = 'ce-sidebar-knob';

    function getSidebarWidth() {{
        var sb = window.parent.document.querySelector('[data-testid="stSidebar"]');
        return sb ? sb.getBoundingClientRect().width : 0;
    }}

    function clickStreamlitToggle() {{
        // Streamlit renders the collapse/expand button with these selectors (try all)
        var selectors = [
            'button[data-testid="collapsedControl"]',
            '[data-testid="stSidebarCollapsedControl"] button',
            'button[aria-label="open sidebar"]',
            'button[aria-label="Open sidebar"]',
            'button[aria-label="close sidebar"]',
            'button[aria-label="Close sidebar"]',
            '[data-testid="stSidebar"] ~ div button',
        ];
        for (var i = 0; i < selectors.length; i++) {{
            var el = window.parent.document.querySelector(selectors[i]);
            if (el) {{ el.click(); return; }}
        }}
        // Ultimate fallback: find any button near x=0 in the parent doc
        var allBtns = window.parent.document.querySelectorAll('button');
        allBtns.forEach(function(b) {{
            var r = b.getBoundingClientRect();
            if (r.left < 60 && r.top > 0 && r.width > 0) b.click();
        }});
    }}

    function updateKnob() {{
        var knob = window.parent.document.getElementById(BTN_ID);
        var w = getSidebarWidth();
        var isCollapsed = w < 50;
        if (knob) {{
            knob.style.display = isCollapsed ? 'flex' : 'none';
        }}
    }}

    function createKnob() {{
        if (window.parent.document.getElementById(BTN_ID)) return;

        var btn = window.parent.document.createElement('button');
        btn.id = BTN_ID;
        btn.title = 'Open sidebar';
        btn.innerHTML = '&#9776;'; // hamburger ≡
        btn.style.cssText = [
            'position:fixed',
            'top:50%',
            'left:0',
            'transform:translateY(-50%)',
            'z-index:2147483647',
            'background:{accent}',
            'color:#fff',
            'border:none',
            'border-radius:0 10px 10px 0',
            'width:24px',
            'height:60px',
            'cursor:pointer',
            'display:flex',
            'align-items:center',
            'justify-content:center',
            'font-size:0.85rem',
            'box-shadow:3px 0 16px rgba(124,92,252,0.45)',
            'transition:width 0.15s ease,box-shadow 0.15s ease',
            'padding:0',
            'line-height:1',
        ].join(';');

        btn.onmouseenter = function() {{
            btn.style.width = '32px';
            btn.style.boxShadow = '4px 0 24px rgba(124,92,252,0.65)';
        }};
        btn.onmouseleave = function() {{
            btn.style.width = '24px';
            btn.style.boxShadow = '3px 0 16px rgba(124,92,252,0.45)';
        }};
        btn.onclick = function() {{
            clickStreamlitToggle();
            // Hide knob immediately; it'll reappear if sidebar still collapsed after 400ms
            btn.style.display = 'none';
            setTimeout(updateKnob, 400);
            setTimeout(updateKnob, 900);
        }};

        window.parent.document.body.appendChild(btn);
        updateKnob();
    }}

    // Boot: try a few times to catch after Streamlit finishes rendering
    function boot() {{
        createKnob();
        updateKnob();
    }}
    setTimeout(boot, 600);
    setTimeout(boot, 1500);
    setTimeout(boot, 3000);

    // Watch sidebar width changes via ResizeObserver
    function watchSidebar() {{
        var sb = window.parent.document.querySelector('[data-testid="stSidebar"]');
        if (!sb) {{ setTimeout(watchSidebar, 800); return; }}
        var ro = new ResizeObserver(function() {{ updateKnob(); }});
        ro.observe(sb);
    }}
    setTimeout(watchSidebar, 1000);
}})();
</script>
""", height=0)

# ── Load settings into session if not yet loaded ──────────────────────────────
if st.session_state.settings is None:
    st.session_state.settings = load_settings(user["id"])

cfg = st.session_state.settings   # shorthand

# ── Sidebar ───────────────────────────────────────────────────────────────────
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
        if st.button(f"{mode_icon} {'Light' if dark else 'Dark'}", key="theme_toggle", use_container_width=True):
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

    # ── ⚙️ Settings Panel ─────────────────────────────────────────────────────
    st.markdown(
        f'<div style="font-family:\'DM Mono\',monospace;font-size:0.63rem;'
        f'letter-spacing:0.14em;text-transform:uppercase;color:{hist_label};margin-bottom:0.5rem;">'
        f'⚙ Settings</div>',
        unsafe_allow_html=True,
    )

    with st.expander("🔑 API Keys", expanded=st.session_state.settings_open):
        # ── Gemini ─────────────────────────────────────────────────────────
        st.markdown(
            '<div style="font-family:\'DM Mono\',monospace;font-size:0.63rem;'
            f'color:{accent_light};letter-spacing:0.06em;margin-bottom:0.2rem;">GEMINI API KEY</div>'
            '<div style="font-family:\'DM Mono\',monospace;font-size:0.6rem;'
            f'color:{text_muted};margin-bottom:0.35rem;">'
            'Overrides server default · leave blank to use server key · '
            '<a href="https://aistudio.google.com/app/apikey" target="_blank" '
            f'style="color:{accent};text-decoration:none;border-bottom:1px solid {accent_soft};">'
            'Get key ↗</a></div>',
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

        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

        # ── Tavily ─────────────────────────────────────────────────────────
        st.markdown(
            '<div style="font-family:\'DM Mono\',monospace;font-size:0.63rem;'
            f'color:{accent_light};letter-spacing:0.06em;margin-bottom:0.2rem;">TAVILY API KEY</div>'
            '<div style="font-family:\'DM Mono\',monospace;font-size:0.6rem;'
            f'color:{text_muted};margin-bottom:0.35rem;">'
            'For web research (Balanced / Deep / Exhaustive). Free: 1,000 searches/mo · '
            '<a href="https://app.tavily.com/home" target="_blank" '
            f'style="color:{accent};text-decoration:none;border-bottom:1px solid {accent_soft};">'
            'Get key ↗</a></div>',
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
            '<div style="font-family:\'DM Mono\',monospace;font-size:0.6rem;'
            f'color:{text_muted};margin-top:0.3rem;">'
            '🔒 Both keys stored securely in your account</div>',
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
        st.markdown(
            f'<div style="font-family:\'DM Mono\',monospace;font-size:0.6rem;color:{text_muted};margin-top:0.3rem;">'
            + {
                "Study Guide":    "📖 Structured for learning — definitions, examples, key concepts",
                "Blog Post":      "✍️ Engaging narrative with introduction and conclusion",
                "Deep Research":  "🔬 Exhaustive analysis with citations and multiple perspectives",
                "Quick Summary":  "⚡ Concise overview, key takeaways only",
            }.get(cfg["output_type"], "")
            + '</div>',
            unsafe_allow_html=True,
        )

    with st.expander("📏 Length & Depth", expanded=False):
        # ── Section count ──────────────────────────────────────────────────────
        new_section_count = st.slider(
            "Number of Sections",
            min_value=3, max_value=10,
            value=int(cfg.get("section_count", 5)),
            step=1,
            key="s_section_count",
            help="How many sections the output will have (3–10)"
        )
        st.markdown(
            f'<div style="font-family:\'DM Mono\',monospace;font-size:0.6rem;color:{text_muted};margin-bottom:0.6rem;">'
            f'📑 {new_section_count} sections</div>',
            unsafe_allow_html=True,
        )

        # ── Words per section ──────────────────────────────────────────────────
        new_words_per_section = st.slider(
            "Words per Section",
            min_value=100, max_value=1000,
            value=int(cfg.get("words_per_section", 300)),
            step=50,
            key="s_words_per_section",
            help="Target word count per section (100–1000)"
        )
        total_words = new_section_count * new_words_per_section
        st.markdown(
            f'<div style="font-family:\'DM Mono\',monospace;font-size:0.6rem;color:{text_muted};margin-bottom:0.6rem;">'
            f'📝 {new_words_per_section}w/section · ~{total_words:,} total · ≈{total_words // 200} min read</div>',
            unsafe_allow_html=True,
        )

        # ── Research depth ─────────────────────────────────────────────────────
        new_depth = st.select_slider(
            "Research Depth",
            options=["Quick", "Balanced", "Deep", "Exhaustive"],
            value=cfg.get("depth_level", "Balanced"),
            key="s_depth",
        )
        depth_desc = {
            "Quick":     "⚡ Fast — uses model knowledge only, no web research",
            "Balanced":  "⚖️ Mix of model knowledge + targeted web research",
            "Deep":      "🔬 Full research pipeline with multiple sources",
            "Exhaustive":"🌐 Maximum sources, multi-angle analysis, longest output",
        }
        st.markdown(
            f'<div style="font-family:\'DM Mono\',monospace;font-size:0.6rem;color:{text_muted};">'
            f'{depth_desc[new_depth]}</div>',
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
            f'<div style="font-family:\'DM Mono\',monospace;font-size:0.6rem;color:{text_muted};">'
            f'{tone_desc[new_tone]}</div>',
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
            f'<div style="font-family:\'DM Mono\',monospace;font-size:0.6rem;color:{text_muted};">'
            f'These are injected into the AI system prompt.</div>',
            unsafe_allow_html=True,
        )

    # Save settings button
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

    # ── Study History ─────────────────────────────────────────────────────────
    st.markdown(
        f'<div style="font-family:\'DM Mono\',monospace;font-size:0.63rem;'
        f'letter-spacing:0.14em;text-transform:uppercase;color:{hist_label};margin-bottom:0.8rem;">'
        f'Study History ({len(history)})</div>',
        unsafe_allow_html=True,
    )

    if not history:
        st.markdown(
            f'<div style="font-family:\'DM Mono\',monospace;font-size:0.72rem;'
            f'color:{hist_label};padding:0.3rem 0;">No guides yet — generate your first!</div>',
            unsafe_allow_html=True,
        )
    else:
        for entry in history:
            mode        = entry.get("mode", "closed_book")
            title       = entry.get("blog_title", "Untitled")
            ts          = entry.get("created_at", "")
            bid         = entry["_id"]
            otype       = entry.get("output_type", "")
            nsec        = entry.get("section_count", "")
            wps         = entry.get("words_per_section", "")
            size_info   = f"{nsec}×{wps}w" if nsec and wps else ""
            is_active   = st.session_state.viewing_id == bid

            # Card container
            card_border = "rgba(124,92,252,0.6)" if is_active else "rgba(255,255,255,0.07)"
            st.markdown(
                f'<div style="background:#13131e;border:1px solid {card_border};border-radius:10px;'
                f'padding:0.7rem 0.85rem 0.5rem;margin-bottom:0.55rem;">',
                unsafe_allow_html=True,
            )

            confirming = st.session_state.confirm_delete == bid

            if not confirming:
                # ── Normal view: title button + trash icon ────────────────────
                col_b, col_d = st.columns([7, 1])
                with col_b:
                    if st.button(
                        f"{'▶ ' if is_active else ''}{title[:28]}{'…' if len(title) > 28 else ''}",
                        key=f"v_{bid}",
                        use_container_width=True,
                    ):
                        st.session_state.viewing_id     = bid
                        st.session_state.current_result = None
                        st.rerun()
                with col_d:
                    st.markdown(
                        f'<div style="display:flex;align-items:center;justify-content:center;height:2.4rem;">',
                        unsafe_allow_html=True,
                    )
                    if st.button("🗑", key=f"d_{bid}", help="Delete this entry"):
                        st.session_state.confirm_delete = bid
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                # ── Confirm view: "Delete?" + Yes / No ────────────────────────
                st.markdown(
                    f'<div style="font-family:\'DM Mono\',monospace;font-size:0.68rem;'
                    f'color:#f08080;margin-bottom:0.35rem;padding:0 0.1rem;">'
                    f'🗑 Delete this entry?</div>',
                    unsafe_allow_html=True,
                )
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✓ Yes, delete", key=f"yes_{bid}", use_container_width=True):
                        delete_blog(bid)
                        st.session_state.history = [h for h in history if h["_id"] != bid]
                        st.session_state.confirm_delete = None
                        if st.session_state.viewing_id == bid:
                            st.session_state.viewing_id = None
                        st.rerun()
                with col_no:
                    if st.button("✗ Cancel", key=f"no_{bid}", use_container_width=True):
                        st.session_state.confirm_delete = None
                        st.rerun()

            # Meta row — timestamp + type pill + size
            type_color = {
                "Study Guide":  ("#1a1035","#b89cfa"),
                "Blog Post":    ("#0d1f12","#60d890"),
                "Deep Research":("#1a1210","#f0a060"),
                "Quick Summary":("#0d1828","#60c8f8"),
            }.get(otype, ("#1a1a2e","#9a96c0"))
            pill_html = f'<span style="background:{type_color[0]};color:{type_color[1]};font-family:\'DM Mono\',monospace;font-size:0.55rem;padding:0.1rem 0.45rem;border-radius:100px;">{otype}</span>' if otype else ""
            size_html  = f'<span style="color:#4a4658;font-size:0.6rem;font-family:\'DM Mono\',monospace;">{size_info}</span>' if size_info else ""
            st.markdown(
                f'<div style="font-family:\'DM Mono\',monospace;font-size:0.6rem;color:#3a3640;'
                f'margin-top:0.1rem;display:flex;align-items:center;gap:0.4rem;flex-wrap:wrap;">'
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
        st.download_button("↓ Download", data=md, file_name=fn, mime="text/markdown", use_container_width=True)

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
            btn_labels.get(cfg.get("output_type","Study Guide"), "✦ Generate"),
            use_container_width=True
        )
    with col_hint:
        st.markdown(
            f'<div style="font-family:\'DM Mono\',monospace;font-size:0.68rem;color:{hist_label};padding-top:0.85rem;">'
            f'Research → Outline → Deep content → Structured Markdown'
            f'</div>',
            unsafe_allow_html=True,
        )

    if generate:
        if not topic.strip():
            st.warning("Please enter a topic before generating.")
        else:
            # ── Validate API key ──────────────────────────────────────────────
            active_key = cfg.get("gemini_api_key", "").strip() or os.getenv("GOOGLE_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
            if not active_key:
                st.error("⚠️ No Google API key found. Add your Gemini key in ⚙️ Settings → 🔑 API Key & Model (top of sidebar), or set GOOGLE_API_KEY in your .env file.")
                st.stop()

            # ── Inject user config into environment for backend to pick up ───
            # Set key under both names — ace_config checks GEMINI_API_KEY first,
            # ChatGoogleGenerativeAI falls back to GOOGLE_API_KEY
            os.environ["GOOGLE_API_KEY"]          = active_key
            os.environ["GEMINI_API_KEY"]          = active_key
            # Tavily key: user key takes priority over server .env key
            tavily_key = cfg.get("tavily_api_key", "").strip() or os.getenv("TAVILY_API_KEY", "")
            if tavily_key:
                os.environ["TAVILY_API_KEY"]      = tavily_key
            os.environ["ACE_OUTPUT_TYPE"]         = cfg.get("output_type", "Study Guide")
            os.environ["ACE_SECTION_COUNT"]       = str(cfg.get("section_count", 5))
            os.environ["ACE_WORDS_PER_SECTION"]   = str(cfg.get("words_per_section", 300))
            os.environ["ACE_DEPTH_LEVEL"]         = cfg.get("depth_level", "Balanced")
            os.environ["ACE_TONE"]                = cfg.get("tone", "Educational")
            os.environ["ACE_EXTRA_INSTRUCTION"]   = cfg.get("extra_instruction", "")

            try:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                # Force reimport so backend picks up new env values
                if "ACE_backend" in sys.modules:
                    del sys.modules["ACE_backend"]
                from ACE_backend import app as engine_app  # type: ignore
            except ImportError:
                st.error("**ACE_backend.py not found.** Place it in the same folder as app.py.")
                st.stop()

            # ── Show active config badge ──────────────────────────────────────
            otype    = cfg.get("output_type", "Study Guide")
            nsec     = cfg.get("section_count", 5)
            wps      = cfg.get("words_per_section", 300)
            depth    = cfg.get("depth_level", "Balanced")
            tone     = cfg.get("tone", "Educational")
            total_w  = nsec * wps
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
                filename   = (
                    "".join(c if c.isalnum() or c in (" ", "_", "-") else "" for c in blog_title)
                    .strip().lower().replace(" ", "_") + ".md"
                )
                entry = {
                    "blog_title": blog_title,
                    "markdown":   result_md,
                    "filename":   filename,
                    "mode":       mode_used,
                    "output_type":       cfg.get("output_type", "Study Guide"),
                    "section_count":     cfg.get("section_count", 5),
                    "words_per_section": cfg.get("words_per_section", 300),
                    "depth_level":       cfg.get("depth_level", "Balanced"),
                    "tone":        cfg.get("tone", "Educational"),
                    "topic":      topic.strip(),
                    "created_at": datetime.now().strftime("%b %d %Y, %H:%M"),
                }
                save_blog(user["id"], entry)
                refreshed = load_blogs(user["id"])
                st.session_state.history = refreshed
                st.session_state.current_result = refreshed[0]
                st.rerun()
            else:
                st.error("No output produced. Check your API keys and backend.")