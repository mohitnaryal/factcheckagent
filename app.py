import streamlit as st
import fitz
import pandas as pd
from google import genai
from tavily import TavilyClient
import json

st.set_page_config(page_title="Fact-Check Agent", layout="wide")

st.title("Fact-Check Agent")
st.write("Upload a PDF. The app extracts factual claims and verifies them using live web data.")

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]

client = genai.Client(api_key=GEMINI_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)


def clean_json(output):
    output = output.replace("```json", "").replace("```", "").strip()
    return output


def extract_pdf_text(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text[:12000]


def ask_llm(prompt):
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt
    )
    return response.text


def extract_claims(text):
    prompt = f"""
Extract 8-15 factual claims from this PDF text.
Focus on numbers, dates, statistics, financial data, technical claims, rankings, company facts.

Return ONLY valid JSON array:
[
  {{
    "claim": "...",
    "claim_type": "stat/date/financial/technical/company",
    "search_query": "..."
  }}
]

PDF TEXT:
{text}
"""
    output = ask_llm(prompt)
    output = clean_json(output)
    return json.loads(output)


def verify_claim(claim, search_query):
    search = tavily.search(query=search_query, max_results=5)

    evidence = ""
    urls = []

    for r in search.get("results", []):
        evidence += f"Title: {r.get('title')}\n"
        evidence += f"Content: {r.get('content')}\n"
        evidence += f"URL: {r.get('url')}\n\n"
        urls.append(r.get("url"))

    prompt = f"""
You are a strict fact checker.

Claim:
{claim}

Web evidence:
{evidence}

Classify the claim as one of:
Verified
Inaccurate
False / Not enough evidence

If the claim is inaccurate or false, provide the correct fact if available.

Return ONLY valid JSON:
{{
  "status": "...",
  "corrected_fact": "...",
  "explanation": "...",
  "confidence": 0-100
}}
"""
    output = ask_llm(prompt)
    output = clean_json(output)
    result = json.loads(output)
    result["sources"] = urls[:3]
    return result


uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("Extracting PDF text..."):
        text = extract_pdf_text(uploaded_file)

    if not text.strip():
        st.error("PDF text extract nahi ho paya. Scanned PDF ho sakta hai.")
    else:
        st.success("PDF text extracted successfully.")

        if st.button("Run Fact Check"):
            rows = []

            with st.spinner("Extracting claims..."):
                claims = extract_claims(text)

            progress = st.progress(0)

            for i, item in enumerate(claims):
                claim = item.get("claim", "")
                query = item.get("search_query", claim)

                try:
                    result = verify_claim(claim, query)

                    rows.append({
                        "Claim": claim,
                        "Type": item.get("claim_type", ""),
                        "Status": result.get("status", ""),
                        "Correct Fact": result.get("corrected_fact", ""),
                        "Explanation": result.get("explanation", ""),
                        "Confidence": result.get("confidence", ""),
                        "Sources": "\n".join(result.get("sources", []))
                    })

                except Exception as e:
                    rows.append({
                        "Claim": claim,
                        "Type": item.get("claim_type", ""),
                        "Status": "Error",
                        "Correct Fact": "",
                        "Explanation": str(e),
                        "Confidence": "",
                        "Sources": ""
                    })

                progress.progress((i + 1) / len(claims))

            df = pd.DataFrame(rows)

            st.subheader("Fact Check Report")
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode("utf-8")

            st.download_button(
                "Download CSV Report",
                csv,
                "fact_check_report.csv",
                "text/csv"
            )
