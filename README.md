# LO Taiwan Monthly Pulse Generator

A Streamlit prototype for generating LO Taiwan monthly newsletter drafts.

## What this version supports

- Newsletter-style editorial layout
- Optional top badge / header image upload
- Article badges and article images
- Continuous PDF export
- JPG export for email preview / inline email use
- PNG export for higher-quality image sharing

## Project structure

```text
lo-taiwan-newsletter-generator/
├── app.py
├── requirements.txt
└── README.md
```

## How to run locally

1. Install Python.
2. Open Terminal or Command Prompt in this folder.
3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Install Playwright Chromium for local PDF/JPG/PNG export:

```bash
playwright install chromium
```

5. Start the app:

```bash
streamlit run app.py
```

## Deployment notes

This app uses Playwright for PDF/JPG/PNG export. Chromium is installed on demand by the app if the browser is not already available.

## Notes

This is a prototype tool. Please avoid uploading confidential or sensitive company information during testing.
