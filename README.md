<div align="center">
  <img src="kabuli.png" alt="Project Kabuliwala" width="180"/>

  <h1>PROJECT KABULIWALA</h1>
  <p><b>Offline-First AI Triage Copilot for Post-Cyclone Infrastructure Assessment</b></p>
  
  <p>
    <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=Streamlit&logoColor=white" alt="Streamlit"/>
    <img src="https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python"/>
    <img src="https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite"/>
    <img src="https://img.shields.io/badge/Gemini_2.5_Flash-8E75B2?style=flat-square&logo=googlebard&logoColor=white" alt="Gemini"/>
  </p>
  
  <p><i>Engineered for the Bangladesh Local Government Engineering Department (LGED) & CRELIC Protocols</i></p>

  <p>
    <a href="[https://kabuliwala.streamlit.app/]"><b>View Live System Demonstration</b></a> 
  </p>
</div>

<hr>

## 1. Executive Summary

Following severe cyclone landfalls in coastal Bangladesh (e.g., Sidr, Amphan), normative SOS/D-Form reporting occurs within hours, but actual reconstruction funding via detailed Damage and Needs Assessment (DNA) workflows routinely lags 12 to 36 months. Furthermore, a 2020 Transparency International Bangladesh (TIB) study identified that up to 76.92% of coastal climate-resilient project values can be lost to fiduciary risks, primarily through material over-reporting and invoice discrepancies.

Project KABULIWALA is an offline-first, telemetry-verified AI triage ecosystem. It bridges the gap between multimodal AI perception and deterministic civil engineering mathematics, allowing LGED District Engineers to generate instant, cryptographically verifiable, and unalterable material requisitions in a disconnected disaster environment.

## 2. Core Architecture & Features

The platform explicitly decouples AI visual perception from engineering cost calculations to ensure absolute mathematical compliance with government rate schedules.

*   **Anti-Fraud Telemetry (EXIF/GPS Validation):** Bypasses manual entry by extracting hardware-stamped EXIF data. Ensures all damage reports are tied strictly to Bangladesh geographic boundaries (Lat: 20.5-26.6, Lon: 88.0-92.7). If EXIF data is stripped, the system flags a "Fraud Risk" and forces a manual override justification.
*   **Visual Triage Copilot:** Utilizes Google Gemini 2.5 Flash via Few-Shot In-Context Learning (ICL). The AI is constrained via Pydantic schemas to classify specific coastal damage mechanisms (e.g., Embankment Toe Erosion, Approach Slab Undermining, Pavement Stripping).
*   **The Expert Validation Gate:** Recognizing standard LLM hallucination variance, KABULIWALA isolates the AI to perception only. A human District Engineer must manually confirm or override the severity assessment before volumetric calculations execute.
*   **Deterministic BOM Engine:** Applies the historical LGED Schedule of Rates (SOR 2023 - Zone B) and BNBC-2020 volumetric heuristics to generate rapid Class-5 material estimates (e.g., routing Rebar at 114.00 BDT/kg and Geotextile Sandbags at 450.00 BDT/bag).
*   **Offline-First Vault & CRELIC Sync:** Built on an embedded SQLite instance to queue records during telecommunication blackouts. Features a thin-sync protocol to batch-export structured JSON/CSV data directly to the Climate Resilient Local Infrastructure Centre (CRELIC) databases upon network restoration.
*   **Native Bilingual Generation:** Exports procurement-ready D-Form PDFs in both English and Bengali, utilizing localized HTML-to-PDF rendering to accurately preserve complex Bengali text shaping (যুক্তাক্ষর).
<img width="4700" height="6650" alt="Part a pdf" src="https://github.com/user-attachments/assets/a26a3947-2de9-4bb1-92ea-a81c6141d04b" />

## 3. Technology Stack

*   **Frontend / UI:** Streamlit (Custom Metric Dashboard), HTML/CSS Injection
*   **Backend / Persistence:** Python, SQLite3, Pandas
*   **AI / ML:** Google GenAI SDK (gemini-2.5-flash), Few-Shot ICL, Pydantic validation
*   **Geospatial:** PIL (Pillow), EXIF parsing
*   **Reporting:** Jinja2 / HTML-to-PDF rendering

## 4. Engineering Disclaimer

> **CLASS 5 ESTIMATE ONLY:** Within LGED and BNBC practice, parametric estimates produced by this software are suitable only for preliminary screening, SOS/D-Form reporting, and emergency budgeting. They do not satisfy the deterministic analysis, safety, and legal accountability requirements of the Disaster Management Act or BNBC-2020. All reconstruction packages must be re-derived by a licensed structural engineer from code-compliant loads and vetted drawings before inclusion in any LGED Bill of Quantities (BOQ) or tender contract.

## 5. Local Installation & Deployment

To execute the triage copilot in a local development environment:

**1. Clone the repository**
```bash
git clone [https://github.com/yourusername/cyclone-infrastructure-assessor.git](https://github.com/yourusername/cyclone-infrastructure-assessor.git)
cd cyclone-infrastructure-assessor
```
**2. Initialize a virtual environment and install dependencies**

```Bash
python -m venv venv
source venv/bin/activate  # Windows systems: venv\Scripts\activate
pip install -r requirements.txt
```
**3. Configure Environment Secrets**
Create a .streamlit directory and configure the secrets protocol.

```Bash
mkdir .streamlit
touch .streamlit/secrets.toml
```
Input credentials into .streamlit/secrets.toml:

```Ini, TOML

GOOGLE_API_KEY = "your_gemini_api_key_here"
admin_password = "your_secure_password"
```
**4. Execute the Application**

```Bash
streamlit run app.py
```
**6. Evaluation & Metrics**

The visual perception module was benchmarked against 10 historical, localized cyclone damage images originating from the Chittagong topography.

**Zero-Shot Visual Accuracy:** 90.0%

**Safety Threshold Trigger:** 100% of test cases yielding a confidence score of < 0.70 (e.g., heavy debris occlusion) successfully halted automated BOM generation and forced mandatory manual override, ensuring fail-safe states in chaotic field conditions.
