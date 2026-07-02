import base64
import html
import io
import subprocess
import sys

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from playwright.sync_api import sync_playwright


# =========================================================
# Page Config
# =========================================================

st.set_page_config(
    page_title="LO Taiwan Monthly Pulse Generator",
    page_icon="📰",
    layout="wide",
)


# =========================================================
# Playwright / Chromium Setup
# =========================================================

@st.cache_resource(show_spinner=False)
def ensure_playwright_chromium():
    """
    Streamlit Cloud installs the Python package 'playwright',
    but Chromium may not be downloaded automatically.
    """
    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return True, ""
    except subprocess.CalledProcessError as e:
        return False, e.stderr or e.stdout or str(e)


chromium_ready, chromium_error = ensure_playwright_chromium()


# =========================================================
# Visual Theme Presets
# =========================================================

THEMES = {
    "Classic": {
        "accent": "#111111",
        "accent_text": "#FFFFFF",
        "background": "#FFFFFF",
        "soft_background": "#F5F5F5",
        "divider": "#D8D8D8",
        "badge_style": "pill",
        "title_transform": "none",
        "cover_phrase": "A clean monthly recap of people, culture, suppliers, and milestones.",
        "description": "Clean, corporate, stable",
    },
    "Energy": {
        "accent": "#C6FF00",
        "accent_text": "#111111",
        "background": "#FFFFFF",
        "soft_background": "#F8FAEE",
        "divider": "#DDE5C2",
        "badge_style": "block",
        "title_transform": "uppercase",
        "cover_phrase": "This month moved fast.",
        "description": "Sporty, active, bold",
    },
    "Milestone": {
        "accent": "#C8A24A",
        "accent_text": "#111111",
        "background": "#FFFFFF",
        "soft_background": "#F8F4EA",
        "divider": "#DED2B0",
        "badge_style": "eyebrow",
        "title_transform": "none",
        "cover_phrase": "Celebrating what we have built together.",
        "description": "Premium, celebratory, memorable",
    },
    "People": {
        "accent": "#4A90E2",
        "accent_text": "#FFFFFF",
        "background": "#FFFFFF",
        "soft_background": "#F2F7FD",
        "divider": "#C8DDF4",
        "badge_style": "pill",
        "title_transform": "none",
        "cover_phrase": "The people, stories, and moments behind the team.",
        "description": "Warm, people-focused, friendly",
    },
    "Field Notes": {
        "accent": "#C96F32",
        "accent_text": "#FFFFFF",
        "background": "#FFFFFF",
        "soft_background": "#F8F1EA",
        "divider": "#E0C4AD",
        "badge_style": "stamp",
        "title_transform": "none",
        "cover_phrase": "Notes from supplier visits, business updates, and the field.",
        "description": "Travel, supplier visit, documentary",
    },
}


DEFAULT_BADGES = {
    "People": "People Spotlight",
    "Milestone": "Milestone Moment",
    "Supplier": "From the Field",
    "Culture": "Team Moments",
    "Coming Up": "Next Up",
}


def image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode("utf-8")


def image_mime_type(image_name):
    lower_name = image_name.lower()
    if lower_name.endswith(".png"):
        return "image/png"
    if lower_name.endswith(".jpg") or lower_name.endswith(".jpeg"):
        return "image/jpeg"
    return "image/jpeg"


def safe_html_text(text):
    if text is None:
        return ""
    return html.escape(str(text)).replace("\n", "<br>")


def title_case_by_theme(title, theme_style):
    if theme_style["title_transform"] == "uppercase":
        return title.upper()
    return title


def get_badge_text(section):
    custom_badge = section.get("badge_label", "").strip()
    if custom_badge:
        return custom_badge
    return DEFAULT_BADGES.get(section["category"], section["category"])


def month_to_filename(month_text):
    cleaned = month_text.replace(" ", "_").replace("/", "_")
    cleaned = "".join(char for char in cleaned if char.isalnum() or char in ["_", "-"])
    return cleaned or "Newsletter"


def build_image_src(image):
    mime = image_mime_type(image["name"])
    encoded = image_to_base64(image["bytes"])
    return f"data:{mime};base64,{encoded}"


def uploaded_file_to_image_dict(uploaded_file):
    return {
        "name": uploaded_file.name,
        "bytes": uploaded_file.getvalue(),
    }


def get_auto_template(section):
    """
    Auto-template logic:
    - No image + short content: brief card
    - No image + longer content: text story
    - One image: feature story
    - Two or more images: gallery story
    """
    images = section.get("images", [])
    content = section.get("content", "")
    image_count = len(images)
    word_count = len(content.split())
    if image_count == 0 and word_count <= 45:
        return "brief"
    if image_count == 0:
        return "text"
    if image_count == 1:
        return "feature"
    return "gallery"


def get_badge_css(theme_style):
    badge_style = theme_style["badge_style"]
    if badge_style == "pill":
        return f"""
        background: {theme_style["accent"]};
        color: {theme_style["accent_text"]};
        border-radius: 999px;
        padding: 7px 16px;
        font-size: 11px;
        font-weight: 900;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 10px;
        """
    if badge_style == "block":
        return f"""
        background: {theme_style["accent"]};
        color: {theme_style["accent_text"]};
        border-radius: 3px;
        padding: 7px 14px;
        font-size: 11px;
        font-weight: 900;
        letter-spacing: 0.7px;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 10px;
        """
    if badge_style == "eyebrow":
        return f"""
        background: transparent;
        color: {theme_style["accent"]};
        border-bottom: 3px solid {theme_style["accent"]};
        padding: 0 0 4px 0;
        font-size: 11px;
        font-weight: 900;
        letter-spacing: 1px;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 12px;
        """
    if badge_style == "stamp":
        return f"""
        background: transparent;
        color: {theme_style["accent"]};
        border: 2px solid {theme_style["accent"]};
        border-radius: 4px;
        padding: 6px 12px;
        font-size: 11px;
        font-weight: 900;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 12px;
        """
    return ""


def generate_images_html(images, layout="grid"):
    if not images:
        return ""

    image_count = len(images)

    image_tags = []
    for index, image in enumerate(images, start=1):
        image_tags.append(
            f"""
            <figure class="image-frame image-item image-item-{index}">
                <img class="section-image" src="{build_image_src(image)}" alt="">
            </figure>
            """
        )

    if layout == "feature":
        first_image = image_tags[0]
        remaining_images = image_tags[1:]
        remaining_html = ""
        if remaining_images:
            remaining_html = f"""
            <div class="image-grid image-grid-2">
                {''.join(remaining_images)}
            </div>
            """
        return f"""
        <div class="feature-image-wrap">
            {first_image}
        </div>
        {remaining_html}
        """

    if layout == "single-column":
        return f"""
        <div class="image-column">
            {''.join(image_tags)}
        </div>
        """

    if image_count == 2:
        layout_class = "image-grid image-grid-2"
    elif image_count == 3:
        layout_class = "image-collage image-collage-3"
    elif image_count == 4:
        layout_class = "image-collage image-collage-4"
    elif image_count == 5:
        layout_class = "image-collage image-collage-5"
    elif image_count == 6:
        layout_class = "image-collage image-collage-6"
    elif image_count == 7:
        layout_class = "image-collage image-collage-7"
    elif image_count == 8:
        layout_class = "image-collage image-collage-8"
    elif image_count == 9:
        layout_class = "image-collage image-collage-9"
    else:
        layout_class = "image-collage image-collage-10"

    return f"""
    <div class="{layout_class}">
        {''.join(image_tags)}
    </div>
    """


def generate_section_html(section, theme_style, template_mode):
    badge_text = safe_html_text(get_badge_text(section))
    title = safe_html_text(title_case_by_theme(section["title"], theme_style))
    content = safe_html_text(section["content"])
    images = section.get("images", [])
    selected_template = section.get("manual_template", "Auto")
    if template_mode == "Auto" or selected_template == "Auto":
        template = get_auto_template(section)
    else:
        template = selected_template.lower().replace(" ", "-")
    if template == "brief":
        return f"""
        <section class="section-card brief-card">
            <div>
                <div class="badge">{badge_text}</div>
                <h2 class="section-title brief-title">{title}</h2>
            </div>
            <div class="section-content brief-content">{content}</div>
        </section>
        """
    if template == "text":
        return f"""
        <section class="section-card text-story-card">
            <div class="badge">{badge_text}</div>
            <h2 class="section-title">{title}</h2>
            <div class="section-content">{content}</div>
        </section>
        """
    if template == "feature" or template == "feature-story":
        images_html = generate_images_html(images, layout="feature")
        return f"""
        <section class="section-card feature-card">
            <div class="badge">{badge_text}</div>
            <h2 class="section-title">{title}</h2>
            {images_html}
            <div class="section-content after-image">{content}</div>
        </section>
        """
    if template == "field-report":
        images_html = generate_images_html(images, layout="single-column")
        if images:
            return f"""
            <section class="section-card field-report-card">
                <div class="badge">{badge_text}</div>
                <h2 class="section-title">{title}</h2>
                <div class="field-report-layout">
                    <div class="field-report-text">
                        <div class="section-content">{content}</div>
                    </div>
                    <div class="field-report-images">
                        {images_html}
                    </div>
                </div>
            </section>
            """
        return f"""
        <section class="section-card text-story-card">
            <div class="badge">{badge_text}</div>
            <h2 class="section-title">{title}</h2>
            <div class="section-content">{content}</div>
        </section>
        """
    images_html = generate_images_html(images, layout="grid")
    return f"""
    <section class="section-card gallery-card">
        <div class="badge">{badge_text}</div>
        <h2 class="section-title">{title}</h2>
        <div class="section-content">{content}</div>
        {images_html}
    </section>
    """


def generate_banner_html(banner_mode, uploaded_banner, uploaded_background, month, volume, issue, banner_title):
    month_text = safe_html_text(month)
    volume_text = safe_html_text(volume)
    issue_text = safe_html_text(issue)
    title_text = safe_html_text(banner_title)
    if banner_mode == "Upload Ready-Made Banner" and uploaded_banner is not None:
        image = uploaded_file_to_image_dict(uploaded_banner)
        return f"""
        <section class="top-banner ready-banner">
            <img src="{build_image_src(image)}" alt="Newsletter banner">
        </section>
        """
    if banner_mode == "Generate Banner from Background Photo" and uploaded_background is not None:
        image = uploaded_file_to_image_dict(uploaded_background)
        return f"""
        <section class="top-banner generated-banner" style="background-image: url('{build_image_src(image)}');">
            <div class="banner-overlay">
                <div class="banner-title">{title_text}</div>
                <div class="banner-month">{month_text.upper()} NEWSLETTER</div>
            </div>
        </section>
        """
    return f"""
    <section class="top-banner generated-banner banner-placeholder">
        <div class="banner-overlay">
            <div class="banner-title">{title_text}</div>
            <div class="banner-month">{month_text.upper()} NEWSLETTER</div>
            <div class="banner-meta">Volume {volume_text} &nbsp; | &nbsp; Issue {issue_text}</div>
        </div>
    </section>
    """


def generate_newsletter_html(month, main_theme, editor, volume, issue, banner_mode, uploaded_banner, uploaded_background, banner_title, sections, visual_theme, template_mode):
    theme_style = THEMES[visual_theme]
    banner_html = generate_banner_html(banner_mode, uploaded_banner, uploaded_background, month, volume, issue, banner_title)
    issue_items_html = ""
    for index, section in enumerate(sections, start=1):
        issue_badge = safe_html_text(get_badge_text(section))
        issue_title = safe_html_text(section["title"])
        auto_template = get_auto_template(section).title()
        issue_items_html += f"""
        <div class="issue-item">
            <div class="issue-number">{index}</div>
            <div class="issue-text">
                <div class="issue-badge">{issue_badge} · {auto_template}</div>
                <div class="issue-title">{issue_title}</div>
            </div>
        </div>
        """
    section_html = ""
    for section in sections:
        section_html += generate_section_html(section, theme_style, template_mode)
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ margin: 0; }}
            * {{ box-sizing: border-box; }}
            html, body {{ margin: 0; padding: 0; background: #ffffff; color: #111111; font-family: Arial, Helvetica, sans-serif; }}
            .page {{ width: 100%; max-width: 820px; margin: 0 auto; padding: 18px 28px 22px 28px; }}
            .top-banner {{ width: 100%; height: 180px; margin: 0 0 22px 0; border-radius: 16px; overflow: hidden; border: 1px solid {theme_style["divider"]}; background-color: #f2f2f2; }}
            .ready-banner {{ background: #ffffff; display: flex; align-items: center; justify-content: center; }}
            .ready-banner img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
            .generated-banner {{ background-size: cover; background-position: center; position: relative; }}
            .banner-placeholder {{ background: linear-gradient(135deg, rgba(17,17,17,0.92), rgba(17,17,17,0.62)), linear-gradient(90deg, {theme_style["soft_background"]}, #d9d9d9); }}
            .generated-banner::after {{ content: ""; position: absolute; inset: 0; background: linear-gradient(90deg, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.42) 48%, rgba(0,0,0,0.05) 100%); z-index: 1; }}
            .banner-overlay {{ position: relative; z-index: 2; height: 100%; padding: 28px 34px; display: flex; flex-direction: column; justify-content: center; color: #ffffff; }}
            .banner-title {{ font-size: 44px; line-height: 0.95; font-weight: 950; letter-spacing: -1.5px; text-transform: uppercase; text-shadow: 0 2px 10px rgba(0,0,0,0.25); }}
            .banner-month {{ margin-top: 12px; font-size: 24px; line-height: 1; font-weight: 900; letter-spacing: -0.4px; text-shadow: 0 2px 10px rgba(0,0,0,0.25); }}
            .issue-overview {{ margin-bottom: 30px; }}
            .issue-header {{ margin-bottom: 14px; }}
            .issue-heading {{ font-size: 22px; font-weight: 950; margin: 0 0 5px 0; letter-spacing: -0.3px; }}
            .issue-subtitle {{ font-size: 11px; line-height: 1.4; color: #666666; font-weight: 700; }}
            .issue-list {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
            .issue-item {{ display: grid; grid-template-columns: 34px 1fr; gap: 12px; align-items: center; background: {theme_style["soft_background"]}; border: 1px solid {theme_style["divider"]}; border-left: 5px solid {theme_style["accent"]}; border-radius: 12px; padding: 13px 14px; }}
            .issue-number {{ width: 30px; height: 30px; border-radius: 999px; background: {theme_style["accent"]}; color: {theme_style["accent_text"]}; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 950; }}
            .issue-badge {{ font-size: 9px; line-height: 1.2; color: #666666; font-weight: 900; letter-spacing: 0.4px; text-transform: uppercase; margin-bottom: 3px; }}
            .issue-title {{ font-size: 14px; line-height: 1.3; font-weight: 900; color: #111111; }}
            .section-card {{ border: 1px solid {theme_style["divider"]}; border-top: 6px solid {theme_style["accent"]}; border-radius: 16px; padding: 24px 26px 24px 26px; margin-bottom: 24px; background: {theme_style["background"]}; page-break-inside: avoid; }}
            .brief-card {{ display: grid; grid-template-columns: 0.9fr 1.8fr; gap: 22px; align-items: start; }}
            .badge {{ {get_badge_css(theme_style)} }}
            .section-title {{ font-size: 31px; font-weight: 950; line-height: 1.06; letter-spacing: -0.7px; margin: 0 0 16px 0; text-transform: {theme_style["title_transform"]}; }}
            .brief-title {{ font-size: 24px; margin-bottom: 0; }}
            .section-content {{ font-size: 14px; line-height: 1.55; font-weight: 500; margin: 0 0 16px 0; }}
            .brief-content {{ margin-top: 26px; font-size: 13px; }}
            .section-content.after-image {{ margin-top: 14px; }}

            .image-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 12px; align-items: start; }}
            .image-grid-2 .image-frame {{ aspect-ratio: 16 / 10; }}
            .image-grid-2 .section-image {{ width: 100%; height: 100%; object-fit: cover; }}

            .image-collage {{ display: grid; gap: 8px; margin-top: 14px; width: 100%; }}
            .image-collage .image-frame {{ height: 100%; aspect-ratio: auto; }}
            .image-collage .section-image {{ width: 100%; height: 100%; object-fit: cover; }}

            .image-collage-3 {{ grid-template-columns: 2fr 1fr; grid-template-rows: repeat(2, 128px); }}
            .image-collage-3 .image-item-1 {{ grid-row: span 2; }}

            .image-collage-4 {{ grid-template-columns: repeat(2, minmax(0, 1fr)); grid-template-rows: repeat(2, 126px); }}

            .image-collage-5 {{ grid-template-columns: repeat(4, minmax(0, 1fr)); grid-template-rows: repeat(2, 118px); }}
            .image-collage-5 .image-item-1 {{ grid-column: span 2; grid-row: span 2; }}

            .image-collage-6 {{ grid-template-columns: repeat(4, minmax(0, 1fr)); grid-template-rows: repeat(2, 112px); }}
            .image-collage-6 .image-item-1 {{ grid-column: span 2; }}
            .image-collage-6 .image-item-6 {{ grid-column: span 2; }}

            .image-collage-7 {{ grid-template-columns: repeat(4, minmax(0, 1fr)); grid-template-rows: repeat(2, 108px); }}
            .image-collage-7 .image-item-1 {{ grid-column: span 2; }}

            .image-collage-8 {{ grid-template-columns: repeat(4, minmax(0, 1fr)); grid-template-rows: repeat(3, 88px); }}
            .image-collage-8 .image-item-1 {{ grid-column: span 2; grid-row: span 2; }}
            .image-collage-8 .image-item-8 {{ grid-column: span 2; }}

            .image-collage-9 {{ grid-template-columns: repeat(3, minmax(0, 1fr)); grid-template-rows: repeat(3, 96px); }}

            .image-collage-10 {{ grid-template-columns: repeat(5, minmax(0, 1fr)); grid-template-rows: repeat(3, 82px); }}
            .image-collage-10 .image-item-1 {{ grid-column: span 2; grid-row: span 2; }}
            .image-collage-10 .image-item-10 {{ grid-column: span 2; }}

            .feature-image-wrap {{ margin: 8px 0 14px 0; }}
            .image-frame {{ width: 100%; margin: 0; border-radius: 12px; overflow: hidden; border: 1px solid {theme_style["divider"]}; background: transparent; }}
            .section-image {{ width: 100%; height: auto; display: block; }}
            .image-column {{ display: flex; flex-direction: column; gap: 12px; }}
            .field-report-layout {{ display: grid; grid-template-columns: 1.12fr 0.88fr; gap: 22px; align-items: start; }}
            .field-report-text .section-content {{ margin-bottom: 0; }}
            .footer {{ color: #666666; font-size: 9px; line-height: 1.4; margin-top: 22px; border-top: 1px solid {theme_style["divider"]}; padding-top: 12px; }}
            @media screen {{ body {{ padding: 16px; }} .page {{ max-width: 820px; }} }}
            @media print {{ html, body {{ width: 100%; background: #ffffff; }} .page {{ max-width: none; padding: 18px 28px 22px 28px; }} }}
            @media screen and (max-width: 720px) {{ .page {{ padding: 16px; }} .top-banner {{ height: 150px; }} .banner-title {{ font-size: 34px; }} .banner-month {{ font-size: 19px; }} .issue-list {{ grid-template-columns: 1fr; }} .image-grid {{ grid-template-columns: 1fr; }} .image-collage {{ grid-template-columns: 1fr !important; grid-template-rows: none !important; }} .image-collage .image-item {{ grid-column: auto !important; grid-row: auto !important; }} .image-collage .image-frame {{ aspect-ratio: 16 / 10; }} .field-report-layout, .brief-card {{ grid-template-columns: 1fr; }} .brief-content {{ margin-top: 0; }} }}
        </style>
    </head>
    <body>
        <main class="page" id="newsletter">
            {banner_html}
            <section class="issue-overview">
                <div class="issue-header">
                    <h2 class="issue-heading">In This Issue</h2>
                    <div class="issue-subtitle">{safe_html_text(main_theme or "A quick guide to this month’s key stories.")}</div>
                </div>
                <div class="issue-list">{issue_items_html}</div>
            </section>
            {section_html}
            <div class="footer">Generated by LO Taiwan Monthly Pulse Generator Prototype. Human review is required before publishing.</div>
        </main>
    </body>
    </html>
    """


def html_to_pdf_bytes(newsletter_html):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=1)
        page.set_content(newsletter_html, wait_until="networkidle")
        document_height = page.evaluate("""
            () => {
                const body = document.body;
                const html = document.documentElement;
                return Math.max(body.scrollHeight, body.offsetHeight, html.clientHeight, html.scrollHeight, html.offsetHeight);
            }
        """)
        pdf_bytes = page.pdf(width="794px", height=f"{document_height + 40}px", print_background=True, margin={"top": "0px", "right": "0px", "bottom": "0px", "left": "0px"})
        browser.close()
    return pdf_bytes


def html_to_jpg_bytes(newsletter_html):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": 900, "height": 1600}, device_scale_factor=2)
        page.set_content(newsletter_html, wait_until="networkidle")
        element = page.query_selector("#newsletter")
        if element:
            png_bytes = element.screenshot(type="png")
        else:
            png_bytes = page.screenshot(type="png", full_page=True)
        browser.close()
    image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    output = io.BytesIO()
    image.save(output, format="JPEG", quality=95, optimize=True)
    return output.getvalue()


# =========================================================
# Session State
# =========================================================

if "sections" not in st.session_state:
    st.session_state.sections = []
if "form_counter" not in st.session_state:
    st.session_state.form_counter = 0


# =========================================================
# App Title
# =========================================================

st.title("LO Taiwan Monthly Pulse Generator")
st.caption("From raw monthly updates to a branded newsletter draft.")


# =========================================================
# Sidebar Settings
# =========================================================

st.sidebar.header("Newsletter Settings")
newsletter_month = st.sidebar.text_input("Month", "June 2026")
newsletter_volume = st.sidebar.text_input("Volume", "2")
newsletter_issue = st.sidebar.text_input("Issue", "17")
main_theme = st.sidebar.text_input("Main Theme", "People, culture, suppliers, and milestones")
editor_name = st.sidebar.text_input("Editor", "Luz Lin")
visual_theme = st.sidebar.selectbox("Visual Theme", ["Classic", "Energy", "Milestone", "People", "Field Notes"])
template_mode = st.sidebar.selectbox("Template Mode", ["Auto", "Manual"], help="Auto chooses a section layout based on text length and image count. Manual lets each section choose a layout.")
theme = THEMES[visual_theme]
st.sidebar.caption(f"Theme mood: {theme['description']}")
st.sidebar.markdown("---")
st.sidebar.write("Prototype Version 2.6")
st.sidebar.caption("Banner-led layout. Auto templates, collage gallery, PDF/JPG export.")


# =========================================================
# Banner Settings
# =========================================================

st.header("1. Banner Settings")
banner_col1, banner_col2 = st.columns([1, 1])
with banner_col1:
    banner_mode = st.selectbox("Banner Mode", ["Generate Banner from Background Photo", "Upload Ready-Made Banner"])
    banner_title = st.text_input("Banner Title", "LO TAIWAN")
with banner_col2:
    uploaded_banner = None
    uploaded_background = None
    if banner_mode == "Upload Ready-Made Banner":
        uploaded_banner = st.file_uploader("Upload Ready-Made Banner", type=["png", "jpg", "jpeg"], help="Use this if you already designed the full horizontal banner.", key="ready_banner_upload")
        if uploaded_banner is not None:
            st.image(uploaded_banner, caption="Ready-made banner preview", use_container_width=True)
    else:
        uploaded_background = st.file_uploader("Upload Background Photo", type=["png", "jpg", "jpeg"], help="Upload a regular photo. The app will crop it into a newsletter banner and add text automatically.", key="background_banner_upload")
        if uploaded_background is not None:
            st.image(uploaded_background, caption="Background photo preview", use_container_width=True)


# =========================================================
# Input Form
# =========================================================

st.header("2. Add Monthly Update")
with st.form(f"update_form_{st.session_state.form_counter}"):
    category = st.selectbox("Category", ["People", "Milestone", "Supplier", "Culture", "Coming Up"])
    default_badge = DEFAULT_BADGES.get(category, category)
    badge_label = st.text_input("Badge Label", value="", placeholder=f"Example: {default_badge}, Big Moves, From the Field, Team Energy")
    title = st.text_input("Section Title", placeholder="Example: Promotions")
    raw_content = st.text_area("Raw Content", placeholder="Paste or type the original update here...", height=160)
    manual_template = "Auto"
    if template_mode == "Manual":
        manual_template = st.selectbox("Section Template", ["Auto", "Brief", "Text", "Feature Story", "Gallery", "Field Report"], help="Use Auto for the system to choose based on images and text length.")
    uploaded_images = st.file_uploader("Upload images for this section", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    submitted = st.form_submit_button("Add Section")
    if submitted:
        if title and raw_content:
            images = []
            if uploaded_images:
                for uploaded_image in uploaded_images:
                    images.append(uploaded_file_to_image_dict(uploaded_image))
            st.session_state.sections.append({"category": category, "badge_label": badge_label.strip(), "title": title, "content": raw_content, "manual_template": manual_template, "images": images})
            st.session_state.form_counter += 1
            st.success("Section added successfully!")
            st.rerun()
        else:
            st.warning("Please enter both a title and content.")


# =========================================================
# Preview
# =========================================================

st.header("3. Newsletter Preview")
if len(st.session_state.sections) == 0:
    st.info("Add at least one section to generate the newsletter preview.")
else:
    col1, col2 = st.columns([0.65, 1.75])
    with col1:
        st.subheader("Added Sections")
        for i, section in enumerate(st.session_state.sections):
            badge_text = get_badge_text(section)
            auto_template = get_auto_template(section)
            with st.expander(f"{i + 1}. {section['category']} — {section['title']}"):
                st.caption(f"Badge: {badge_text}")
                st.caption(f"Template: {section.get('manual_template', 'Auto')} / Auto suggestion: {auto_template}")
                st.write(section["content"])
                images = section.get("images", [])
                if images:
                    st.caption(f"Images: {len(images)} uploaded")
                else:
                    st.caption("Images: None")
                if st.button(f"Delete Section {i + 1}", key=f"delete_{i}"):
                    st.session_state.sections.pop(i)
                    st.rerun()
    with col2:
        st.subheader("Newsletter Draft")
        newsletter_html = generate_newsletter_html(newsletter_month, main_theme, editor_name, newsletter_volume, newsletter_issue, banner_mode, uploaded_banner, uploaded_background, banner_title, st.session_state.sections, visual_theme, template_mode)
        components.html(newsletter_html, height=1100, scrolling=True)


# =========================================================
# Export and Clear Buttons
# =========================================================

st.markdown("---")
if st.session_state.sections:
    newsletter_html = generate_newsletter_html(newsletter_month, main_theme, editor_name, newsletter_volume, newsletter_issue, banner_mode, uploaded_banner, uploaded_background, banner_title, st.session_state.sections, visual_theme, template_mode)
    if not chromium_ready:
        st.error("Playwright Chromium installation failed.")
        st.code(chromium_error)
    else:
        export_col1, export_col2 = st.columns(2)
        with export_col1:
            try:
                pdf_bytes = html_to_pdf_bytes(newsletter_html)
                st.download_button(label="Download Newsletter PDF", data=pdf_bytes, file_name=f"LO_Taiwan_Monthly_Pulse_{month_to_filename(newsletter_month)}_{visual_theme}.pdf", mime="application/pdf", use_container_width=True)
            except Exception as e:
                st.error("PDF export failed. Please check Playwright/Chromium setup.")
                st.caption(str(e))
        with export_col2:
            try:
                jpg_bytes = html_to_jpg_bytes(newsletter_html)
                st.download_button(label="Download Newsletter JPG", data=jpg_bytes, file_name=f"LO_Taiwan_Monthly_Pulse_{month_to_filename(newsletter_month)}_{visual_theme}.jpg", mime="image/jpeg", use_container_width=True)
            except Exception as e:
                st.error("JPG export failed. Please check Playwright/Chromium setup.")
                st.caption(str(e))

if st.button("Clear All Sections"):
    st.session_state.sections = []
    st.session_state.form_counter += 1
    st.rerun()
