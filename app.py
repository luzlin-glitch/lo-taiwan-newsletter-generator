import base64
import html
import io
import subprocess
import sys
from pathlib import Path
from datetime import datetime

import streamlit as st
from PIL import Image
from playwright.sync_api import sync_playwright


# =========================================================
# App Config
# =========================================================

st.set_page_config(
    page_title="LO Taiwan Monthly Pulse Generator",
    page_icon="🇹🇼",
    layout="wide",
)


# =========================================================
# Playwright / Chromium Setup
# =========================================================

@st.cache_resource(show_spinner=False)
def ensure_playwright_chromium():
    """
    Streamlit Cloud installs the Python package 'playwright',
    but it may not automatically download Chromium.
    This function makes sure Chromium exists before export.
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
        error_message = e.stderr or e.stdout or str(e)
        return False, error_message


chromium_ready, chromium_error = ensure_playwright_chromium()


# =========================================================
# Utility Functions
# =========================================================

def safe_text(value):
    if value is None:
        return ""
    return html.escape(str(value))


def month_to_filename(month_text):
    cleaned = month_text.lower().replace(" ", "-").replace("/", "-")
    cleaned = "".join(char for char in cleaned if char.isalnum() or char in ["-", "_"])
    return cleaned


def image_to_base64(uploaded_file):
    if uploaded_file is None:
        return None

    bytes_data = uploaded_file.getvalue()
    encoded = base64.b64encode(bytes_data).decode("utf-8")
    file_type = uploaded_file.type

    return f"data:{file_type};base64,{encoded}"


def render_newsletter_html(
    month,
    main_theme,
    editor,
    visual_theme,
    layout_style,
    hero_title,
    hero_subtitle,
    hero_image_data_url,
    sections,
):
    theme_map = {
        "Classic": {
            "primary": "#0B1F3A",
            "secondary": "#D71920",
            "accent": "#2F6FED",
            "bg": "#F4F6F8",
            "card": "#FFFFFF",
            "text": "#1F2937",
            "muted": "#6B7280",
        },
        "Fresh": {
            "primary": "#0F766E",
            "secondary": "#F97316",
            "accent": "#14B8A6",
            "bg": "#F0FDFA",
            "card": "#FFFFFF",
            "text": "#134E4A",
            "muted": "#64748B",
        },
        "Bold": {
            "primary": "#111827",
            "secondary": "#EF4444",
            "accent": "#F59E0B",
            "bg": "#F9FAFB",
            "card": "#FFFFFF",
            "text": "#111827",
            "muted": "#6B7280",
        },
        "Sporty": {
            "primary": "#001E62",
            "secondary": "#00AEEF",
            "accent": "#84CC16",
            "bg": "#EEF4FF",
            "card": "#FFFFFF",
            "text": "#0F172A",
            "muted": "#64748B",
        },
    }

    theme = theme_map.get(visual_theme, theme_map["Classic"])

    if layout_style == "Compact":
        card_padding = "18px"
        section_gap = "14px"
        body_font_size = "14px"
        hero_image_height = "220px"
    elif layout_style == "Magazine":
        card_padding = "28px"
        section_gap = "24px"
        body_font_size = "15px"
        hero_image_height = "300px"
    else:
        card_padding = "22px"
        section_gap = "18px"
        body_font_size = "15px"
        hero_image_height = "260px"

    hero_image_html = ""
    if hero_image_data_url:
        hero_image_html = f"""
        <div class="hero-image-wrap">
            <img src="{hero_image_data_url}" class="hero-image" alt="Newsletter visual">
        </div>
        """

    section_html = ""

    for index, section in enumerate(sections, start=1):
        title = safe_text(section.get("title", ""))
        category = safe_text(section.get("category", ""))
        body = safe_text(section.get("body", "")).replace("\n", "<br>")
        highlight = safe_text(section.get("highlight", ""))

        if not title and not body and not highlight:
            continue

        highlight_html = ""
        if highlight:
            highlight_html = f"""
            <div class="highlight-box">
                {highlight}
            </div>
            """

        section_html += f"""
        <section class="content-card">
            <div class="section-meta">
                <span class="section-number">{index:02d}</span>
                <span class="section-category">{category}</span>
            </div>
            <h2>{title}</h2>
            <p>{body}</p>
            {highlight_html}
        </section>
        """

    if not section_html:
        section_html = """
        <section class="content-card">
            <div class="section-meta">
                <span class="section-number">01</span>
                <span class="section-category">Preview</span>
            </div>
            <h2>Your newsletter content will appear here</h2>
            <p>Add section titles, highlights, and body content from the editor panel.</p>
        </section>
        """

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>LO Taiwan Monthly Pulse</title>

<style>
    * {{
        box-sizing: border-box;
    }}

    body {{
        margin: 0;
        padding: 0;
        background: {theme["bg"]};
        font-family: Arial, "Helvetica Neue", Helvetica, sans-serif;
        color: {theme["text"]};
    }}

    .newsletter-page {{
        width: 900px;
        margin: 0 auto;
        background: {theme["bg"]};
        padding: 36px;
    }}

    .top-line {{
        height: 8px;
        background: linear-gradient(
            90deg,
            {theme["primary"]} 0%,
            {theme["primary"]} 45%,
            {theme["secondary"]} 45%,
            {theme["secondary"]} 70%,
            {theme["accent"]} 70%,
            {theme["accent"]} 100%
        );
        border-radius: 999px;
        margin-bottom: 24px;
    }}

    .hero {{
        background: {theme["primary"]};
        color: white;
        border-radius: 28px;
        padding: 38px;
        position: relative;
        overflow: hidden;
        margin-bottom: 24px;
    }}

    .hero::after {{
        content: "";
        position: absolute;
        right: -80px;
        top: -80px;
        width: 240px;
        height: 240px;
        background: {theme["secondary"]};
        opacity: 0.85;
        border-radius: 50%;
    }}

    .hero::before {{
        content: "";
        position: absolute;
        right: 70px;
        bottom: -70px;
        width: 180px;
        height: 180px;
        background: {theme["accent"]};
        opacity: 0.7;
        border-radius: 50%;
    }}

    .badge {{
        display: inline-block;
        position: relative;
        z-index: 2;
        background: white;
        color: {theme["primary"]};
        padding: 8px 14px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 18px;
    }}

    .hero h1 {{
        position: relative;
        z-index: 2;
        margin: 0;
        font-size: 42px;
        line-height: 1.05;
        letter-spacing: -0.04em;
        max-width: 650px;
    }}

    .hero p {{
        position: relative;
        z-index: 2;
        margin: 16px 0 0;
        font-size: 16px;
        line-height: 1.6;
        max-width: 620px;
        opacity: 0.92;
    }}

    .hero-image-wrap {{
        position: relative;
        z-index: 2;
        margin-top: 24px;
        width: 100%;
        height: {hero_image_height};
        border-radius: 22px;
        overflow: hidden;
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.24);
    }}

    .hero-image {{
        display: block;
        width: 100%;
        height: 100%;
        object-fit: cover;
    }}

    .theme-strip {{
        background: white;
        border-radius: 20px;
        padding: 18px 22px;
        margin-bottom: 24px;
        display: grid;
        grid-template-columns: 1.3fr 2fr 1fr;
        gap: 16px;
        border: 1px solid rgba(15, 23, 42, 0.08);
    }}

    .theme-strip .label {{
        font-size: 11px;
        color: {theme["muted"]};
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700;
        margin-bottom: 6px;
    }}

    .theme-strip .value {{
        font-size: 14px;
        font-weight: 700;
        color: {theme["text"]};
        line-height: 1.4;
    }}

    .content-grid {{
        display: grid;
        grid-template-columns: 1fr;
        gap: {section_gap};
    }}

    .content-card {{
        background: {theme["card"]};
        border-radius: 24px;
        padding: {card_padding};
        border: 1px solid rgba(15, 23, 42, 0.08);
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
        page-break-inside: avoid;
    }}

    .section-meta {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 14px;
    }}

    .section-number {{
        background: {theme["primary"]};
        color: white;
        border-radius: 999px;
        padding: 5px 10px;
        font-size: 11px;
        font-weight: 700;
    }}

    .section-category {{
        color: {theme["secondary"]};
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}

    .content-card h2 {{
        margin: 0 0 10px;
        font-size: 24px;
        line-height: 1.2;
        letter-spacing: -0.02em;
        color: {theme["text"]};
    }}

    .content-card p {{
        margin: 0;
        font-size: {body_font_size};
        line-height: 1.75;
        color: {theme["text"]};
    }}

    .highlight-box {{
        margin-top: 16px;
        padding: 14px 16px;
        background: {theme["bg"]};
        border-left: 5px solid {theme["secondary"]};
        border-radius: 14px;
        font-size: 14px;
        line-height: 1.6;
        font-weight: 700;
    }}

    .footer {{
        margin-top: 26px;
        padding: 20px 6px 0;
        color: {theme["muted"]};
        font-size: 12px;
        display: flex;
        justify-content: space-between;
        border-top: 1px solid rgba(15, 23, 42, 0.12);
    }}

    @media print {{
        body {{
            background: white;
        }}

        .newsletter-page {{
            width: 100%;
            padding: 24px;
        }}

        .content-card {{
            box-shadow: none;
        }}
    }}
</style>
</head>

<body>
    <main class="newsletter-page" id="newsletter">
        <div class="top-line"></div>

        <section class="hero">
            <div class="badge">LO Taiwan Monthly Pulse · {safe_text(month)}</div>
            <h1>{safe_text(hero_title)}</h1>
            <p>{safe_text(hero_subtitle)}</p>
            {hero_image_html}
        </section>

        <section class="theme-strip">
            <div>
                <div class="label">Main Theme</div>
                <div class="value">{safe_text(main_theme)}</div>
            </div>
            <div>
                <div class="label">Visual Direction</div>
                <div class="value">{safe_text(visual_theme)} · {safe_text(layout_style)}</div>
            </div>
            <div>
                <div class="label">Editor</div>
                <div class="value">{safe_text(editor)}</div>
            </div>
        </section>

        <section class="content-grid">
            {section_html}
        </section>

        <footer class="footer">
            <div>LO Taiwan Monthly Pulse</div>
            <div>Generated on {datetime.now().strftime("%Y-%m-%d")}</div>
        </footer>
    </main>
</body>
</html>
"""
    return html_content


def html_to_pdf_bytes(html_content):
    """
    Synchronous Playwright PDF export.
    Do not use await / async in Streamlit.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

        page = browser.new_page(
            viewport={"width": 960, "height": 1400},
            device_scale_factor=1,
        )

        page.set_content(html_content, wait_until="networkidle")

        pdf_bytes = page.pdf(
            format="A4",
            print_background=True,
            margin={
                "top": "0.25in",
                "right": "0.25in",
                "bottom": "0.25in",
                "left": "0.25in",
            },
        )

        browser.close()
        return pdf_bytes


def html_to_jpg_bytes(html_content):
    """
    Export newsletter as JPG for email body usage.
    Playwright captures PNG first, then Pillow converts to JPG.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

        page = browser.new_page(
            viewport={"width": 960, "height": 1700},
            device_scale_factor=2,
        )

        page.set_content(html_content, wait_until="networkidle")

        element = page.query_selector("#newsletter")

        if element:
            png_bytes = element.screenshot(type="png")
        else:
            png_bytes = page.screenshot(type="png", full_page=True)

        browser.close()

    image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    jpg_buffer = io.BytesIO()
    image.save(jpg_buffer, format="JPEG", quality=95, optimize=True)
    return jpg_buffer.getvalue()


def html_preview_component(html_content):
    encoded_html = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")

    iframe_html = f"""
    <iframe
        src="data:text/html;base64,{encoded_html}"
        width="100%"
        height="950"
        style="border: 1px solid #E5E7EB; border-radius: 18px; background: white;"
    ></iframe>
    """

    return iframe_html


# =========================================================
# Session State Defaults
# =========================================================

if "sections" not in st.session_state:
    st.session_state.sections = [
        {
            "category": "People",
            "title": "Team Highlights",
            "body": "Share key updates, milestones, or moments from the team this month.",
            "highlight": "Suggested angle: keep it human, specific, and easy to scan.",
        },
        {
            "category": "Culture",
            "title": "Office Moments",
            "body": "Add office activities, gatherings, celebrations, or cross-team collaboration stories.",
            "highlight": "Suggested angle: make the office feel active, connected, and warm.",
        },
        {
            "category": "Suppliers",
            "title": "Supplier & Project Updates",
            "body": "Summarize supplier visits, project progress, operational insights, or business updates.",
            "highlight": "Suggested angle: focus on what changed and why it matters.",
        },
    ]


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:
    st.title("Newsletter Settings")

    month = st.text_input("Month", value="June 2026")

    main_theme = st.text_input(
        "Main Theme",
        value="People, culture, suppliers, and milestones",
    )

    editor = st.text_input("Editor", value="Luz Lin")

    visual_theme = st.selectbox(
        "Visual Theme",
        ["Classic", "Fresh", "Bold", "Sporty"],
        index=0,
    )

    layout_style = st.selectbox(
        "Layout Style",
        ["Standard", "Compact", "Magazine"],
        index=0,
    )

    theme_mood = {
        "Classic": "Clean, corporate, stable",
        "Fresh": "Light, energetic, people-centered",
        "Bold": "Strong, sharp, high-contrast",
        "Sporty": "Dynamic, active, modern",
    }

    st.caption(f"Theme mood: {theme_mood.get(visual_theme, '')}")

    st.divider()
    st.caption("Prototype Version 3.1")
    st.caption("PDF and JPG export with hero image upload.")


# =========================================================
# Main Editor
# =========================================================

st.title("🇹🇼 LO Taiwan Monthly Pulse Generator")
st.caption("Create a monthly newsletter preview and export it as PDF or JPG.")

if not chromium_ready:
    st.error("Playwright Chromium installation failed.")
    st.code(chromium_error)
    st.stop()


hero_image_data_url = None

left_col, right_col = st.columns([0.95, 1.25], gap="large")

with left_col:
    st.subheader("Hero Section")

    hero_title = st.text_input(
        "Hero Title",
        value="LO Taiwan Monthly Pulse",
    )

    hero_subtitle = st.text_area(
        "Hero Subtitle",
        value="A monthly snapshot of people, culture, supplier updates, and key milestones across LO Taiwan.",
        height=100,
    )

    hero_image_file = st.file_uploader(
        "Hero Image / Badge Image",
        type=["png", "jpg", "jpeg"],
        help="Upload the visual badge or header image for the newsletter.",
    )

    hero_image_data_url = image_to_base64(hero_image_file)

    if hero_image_file is not None:
        st.image(
            hero_image_file,
            caption="Uploaded hero image",
            use_container_width=True,
        )

    st.divider()
    st.subheader("Newsletter Sections")

    section_count = st.number_input(
        "Number of Sections",
        min_value=1,
        max_value=8,
        value=len(st.session_state.sections),
        step=1,
    )

    current_count = len(st.session_state.sections)

    if section_count > current_count:
        for _ in range(section_count - current_count):
            st.session_state.sections.append(
                {
                    "category": "Update",
                    "title": "",
                    "body": "",
                    "highlight": "",
                }
            )

    if section_count < current_count:
        st.session_state.sections = st.session_state.sections[:section_count]

    for i in range(section_count):
        with st.expander(f"Section {i + 1}", expanded=(i == 0)):
            st.session_state.sections[i]["category"] = st.text_input(
                "Category",
                value=st.session_state.sections[i].get("category", ""),
                key=f"category_{i}",
            )

            st.session_state.sections[i]["title"] = st.text_input(
                "Title",
                value=st.session_state.sections[i].get("title", ""),
                key=f"title_{i}",
            )

            st.session_state.sections[i]["body"] = st.text_area(
                "Body",
                value=st.session_state.sections[i].get("body", ""),
                height=140,
                key=f"body_{i}",
            )

            st.session_state.sections[i]["highlight"] = st.text_area(
                "Highlight / Key Message",
                value=st.session_state.sections[i].get("highlight", ""),
                height=80,
                key=f"highlight_{i}",
            )

    if st.button("Clear All Sections"):
        st.session_state.sections = [
            {
                "category": "Update",
                "title": "",
                "body": "",
                "highlight": "",
            }
        ]
        st.rerun()


# =========================================================
# Preview + Export
# =========================================================

html_content = render_newsletter_html(
    month=month,
    main_theme=main_theme,
    editor=editor,
    visual_theme=visual_theme,
    layout_style=layout_style,
    hero_title=hero_title,
    hero_subtitle=hero_subtitle,
    hero_image_data_url=hero_image_data_url,
    sections=st.session_state.sections,
)

with right_col:
    st.subheader("Live Preview")

    st.components.v1.html(
        html_preview_component(html_content),
        height=980,
        scrolling=True,
    )

    st.divider()
    st.subheader("Export")

    filename_base = f"lo-taiwan-monthly-pulse-{month_to_filename(month)}"

    pdf_col, jpg_col = st.columns(2)

    with pdf_col:
        try:
            pdf_bytes = html_to_pdf_bytes(html_content)

            st.download_button(
                label="📄 Download PDF for attachment",
                data=pdf_bytes,
                file_name=f"{filename_base}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        except Exception as e:
            st.error("PDF export failed.")
            st.code(str(e))

    with jpg_col:
        try:
            jpg_bytes = html_to_jpg_bytes(html_content)

            st.download_button(
                label="🖼️ Download JPG for email body",
                data=jpg_bytes,
                file_name=f"{filename_base}.jpg",
                mime="image/jpeg",
                use_container_width=True,
            )

        except Exception as e:
            st.error("JPG export failed.")
            st.code(str(e))

    st.info(
        "Use JPG if you want the newsletter to appear directly in the email body. "
        "Use PDF if you want to send it as an attachment or keep it for archive."
    )
