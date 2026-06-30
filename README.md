# LO Taiwan Monthly Pulse Generator

A prototype Streamlit tool for generating LO Taiwan monthly newsletter drafts and exporting them as a continuous PDF.

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

4. Install Playwright Chromium for PDF export:

```bash
playwright install chromium
```

5. Start the app:

```bash
streamlit run app.py
```

## Notes

This is a prototype tool. Please avoid uploading confidential or sensitive company information during testing.

The PDF export feature uses Playwright. If the PDF download button fails, run:

```bash
playwright install chromium
```
