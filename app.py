import streamlit as st
import streamlit.components.v1 as components

import base64
import html
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
st.sidebar.write("Prototype Version 3.0")
st.sidebar.caption("Newsletter layout with PDF, JPG, and PNG export.")


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
        <img
            class="top-badge-image"
            src="data:{mime};base64,{encoded}"
            alt="Newsletter badge"
        >
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
                background:
                    linear-gradient(135deg, {theme_style["soft_background"]} 0%, #ffffff 58%);
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
                background:
                    linear-gradient(135deg, {theme_style["soft_background"]} 0%, #ffffff 70%);
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

            .article-card::after {{
                content: "";
                position: absolute;
                top: 18px;
                right: 18px;
                width: 42px;
                height: 4px;
                background: {theme_style["accent"]};
                border-radius: 999px;
                opacity: 0.22;
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

            .compact-images:empty {{
                display: none;
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

            @media print {{
                html, body {{
                    width: 100%;
                    background: #ffffff;
                }}

                .page {{
                    max-width: none;
                    padding: 24px 38px 32px 38px;
                    box-shadow: none;
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


def launch_chromium(playwright):
    try:
        return playwright.chromium.launch(args=["--no-sandbox"])
    except Exception:
        return playwright.chromium.launch(
            executable_path="/usr/bin/chromium",
            args=["--no-sandbox"]
        )


def html_to_pdf_bytes(newsletter_html):
    with sync_playwright() as p:
        browser = launch_chromium(p)

        page = browser.new_page(
            viewport={
                "width": 1000,
                "height": 1400
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
            width="1000px",
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


def html_to_image_bytes(newsletter_html, image_type="jpeg"):
    with sync_playwright() as p:
        browser = launch_chromium(p)

        page = browser.new_page(
            viewport={
                "width": 1000,
                "height": 1400
            },
            device_scale_factor=2
        )

        page.set_content(newsletter_html, wait_until="networkidle")

        screenshot_kwargs = {
            "full_page": True,
            "type": image_type
        }

        if image_type == "jpeg":
            screenshot_kwargs["quality"] = 92

        image_bytes = page.screenshot(**screenshot_kwargs)

        browser.close()

    return image_bytes


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
    newsletter_html = generate_newsletter_html(
        newsletter_month,
        issue_label,
        editor_name,
        st.session_state.sections,
        visual_theme,
        layout_style,
        top_badge_data
    )

    st.header("3. Export")

    try:
        pdf_bytes = html_to_pdf_bytes(newsletter_html)
        jpg_bytes = html_to_image_bytes(newsletter_html, image_type="jpeg")
        png_bytes = html_to_image_bytes(newsletter_html, image_type="png")

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

    except Exception as e:
        st.error("Export failed. Please make sure Playwright and Chromium are installed.")
        st.code("pip install playwright\nplaywright install chromium")
        st.caption(str(e))

if st.button("Clear All Articles"):
    st.session_state.sections = []
    st.session_state.form_counter += 1
    st.rerun()
