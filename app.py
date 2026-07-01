import base64
import html
import io
import subprocess
import sys
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
# Utility Functions
# =========================================================

def safe_text(value):
    if value is None:
        return ""
    return html.escape(str(value))


def month_to_filename(month_text):
    cleaned = month_text.lower().replace(" ", "-").replace("/", "-")
    cleaned = "".join(char for char in cleaned if char.isalnum() or char in ["-", "_"])
    return cleaned or "newsletter"


def uploaded_image_to_data_url(uploaded_file):
    if uploaded_file is None:
        return None

    bytes_data = uploaded_file.getvalue()
    encoded = base64.b64encode(bytes_data).decode("utf-8")
    file_type = uploaded_file.type

    return f"data:{file_type};base64,{encoded}"


def uploaded_images_to_data_urls(uploaded_files):
    if not uploaded_files:
        return []

    return [
        uploaded_image_to_data_url(file)
        for file in uploaded_files
        if file is not None
    ]


def build_top_banner_html(top_banner_data_url, month):
    if top_banner_data_url:
        return f"""
        <div class="top-banner">
            <img src="{top_banner_data_url}" alt="Newsletter top banner">
        </div>
        """

    return f"""
    <div class="top-banner-placeholder">
        <div>
            <h1>LO TAIWAN</h1>
            <p>{safe_text(month).upper()} NEWSLETTER</p>
        </div>
    </div>
    """


def build_section_images_html(image_data_urls):
    if not image_data_urls:
        return ""

    image_count_class = f"image-count-{min(len(image_data_urls), 4)}"

    image_items = ""
    for image_url in image_data_urls:
        image_items += f"""
        <div class="section-image-box">
            <img src="{image_url}" class="section-image" alt="Section image">
        </div>
        """

    return f"""
    <div class="section-image-grid {image_count_class}">
        {image_items}
    </div>
    """


# =========================================================
# HTML Rendering
# =========================================================

def render_newsletter_html(
    month,
    volume,
    issue,
    main_theme,
    editor,
    top_banner_data_url,
    sections,
):
    top_banner_html = build_top_banner_html(top_banner_data_url, month)

    index_items = ""
    section_cards = ""

    for index, section in enumerate(sections, start=1):
        category = safe_text(section.get("category", ""))
        title = safe_text(section.get("title", ""))
        body = safe_text(section.get("body", "")).replace("\n", "<br>")
        highlight = safe_text(section.get("highlight", ""))
        image_data_urls = section.get("image_data_urls", [])

        if not title and not body and not highlight and not image_data_urls:
            continue

        index_items += f"""
        <div class="issue-index-item">
            <div class="issue-index-number">{index}</div>
            <div>
                <div class="issue-index-category">{category}</div>
                <div class="issue-index-title">{title}</div>
            </div>
        </div>
        """

        highlight_html = ""
        if highlight:
            highlight_html = f"""
            <div class="highlight-box">
                {highlight}
            </div>
            """

        section_images_html = build_section_images_html(image_data_urls)

        section_cards += f"""
        <section class="story-card">
            <div class="story-top-rule"></div>

            <div class="story-inner">
                <div class="pill-label">{category}</div>
                <div class="story-page-number">{index:02d}</div>

                <h2>{title}</h2>

                <p class="story-body">
                    {body}
                </p>

                {highlight_html}

                {section_images_html}
            </div>
        </section>
        """

    if not index_items:
        index_items = """
        <div class="issue-index-item">
            <div class="issue-index-number">1</div>
            <div>
                <div class="issue-index-category">Preview</div>
                <div class="issue-index-title">Your section title will appear here</div>
            </div>
        </div>
        """

    if not section_cards:
        section_cards = """
        <section class="story-card">
            <div class="story-top-rule"></div>
            <div class="story-inner">
                <div class="pill-label">Preview</div>
                <div class="story-page-number">01</div>
                <h2>Your newsletter content will appear here</h2>
                <p class="story-body">
                    Add section titles, body text, highlights, and images from the editor panel.
                </p>
            </div>
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
        background: #ffffff;
        font-family: Arial, "Helvetica Neue", Helvetica, sans-serif;
        color: #111111;
    }}

    .newsletter-page {{
        width: 900px;
        margin: 0 auto;
        padding: 18px 26px 22px;
        background: #ffffff;
    }}

    .top-banner {{
        width: 100%;
        height: 116px;
        border: 2px solid #111111;
        margin-bottom: 18px;
        overflow: hidden;
        background: #ffffff;
    }}

    .top-banner img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }}

    .top-banner-placeholder {{
        width: 100%;
        height: 116px;
        border: 2px solid #111111;
        margin-bottom: 18px;
        overflow: hidden;
        background: linear-gradient(90deg, #f3f4f6, #d1d5db);
        display: flex;
        align-items: center;
        padding-left: 34px;
    }}

    .top-banner-placeholder h1 {{
        margin: 0;
        font-size: 34px;
        line-height: 0.95;
        font-weight: 900;
        letter-spacing: -0.04em;
    }}

    .top-banner-placeholder p {{
        margin: 6px 0 0;
        font-size: 18px;
        font-weight: 800;
        letter-spacing: 0.02em;
    }}

    .intro-card {{
        background: #f4f4f4;
        border: 1px solid #e5e5e5;
        border-left: 12px solid #000000;
        border-radius: 0 18px 18px 0;
        padding: 22px 28px;
        margin-bottom: 18px;
    }}

    .intro-pill {{
        display: inline-block;
        background: #000000;
        color: #ffffff;
        border-radius: 999px;
        padding: 5px 18px;
        font-size: 10px;
        line-height: 1;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 14px;
    }}

    .intro-card h1 {{
        margin: 0 0 10px;
        font-size: 14px;
        line-height: 1.2;
        font-weight: 800;
    }}

    .intro-card p {{
        margin: 0 0 12px;
        font-size: 12px;
        line-height: 1.55;
        color: #333333;
    }}

    .meta-line {{
        font-size: 11px;
        color: #555555;
        letter-spacing: 0.01em;
    }}

    .issue-title {{
        margin: 14px 0 8px;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
    }}

    .issue-index {{
        border-top: 2px solid #111111;
        padding-top: 12px;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px 14px;
        margin-bottom: 18px;
    }}

    .issue-index-item {{
        background: #f4f4f4;
        border: 1px solid #e6e6e6;
        border-radius: 12px;
        min-height: 42px;
        padding: 8px 14px;
        display: flex;
        align-items: center;
        gap: 12px;
    }}

    .issue-index-number {{
        width: 26px;
        height: 18px;
        border-radius: 999px;
        background: #111111;
        color: #ffffff;
        font-size: 10px;
        font-weight: 800;
        display: flex;
        align-items: center;
        justify-content: center;
        flex: 0 0 auto;
    }}

    .issue-index-category {{
        font-size: 8px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #777777;
        font-weight: 800;
        margin-bottom: 2px;
    }}

    .issue-index-title {{
        font-size: 10px;
        font-weight: 800;
        color: #111111;
        line-height: 1.25;
    }}

    .story-card {{
        margin-bottom: 16px;
        background: #ffffff;
        border: 1px solid #dedede;
        border-radius: 0 0 16px 16px;
        overflow: hidden;
        page-break-inside: avoid;
    }}

    .story-top-rule {{
        height: 5px;
        background: #111111;
        width: 100%;
    }}

    .story-inner {{
        position: relative;
        padding: 18px 28px 20px;
    }}

    .pill-label {{
        display: inline-block;
        background: #000000;
        color: #ffffff;
        border-radius: 999px;
        padding: 5px 18px;
        font-size: 9px;
        line-height: 1;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 12px;
    }}

    .story-page-number {{
        position: absolute;
        top: 18px;
        right: 28px;
        color: #f1f1f1;
        font-size: 12px;
        font-weight: 800;
    }}

    .story-card h2 {{
        margin: 0 0 10px;
        font-size: 13px;
        line-height: 1.25;
        font-weight: 900;
        color: #111111;
    }}

    .story-body {{
        margin: 0;
        font-size: 10.5px;
        line-height: 1.55;
        color: #222222;
    }}

    .highlight-box {{
        margin-top: 12px;
        padding: 10px 12px;
        background: #f4f4f4;
        border-left: 4px solid #111111;
        border-radius: 8px;
        font-size: 10.5px;
        line-height: 1.55;
        font-weight: 700;
        color: #111111;
    }}

    .section-image-grid {{
        margin-top: 14px;
        display: grid;
        gap: 12px;
    }}

    .section-image-grid.image-count-1 {{
        grid-template-columns: 1fr;
    }}

    .section-image-grid.image-count-2 {{
        grid-template-columns: 1fr 1fr;
    }}

    .section-image-grid.image-count-3,
    .section-image-grid.image-count-4 {{
        grid-template-columns: 1fr 1fr;
    }}

    .section-image-box {{
        width: 100%;
        height: 170px;
        overflow: hidden;
        background: #f3f4f6;
        border: 1px solid #e5e5e5;
    }}

    .image-count-1 .section-image-box {{
        height: 250px;
    }}

    .section-image {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
    }}

    .footer {{
        margin-top: 16px;
        padding-top: 8px;
        border-top: 1px solid #e5e5e5;
        font-size: 8px;
        color: #777777;
        display: flex;
        justify-content: space-between;
    }}

    @media print {{
        body {{
            background: #ffffff;
        }}

        .newsletter-page {{
            width: 100%;
            padding: 10px 14px;
        }}
    }}
</style>
</head>

<body>
    <main class="newsletter-page" id="newsletter">
        {top_banner_html}

        <section class="intro-card">
            <div class="intro-pill">Monthly Newsletter</div>
            <h1>LO Taiwan Monthly Pulse</h1>
            <p>{safe_text(main_theme)}</p>
            <div class="meta-line">
                {safe_text(month)} &nbsp; | &nbsp; Volume {safe_text(volume)} &nbsp; | &nbsp; Issue {safe_text(issue)} &nbsp; | &nbsp; Editor: {safe_text(editor)}
            </div>
        </section>

        <div class="issue-title">In This Issue</div>

        <section class="issue-index">
            {index_items}
        </section>

        {section_cards}

        <footer class="footer">
            <div>Generated by LO Taiwan Monthly Pulse Generator Prototype.</div>
            <div>{datetime.now().strftime("%Y-%m-%d")}</div>
        </footer>
    </main>
</body>
</html>
"""
    return html_content


# =========================================================
# Export Functions
# =========================================================

def html_to_pdf_bytes(html_content):
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
                "top": "0.15in",
                "right": "0.15in",
                "bottom": "0.15in",
                "left": "0.15in",
            },
        )

        browser.close()
        return pdf_bytes


def html_to_jpg_bytes(html_content):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

        page = browser.new_page(
            viewport={"width": 960, "height": 1800},
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

    return f"""
    <iframe
        src="data:text/html;base64,{encoded_html}"
        width="100%"
        height="980"
        style="border: 1px solid #E5E7EB; border-radius: 12px; background: white;"
    ></iframe>
    """


# =========================================================
# Session State Defaults
# =========================================================

if "sections" not in st.session_state:
    st.session_state.sections = [
        {
            "category": "People Spotlight",
            "title": "LO Taiwan Turns 30",
            "body": "This year marks LO Taiwan's 30th Anniversary. The field team is working hard to plan a year-end celebration to commemorate this important milestone.",
            "highlight": "",
            "image_data_urls": [],
        },
        {
            "category": "People Spotlight",
            "title": "Promotions",
            "body": "We are excited to share this promotion moment and celebrate the team's continued growth.",
            "highlight": "",
            "image_data_urls": [],
        },
        {
            "category": "From the Field",
            "title": "Field Notes from Taichung",
            "body": "Here are field notes and snapshots from recent supplier visits and team observations.",
            "highlight": "",
            "image_data_urls": [],
        },
    ]


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:
    st.title("Newsletter Settings")

    month = st.text_input("Month", value="June 2026")
    volume = st.text_input("Volume", value="2")
    issue = st.text_input("Issue", value="17")
    editor = st.text_input("Editor", value="Luz Lin")

    main_theme = st.text_area(
        "Intro / Main Theme",
        value="A clean monthly recap of people, culture, suppliers, and milestones.",
        height=90,
    )

    st.divider()

    st.caption("Prototype Version 3.2")
    st.caption("Editorial layout with PDF/JPG export and section image uploads.")


# =========================================================
# Main Editor
# =========================================================

st.title("🇹🇼 LO Taiwan Monthly Pulse Generator")
st.caption("Create a monthly newsletter preview and export it as PDF or JPG.")

if not chromium_ready:
    st.error("Playwright Chromium installation failed.")
    st.code(chromium_error)
    st.stop()


left_col, right_col = st.columns([0.95, 1.25], gap="large")

with left_col:
    st.subheader("Top Badge / Banner")

    top_banner_file = st.file_uploader(
        "Top Badge / Banner Image",
        type=["png", "jpg", "jpeg"],
        help="Upload the main horizontal banner shown at the top of the newsletter.",
        key="top_banner_file",
    )

    top_banner_data_url = uploaded_image_to_data_url(top_banner_file)

    if top_banner_file is not None:
        st.image(
            top_banner_file,
            caption="Top banner preview",
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
                    "image_data_urls": [],
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
                height=130,
                key=f"body_{i}",
            )

            st.session_state.sections[i]["highlight"] = st.text_area(
                "Highlight / Key Message",
                value=st.session_state.sections[i].get("highlight", ""),
                height=70,
                key=f"highlight_{i}",
            )

            section_image_files = st.file_uploader(
                "Section Images",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key=f"section_images_{i}",
                help="Upload one or more images for this section.",
            )

            st.session_state.sections[i]["image_data_urls"] = uploaded_images_to_data_urls(
                section_image_files
            )

            if section_image_files:
                preview_cols = st.columns(min(len(section_image_files), 3))
                for preview_index, uploaded_file in enumerate(section_image_files[:3]):
                    with preview_cols[preview_index % len(preview_cols)]:
                        st.image(uploaded_file, use_container_width=True)

    if st.button("Clear All Sections"):
        st.session_state.sections = [
            {
                "category": "Update",
                "title": "",
                "body": "",
                "highlight": "",
                "image_data_urls": [],
            }
        ]
        st.rerun()


# =========================================================
# Preview + Export
# =========================================================

html_content = render_newsletter_html(
    month=month,
    volume=volume,
    issue=issue,
    main_theme=main_theme,
    editor=editor,
    top_banner_data_url=top_banner_data_url,
    sections=st.session_state.sections,
)

with right_col:
    st.subheader("Live Preview")

    st.components.v1.html(
        html_preview_component(html_content),
        height=1010,
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
                label="📄 Download PDF",
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
                label="🖼️ Download JPG",
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
