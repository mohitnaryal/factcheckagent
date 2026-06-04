# Fact-Check Agent

## Overview

Fact-Check Agent is a web application that automatically verifies claims found in PDF documents.

The application:

- Extracts factual claims from PDFs
- Searches live web data
- Verifies claims against current information
- Labels claims as:
  - Verified
  - Inaccurate
  - False / Not Enough Evidence
- Generates a downloadable report

## Tech Stack

- Streamlit
- OpenAI API
- Tavily Search API
- PyMuPDF
- Pandas

## Features

- PDF Upload
- Claim Extraction
- Live Web Verification
- Confidence Scores
- Source References
- CSV Report Download

## Installation

```bash
pip install -r requirements.txt
```

## Run Locally

```bash
streamlit run app.py
```

## Environment Variables

Add the following secrets:

```toml
OPENAI_API_KEY = "your_openai_key"
TAVILY_API_KEY = "your_tavily_key"
```

## Deployment

Deploy on Streamlit Cloud.

## Author

Mohit Naryal
