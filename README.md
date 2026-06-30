# LO Taiwan Monthly Pulse Generator

A Streamlit prototype for generating LO Taiwan monthly newsletter drafts.

## What this version supports

- Newsletter-style editorial layout
- Optional top badge / header image upload
- Article badges and article images
- PDF export
- JPG export for email preview / inline email use
- PNG export for higher-quality image sharing

## Important technical note

This version does **not** use Playwright or Chromium. Exports are rendered with Pillow, which is more stable on Streamlit Community Cloud.

## How to run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Notes

This is a prototype tool. Please avoid uploading confidential or sensitive company information during testing.
