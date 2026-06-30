import streamlit as st
import streamlit.components.v1 as components

import base64
import html
import io
import textwrap
from PIL import Image, ImageDraw, ImageFont


# -----------------------------
# Page Config
# -----------------------------

st.set_page_config(
    page_title="LO Taiwan Monthly Pulse Generator",
    page_icon="📰",
    layout="wide"
)


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
        "muted": "#666666",
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
        "muted": "#5F6545",
        "title_transform": "uppercase",
        "cover_phrase": "Fast updates, fresh stories, and team momentum.",
        "description": "Sporty, active, bold"
    },
    "Milestone": {
        "accent": "#C8A24A",
        "accent_text": "#111111",
        "background": "#FFFFFF",
        "soft_background": "#F8F4EA",
        "divider": "#DED2B0",
        "muted": "#6C6044",
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
        "muted": "#4C6178",
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
        "muted": "#72513B",
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
st.caption("From raw monthly updates to a newsletter-style draft for PDF, JPG, and PNG export.")


# -----------------------------
# Sidebar Settings
# -----------------------------

st.sidebar.header("Newsletter Settings")

newsletter_month = st.sidebar.text_input("Month", "June 2026")

issue_label = st.sidebar.text_input(
    "Issue Label",
    "Volume 2 · Issue 18"
)

editor_name = st.sidebar.text_input("Editor", "Luz Lin")

visual_theme = st.sidebar.selectbox(
    "Visual Theme",
    ["Classic", "Energy", "Milestone", "People", "Field Notes"]
)

layout_style = st.sidebar.selectbox(
    "Newsletter Layout",
    ["Editorial", "Magazine", "Compact"]
)

top_badge_file = st.sidebar.file_uploader(
    "Upload Top Badge / Header Image",
    type=["png", "jpg", "jpeg"],
    help="Optional. Use this for the existing newsletter badge or banner image."
)

theme = THEMES[visual_theme]

st.sidebar.caption(f"Theme mood: {theme['description']}")

st.sidebar.markdown("---")
st.sidebar.write("Prototype Version 3.1")
st.sidebar.caption("Exports use Pillow, not Chromium.")


# -----------------------------
# Session State
# -----------------------------

if "sections" not in st.session_state:
    st.session_state.sections = []

if "form_counter" not in st.session_state:
    st.session_state.form_counter = 0


# -----------------------------
# HTML Preview Helpers
# -----------------------------

def get_badge_text(section):
    custom_badge = section.get("badge_label", "").strip()
    if custom_badge:
        return custom_badge
    return DEFAULT_BADGES.get(section["category"], section["category"])


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
    return html.escape(text or "").replace("\n", "<br>")


def title_case_by_theme(title, theme_style):
    if theme_style["title_transform"] == "uppercase":
        return title.upper()
    return title


def file_to_image_data(file_obj):
    if file_obj is None:
        return None
    return {
        "name": file_obj.name,
        "bytes": file_obj.getvalue()
    }


def generate_top_badge_html(top_badge):
    if not top_badge:
        return """
        <section class="brand-masthead">
            <div class="masthead-label">LO TAIWAN</div>
            <div class="masthead-title">Monthly Newsletter</div>
        </section>
        """

    mime = image_mime_type(top_badge["name"])
    encoded = image_to_base64(top_badge["bytes"])

    return f"""
    <section class="top-badge-image-wrap">
        <img class="top-badge-image" src="data:{mime};base64,{encoded}" alt="Newsletter badge">
    </section>
    """


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
                <img class="section-image" src="data:{mime};base64,{encoded}" alt="">
            </figure>
            """
        )

    if layout == "single-column":
        return f"""<div class="image-column">{''.join(image_tags)}</div>"""

    if layout == "hero":
        first = image_tags[0]
        rest = image_tags[1:]
        rest_html = f"""<div class="image-grid">{''.join(rest)}</div>""" if rest else ""
        return f"""<div class="hero-image-wrap">{first}</div>{rest_html}"""

    return f"""<div class="image-grid">{''.join(image_tags)}</div>"""


def generate_section_html(section, theme_style, layout_style, index):
    badge_text = safe_html_text(get_badge_text(section))
    title = safe_html_text(title_case_by_theme(section["title"], theme_style))
    content = safe_html_text(section["content"])
    images = section.get("images", [])

    if layout_style == "Magazine" and images:
        images_html = generate_images_html(images, layout="hero")
        return f"""
        <article class="article-card article-magazine">
            <div class="article-number">0{index}</div>
            <div class="article-body">
                <div class="badge">{badge_text}</div>
                <h2 class="section-title">{title}</h2>
                <div class="section-content">{content}</div>
                {images_html}
            </div>
        </article>
        """

    if layout_style == "Compact":
        images_html = generate_images_html(images, layout="single-column")
        return f"""
        <article class="article-card article-compact">
            <div class="badge">{badge_text}</div>
            <h2 class="section-title">{title}</h2>
            <div class="compact-layout">
                <div class="compact-text">
                    <div class="section-content">{content}</div>
                </div>
                <div class="compact-images">
                    {images_html}
                </div>
            </div>
        </article>
        """

    images_html = generate_images_html(images, layout="grid")
    return f"""
    <article class="article-card">
        <div class="article-topline">
            <div class="badge">{badge_text}</div>
            <div class="article-number">0{index}</div>
        </div>
        <h2 class="section-title">{title}</h2>
        <div class="section-content">{content}</div>
        {images_html}
    </article>
    """


def generate_newsletter_html(month, issue_label, editor, sections, visual_theme, layout_style, top_badge):
    theme_style = THEMES[visual_theme]

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
    for index, section in enumerate(sections, start=1):
        section_html += generate_section_html(section, theme_style, layout_style, index)

    top_badge_html = generate_top_badge_html(top_badge)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">

        <style>
            * {{ box-sizing: border-box; }}
            html, body {{
                margin: 0;
                padding: 0;
                background: #ffffff;
                color: #111111;
                font-family: Arial, Helvetica, sans-serif;
            }}
            .page {{
                width: 100%;
                max-width: 920px;
                margin: 0 auto;
                padding: 24px 38px 32px 38px;
            }}
            .top-badge-image-wrap {{
                width: 100%;
                margin: 0 0 18px 0;
                border-radius: 22px;
                overflow: hidden;
                border: 1px solid {theme_style["divider"]};
                background: #ffffff;
            }}
            .top-badge-image {{
                width: 100%;
                height: auto;
                display: block;
            }}
            .brand-masthead {{
                border: 1px solid {theme_style["divider"]};
                border-radius: 22px;
                padding: 20px 26px;
                margin-bottom: 18px;
                background: linear-gradient(135deg, {theme_style["soft_background"]} 0%, #ffffff 58%);
                display: flex;
                align-items: baseline;
                justify-content: space-between;
                gap: 18px;
            }}
            .masthead-label {{
                font-size: 12px;
                font-weight: 950;
                letter-spacing: 1.7px;
                color: {theme_style["muted"]};
            }}
            .masthead-title {{
                font-size: 28px;
                font-weight: 950;
                letter-spacing: -0.8px;
                text-transform: uppercase;
            }}
            .cover {{
                background: linear-gradient(135deg, {theme_style["soft_background"]} 0%, #ffffff 70%);
                border: 1px solid {theme_style["divider"]};
                border-left: 10px solid {theme_style["accent"]};
                border-radius: 24px;
                padding: 34px 38px;
                margin-bottom: 26px;
            }}
            .cover-kicker {{
                display: inline-block;
                background: {theme_style["accent"]};
                color: {theme_style["accent_text"]};
                border-radius: 999px;
                padding: 7px 15px;
                font-size: 10.5px;
                font-weight: 950;
                letter-spacing: 0.7px;
                text-transform: uppercase;
                margin-bottom: 15px;
            }}
            .cover-title {{
                font-size: 42px;
                line-height: 1.03;
                font-weight: 950;
                margin: 0 0 14px 0;
                letter-spacing: -1.2px;
            }}
            .cover-phrase {{
                font-size: 17px;
                font-weight: 800;
                line-height: 1.38;
                margin-bottom: 20px;
                max-width: 680px;
            }}
            .cover-meta-row {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }}
            .cover-meta-pill {{
                border: 1px solid {theme_style["divider"]};
                background: #ffffff;
                border-radius: 999px;
                padding: 8px 12px;
                font-size: 10.5px;
                line-height: 1.2;
                color: {theme_style["muted"]};
                font-weight: 800;
            }}
            .issue-overview {{
                margin-bottom: 26px;
            }}
            .issue-header {{
                margin-bottom: 14px;
                display: flex;
                align-items: end;
                justify-content: space-between;
                gap: 18px;
                border-bottom: 2px solid {theme_style["accent"]};
                padding-bottom: 10px;
            }}
            .issue-heading {{
                font-size: 24px;
                font-weight: 950;
                margin: 0;
                letter-spacing: -0.4px;
            }}
            .issue-subtitle {{
                font-size: 11px;
                line-height: 1.4;
                color: {theme_style["muted"]};
                font-weight: 750;
                text-align: right;
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
                border-radius: 16px;
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
                color: {theme_style["muted"]};
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
            .article-card {{
                position: relative;
                border: 1px solid {theme_style["divider"]};
                border-top: 7px solid {theme_style["accent"]};
                border-radius: 22px;
                padding: 26px 28px 28px 28px;
                margin-bottom: 24px;
                background: {theme_style["background"]};
            }}
            .article-topline {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 16px;
                margin-bottom: 10px;
            }}
            .badge {{
                background: {theme_style["accent"]};
                color: {theme_style["accent_text"]};
                border-radius: 999px;
                padding: 7px 16px;
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                display: inline-block;
            }}
            .article-number {{
                color: {theme_style["divider"]};
                font-size: 30px;
                line-height: 1;
                font-weight: 950;
                letter-spacing: -1px;
            }}
            .section-title {{
                font-size: 32px;
                font-weight: 950;
                line-height: 1.05;
                letter-spacing: -0.7px;
                margin: 0 0 15px 0;
                text-transform: {theme_style["title_transform"]};
            }}
            .section-content {{
                font-size: 14px;
                line-height: 1.58;
                font-weight: 500;
                margin: 0 0 16px 0;
            }}
            .image-grid {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 14px;
                margin-top: 14px;
                align-items: start;
            }}
            .hero-image-wrap {{
                margin: 14px 0 0 0;
            }}
            .image-frame {{
                width: 100%;
                margin: 0;
                border-radius: 15px;
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
            .article-magazine {{
                display: grid;
                grid-template-columns: 56px 1fr;
                gap: 6px;
            }}
            .article-magazine .article-number {{
                writing-mode: vertical-rl;
                transform: rotate(180deg);
                font-size: 28px;
                color: {theme_style["accent"]};
                opacity: 0.35;
                justify-self: start;
            }}
            .compact-layout {{
                display: grid;
                grid-template-columns: 1.08fr 0.92fr;
                gap: 22px;
                align-items: start;
            }}
            .compact-text .section-content {{
                margin-bottom: 0;
            }}
            .footer {{
                color: {theme_style["muted"]};
                font-size: 9px;
                line-height: 1.4;
                margin-top: 24px;
                border-top: 1px solid {theme_style["divider"]};
                padding-top: 12px;
            }}
            @media screen {{
                body {{
                    padding: 16px;
                    background: #f7f7f7;
                }}
                .page {{
                    background: #ffffff;
                    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.08);
                }}
            }}
            @media screen and (max-width: 720px) {{
                .page {{
                    padding: 16px;
                }}
                .brand-masthead {{
                    flex-direction: column;
                    align-items: flex-start;
                }}
                .cover {{
                    padding: 24px;
                }}
                .cover-title {{
                    font-size: 32px;
                }}
                .issue-header {{
                    display: block;
                }}
                .issue-subtitle {{
                    text-align: left;
                    margin-top: 5px;
                }}
                .issue-list,
                .image-grid,
                .compact-layout,
                .article-magazine {{
                    grid-template-columns: 1fr;
                }}
                .article-magazine .article-number {{
                    writing-mode: horizontal-tb;
                    transform: none;
                }}
            }}
        </style>
    </head>

    <body>
        <main class="page">
            {top_badge_html}

            <section class="cover">
                <div class="cover-kicker">Monthly Newsletter</div>
                <h1 class="cover-title">LO Taiwan Monthly Pulse</h1>
                <div class="cover-phrase">{safe_html_text(theme_style["cover_phrase"])}</div>

                <div class="cover-meta-row">
                    <div class="cover-meta-pill">{safe_html_text(month)}</div>
                    <div class="cover-meta-pill">{safe_html_text(issue_label)}</div>
                    <div class="cover-meta-pill">Editor: {safe_html_text(editor)}</div>
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


# -----------------------------
# Pillow Export Helpers
# -----------------------------

def hex_to_rgb(value):
    value = value.strip("#")
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))


def load_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]

    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue

    return ImageFont.load_default()


def draw_rounded_rectangle(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def wrap_text(draw, text, font, max_width):
    lines = []
    for paragraph in str(text or "").split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue

        current = words[0]
        for word in words[1:]:
            test = current + " " + word
            if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
                current = test
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def draw_wrapped_text(draw, text, x, y, font, fill, max_width, line_spacing=6):
    lines = wrap_text(draw, text, font, max_width)
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((x, y), line or "Ag", font=font)
        y += (bbox[3] - bbox[1]) + line_spacing
    return y


def open_image_from_bytes(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return img


def resize_to_width(img, width):
    if img.width <= 0:
        return img
    ratio = width / img.width
    height = max(1, int(img.height * ratio))
    return img.resize((width, height), Image.LANCZOS)


def render_newsletter_image(month, issue_label, editor, sections, visual_theme, layout_style, top_badge):
    theme_style = THEMES[visual_theme]
    accent = hex_to_rgb(theme_style["accent"])
    accent_text = hex_to_rgb(theme_style["accent_text"])
    soft = hex_to_rgb(theme_style["soft_background"])
    divider = hex_to_rgb(theme_style["divider"])
    muted = hex_to_rgb(theme_style["muted"])

    W = 1000
    margin = 50
    content_w = W - margin * 2

    # First pass creates a tall canvas; final crop happens at the end.
    H = 5000 + len(sections) * 1400
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    font_h1 = load_font(48, True)
    font_h2 = load_font(34, True)
    font_h3 = load_font(24, True)
    font_body = load_font(18, False)
    font_small = load_font(14, True)
    font_tiny = load_font(12, True)
    font_num = load_font(28, True)

    y = 34

    # Top badge/header image
    if top_badge:
        try:
            badge_img = open_image_from_bytes(top_badge["bytes"])
            badge_img = resize_to_width(badge_img, content_w)
            img.paste(badge_img, (margin, y))
            y += badge_img.height + 26
        except Exception:
            pass
    else:
        draw_rounded_rectangle(draw, (margin, y, margin + content_w, y + 86), 24, soft, divider, 1)
        draw.text((margin + 28, y + 28), "LO TAIWAN", font=font_small, fill=muted)
        title = "MONTHLY NEWSLETTER"
        tb = draw.textbbox((0, 0), title, font=font_h3)
        draw.text((margin + content_w - (tb[2] - tb[0]) - 28, y + 24), title, font=font_h3, fill=(17, 17, 17))
        y += 112

    # Cover
    cover_h = 260
    draw_rounded_rectangle(draw, (margin, y, margin + content_w, y + cover_h), 26, soft, divider, 1)
    draw.rounded_rectangle((margin, y, margin + 12, y + cover_h), radius=6, fill=accent)

    pill_x = margin + 40
    pill_y = y + 34
    draw_rounded_rectangle(draw, (pill_x, pill_y, pill_x + 190, pill_y + 34), 17, accent)
    draw.text((pill_x + 16, pill_y + 9), "MONTHLY NEWSLETTER", font=font_tiny, fill=accent_text)

    draw.text((margin + 40, y + 88), "LO Taiwan Monthly Pulse", font=font_h1, fill=(17, 17, 17))
    y_text = draw_wrapped_text(
        draw,
        theme_style["cover_phrase"],
        margin + 40,
        y + 152,
        font_body,
        (17, 17, 17),
        content_w - 80,
        line_spacing=7
    )

    meta = f"{month}    |    {issue_label}    |    Editor: {editor}"
    draw.text((margin + 40, y_text + 14), meta, font=font_small, fill=muted)
    y += cover_h + 34

    # In this issue
    draw.text((margin, y), "In This Issue", font=font_h2, fill=(17, 17, 17))
    draw.line((margin, y + 48, margin + content_w, y + 48), fill=accent, width=3)
    y += 70

    card_gap = 16
    card_w = (content_w - card_gap) // 2
    card_h = 82

    for idx, section in enumerate(sections, start=1):
        col = (idx - 1) % 2
        row = (idx - 1) // 2
        x = margin + col * (card_w + card_gap)
        cy = y + row * (card_h + card_gap)
        draw_rounded_rectangle(draw, (x, cy, x + card_w, cy + card_h), 18, soft, divider, 1)
        draw.ellipse((x + 18, cy + 23, x + 50, cy + 55), fill=accent)
        draw.text((x + 30 - 4, cy + 29), str(idx), font=font_tiny, fill=accent_text)
        draw.text((x + 66, cy + 20), get_badge_text(section).upper(), font=font_tiny, fill=muted)
        draw.text((x + 66, cy + 42), section["title"], font=font_small, fill=(17, 17, 17))

    if sections:
        y += ((len(sections) + 1) // 2) * (card_h + card_gap) + 22

    # Articles
    for idx, section in enumerate(sections, start=1):
        article_top = y
        article_h_min = 230
        x = margin

        # estimate text height
        temp_y = y + 112
        temp_y = draw_wrapped_text(
            draw, section["content"], x + 32, temp_y, font_body, (17, 17, 17), content_w - 64, 7
        )
        text_h = temp_y - (y + 112)

        images = section.get("images", [])
        image_area_h = 0
        prepared_images = []
        if images:
            img_w = (content_w - 64 - 18) // 2 if len(images) > 1 else content_w - 64
            row_heights = []
            for item in images:
                try:
                    sec_img = open_image_from_bytes(item["bytes"])
                    sec_img = resize_to_width(sec_img, img_w)
                    prepared_images.append(sec_img)
                    row_heights.append(sec_img.height)
                except Exception:
                    pass
            if prepared_images:
                if len(prepared_images) == 1:
                    image_area_h = prepared_images[0].height + 22
                else:
                    image_area_h = max(i.height for i in prepared_images[:2]) + 22
                    if len(prepared_images) > 2:
                        image_area_h += max(i.height for i in prepared_images[2:4]) + 18

        article_h = max(article_h_min, 126 + text_h + image_area_h + 34)

        draw_rounded_rectangle(draw, (x, y, x + content_w, y + article_h), 24, (255, 255, 255), divider, 1)
        draw.rounded_rectangle((x, y, x + content_w, y + 8), radius=4, fill=accent)

        badge = get_badge_text(section).upper()
        badge_w = draw.textbbox((0, 0), badge, font=font_tiny)[2] + 34
        draw_rounded_rectangle(draw, (x + 32, y + 34, x + 32 + badge_w, y + 66), 16, accent)
        draw.text((x + 49, y + 43), badge, font=font_tiny, fill=accent_text)

        num = f"0{idx}"
        draw.text((x + content_w - 82, y + 28), num, font=font_num, fill=divider)

        title = title_case_by_theme(section["title"], theme_style)
        draw.text((x + 32, y + 82), title, font=font_h2, fill=(17, 17, 17))

        content_y = y + 132
        content_y = draw_wrapped_text(
            draw, section["content"], x + 32, content_y, font_body, (17, 17, 17), content_w - 64, 7
        )

        if prepared_images:
            image_y = content_y + 22
            if len(prepared_images) == 1:
                img.paste(prepared_images[0], (x + 32, image_y))
            else:
                img_x = x + 32
                img_w = (content_w - 64 - 18) // 2
                for i, pimg in enumerate(prepared_images[:4]):
                    col = i % 2
                    row = i // 2
                    px = img_x + col * (img_w + 18)
                    py = image_y + row * (max(im.height for im in prepared_images[:2]) + 18)
                    img.paste(pimg, (px, py))

        y += article_h + 28

    draw.line((margin, y, margin + content_w, y), fill=divider, width=1)
    y += 18
    draw.text(
        (margin, y),
        "Generated by LO Taiwan Monthly Pulse Generator Prototype. Human review is required before publishing.",
        font=load_font(12, False),
        fill=muted
    )
    y += 40

    return img.crop((0, 0, W, y))


def image_to_bytes(image, fmt="JPEG"):
    buffer = io.BytesIO()
    save_kwargs = {}
    if fmt.upper() == "JPEG":
        save_kwargs["quality"] = 92
        image = image.convert("RGB")
    image.save(buffer, format=fmt, **save_kwargs)
    return buffer.getvalue()


def image_to_pdf_bytes(image):
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="PDF", resolution=144.0)
    return buffer.getvalue()


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
        "Article Badge Label",
        value="",
        placeholder=f"Example: {default_badge}, Big Moves, From the Field, Team Energy"
    )

    title = st.text_input(
        "Article Title",
        placeholder="Example: Promotions"
    )

    raw_content = st.text_area(
        "Article Content",
        placeholder="Paste or type the monthly update here...",
        height=160
    )

    uploaded_images = st.file_uploader(
        "Upload images for this article",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True
    )

    submitted = st.form_submit_button("Add Article")

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
                "images": images
            })

            st.session_state.form_counter += 1
            st.success("Article added successfully!")
            st.rerun()

        else:
            st.warning("Please enter both an article title and content.")


# -----------------------------
# Preview
# -----------------------------

st.header("2. Newsletter Preview")

top_badge_data = file_to_image_data(top_badge_file)

if len(st.session_state.sections) == 0:
    st.info("Add at least one article to generate the newsletter preview.")

else:
    col1, col2 = st.columns([0.65, 1.75])

    with col1:
        st.subheader("Added Articles")

        for i, section in enumerate(st.session_state.sections):
            badge_text = get_badge_text(section)

            with st.expander(f"{i + 1}. {section['category']} — {section['title']}"):
                st.caption(f"Badge: {badge_text}")
                st.write(section["content"])

                images = section.get("images", [])

                if images:
                    st.caption(f"Images: {len(images)} uploaded")
                else:
                    st.caption("Images: None")

                if st.button(f"Delete Article {i + 1}", key=f"delete_{i}"):
                    st.session_state.sections.pop(i)
                    st.rerun()

    with col2:
        st.subheader("Newsletter Draft")

        newsletter_html = generate_newsletter_html(
            newsletter_month,
            issue_label,
            editor_name,
            st.session_state.sections,
            visual_theme,
            layout_style,
            top_badge_data
        )

        components.html(
            newsletter_html,
            height=1150,
            scrolling=True
        )


# -----------------------------
# Export and Clear Buttons
# -----------------------------

st.markdown("---")

if st.session_state.sections:
    st.header("3. Export")

    try:
        rendered_image = render_newsletter_image(
            newsletter_month,
            issue_label,
            editor_name,
            st.session_state.sections,
            visual_theme,
            layout_style,
            top_badge_data
        )

        pdf_bytes = image_to_pdf_bytes(rendered_image)
        jpg_bytes = image_to_bytes(rendered_image, "JPEG")
        png_bytes = image_to_bytes(rendered_image, "PNG")

        file_base_name = f"LO_Taiwan_Monthly_Pulse_{newsletter_month.replace(' ', '_')}_{visual_theme}_{layout_style}"

        export_col1, export_col2, export_col3 = st.columns(3)

        with export_col1:
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=f"{file_base_name}.pdf",
                mime="application/pdf"
            )

        with export_col2:
            st.download_button(
                label="Download JPG",
                data=jpg_bytes,
                file_name=f"{file_base_name}.jpg",
                mime="image/jpeg"
            )

        with export_col3:
            st.download_button(
                label="Download PNG",
                data=png_bytes,
                file_name=f"{file_base_name}.png",
                mime="image/png"
            )

        with st.expander("Export image preview"):
            st.image(rendered_image, use_container_width=True)

    except Exception as e:
        st.error("Export failed.")
        st.caption(str(e))

if st.button("Clear All Articles"):
    st.session_state.sections = []
    st.session_state.form_counter += 1
    st.rerun()
