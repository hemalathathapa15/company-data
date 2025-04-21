## Overview

This application extracts and aggregates company information from various online sources using domain names as input. The process involves two main steps:

1. Extracting domain names from company data using `domain_names.py`
2. Scraping company details from these domains using `scrape.py`

## Prerequisites

1. **Python 3.8+**
   - Ensure that you are using Python 3.8 or higher for compatibility with all required packages.

2. **Required Python Packages**
   - Install the following packages via `pip`:
     ```bash
     pip install playwright google-generativeai pandas asyncio python-dotenv google-search
     ```

3. **Gemini API Key**
   - You'll need a Gemini API key.

## Usage

**Step 1: Extract Domain Names**

Run the `domain_names.py` script using the following command:

```bash
python domain_names.py
```

**Input:**
Company information (names)

**Output:**
`company_domains.csv` - A list of extracted domain names

**Step 2: Scrape Company Details**

Execute the `scrape.py` script with the generated `company_domains.csv` file:
        
```bash
python scrape.py
```

**Input:**
`company_domains.csv` 

**Output:**
`company_details_output.csv` 






