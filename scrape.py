import asyncio
from playwright.async_api import async_playwright
import google.generativeai as genai
import pandas as pd
import json

# Gemini API key
genai.configure(api_key="AIzaSyAgMkVJLnykG3SvVzPVnERfFfNpxX_KznQ")


# Fields to extract
CSV_COLUMNS = [
    "website", "company_name", "description", "software_classification", 
    "enterprise_grade_classification", "industry", "customers_names_list", 
    "employee_headcount", "investors", "geography", "parent_company", 
    "address_street", "address_zip", "address_city", "address_country_region", 
    "finance", "email", "phone"
]

async def scrape_website(url: str) -> str:
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
            content = await page.content()
            # Remove <style> and <script> tags
            content = await page.evaluate("""
                () => {
                    document.querySelectorAll('style, script').forEach(el => el.remove());
                    return document.body.innerText;
                }
            """)
            await browser.close()
            return content
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return ""

def get_rag_results(raw_text: str, company_name: str):
    prompt = f"""
You are a company information extractor. Based on the following company website content, extract the requested fields and return **only a valid JSON object**.

Your goal is to fill the following fields. If a value cannot be found in the text, return "Not found". Make your best effort to infer common company info (e.g., address, contact, description) from the full context. Prioritize extracting accurate email addresses, phone numbers, and parent company information.

Here are the fields you must extract:
{{
  "website": "{company_name}",
  "company_name": "Full legal name of the company, can appear beside the logo on the homepage.",
  "description": "A concise summary describing what this company does, based on the text.",
  "software_classification": "Describe if the company is a SaaS provider, product-based, service-based, etc.",
  "enterprise_grade_classification": "Is this an enterprise-grade company? (e.g., SMB, Enterprise, Startup,Top-Tier, Secure etc.)",
  "industry": "Industry or domain the company operates in (e.g., Finance, Healthcare, IT Services).",
  "customers_names_list": "List of notable customers or clients mentioned, separated by commas.",
  "employee_headcount": "Approximate number of employees or range (e.g., 51-200).",
  "investors": "List of investors if mentioned.",
  "geography": "Mention countries or regions where the company operates or has a presence.",
  "parent_company": "Name of parent company, if any. Look for phrases like 'subsidiary of', 'part of', 'owned by','acquired by' or similar.",
  "address_street": "Street address of headquarters or main office.",
  "address_zip": "Postal/ZIP code.",
  "address_city": "City of headquarters or main office.",
  "address_country_region": "Country or region.",
  "finance": "Any financial info like revenue, funding rounds, profits, etc., if available.",
  "email": "Official company email address, preferably from contact section. Ensure it's extracted accurately.",
  "phone": "Phone number found on the site, if any. Use country codes where possible."
}}
Company Content:
\"\"\"
{raw_text}
\"\"\"
"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print("Gemini Error:", e)
        return "{}"

def fill_no_website_row():
    return {col: "no website provided" for col in CSV_COLUMNS}


def read_domains_from_csv(input_csv_path: str):

    # Use fallback encoding
    df = pd.read_csv(input_csv_path, encoding="ISO-8859-1")

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    if "domain" not in df.columns or "company_name" not in df.columns:
        raise ValueError("CSV must contain 'Company Name' and 'Domain' columns.")

    return df.to_dict("records")



async def main_from_csv(input_csv_path):
    data = read_domains_from_csv(input_csv_path)
    rows = []

    for entry in data:
        website = entry["domain"].strip()
        company_name = entry["company_name"].strip()


        if not website:
            rows.append(fill_no_website_row())
            continue

        print(f"Processing: {website}")
        raw_text = await scrape_website(website)
        if not raw_text:
            rows.append({col: f"Failed to scrape {website}" for col in CSV_COLUMNS})
            continue

        structured = get_rag_results(raw_text, company_name)

        try:
            json_start = structured.find('{')
            json_end = structured.rfind('}') + 1
            structured_json = structured[json_start:json_end]
            structured_data = json.loads(structured_json)
            structured_data["website"] = website
            row = {col: structured_data.get(col, "") for col in CSV_COLUMNS}
            rows.append(row)
        except Exception as e:
            print(f"Error parsing Gemini response for {website}: {e}")
            rows.append({col: f"Error extracting {website}" for col in CSV_COLUMNS})

    df = pd.DataFrame(rows)
    df.to_csv("company_details.csv", index=False)
    print("Saved to company_details.csv")


if __name__ == "__main__":
    csv_input_file = "company.csv"  
    asyncio.run(main_from_csv(csv_input_file))
