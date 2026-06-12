import streamlit as st
from PIL import Image
from google import genai
from google.genai import types
import json
from fpdf import FPDF
from pydantic import BaseModel
from lged_knowledge import LGED_CONTEXT

# 1. Page Configuration & API Initialisation
st.set_page_config(page_title="Infrastructure Assessor", page_icon="🏗️", layout="centered")

# Secure Client Initialization via Streamlit Secrets
client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

# 2. Structured Output Schema Definition
class AssessmentReport(BaseModel):
    damage_type: str
    severity: str
    materials_needed: list[str]
    estimated_repair_time: str

# 3. PDF Report Generator Function
def create_procurement_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # Header Section
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "EMERGENCY PROCUREMENT & REQUISITION REPORT", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, "Generated via Post-Cyclone AI Infrastructure Assessor (SciBlitz 2026)", ln=True, align="C")
    pdf.ln(10)
    
    # Section 1: Metrics
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "1. Disaster Impact Metrics", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font("Arial", "", 11)
    pdf.cell(50, 8, "Damage Severity:", 0)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, f"{data.get('severity', 'N/A')}", ln=True)
    
    pdf.set_font("Arial", "", 11)
    pdf.cell(50, 8, "Est. Repair Timeline:", 0)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, f"{data.get('estimated_repair_time', 'N/A')}", ln=True)
    pdf.ln(4)
    
    # Section 2: Assessment
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "2. Structural Engineering Assessment", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, f"Failure Type Identified: {data.get('damage_type', 'N/A')}")
    pdf.ln(6)
    
    # Section 3: BOM Table
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "3. Required Emergency Materials (Bill of Materials)", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(15, 8, "Item", 1, 0, "C")
    pdf.cell(165, 8, "Material Description & Estimated Quantity", 1, 1, "L")
    
    pdf.set_font("Arial", "", 11)
    for i, item in enumerate(data.get("materials_needed", []), 1):
        pdf.cell(15, 8, str(i), 1, 0, "C")
        pdf.cell(165, 8, f" {item}", 1, 1, "L")
        
    pdf.ln(15)
    pdf.set_font("Arial", "I", 9)
    pdf.cell(0, 5, "DISCLAIMER: AI-Generated Triage Estimate. Requires formal validation by LGED Executive Engineer.", ln=True, align="C")
    
    return bytes(pdf.output())

# 4. Main UI Architecture
st.title("🏗️ Post-Cyclone Infrastructure Assessor")
st.subheader("Automated Procurement Engine for a Flood-Resilient Bangladesh")
st.divider()

# --- Contextual Grounding UI ---
st.subheader("📍 Field Agent Context Data")
st.write("Provide structural dimensions to calibrate the AI model's scale.")

col1, col2 = st.columns(2)
with col1:
    gps_location = st.text_input("GPS Location (Lat/Long)", placeholder="e.g., 22.3569, 91.7832 (Chattogram)")
    infra_type = st.selectbox("Infrastructure Type", ["RC Bridge", "Culvert", "LGED Office Building", "Coastal Embankment"])
with col2:
    est_span = st.number_input("Estimated Span/Area (sq meters)", min_value=1, value=50)
    current_status = st.selectbox("Current Status", ["Active Collapse", "Stabilized", "Submerged"])

st.divider()

# ---> MAKE SURE THIS LINE ONLY APPEARS ONCE <---
uploaded_file = st.file_uploader("Upload Infrastructure Damage Image (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)
    
    # ... (rest of your system_instruction code continues here)
    
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)
    
    system_instruction = f"""
    You are a senior civil engineer at the LGED, Bangladesh, operating as a Rapid Triage Copilot.
    CRITICAL: You must classify every image provided. Do not use 'Unknown'.

    FIELD AGENT CONTEXT (USE THIS FOR SCALE):
    - Location: {gps_location}
    - Infrastructure Type: {infra_type}
    - Estimated Affected Area/Span: {est_span} sq meters
    - Current Status: {current_status}

    KNOWLEDGE BASE GROUNDING:
    {LGED_CONTEXT}

    Task:
    1. Identify the damage type from the KNOWLEDGE BASE. 
    2. Assign Severity based on visual indicators.
    3. Generate a Bill of Materials. YOU MUST USE THE 'Estimated Affected Area' ({est_span} sqm) to calculate realistic quantities of materials based on standard LGED ratios.
    4. Estimate repair time based on typical Bangladesh site conditions.
    
    The 'estimated_repair_time' field must be a SINGLE clean string (e.g., '4-7 months').
    """

    if st.button("Run AI Damage Assessment", type="primary"):
        with st.spinner("Analyzing structural integrity with LGED grounding..."):
            try:
                # Primary Content Generation Call utilizing Structured Output Schemas
                try:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[system_instruction, image],
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=AssessmentReport,
                        ),
                    )
                except Exception as model_error:
                    # Automatic Fallback Route for server congestion
                    if "503" in str(model_error) or "429" in str(model_error):
                        st.warning("Primary server congested. Routing to secure fallback model...")
                        response = client.models.generate_content(
                            model='gemini-2.5-pro',  # Upgraded to modern v2 target string
                            contents=[system_instruction, image],
                            config=types.GenerateContentConfig(
                                response_mime_type="application/json",
                                response_schema=AssessmentReport,
                            ),
                        )
                    else:
                        raise model_error
                
                # Zero string slicing required; response is guaranteed to conform to schema
                ai_data = json.loads(response.text)
                
                st.success("Analysis Complete.")
                st.subheader("Structural Assessment Report")
                
                col1, col2 = st.columns(2)
                col1.metric("Damage Severity", ai_data.get("severity", "Unknown"))
                col2.metric("Est. Repair Time", ai_data.get("estimated_repair_time", "Unknown"))
                
                st.write("**Damage Type:**", ai_data.get("damage_type", "Unknown"))
                st.write("**Required Bill of Materials (BOM):**")
                for item in ai_data.get("materials_needed", []):
                    st.write(f"- {item}")
                
                # Document Automation Generation Sequence
                pdf_bytes = create_procurement_pdf(ai_data)
                st.divider()
                st.subheader("📋 Document Automation")
                
                st.download_button(
                    label="Download Official Procurement PDF",
                    data=pdf_bytes,
                    file_name="Emergency_Procurement_Report.pdf",
                    mime="application/pdf",
                    type="primary"
                )
                
            except Exception as e:
                st.error(f"Agent Pipeline Failed: {e}")