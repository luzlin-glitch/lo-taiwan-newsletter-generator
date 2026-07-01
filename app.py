import streamlit as st
import streamlit.components.v1 as components

import base64
import html
import io
import subprocess
import sys

from PIL import Image
from playwright.sync_api import sync_playwright


# -----------------------------
# Page Config
# -----------------------------

st.set_page_config(
    page_title="LO Taiwan Monthly Pulse Generator",
    page_icon="📰",
    layout="wide"
)


# -----------------------------
# Playwright / Chromium Setup
# -----------------------------

@st.cache_resource(show_spinner=False)
def ensure_playwright_chromium():
    """
    Streamlit Cloud may install the Python Playwright package
    without downloading the Chromium browser binary.
    This keeps PDF/JPG export working after deployment.
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


# -----------------------------
# Visual Theme Presets
# -----------------------------

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
        "description": "Clean, corporate, stable"
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
        "description": "Sporty, active, bold"
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
        "description": "Premium, celebratory, memorable"
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
        "description": "Warm, people-focused, friendly"
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
        "description": "Travel, supplier visit, documentary"
    }
}


DEFAULT_BADGES = {
    "People": "People Spotlight",
    "Milestone": "Milestone Moment",
    "Supplier": "From the Field",
    "Culture": "Team Moments",
    "Coming Up": "Next Up"
}


# -----------------------------
# App Title
# -----------------------------

st.title("LO Taiwan Monthly Pulse Generator")
st.caption("From raw monthly updates to a branded newsletter draft.")


# -----------------------------
# Sidebar Settings
# -----------------------------

st.sidebar.header("Newsletter Settings")

newsletter_month = st.sidebar.text_input("Month", "June 2026")

main_theme = st.sidebar.text_input(
    "Main Theme",
    "People, culture, suppliers, and milestones"
)

editor_name = st.sidebar.text_input("Editor", "Luz Lin")

visual_theme = st.sidebar.selectbox(
    "Visual Theme",
    ["Classic", "Energy", "Milestone", "People", "Field Notes"]
)

layout_style = st.sidebar.selectbox(
    "Layout Style",
    ["Standard", "Magazine", "Gallery", "Field Report"]
)

theme = THEMES[visual_theme]

st.sidebar.caption(f"Theme mood: {theme['description']}")

st.sidebar.markdown("---")
st.sidebar.write("Prototype Version 2.3")
st.sidebar.caption("Continuous newsletter PDF export.")


# -----------------------------
# Session State
# -----------------------------

if "sections" not in st.session_state:
    st.session_state.sections = []

if "form_counter" not in st.session_state:
    st.session_state.form_counter = 0


# -----------------------------
# Helper Functions
# -----------------------------

def polish_content(content, tone):
    if tone == "Warm and professional":
        return f"We are pleased to share the following update. {content}"

    if tone == "Fun and energetic":
        return f"Here is a highlight worth celebrating this month! {content}"

    if tone == "Concise and business-like":
        return f"Key update: {content}"

    return content


def get_badge_text(section):
    custom_badge = section.get("badge_label", "").strip()

    if custom_badge:
        return custom_badge

    return DEFAULT_BADGES.get(section["category"], section["category"])


def get_final_content(section):
    if section.get("use_polish", False):
        return polish_content(section["content"], section["tone"])

    return section["content"]


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
    return html.escape(text).replace("\n", "<br>")


def title_case_by_theme(title, theme_style):
    if theme_style["title_transform"] == "uppercase":
        return title.upper()

    return title


def generate_images_html(images, layout="grid"):
    if not images:
        return ""

    image_tags = []

    for image in images:
        mime = image_mime_type(image["name"])
        encoded = image_to_base64(image["bytes"])

        image_tags.append(
            f"""
            <figure class="image-frame">
                <img
                    class="section-image"
                    src="data:{mime};base64,{encoded}"
                    alt=""
                >
            </figure>
            """
        )

    if layout == "hero":
        first_image = image_tags[0]
        remaining_images = image_tags[1:]

        remaining_html = ""

        if remaining_images:
            remaining_html = f"""
            <div class="image-grid">
                {''.join(remaining_images)}
            </div>
            """

        return f"""
        <div class="hero-image-wrap">
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

    return f"""
    <div class="image-grid">
        {''.join(image_tags)}
    </div>
    """


def generate_section_html(section, theme_style, layout_style):
    badge_text = safe_html_text(get_badge_text(section))
    title = safe_html_text(title_case_by_theme(section["title"], theme_style))
    content = safe_html_text(get_final_content(section))
    images = section.get("images", [])

    if layout_style == "Gallery":
        images_html = generate_images_html(images, layout="grid")

        return f"""
        <section class="section-card">
            <div class="badge">{badge_text}</div>
            <h2 class="section-title">{title}</h2>
            {images_html}
            <div class="section-content after-image">{content}</div>
        </section>
        """

    if layout_style == "Magazine":
        images_html = generate_images_html(images, layout="hero")

        return f"""
        <section class="section-card">
            <div class="badge">{badge_text}</div>
            <h2 class="section-title">{title}</h2>
            {images_html}
            <div class="section-content after-image">{content}</div>
        </section>
        """

    if layout_style == "Field Report" and images:
        images_html = generate_images_html(images, layout="single-column")

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

    images_html = generate_images_html(images, layout="grid")

    return f"""
    <section class="section-card">
        <div class="badge">{badge_text}</div>
        <h2 class="section-title">{title}</h2>
        <div class="section-content">{content}</div>
        {images_html}
    </section>
    """


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


def generate_top_banner_html(top_banner_image):
    """
    Optional top banner/badge image.
    Uses the original uploaded ratio and avoids cropping, so the badge will not be forced into a fixed box.
    """
    if not top_banner_image:
        return ""

    mime = image_mime_type(top_banner_image["name"])
    encoded = image_to_base64(top_banner_image["bytes"])

    return f"""
    <section class="top-banner">
        <img
            class="top-banner-image"
            src="data:{mime};base64,{encoded}"
            alt="LO Taiwan newsletter banner"
        >
    </section>
    """


def generate_newsletter_html(month, main_theme, editor, sections, visual_theme, layout_style, top_banner_image=None):
    theme_style = THEMES[visual_theme]
    top_banner_html = generate_top_banner_html(top_banner_image)

    issue_items_html = ""

    for index, section in enumerate(sections, start=1):
        issue_badge = safe_html_text(get_badge_text(section))
        issue_title = safe_html_text(section["title"])

        issue_items_html += f"""
        <div class="issue-item">
            <div class="issue-number">{index}</div>
            <div class="issue-text">
                <div class="issue-badge">{issue_badge}</div>
                <div class="issue-title">{issue_title}</div>
            </div>
        </div>
        """

    section_html = ""

    for section in sections:
        section_html += generate_section_html(section, theme_style, layout_style)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">

        <style>
            @page {{
                margin: 0;
            }}

            * {{
                box-sizing: border-box;
            }}

            html, body {{
                margin: 0;
                padding: 0;
                background: #ffffff;
                color: #111111;
                font-family: Arial, Helvetica, sans-serif;
            }}

            body {{
                padding: 0;
            }}

            .page {{
                width: 100%;
                max-width: 820px;
                margin: 0 auto;
                padding: 18px 28px 22px 28px;
            }}


            .top-banner {{
                width: 100%;
                margin: 0 0 18px 0;
                border: 1px solid {theme_style["divider"]};
                border-radius: 8px;
                overflow: hidden;
                background: #ffffff;
            }}

            .top-banner-image {{
                width: 100%;
                height: auto;
                max-height: 160px;
                object-fit: contain;
                display: block;
            }}

            .cover {{
                background: {theme_style["soft_background"]};
                border: 1px solid {theme_style["divider"]};
                border-left: 9px solid {theme_style["accent"]};
                border-radius: 16px;
                padding: 28px 34px;
                margin-bottom: 26px;
            }}

            .cover-title {{
                font-size: 36px;
                line-height: 1.05;
                font-weight: 950;
                margin: 0 0 14px 0;
                letter-spacing: -1px;
            }}

            .cover-month {{
                font-size: 15px;
                font-weight: 850;
                color: #555555;
                margin-bottom: 18px;
            }}

            .cover-phrase {{
                font-size: 16px;
                font-weight: 800;
                line-height: 1.35;
                margin-bottom: 16px;
            }}

            .cover-meta {{
                font-size: 10.5px;
                line-height: 1.4;
                color: #666666;
                font-weight: 700;
            }}

            .issue-overview {{
                margin-bottom: 30px;
            }}

            .issue-header {{
                margin-bottom: 14px;
            }}

            .issue-heading {{
                font-size: 22px;
                font-weight: 950;
                margin: 0 0 5px 0;
                letter-spacing: -0.3px;
            }}

            .issue-subtitle {{
                font-size: 11px;
                line-height: 1.4;
                color: #666666;
                font-weight: 700;
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
                background: {theme_style["soft_background"]};
                border: 1px solid {theme_style["divider"]};
                border-left: 5px solid {theme_style["accent"]};
                border-radius: 12px;
                padding: 13px 14px;
            }}

            .issue-number {{
                width: 30px;
                height: 30px;
                border-radius: 999px;
                background: {theme_style["accent"]};
                color: {theme_style["accent_text"]};
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 13px;
                font-weight: 950;
            }}

            .issue-badge {{
                font-size: 9px;
                line-height: 1.2;
                color: #666666;
                font-weight: 900;
                letter-spacing: 0.4px;
                text-transform: uppercase;
                margin-bottom: 3px;
            }}

            .issue-title {{
                font-size: 14px;
                line-height: 1.3;
                font-weight: 900;
                color: #111111;
            }}

            .section-card {{
                border: 1px solid {theme_style["divider"]};
                border-top: 6px solid {theme_style["accent"]};
                border-radius: 16px;
                padding: 24px 26px 24px 26px;
                margin-bottom: 24px;
                background: {theme_style["background"]};
            }}

            .badge {{
                {get_badge_css(theme_style)}
            }}

            .section-title {{
                font-size: 31px;
                font-weight: 950;
                line-height: 1.06;
                letter-spacing: -0.7px;
                margin: 0 0 16px 0;
                text-transform: {theme_style["title_transform"]};
            }}

            .section-content {{
                font-size: 14px;
                line-height: 1.55;
                font-weight: 500;
                margin: 0 0 16px 0;
            }}

            .section-content.after-image {{
                margin-top: 14px;
            }}

            .image-grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 14px;
                margin-top: 12px;
                align-items: start;
            }}

            .hero-image-wrap {{
                margin: 8px 0 14px 0;
            }}

            .image-frame {{
                width: 100%;
                margin: 0;
                border-radius: 12px;
                overflow: hidden;
                border: 1px solid {theme_style["divider"]};
                background: transparent;
            }}

            .section-image {{
                width: 100%;
                height: auto;
                display: block;
            }}

            .image-column {{
                display: flex;
                flex-direction: column;
                gap: 12px;
            }}

            .field-report-layout {{
                display: grid;
                grid-template-columns: 1.12fr 0.88fr;
                gap: 22px;
                align-items: start;
            }}

            .field-report-text .section-content {{
                margin-bottom: 0;
            }}

            .footer {{
                color: #666666;
                font-size: 9px;
                line-height: 1.4;
                margin-top: 22px;
                border-top: 1px solid {theme_style["divider"]};
                padding-top: 12px;
            }}

            @media screen {{
                body {{
                    padding: 16px;
                }}

                .page {{
                    max-width: 820px;
                }}
            }}

            @media print {{
                html, body {{
                    width: 100%;
                    background: #ffffff;
                }}

                .page {{
                    max-width: none;
                    padding: 18px 28px 22px 28px;
                }}
            }}

            @media screen and (max-width: 720px) {{
                .page {{
                    padding: 16px;
                }}

                .cover {{
                    padding: 24px;
                }}

                .cover-title {{
                    font-size: 30px;
                }}

                .issue-list {{
                    grid-template-columns: 1fr;
                }}

                .image-grid {{
                    grid-template-columns: 1fr;
                }}

                .field-report-layout {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>

    <body>
        <main class="page" id="newsletter">
            {top_banner_html}

            <section class="cover">
                <h1 class="cover-title">LO Taiwan Monthly Pulse</h1>
                <div class="cover-month">{safe_html_text(month)} Edition</div>
                <div class="cover-phrase">{safe_html_text(theme_style["cover_phrase"])}</div>
                <div class="cover-meta">
                    Editor: {safe_html_text(editor)}
                </div>
            </section>

            <section class="issue-overview">
                <div class="issue-header">
                    <h2 class="issue-heading">In This Issue</h2>
                    <div class="issue-subtitle">A quick guide to this month’s key stories.</div>
                </div>

                <div class="issue-list">
                    {issue_items_html}
                </div>
            </section>

            {section_html}

            <div class="footer">
                Generated by LO Taiwan Monthly Pulse Generator Prototype. Human review is required before publishing.
            </div>
        </main>
    </body>
    </html>
    """


def html_to_pdf_bytes(newsletter_html):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        page = browser.new_page(
            viewport={
                "width": 794,
                "height": 1123
            },
            device_scale_factor=1
        )

        page.set_content(newsletter_html, wait_until="networkidle")

        document_height = page.evaluate(
            """
            () => {
                const body = document.body;
                const html = document.documentElement;

                return Math.max(
                    body.scrollHeight,
                    body.offsetHeight,
                    html.clientHeight,
                    html.scrollHeight,
                    html.offsetHeight
                );
            }
            """
        )

        pdf_bytes = page.pdf(
            width="794px",
            height=f"{document_height + 40}px",
            print_background=True,
            margin={
                "top": "0px",
                "right": "0px",
                "bottom": "0px",
                "left": "0px"
            }
        )

        browser.close()

    return pdf_bytes


def html_to_jpg_bytes(newsletter_html):
    """
    Export the same newsletter HTML as JPG.
    This is useful for putting the newsletter directly inside an email body.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        page = browser.new_page(
            viewport={
                "width": 794,
                "height": 1400
            },
            device_scale_factor=2
        )

        page.set_content(newsletter_html, wait_until="networkidle")

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


# -----------------------------
# Runtime Check
# -----------------------------

if not chromium_ready:
    st.error("Playwright Chromium installation failed.")
    st.code(chromium_error)
    st.stop()


# -----------------------------
# Top Banner / Badge Upload
# -----------------------------

st.header("0. Top Badge / Banner")

top_banner_file = st.file_uploader(
    "Upload optional top badge / banner image",
    type=["png", "jpg", "jpeg"],
    help="Use a horizontal banner image. The preview/export will keep the image ratio and avoid cropping.",
    key="top_banner_file"
)

top_banner_image = None

if top_banner_file is not None:
    top_banner_image = {
        "name": top_banner_file.name,
        "bytes": top_banner_file.getvalue()
    }
    st.image(top_banner_file, caption="Top badge / banner preview", use_container_width=True)


# -----------------------------
# Input Form
# -----------------------------

st.header("1. Add Monthly Update")

with st.form(f"update_form_{st.session_state.form_counter}"):
    category = st.selectbox(
        "Category",
        ["People", "Milestone", "Supplier", "Culture", "Coming Up"]
    )

    default_badge = DEFAULT_BADGES.get(category, category)

    badge_label = st.text_input(
        "Badge Label",
        value="",
        placeholder=f"Example: {default_badge}, Big Moves, From the Field, Team Energy"
    )

    title = st.text_input(
        "Section Title",
        placeholder="Example: Promotions"
    )

    raw_content = st.text_area(
        "Raw Content",
        placeholder="Paste or type the original update here...",
        height=160
    )

    tone = st.selectbox(
        "Newsletter Tone",
        ["Warm and professional", "Fun and energetic", "Concise and business-like"]
    )

    use_polish = st.checkbox("Use AI-style polish for this section")

    uploaded_images = st.file_uploader(
        "Upload images for this section",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    submitted = st.form_submit_button("Add Section")

    if submitted:
        if title and raw_content:
            images = []

            if uploaded_images:
                for uploaded_image in uploaded_images:
                    images.append({
                        "name": uploaded_image.name,
                        "bytes": uploaded_image.getvalue()
                    })

            st.session_state.sections.append({
                "category": category,
                "badge_label": badge_label.strip(),
                "title": title,
                "content": raw_content,
                "tone": tone,
                "use_polish": use_polish,
                "images": images
            })

            st.session_state.form_counter += 1
            st.success("Section added successfully!")
            st.rerun()

        else:
            st.warning("Please enter both a title and content.")


# -----------------------------
# Preview
# -----------------------------

st.header("2. Newsletter Preview")

if len(st.session_state.sections) == 0:
    st.info("Add at least one section to generate the newsletter preview.")

else:
    col1, col2 = st.columns([0.65, 1.75])

    with col1:
        st.subheader("Added Sections")

        for i, section in enumerate(st.session_state.sections):
            badge_text = get_badge_text(section)

            with st.expander(f"{i + 1}. {section['category']} — {section['title']}"):
                st.caption(f"Badge: {badge_text}")
                st.write(section["content"])
                st.caption(f"Tone: {section['tone']}")

                if section.get("use_polish", False):
                    st.caption("Polish: On")
                else:
                    st.caption("Polish: Off")

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

        newsletter_html = generate_newsletter_html(
            newsletter_month,
            main_theme,
            editor_name,
            st.session_state.sections,
            visual_theme,
            layout_style,
            top_banner_image
        )

        components.html(
            newsletter_html,
            height=1100,
            scrolling=True
        )


# -----------------------------
# Export and Clear Buttons
# -----------------------------

st.markdown("---")

if st.session_state.sections:
    newsletter_html = generate_newsletter_html(
        newsletter_month,
        main_theme,
        editor_name,
        st.session_state.sections,
        visual_theme,
        layout_style,
        top_banner_image
    )

    file_base = f"LO_Taiwan_Monthly_Pulse_{newsletter_month.replace(' ', '_')}_{visual_theme}_{layout_style}"

    export_col_pdf, export_col_jpg = st.columns(2)

    with export_col_pdf:
        try:
            pdf_bytes = html_to_pdf_bytes(newsletter_html)

            st.download_button(
                label="Download Newsletter PDF",
                data=pdf_bytes,
                file_name=f"{file_base}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        except Exception as e:
            st.error("PDF export failed. Please make sure Playwright and Chromium are installed.")
            st.code("py -m pip install playwright\npy -m playwright install chromium")
            st.caption(str(e))

    with export_col_jpg:
        try:
            jpg_bytes = html_to_jpg_bytes(newsletter_html)

            st.download_button(
                label="Download Newsletter JPG",
                data=jpg_bytes,
                file_name=f"{file_base}.jpg",
                mime="image/jpeg",
                use_container_width=True
            )

        except Exception as e:
            st.error("JPG export failed. Please make sure Playwright and Chromium are installed.")
            st.code("py -m pip install playwright\npy -m playwright install chromium")
            st.caption(str(e))

    st.info("Use JPG if you want the newsletter to appear directly in the email body. Use PDF if you want to send it as an attachment or archive copy.")

if st.button("Clear All Sections"):
    st.session_state.sections = []
    st.session_state.form_counter += 1
    st.rerun()