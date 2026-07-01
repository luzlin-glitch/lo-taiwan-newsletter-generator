import base64
import html
import io
import subprocess
import sys
from datetime import datetime
from typing import Dict, List

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
# Style Presets
# -----------------------------

VISUAL_THEMES = {
    "Classic": {
        "accent": "#111111",
        "accent_2": "#2F5FD0",
        "accent_3": "#F59E0B",
        "accent_text": "#FFFFFF",
        "background": "#FFFFFF",
        "soft_background": "#F4F4F4",
        "divider": "#D8D8D8",
        "text": "#111111",
        "muted": "#666666",
    },
    "Energy": {
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
    "Milestone": {
        "accent": "#173B73",
        "accent_2": "#C8A24A",
        "accent_3": "#F3E6BF",
        "accent_text": "#FFFFFF",
        "background": "#FFFFFF",
        "soft_background": "#F9F4E8",
        "divider": "#D8C79A",
        "text": "#111111",
        "muted": "#665F4D",
    },
    "Field Notes": {
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
        "tagline": "Structured business recap",
    },
    "Photo Digest": {
        "description": "Best for event recaps, team moments, supplier visits, and photo-heavy months.",
        "tagline": "Visual-first monthly highlights",
    },
    "Magazine Feature": {
        "description": "Best for one major story, milestone, anniversary, or a hero topic that deserves emphasis.",
        "tagline": "Editorial lead story layout",
    },
    "Field Report": {
        "description": "Best for supplier visits, factory observations, business trips, and field notes.",
        "tagline": "Observation-based report digest",
    },
}

DEFAULT_BADGES = {
    "People": "People Spotlight",
    "Milestone": "Milestone Moment",
    "Supplier": "From the Field",
    "Culture": "Team Moments",
    "Coming Up": "Next Up",
}

SECTION_TEMPLATES = ["Auto", "Brief", "Text", "Feature", "Gallery", "Field Report"]

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


def plain_escape(text):
    if text is None:
        return ""
    return html.escape(str(text))


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


def get_badge_text(section):
    custom_badge = section.get("badge_label", "").strip()
    if custom_badge:
        return custom_badge
    return DEFAULT_BADGES.get(section.get("category", ""), section.get("category", "Update"))


def infer_section_template(section):
    images = section.get("images", [])
    text = section.get("content", "")
    text_len = len(text.strip())
    category = section.get("category", "")

    if len(images) >= 2:
        return "Gallery"
    if len(images) == 1:
        return "Feature"
    if category == "Supplier" and text_len > 80:
        return "Field Report"
    if text_len <= 130:
        return "Brief"
    return "Text"


def get_section_template(section, section_layout):
    if section_layout == "Auto":
        return infer_section_template(section)
    manual_template = section.get("manual_template", "Auto")
    if manual_template == "Auto":
        return infer_section_template(section)
    return manual_template


def create_image_figure(image, extra_class=""):
    return f"""
    <figure class="image-frame {extra_class}">
        <img class="section-image" src="{image_data_url(image)}" alt="">
    </figure>
    """


def generate_masonry_images_html(images, layout="masonry"):
    if not images:
        return ""

    if layout == "small-supporting":
        tags = "".join(create_image_figure(image, "supporting-image") for image in images)
        return f"<div class='supporting-image-row'>{tags}</div>"

    if len(images) == 1:
        return f"<div class='single-image-wrap'>{create_image_figure(images[0], 'single-image')}</div>"

    tags = "".join(create_image_figure(image) for image in images)
    return f"<div class='masonry-gallery image-count-{min(len(images), 8)}'>{tags}</div>"


def generate_banner_html(month, top_banner_mode, top_banner_file, theme, newsletter_style):
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

    image = {"name": top_banner_file.name, "bytes": top_banner_file.getvalue()}
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
# Section HTML Builders
# -----------------------------

def section_common_header(section, template, theme):
    badge = safe_html_text(get_badge_text(section))
    title = safe_html_text(section.get("title", ""))
    return f"""
    <div class="section-badge-row">
        <span class="badge">{badge}</span>
        <span class="template-tag">{template}</span>
    </div>
    <h2 class="section-title">{title}</h2>
    """


def generate_section_html(section, template, theme, newsletter_style, index):
    content = safe_html_text(section.get("content", ""))
    images = section.get("images", [])
    header = section_common_header(section, template, theme)

    if template == "Brief":
        images_html = generate_masonry_images_html(images, layout="small-supporting")
        return f"""
        <section class="section-card brief-card style-{newsletter_style_class(newsletter_style)}">
            {header}
            <div class="section-content brief-content">{content}</div>
            {images_html}
        </section>
        """

    if template == "Feature":
        images_html = generate_masonry_images_html(images)
        return f"""
        <section class="section-card feature-card style-{newsletter_style_class(newsletter_style)}">
            {header}
            {images_html}
            <div class="section-content after-image">{content}</div>
        </section>
        """

    if template == "Gallery":
        images_html = generate_masonry_images_html(images)
        return f"""
        <section class="section-card gallery-card style-{newsletter_style_class(newsletter_style)}">
            {header}
            <div class="section-content gallery-intro">{content}</div>
            {images_html}
        </section>
        """

    if template == "Field Report":
        images_html = generate_masonry_images_html(images)
        return f"""
        <section class="section-card field-report-card style-{newsletter_style_class(newsletter_style)}">
            {header}
            <div class="field-report-layout">
                <div class="field-report-copy">
                    <div class="field-note-label">Observation {index:02d}</div>
                    <div class="section-content">{content}</div>
                </div>
                <div class="field-report-media">
                    {images_html}
                </div>
            </div>
        </section>
        """

    # Text default
    images_html = generate_masonry_images_html(images, layout="small-supporting")
    return f"""
    <section class="section-card text-card style-{newsletter_style_class(newsletter_style)}">
        {header}
        <div class="section-content">{content}</div>
        {images_html}
    </section>
    """


def newsletter_style_class(newsletter_style):
    return newsletter_style.lower().replace(" ", "-").replace("&", "and")

# -----------------------------
# Newsletter HTML Rendering
# -----------------------------

def build_issue_overview(sections, section_layout, newsletter_style, theme):
    items = ""
    for index, section in enumerate(sections, start=1):
        template = get_section_template(section, section_layout)
        badge = safe_html_text(get_badge_text(section))
        title = safe_html_text(section.get("title", ""))
        items += f"""
        <div class="issue-item">
            <div class="issue-number">{index}</div>
            <div class="issue-text">
                <div class="issue-badge">{badge} · {template}</div>
                <div class="issue-title">{title}</div>
            </div>
        </div>
        """

    if not items:
        return ""

    heading = "In This Issue"
    subtitle = "A quick guide to this month’s key stories."
    if newsletter_style == "Photo Digest":
        heading = "Photo Highlights"
        subtitle = "A visual recap of this month’s key moments."
    elif newsletter_style == "Field Report":
        heading = "Field Notes Overview"
        subtitle = "A structured guide to observations, updates, and next steps."
    elif newsletter_style == "Magazine Feature":
        heading = "Inside This Feature"
        subtitle = "Lead story first, followed by supporting updates."

    return f"""
    <section class="issue-overview">
        <div class="issue-header">
            <h2 class="issue-heading">{heading}</h2>
            <div class="issue-subtitle">{subtitle}</div>
        </div>
        <div class="issue-list">
            {items}
        </div>
    </section>
    """


def build_corporate_layout(sections, month, editor, theme, section_layout):
    section_html = ""
    for index, section in enumerate(sections, start=1):
        template = get_section_template(section, section_layout)
        # Corporate is more text-first: gallery images are supporting, not dominant.
        if template == "Gallery":
            template = "Text"
        section_html += generate_section_html(section, template, theme, "Corporate Classic", index)
    return section_html


def build_photo_digest_layout(sections, month, editor, theme, section_layout):
    section_html = ""
    for index, section in enumerate(sections, start=1):
        template = get_section_template(section, section_layout)
        if section.get("images"):
            template = "Gallery"
        section_html += generate_section_html(section, template, theme, "Photo Digest", index)
    return section_html


def build_magazine_layout(sections, month, editor, theme, section_layout):
    section_html = ""
    for index, section in enumerate(sections, start=1):
        template = get_section_template(section, section_layout)
        if index == 1:
            template = "Feature" if section.get("images") else "Text"
            section_html += f"<div class='lead-story-label'>Lead Story</div>"
        section_html += generate_section_html(section, template, theme, "Magazine Feature", index)
    return section_html


def build_field_report_layout(sections, month, editor, theme, section_layout):
    section_html = ""
    for index, section in enumerate(sections, start=1):
        template = get_section_template(section, section_layout)
        if section.get("category") == "Supplier" or section.get("images"):
            template = "Field Report"
        section_html += generate_section_html(section, template, theme, "Field Report", index)
    return section_html


def generate_newsletter_html(
    month,
    editor,
    sections,
    visual_theme,
    newsletter_style,
    section_layout,
    top_banner_mode,
    top_banner_file,
):
    theme = VISUAL_THEMES[visual_theme]
    style_class = newsletter_style_class(newsletter_style)
    banner_html = generate_banner_html(month, top_banner_mode, top_banner_file, theme, newsletter_style)
    issue_html = build_issue_overview(sections, section_layout, newsletter_style, theme)

    if newsletter_style == "Photo Digest":
        sections_html = build_photo_digest_layout(sections, month, editor, theme, section_layout)
    elif newsletter_style == "Magazine Feature":
        sections_html = build_magazine_layout(sections, month, editor, theme, section_layout)
    elif newsletter_style == "Field Report":
        sections_html = build_field_report_layout(sections, month, editor, theme, section_layout)
    else:
        sections_html = build_corporate_layout(sections, month, editor, theme, section_layout)

    if not sections_html:
        sections_html = """
        <section class="section-card text-card">
            <span class="badge">Preview</span>
            <h2 class="section-title">Your newsletter content will appear here</h2>
            <div class="section-content">Add sections from the editor panel to generate the newsletter draft.</div>
        </section>
        """

    css = generate_css(theme, style_class, newsletter_style)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{css}</style>
    </head>
    <body>
        <main class="page {style_class}">
            {banner_html}
            <section class="style-intro">
                <div>
                    <div class="style-kicker">{safe_html_text(NEWSLETTER_STYLES[newsletter_style]['tagline'])}</div>
                    <h1>{safe_html_text(month)} Monthly Pulse</h1>
                </div>
                <div class="style-meta">Editor: {safe_html_text(editor)}</div>
            </section>
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

def generate_css(theme, style_class, newsletter_style):
    corporate_extra = ""
    photo_extra = ""
    magazine_extra = ""
    field_extra = ""

    if newsletter_style == "Corporate Classic":
        corporate_extra = f"""
        .corporate-classic .section-card {{ border-radius: 4px; box-shadow: none; }}
        .corporate-classic .section-title {{ font-size: 24px; }}
        .corporate-classic .supporting-image-row {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
        .corporate-classic .section-content {{ font-size: 13px; }}
        .corporate-classic .issue-list {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
        """

    if newsletter_style == "Photo Digest":
        photo_extra = f"""
        .photo-digest .style-intro {{ display: none; }}
        .photo-digest .issue-overview {{ border: none; padding: 0; }}
        .photo-digest .section-card {{ padding: 18px; border-radius: 22px; }}
        .photo-digest .section-title {{ font-size: 28px; }}
        .photo-digest .section-content {{ font-size: 12px; color: {theme['muted']}; }}
        .photo-digest .masonry-gallery {{ column-count: 2; column-gap: 14px; }}
        .photo-digest .image-frame {{ border-radius: 16px; margin-bottom: 14px; }}
        """

    if newsletter_style == "Magazine Feature":
        magazine_extra = f"""
        .magazine-feature .style-intro {{ background: transparent; border: none; border-left: 12px solid {theme['accent_2']}; padding: 10px 0 10px 22px; }}
        .magazine-feature .style-intro h1 {{ font-size: 42px; text-transform: uppercase; letter-spacing: -1.3px; }}
        .magazine-feature .lead-story-label {{ font-size: 11px; font-weight: 950; color: {theme['accent_2']}; text-transform: uppercase; letter-spacing: 1.5px; margin: 8px 0; }}
        .magazine-feature .feature-card:first-of-type {{ display: grid; grid-template-columns: 0.9fr 1.1fr; gap: 20px; align-items: start; background: {theme['accent']}; color: white; }}
        .magazine-feature .feature-card:first-of-type .section-title, .magazine-feature .feature-card:first-of-type .section-content {{ color: white; }}
        .magazine-feature .feature-card:first-of-type .badge {{ background: {theme['accent_2']}; color: white; }}
        .magazine-feature .feature-card:first-of-type .masonry-gallery, .magazine-feature .feature-card:first-of-type .single-image-wrap {{ grid-column: 2; grid-row: 1 / span 4; }}
        .magazine-feature .feature-card:first-of-type .section-badge-row, .magazine-feature .feature-card:first-of-type .section-title, .magazine-feature .feature-card:first-of-type .section-content {{ grid-column: 1; }}
        """

    if newsletter_style == "Field Report":
        field_extra = f"""
        .field-report .style-intro {{ border-left: 0; border-top: 5px solid {theme['accent_2']}; background: {theme['soft_background']}; }}
        .field-report .section-card {{ border-radius: 0; border-left: 7px solid {theme['accent_2']}; }}
        .field-report .section-title {{ font-size: 25px; }}
        .field-report .field-report-layout {{ display: grid; grid-template-columns: 0.95fr 1.05fr; gap: 20px; }}
        .field-report .field-note-label {{ color: {theme['accent_2']}; font-size: 11px; font-weight: 950; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }}
        """

    return f"""
    @page {{ margin: 0; }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; padding: 0; background: #ffffff; color: {theme['text']}; font-family: Arial, Helvetica, sans-serif; }}
    body {{ padding: 0; }}
    .page {{ width: 100%; max-width: 900px; margin: 0 auto; padding: 18px 28px 22px; background: #ffffff; }}

    .ready-banner, .generated-banner {{ width: 100%; height: 210px; border-radius: 20px; overflow: hidden; margin-bottom: 28px; position: relative; border: 1px solid {theme['divider']}; background: {theme['soft_background']}; }}
    .ready-banner img {{ width: 100%; height: 100%; object-fit: contain; display: block; background: #ffffff; }}
    .generated-banner img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
    .fallback-banner {{ background: linear-gradient(135deg, {theme['accent']} 0%, {theme['accent_2']} 100%); }}
    .banner-overlay {{ position: absolute; inset: 0; background: linear-gradient(90deg, rgba(0,0,0,0.72), rgba(0,0,0,0.22), rgba(0,0,0,0.05)); }}
    .banner-content {{ position: absolute; left: 38px; bottom: 34px; color: white; }}
    .banner-kicker {{ font-size: 48px; line-height: 0.95; font-weight: 950; letter-spacing: -1.5px; text-transform: uppercase; }}
    .banner-title {{ margin-top: 10px; font-size: 26px; font-weight: 900; letter-spacing: 1px; text-transform: uppercase; }}

    .style-intro {{ display: flex; justify-content: space-between; gap: 24px; align-items: flex-end; background: {theme['soft_background']}; border: 1px solid {theme['divider']}; border-left: 10px solid {theme['accent']}; border-radius: 18px; padding: 24px 28px; margin-bottom: 28px; }}
    .style-kicker {{ color: {theme['accent_2']}; font-size: 11px; font-weight: 950; text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 8px; }}
    .style-intro h1 {{ margin: 0; font-size: 32px; line-height: 1.05; letter-spacing: -0.8px; }}
    .style-meta {{ font-size: 11px; color: {theme['muted']}; font-weight: 800; white-space: nowrap; }}

    .issue-overview {{ margin-bottom: 28px; border-top: 2px solid {theme['accent']}; padding-top: 16px; }}
    .issue-heading {{ font-size: 26px; margin: 0 0 5px; letter-spacing: -0.5px; }}
    .issue-subtitle {{ color: {theme['muted']}; font-size: 12px; font-weight: 750; margin-bottom: 14px; }}
    .issue-list {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .issue-item {{ display: grid; grid-template-columns: 34px 1fr; gap: 12px; align-items: center; background: {theme['soft_background']}; border: 1px solid {theme['divider']}; border-left: 5px solid {theme['accent']}; border-radius: 12px; padding: 13px 14px; }}
    .issue-number {{ width: 30px; height: 30px; border-radius: 999px; background: {theme['accent']}; color: {theme['accent_text']}; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 950; }}
    .issue-badge {{ font-size: 9px; color: {theme['muted']}; font-weight: 950; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 4px; }}
    .issue-title {{ font-size: 14px; font-weight: 950; line-height: 1.25; }}

    .section-card {{ background: {theme['background']}; border: 1px solid {theme['divider']}; border-top: 6px solid {theme['accent']}; border-radius: 18px; padding: 24px 26px; margin-bottom: 24px; page-break-inside: avoid; }}
    .section-badge-row {{ display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 10px; }}
    .badge {{ display: inline-block; background: {theme['accent']}; color: {theme['accent_text']}; border-radius: 999px; padding: 7px 15px; font-size: 10px; font-weight: 950; letter-spacing: 0.6px; text-transform: uppercase; }}
    .template-tag {{ color: {theme['muted']}; font-size: 9px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.8px; }}
    .section-title {{ font-size: 30px; font-weight: 950; line-height: 1.08; letter-spacing: -0.7px; margin: 0 0 15px; }}
    .section-content {{ font-size: 14px; line-height: 1.58; font-weight: 500; margin: 0 0 14px; }}
    .after-image {{ margin-top: 14px; }}
    .gallery-intro {{ margin-bottom: 14px; }}

    .masonry-gallery {{ column-count: 2; column-gap: 14px; margin-top: 14px; }}
    .image-frame {{ break-inside: avoid; width: 100%; margin: 0 0 14px; border-radius: 12px; overflow: hidden; border: 1px solid {theme['divider']}; background: #ffffff; }}
    .section-image {{ width: 100%; height: auto; object-fit: contain; display: block; }}
    .single-image-wrap .image-frame {{ max-width: 100%; }}
    .supporting-image-row {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 14px; }}
    .supporting-image-row .image-frame {{ margin-bottom: 0; }}

    .brief-card {{ background: {theme['soft_background']}; }}
    .brief-card .section-title {{ font-size: 22px; margin-bottom: 8px; }}
    .brief-content {{ font-size: 13px; }}

    .footer {{ color: {theme['muted']}; font-size: 9px; line-height: 1.4; margin-top: 22px; border-top: 1px solid {theme['divider']}; padding-top: 12px; }}

    {corporate_extra}
    {photo_extra}
    {magazine_extra}
    {field_extra}

    @media screen {{ body {{ padding: 16px; }} }}
    @media print {{ html, body {{ width: 100%; background: #ffffff; }} .page {{ max-width: none; padding: 18px 28px 22px; }} }}
    @media screen and (max-width: 720px) {{
        .page {{ padding: 16px; }}
        .style-intro, .field-report .field-report-layout, .magazine-feature .feature-card:first-of-type {{ display: block; }}
        .issue-list {{ grid-template-columns: 1fr; }}
        .masonry-gallery {{ column-count: 1; }}
        .supporting-image-row {{ grid-template-columns: 1fr; }}
        .banner-kicker {{ font-size: 34px; }}
        .banner-title {{ font-size: 20px; }}
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
        page = browser.new_page(viewport={"width": 900, "height": 1300}, device_scale_factor=1)
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
            margin={"top": "0px", "right": "0px", "bottom": "0px", "left": "0px"},
        )
        browser.close()
    return pdf_bytes


def html_to_jpg_bytes(newsletter_html):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = browser.new_page(viewport={"width": 900, "height": 1500}, device_scale_factor=2)
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

st.sidebar.header("Newsletter Settings")
newsletter_month = st.sidebar.text_input("Month", "June 2026")
editor_name = st.sidebar.text_input("Editor", "Luz Lin")
visual_theme = st.sidebar.selectbox("Visual Theme", ["Classic", "Energy", "Milestone", "Field Notes"])
newsletter_style = st.sidebar.selectbox("Newsletter Style", list(NEWSLETTER_STYLES.keys()))
section_layout = st.sidebar.selectbox("Section Layout", ["Auto", "Manual"])

with st.sidebar.expander("Which Newsletter Style should I use?"):
    for style_name, style_info in NEWSLETTER_STYLES.items():
        st.markdown(f"**{style_name}**")
        st.caption(style_info["description"])

st.sidebar.markdown("---")
st.sidebar.write("Prototype Version 2.9")
st.sidebar.caption("Distinct Canva-style templates, masonry images, and no image cropping.")

if "sections" not in st.session_state:
    st.session_state.sections = []
if "form_counter" not in st.session_state:
    st.session_state.form_counter = 0

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
        st.image(top_banner_file, caption="Banner image preview", use_container_width=True)

st.header("1. Add Monthly Update")

with st.form(f"update_form_{st.session_state.form_counter}"):
    category = st.selectbox("Category", ["People", "Milestone", "Supplier", "Culture", "Coming Up"])
    default_badge = DEFAULT_BADGES.get(category, category)
    badge_label = st.text_input(
        "Badge Label",
        value="",
        placeholder=f"Example: {default_badge}, Big Moves, From the Field, Team Energy",
    )
    title = st.text_input("Section Title", placeholder="Example: Promotions")
    raw_content = st.text_area("Raw Content", placeholder="Paste or type the original update here...", height=160)

    manual_template = "Auto"
    if section_layout == "Manual":
        manual_template = st.selectbox("Section Template", SECTION_TEMPLATES)

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
                    images.append({"name": uploaded_image.name, "bytes": uploaded_image.getvalue()})
            st.session_state.sections.append(
                {
                    "category": category,
                    "badge_label": badge_label.strip(),
                    "title": title,
                    "content": raw_content,
                    "manual_template": manual_template,
                    "images": images,
                }
            )
            st.session_state.form_counter += 1
            st.success("Section added successfully!")
            st.rerun()
        else:
            st.warning("Please enter both a title and content.")

st.header("2. Newsletter Preview")

if not st.session_state.sections:
    st.info("Add at least one section to generate the newsletter preview.")
else:
    col1, col2 = st.columns([0.62, 1.78])
    with col1:
        st.subheader("Added Sections")
        for i, section in enumerate(st.session_state.sections):
            template = get_section_template(section, section_layout)
            with st.expander(f"{i + 1}. {section['category']} — {section['title']}"):
                st.caption(f"Badge: {get_badge_text(section)}")
                st.caption(f"Template: {template}")
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
            visual_theme,
            newsletter_style,
            section_layout,
            top_banner_mode,
            top_banner_file,
        )
        components.html(newsletter_html, height=1120, scrolling=True)

st.markdown("---")

if st.session_state.sections:
    newsletter_html = generate_newsletter_html(
        newsletter_month,
        editor_name,
        st.session_state.sections,
        visual_theme,
        newsletter_style,
        section_layout,
        top_banner_mode,
        top_banner_file,
    )

    pdf_col, jpg_col = st.columns(2)
    file_base = f"LO_Taiwan_Monthly_Pulse_{newsletter_month.replace(' ', '_')}_{newsletter_style.replace(' ', '_')}"

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
