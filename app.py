import base64
import html
import io
import subprocess
import sys
from typing import List, Dict

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from playwright.sync_api import sync_playwright


# -----------------------------
# Page Config
# -----------------------------

st.set_page_config(
    page_title="LO Taiwan Monthly Pulse Generator",
    page_icon="📰",
    layout="wide",
)


# -----------------------------
# Color Palettes
# -----------------------------

COLOR_PALETTES = {
    "Classic · Black / Blue": {
        "accent": "#111111",
        "accent_2": "#2F5FD0",
        "accent_3": "#F59E0B",
        "accent_text": "#FFFFFF",
        "background": "#FFFFFF",
        "soft_background": "#F6F6F6",
        "divider": "#D8D8D8",
        "text": "#111111",
        "muted": "#666666",
    },
    "Energy · Blue / Orange": {
        "accent": "#1038A8",
        "accent_2": "#FF8A00",
        "accent_3": "#C6FF00",
        "accent_text": "#FFFFFF",
        "background": "#FFFFFF",
        "soft_background": "#F7F9FF",
        "divider": "#D5DDF5",
        "text": "#111111",
        "muted": "#666666",
    },
    "Milestone · Navy / Gold": {
        "accent": "#173B73",
        "accent_2": "#C8A24A",
        "accent_3": "#F3E6BF",
        "accent_text": "#FFFFFF",
        "background": "#FFFFFF",
        "soft_background": "#FAF6EA",
        "divider": "#D8C79A",
        "text": "#111111",
        "muted": "#665F4D",
    },
    "Field Notes · Green / Earth": {
        "accent": "#184E3A",
        "accent_2": "#C96F32",
        "accent_3": "#E7C7A8",
        "accent_text": "#FFFFFF",
        "background": "#FFFFFF",
        "soft_background": "#F5F0EA",
        "divider": "#D8C4B2",
        "text": "#141414",
        "muted": "#6A5A4E",
    },
}


NEWSLETTER_STYLES = {
    "Corporate Classic": {
        "description": "Best for formal monthly recaps, business updates, promotions, and clear office announcements.",
    },
    "Photo Digest": {
        "description": "Best for event recaps, team moments, supplier visits, and photo-heavy months.",
    },
    "Magazine Feature": {
        "description": "Best for one major story, milestone, anniversary, or a hero topic that deserves emphasis.",
    },
    "Field Report": {
        "description": "Best for supplier visits, factory observations, business trips, and field notes.",
    },
}

SECTION_STYLE_OPTIONS = ["Auto"] + list(NEWSLETTER_STYLES.keys())


# -----------------------------
# Playwright Setup
# -----------------------------

@st.cache_resource(show_spinner=False)
def ensure_playwright_chromium():
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


# -----------------------------
# Helper Functions
# -----------------------------

def safe_html_text(text):
    if text is None:
        return ""
    return html.escape(str(text)).replace("\n", "<br>")


def image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode("utf-8")


def image_mime_type(image_name):
    lower_name = image_name.lower()
    if lower_name.endswith(".png"):
        return "image/png"
    if lower_name.endswith(".jpg") or lower_name.endswith(".jpeg"):
        return "image/jpeg"
    return "image/jpeg"


def image_data_url(image):
    mime = image_mime_type(image["name"])
    encoded = image_to_base64(image["bytes"])
    return f"data:{mime};base64,{encoded}"


def newsletter_style_class(newsletter_style):
    return newsletter_style.lower().replace(" ", "-").replace("&", "and")


def infer_section_style(section):
    images = section.get("images", [])
    text = f"{section.get('title', '')} {section.get('content', '')}".lower()
    text_len = len(section.get("content", "").strip())

    field_keywords = [
        "supplier",
        "factory",
        "field",
        "visit",
        "taichung",
        "vendor",
        "observation",
        "material",
        "business update",
    ]
    milestone_keywords = [
        "milestone",
        "anniversary",
        "celebrat",
        "turns",
        "promotion",
        "award",
        "journey",
    ]

    if any(keyword in text for keyword in field_keywords):
        return "Field Report"

    if len(images) >= 4:
        return "Photo Digest"

    if len(images) >= 2 and text_len <= 260:
        return "Photo Digest"

    if len(images) == 1 or any(keyword in text for keyword in milestone_keywords):
        return "Magazine Feature"

    return "Corporate Classic"


def get_section_style(section):
    selected_style = section.get("newsletter_style", "Auto")
    if selected_style == "Auto":
        return infer_section_style(section)
    return selected_style


def get_section_template(section, section_style):
    images = section.get("images", [])
    text_len = len(section.get("content", "").strip())

    if section_style == "Corporate Classic":
        if images:
            return "Side Images"
        return "Brief" if text_len <= 130 else "Text"

    if section_style == "Photo Digest":
        if images:
            return "Gallery"
        return "Brief" if text_len <= 130 else "Text"

    if section_style == "Magazine Feature":
        if images:
            return "Side Images"
        return "Text"

    if section_style == "Field Report":
        if images:
            return "Side Images"
        return "Text"

    if len(images) >= 3:
        return "Gallery"
    if len(images) in [1, 2]:
        return "Side Images"
    if text_len <= 130:
        return "Brief"

    return "Text"


def create_image_figure(image):
    return f"""
    <figure class="image-frame clean-image-frame">
        <img class="section-image" src="{image_data_url(image)}" alt="">
    </figure>
    """


def generate_images_html(images, layout="gallery"):
    if not images:
        return ""

    if len(images) <= 2 or layout == "side-stack":
        tags = "".join(create_image_figure(image) for image in images)
        return f"""
        <div class="side-image-stack">
            {tags}
        </div>
        """

    tags = "".join(create_image_figure(image) for image in images)
    return f"""
    <div class="compact-gallery image-count-{min(len(images), 8)}">
        {tags}
    </div>
    """


def generate_banner_html(month, top_banner_mode, top_banner_file, theme):
    if not top_banner_file:
        return f"""
        <section class="generated-banner fallback-banner">
            <div class="banner-overlay"></div>
            <div class="banner-content">
                <div class="banner-kicker">LO TAIWAN</div>
                <div class="banner-title">{safe_html_text(month).upper()} NEWSLETTER</div>
            </div>
        </section>
        """

    image = {
        "name": top_banner_file.name,
        "bytes": top_banner_file.getvalue(),
    }
    data_url = image_data_url(image)

    if top_banner_mode == "Upload Ready-Made Banner":
        return f"""
        <section class="ready-banner">
            <img src="{data_url}" alt="Newsletter banner">
        </section>
        """

    return f"""
    <section class="generated-banner">
        <img src="{data_url}" alt="Newsletter banner background">
        <div class="banner-overlay"></div>
        <div class="banner-content">
            <div class="banner-kicker">LO TAIWAN</div>
            <div class="banner-title">{safe_html_text(month).upper()} NEWSLETTER</div>
        </div>
    </section>
    """


# -----------------------------
# Newsletter Builders
# -----------------------------

def build_issue_overview(sections, theme):
    if not sections:
        return ""

    items = ""

    for index, section in enumerate(sections, start=1):
        title = safe_html_text(section.get("title", ""))
        items += f"""
        <div class="issue-item">
            <div class="issue-number">{index}</div>
            <div class="issue-title">{title}</div>
        </div>
        """

    return f"""
    <section class="issue-overview">
        <div class="issue-header">
            <h2 class="issue-heading">In This Issue</h2>
            <div class="issue-subtitle">A quick guide to this month’s key stories.</div>
        </div>
        <div class="issue-list">
            {items}
        </div>
    </section>
    """


def generate_section_html(section, index):
    section_style = get_section_style(section)
    template = get_section_template(section, section_style)

    style_class = newsletter_style_class(section_style)
    title = safe_html_text(section.get("title", ""))
    content = safe_html_text(section.get("content", ""))
    images = section.get("images", [])

    if template == "Brief":
        return f"""
        <section class="section-card brief-card style-{style_class}">
            <h2 class="section-title">{title}</h2>
            <div class="section-content brief-content">{content}</div>
        </section>
        """

    if template == "Text":
        return f"""
        <section class="section-card text-card style-{style_class}">
            <h2 class="section-title">{title}</h2>
            <div class="section-content full-width-text">{content}</div>
        </section>
        """

    if template == "Side Images":
        images_html = generate_images_html(images, layout="side-stack")

        return f"""
        <section class="section-card side-layout-card style-{style_class}">
            <div class="side-copy">
                <h2 class="section-title">{title}</h2>
                <div class="section-content">{content}</div>
            </div>
            <div class="side-media">
                {images_html}
            </div>
        </section>
        """

    if template == "Gallery":
        images_html = generate_images_html(images, layout="gallery")

        return f"""
        <section class="section-card gallery-card style-{style_class}">
            <h2 class="section-title">{title}</h2>
            <div class="section-content gallery-intro">{content}</div>
            {images_html}
        </section>
        """

    return f"""
    <section class="section-card text-card style-{style_class}">
        <h2 class="section-title">{title}</h2>
        <div class="section-content full-width-text">{content}</div>
    </section>
    """


def build_sections_html(sections):
    section_html = ""

    for index, section in enumerate(sections, start=1):
        section_html += generate_section_html(section, index)

    if section_html:
        return section_html

    return """
    <section class="section-card text-card">
        <h2 class="section-title">Your newsletter content will appear here</h2>
        <div class="section-content">
            Add sections from the editor panel to generate the newsletter draft.
        </div>
    </section>
    """


def generate_newsletter_html(
    month,
    editor,
    sections,
    color_palette,
    top_banner_mode,
    top_banner_file,
):
    theme = COLOR_PALETTES[color_palette]

    banner_html = generate_banner_html(
        month=month,
        top_banner_mode=top_banner_mode,
        top_banner_file=top_banner_file,
        theme=theme,
    )

    issue_html = build_issue_overview(sections, theme)
    sections_html = build_sections_html(sections)
    css = generate_css(theme)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{css}</style>
    </head>
    <body>
        <main class="page">
            {banner_html}
            {issue_html}
            <section class="sections-wrap">
                {sections_html}
            </section>
            <div class="footer">
                Generated by LO Taiwan Monthly Pulse Generator Prototype. Human review is required before publishing.
            </div>
        </main>
    </body>
    </html>
    """


# -----------------------------
# CSS
# -----------------------------

def generate_css(theme):
    return f"""
    @page {{ margin: 0; }}

    * {{
        box-sizing: border-box;
    }}

    html, body {{
        margin: 0;
        padding: 0;
        background: #ffffff;
        color: {theme["text"]};
        font-family: Arial, Helvetica, sans-serif;
    }}

    body {{
        padding: 0;
    }}

    .page {{
        width: 100%;
        max-width: 900px;
        margin: 0 auto;
        padding: 18px 28px 22px;
        background: #ffffff;
    }}

    .ready-banner,
    .generated-banner {{
        width: 100%;
        height: 210px;
        border-radius: 20px;
        overflow: hidden;
        margin-bottom: 28px;
        position: relative;
        border: 1px solid {theme["divider"]};
        background: {theme["soft_background"]};
    }}

    .ready-banner img {{
        width: 100%;
        height: 100%;
        object-fit: contain;
        display: block;
        background: #ffffff;
    }}

    .generated-banner img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }}

    .fallback-banner {{
        background: linear-gradient(135deg, {theme["accent"]} 0%, {theme["accent_2"]} 100%);
    }}

    .banner-overlay {{
        position: absolute;
        inset: 0;
        background: linear-gradient(
            90deg,
            rgba(0, 0, 0, 0.72),
            rgba(0, 0, 0, 0.22),
            rgba(0, 0, 0, 0.05)
        );
    }}

    .banner-content {{
        position: absolute;
        left: 38px;
        bottom: 34px;
        color: white;
    }}

    .banner-kicker {{
        font-size: 48px;
        line-height: 0.95;
        font-weight: 950;
        letter-spacing: -1.5px;
        text-transform: uppercase;
    }}

    .banner-title {{
        margin-top: 10px;
        font-size: 26px;
        font-weight: 900;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}

    .issue-overview {{
        margin-bottom: 28px;
        border-top: 2px solid {theme["accent"]};
        padding-top: 16px;
    }}

    .issue-heading {{
        font-size: 26px;
        margin: 0 0 5px;
        letter-spacing: -0.5px;
    }}

    .issue-subtitle {{
        color: {theme["muted"]};
        font-size: 12px;
        font-weight: 750;
        margin-bottom: 14px;
    }}

    .issue-list {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
    }}

    .issue-item {{
        display: grid;
        grid-template-columns: 34px 1fr;
        gap: 12px;
        align-items: center;
        background: #F7F7F7;
        border: 1px solid {theme["divider"]};
        border-left: 5px solid {theme["accent"]};
        border-radius: 12px;
        padding: 13px 14px;
    }}

    .issue-number {{
        width: 30px;
        height: 30px;
        border-radius: 999px;
        background: {theme["accent"]};
        color: {theme["accent_text"]};
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        font-weight: 950;
    }}

    .issue-title {{
        font-size: 14px;
        font-weight: 950;
        line-height: 1.25;
    }}

    .sections-wrap {{
        width: 100%;
    }}

    .section-card {{
        background: {theme["background"]};
        border: 1px solid {theme["divider"]};
        border-top: 6px solid {theme["accent_2"]};
        border-radius: 18px;
        padding: 24px 26px;
        margin-bottom: 24px;
        page-break-inside: avoid;
        overflow: hidden;
    }}

    .section-title {{
        font-size: 30px;
        font-weight: 950;
        line-height: 1.08;
        letter-spacing: -0.7px;
        margin: 0 0 15px;
        color: {theme["text"]};
    }}

    .section-content {{
        font-size: 14px;
        line-height: 1.58;
        font-weight: 500;
        margin: 0;
        color: {theme["text"]};
    }}

    .gallery-intro {{
        margin-bottom: 14px;
        color: {theme["muted"]};
    }}

    .full-width-text {{
        width: 100%;
        max-width: none;
    }}

    .brief-card {{
        background: {theme["soft_background"]};
    }}

    .brief-card .section-title {{
        font-size: 22px;
        margin-bottom: 8px;
    }}

    .brief-content {{
        font-size: 13px;
    }}

    .side-layout-card {{
        display: grid;
        grid-template-columns: 0.95fr 1.05fr;
        gap: 26px;
        align-items: start;
    }}

    .side-copy {{
        min-width: 0;
    }}

    .side-media {{
        min-width: 0;
    }}

    .side-image-stack {{
        display: flex;
        flex-direction: column;
        gap: 14px;
    }}

    .compact-gallery {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
        margin-top: 14px;
        align-items: start;
    }}

    .image-frame {{
        width: 100%;
        margin: 0;
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid {theme["divider"]};
        background: #ffffff;
        position: relative;
    }}

    .image-frame::before {{
        display: none !important;
        content: none !important;
    }}

    .section-image {{
        width: 100%;
        height: auto;
        display: block;
        object-fit: contain;
        position: relative;
        z-index: 1;
        background: #ffffff;
    }}

    .side-image-stack .image-frame,
    .compact-gallery .image-frame {{
        background: #ffffff;
    }}

    .side-image-stack .section-image,
    .compact-gallery .section-image {{
        width: 100%;
        height: auto;
        object-fit: contain;
    }}

    .style-corporate-classic {{
        border-top-color: {theme["accent"]};
    }}

    .style-corporate-classic .section-title {{
        font-size: 28px;
    }}

    .style-photo-digest {{
        border-top-color: {theme["accent_2"]};
        background: #ffffff;
    }}

    .style-photo-digest .section-title {{
        font-size: 28px;
    }}

    .style-magazine-feature {{
        border-top-color: {theme["accent_2"]};
    }}

    .style-magazine-feature.side-layout-card {{
        background: {theme["accent"]};
        color: white;
    }}

    .style-magazine-feature.side-layout-card .section-title,
    .style-magazine-feature.side-layout-card .section-content {{
        color: white;
    }}

    .style-field-report {{
        border-top-color: {theme["accent_2"]};
        background: {theme["soft_background"]};
    }}

    .style-field-report .section-title {{
        font-size: 28px;
    }}

    .footer {{
        color: {theme["muted"]};
        font-size: 9px;
        line-height: 1.4;
        margin-top: 22px;
        border-top: 1px solid {theme["divider"]};
        padding-top: 12px;
    }}

    @media screen {{
        body {{
            padding: 16px;
        }}
    }}

    @media print {{
        html, body {{
            width: 100%;
            background: #ffffff;
        }}

        .page {{
            max-width: none;
            padding: 18px 28px 22px;
        }}
    }}

    @media screen and (max-width: 720px) {{
        .page {{
            padding: 16px;
        }}

        .side-layout-card {{
            display: block;
        }}

        .side-media {{
            margin-top: 16px;
        }}

        .issue-list {{
            grid-template-columns: 1fr;
        }}

        .compact-gallery {{
            grid-template-columns: 1fr;
        }}

        .banner-kicker {{
            font-size: 34px;
        }}

        .banner-title {{
            font-size: 20px;
        }}
    }}
    """


# -----------------------------
# Export Functions
# -----------------------------

def html_to_pdf_bytes(newsletter_html):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

        page = browser.new_page(
            viewport={"width": 900, "height": 1300},
            device_scale_factor=1,
        )

        page.set_content(newsletter_html, wait_until="networkidle")

        document_height = page.evaluate(
            """
            () => Math.max(
                document.body.scrollHeight,
                document.body.offsetHeight,
                document.documentElement.clientHeight,
                document.documentElement.scrollHeight,
                document.documentElement.offsetHeight
            )
            """
        )

        pdf_bytes = page.pdf(
            width="900px",
            height=f"{document_height + 40}px",
            print_background=True,
            margin={
                "top": "0px",
                "right": "0px",
                "bottom": "0px",
                "left": "0px",
            },
        )

        browser.close()

    return pdf_bytes


def html_to_jpg_bytes(newsletter_html):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

        page = browser.new_page(
            viewport={"width": 900, "height": 1500},
            device_scale_factor=2,
        )

        page.set_content(newsletter_html, wait_until="networkidle")

        element = page.query_selector(".page")

        if element:
            png_bytes = element.screenshot(type="png")
        else:
            png_bytes = page.screenshot(type="png", full_page=True)

        browser.close()

    image = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    jpg_buffer = io.BytesIO()
    image.save(jpg_buffer, format="JPEG", quality=95, optimize=True)

    return jpg_buffer.getvalue()


# -----------------------------
# App UI
# -----------------------------

st.title("LO Taiwan Monthly Pulse Generator")
st.caption("Create a monthly newsletter preview and export it as PDF or JPG.")

if not chromium_ready:
    st.error("Playwright Chromium installation failed.")
    st.code(chromium_error)
    st.stop()


# Sidebar
st.sidebar.header("Newsletter Settings")

newsletter_month = st.sidebar.text_input("Month", "June 2026")
editor_name = st.sidebar.text_input("Editor", "Luz Lin")

color_palette = st.sidebar.selectbox(
    "Color Palette",
    list(COLOR_PALETTES.keys()),
)

palette = COLOR_PALETTES[color_palette]

st.sidebar.markdown(
    f"""
    <div style="display:flex; gap:6px; margin:8px 0 14px;">
        <div style="width:28px; height:16px; border-radius:4px; background:{palette['accent']};"></div>
        <div style="width:28px; height:16px; border-radius:4px; background:{palette['accent_2']};"></div>
        <div style="width:28px; height:16px; border-radius:4px; background:{palette['accent_3']};"></div>
        <div style="width:28px; height:16px; border-radius:4px; background:{palette['soft_background']}; border:1px solid {palette['divider']};"></div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar.expander("Which Newsletter Style should I use?"):
    st.caption(
        "Each section can use its own style. Select Auto if you want the app to decide based on text and images."
    )

    for style_name, style_info in NEWSLETTER_STYLES.items():
        st.markdown(f"**{style_name}**")
        st.caption(style_info["description"])

st.sidebar.markdown("---")
st.sidebar.write("Prototype Version 3.5")
st.sidebar.caption("Clean image backgrounds, side image layout, and section-by-section styles.")


# Session State
if "sections" not in st.session_state:
    st.session_state.sections = []

if "form_counter" not in st.session_state:
    st.session_state.form_counter = 0


# Banner
with st.expander("Banner Settings", expanded=True):
    top_banner_mode = st.radio(
        "Banner Mode",
        ["Generate Banner from Background Photo", "Upload Ready-Made Banner"],
        horizontal=True,
    )

    top_banner_file = st.file_uploader(
        "Upload banner image or background photo",
        type=["png", "jpg", "jpeg"],
        key="top_banner_upload",
        help="Use a background photo to auto-generate a branded banner, or upload a ready-made banner.",
    )

    if top_banner_file is not None:
        st.image(
            top_banner_file,
            caption="Banner image preview",
            use_container_width=True,
        )


# Input Form
st.header("1. Add Monthly Update")

with st.form(f"update_form_{st.session_state.form_counter}"):
    title = st.text_input(
        "Section Title",
        placeholder="Example: Promotions",
    )

    raw_content = st.text_area(
        "Raw Content",
        placeholder="Paste or type the original update here...",
        height=160,
    )

    section_newsletter_style = st.selectbox(
        "Newsletter Style for this section",
        SECTION_STYLE_OPTIONS,
        help="Choose Auto, or select the newsletter style that best matches this section's content.",
    )

    uploaded_images = st.file_uploader(
        "Upload images for this section",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )

    submitted = st.form_submit_button("Add Section")

    if submitted:
        if title and raw_content:
            images = []

            if uploaded_images:
                for uploaded_image in uploaded_images:
                    images.append(
                        {
                            "name": uploaded_image.name,
                            "bytes": uploaded_image.getvalue(),
                        }
                    )

            st.session_state.sections.append(
                {
                    "title": title,
                    "content": raw_content,
                    "newsletter_style": section_newsletter_style,
                    "images": images,
                }
            )

            st.session_state.form_counter += 1
            st.success("Section added successfully!")
            st.rerun()

        else:
            st.warning("Please enter both a title and content.")


# Preview
st.header("2. Newsletter Preview")

if not st.session_state.sections:
    st.info("Add at least one section to generate the newsletter preview.")

else:
    col1, col2 = st.columns([0.62, 1.78])

    with col1:
        st.subheader("Added Sections")

        for i, section in enumerate(st.session_state.sections):
            section_style = get_section_style(section)
            template = get_section_template(section, section_style)

            with st.expander(f"{i + 1}. {section['title']}"):
                st.caption(f"Newsletter Style: {section_style} · Layout: {template}")
                st.write(section["content"])

                images = section.get("images", [])
                st.caption(f"Images: {len(images)} uploaded" if images else "Images: None")

                if st.button(f"Delete Section {i + 1}", key=f"delete_{i}"):
                    st.session_state.sections.pop(i)
                    st.rerun()

    with col2:
        newsletter_html = generate_newsletter_html(
            newsletter_month,
            editor_name,
            st.session_state.sections,
            color_palette,
            top_banner_mode,
            top_banner_file,
        )

        components.html(
            newsletter_html,
            height=1120,
            scrolling=True,
        )


# Export
st.markdown("---")

if st.session_state.sections:
    newsletter_html = generate_newsletter_html(
        newsletter_month,
        editor_name,
        st.session_state.sections,
        color_palette,
        top_banner_mode,
        top_banner_file,
    )

    pdf_col, jpg_col = st.columns(2)

    file_base = f"LO_Taiwan_Monthly_Pulse_{newsletter_month.replace(' ', '_')}_Mixed_Styles"

    with pdf_col:
        try:
            pdf_bytes = html_to_pdf_bytes(newsletter_html)

            st.download_button(
                label="Download Newsletter PDF",
                data=pdf_bytes,
                file_name=f"{file_base}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        except Exception as e:
            st.error("PDF export failed. Please make sure Playwright and Chromium are installed.")
            st.caption(str(e))

    with jpg_col:
        try:
            jpg_bytes = html_to_jpg_bytes(newsletter_html)

            st.download_button(
                label="Download Newsletter JPG",
                data=jpg_bytes,
                file_name=f"{file_base}.jpg",
                mime="image/jpeg",
                use_container_width=True,
            )

        except Exception as e:
            st.error("JPG export failed.")
            st.caption(str(e))


if st.button("Clear All Sections"):
    st.session_state.sections = []
    st.session_state.form_counter += 1
    st.rerun()
