import streamlit as st
from PIL import Image
from google import genai       # Corrected modern import
import json
from fpdf import FPDF

# 1. Page Configuration & API Setup
st.set_page_config(page_title="Infrastructure Assessor", page_icon="🏗️", layout="centered")

# Force-inject the API key directly into the client instance
client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

def create_procurement_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # Set Document Header (Simulating an official LGED/Government format)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "EMERGENCY PROCUREMENT & REQUISITION REPORT", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, "Generated via Post-Cyclone AI Infrastructure Assessor (SciBlitz 2026)", ln=True, align="C")
    pdf.ln(10)
    
    # Metadata Block
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "1. Disaster Impact Metrics", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font("Arial", "", 11)
    pdf.cell(50, 8, f"Damage Severity:", 0)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, f"{data.get('severity', 'N/A')}", ln=True)
    
    pdf.set_font("Arial", "", 11)
    pdf.cell(50, 8, f"Est. Repair Timeline:", 0)
    pdf.cell(0, 8, f"{data.get('estimated_repair_time', 'N/A')}", ln=True)
    pdf.ln(4)
    
    # Technical Assessment
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "2. Structural Engineering Assessment", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, f"Failure Type Identified: {data.get('damage_type', 'N/A')}")
    pdf.ln(6)
    
    # Bill of Materials Table
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "3. Required Emergency Materials (Bill of Materials)", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    # Table Header
    pdf.set_font("Arial", "B", 11)
    pdf.cell(15, 8, "Item", 1, 0, "C")
    pdf.cell(165, 8, "Material Description & Estimated Quantity", 1, 1, "L")
    
    # Table Rows
    pdf.set_font("Arial", "", 11)
    for i, item in enumerate(data.get("materials_needed", []), 1):
        pdf.cell(15, 8, str(i), 1, 0, "C")
        pdf.cell(165, 8, f" {item}", 1, 1, "L")
        
    pdf.ln(15)
    pdf.set_font("Arial", "I", 9)
    pdf.cell(0, 5, "This is an automated engineering requisition generated for local government assessment.", ln=True, align="C")
    
    # Output PDF as bytes
    return bytes(pdf.output())
# 2. Header Section
st.title("🏗️ Post-Cyclone Infrastructure Assessor")
st.subheader("Automated Procurement Engine for a Flood-Resilient Bangladesh")
st.divider()

# 3. File Upload Interface
uploaded_file = st.file_uploader("Upload Infrastructure Damage Image (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)
    
    # 4. The System Prompt (The Brain)
    system_instruction = """
    You are an expert Bangladeshi civil engineer specializing in post-cyclone disaster recovery.
    Analyze this image of damaged infrastructure. You MUST return your analysis STRICTLY as a JSON object with the following keys, and nothing else:
    - "damage_type": A short technical description of the structural failure.
    - "severity": Must be exactly "Low", "Medium", "High", or "Critical".
    - "materials_needed": A list of specific raw materials needed for emergency repair.
    - "estimated_repair_time": A short string estimating the time to repair.
    Output only the raw JSON.
    """

    if st.button("Run AI Damage Assessment", type="primary"):
        with st.spinner("Analyzing structural integrity..."):
            try:
                # Attempt 1: The Primary Flagship Model
                try:
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[system_instruction, image]
                    )
                # Attempt 2: The Fallback Route
                except Exception as model_error:
                    if "503" in str(model_error) or "429" in str(model_error):
                        st.warning("Primary server congested. Routing to secure fallback model...")
                        response = client.models.generate_content(
                            model='gemini-1.5-pro',
                            contents=[system_instruction, image]
                        )
                    else:
                        raise model_error # If it's a different error, let it fail normally
                
                # Parse output
                raw_text = response.text.strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:-3].strip()
                elif raw_text.startswith("```"):
                    raw_text = raw_text[3:-3].strip()
                    
                ai_data = json.loads(raw_text)
                
                st.success("Analysis Complete.")
                

                st.subheader("Structural Assessment Report")
                
                # Display the extracted data
                col1, col2 = st.columns(2)
                col1.metric("Damage Severity", ai_data.get("severity", "Unknown"))
                col2.metric("Est. Repair Time", ai_data.get("estimated_repair_time", "Unknown"))
                
                st.write("**Damage Type:**", ai_data.get("damage_type", "Unknown"))
                st.write("**Required Bill of Materials (BOM):**")
                for item in ai_data.get("materials_needed", []):
                    st.write(f"- {item}")
                # Generate the binary PDF stream from the session data
                pdf_bytes = create_procurement_pdf(ai_data)
                
                st.divider()
                st.subheader("📋 Document Automation")
                
                # Streamlit Native Download Button
                st.download_button(
                    label="Download Official Procurement PDF",
                    data=pdf_bytes,
                    file_name="Emergency_Procurement_Report.pdf",
                    mime="application/pdf",
                    type="primary"
                )
            except Exception as e:
                st.error(f"Agent Pipeline Failed: {e}")