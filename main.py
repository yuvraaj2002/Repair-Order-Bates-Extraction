import streamlit as st
import logging
import json
import io
from datetime import datetime
from utils.ocr_utils import PdfProcessor
from utils.llm_utils import LLMService
from utils.extraction_utils import PDFTextExtractor

# ------------------- Page Configuration ------------------- #
st.set_page_config(
    page_title="Legal OCR Console - Bates & RO Extraction",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------- Logging Setup ------------------- #
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting Streamlit app...")

# ------------------- Service Initialization ------------------- #
def init_service(service_cls, name: str):
    try:
        service = service_cls()
        logger.info(f"{name} initialized successfully.")
        return service
    except Exception as e:
        logger.error(f"Failed to initialize {name}: {str(e)}", exc_info=True)
        st.error(f"Failed to initialize {name} service. Check logs.")
        st.stop()

pdf_service = init_service(PdfProcessor, "PdfProcessor")
llm_service = init_service(LLMService, "LLMService")
extraction_service = init_service(PDFTextExtractor, "PDFTextExtractor")

# ------------------- Session State Initialization ------------------- #
if 'processing_stage' not in st.session_state:
    # 1 = Upload, 2 = Document Type Identification, 3 = Custom Processing Pipeline, 4 = Extraction & Export
    st.session_state.processing_stage = 1
if 'extraction_complete' not in st.session_state:
    st.session_state.extraction_complete = False
if 'extraction_results' not in st.session_state:
    st.session_state.extraction_results = None

# ------------------- Custom CSS ------------------- #
def inject_custom_css():
    st.markdown(
        """
        <style>
            /* Import Professional Font */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            /* Global Styles */
            * {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }
            
            /* Main Container */
            .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
                max-width: 1200px;
            }
            
            /* Card Component */
            .card {
                background: #ffffff;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.06);
                margin-bottom: 25px;
                border: 1px solid #e8eaed;
            }
            
            /* Header Styles */
            .main-header {
                text-align: center;
                padding: 30px 0 20px 0;
                margin-bottom: 35px;
            }
            
            .main-title {
                font-size: 2.5rem;
                font-weight: 700;
                color: #1C2D4A;
                margin-bottom: 10px;
                letter-spacing: -0.5px;
            }
            
            .main-subtitle {
                font-size: 1.1rem;
                color: #5F6C7B;
                line-height: 1.6;
                max-width: 900px;
                margin: 0 auto;
                font-weight: 400;
            }
            
            /* Step Indicator */
            .step-indicator {
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 35px 0;
                padding: 25px;
                background: #f8f9fa;
                border-radius: 12px;
            }
            
            .step {
                display: flex;
                align-items: center;
                padding: 12px 20px;
                background: #e8eaed;
                color: #5F6C7B;
                border-radius: 8px;
                font-weight: 500;
                font-size: 0.95rem;
                transition: all 0.3s ease;
            }
            
            .step.active {
                background: #1C2D4A;
                color: white;
                box-shadow: 0 4px 12px rgba(28, 45, 74, 0.2);
            }
            
            .step.complete {
                background: #DAF5DB;
                color: #1e7e34;
            }
            
            .step-arrow {
                margin: 0 15px;
                color: #9ca3af;
                font-size: 1.2rem;
            }
            
            /* Upload Zone */
            .upload-zone {
                text-align: center;
                padding: 50px 30px;
                background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                border: 2px dashed #cbd5e0;
                border-radius: 12px;
                transition: all 0.3s ease;
            }
            
            .upload-zone:hover {
                border-color: #1C2D4A;
                background: #ffffff;
            }
            
            .upload-icon {
                font-size: 3rem;
                margin-bottom: 15px;
                color: #5F6C7B;
            }
            
            /* Success Message */
            .success-badge {
                display: inline-flex;
                align-items: center;
                padding: 10px 20px;
                background: #DAF5DB;
                color: #1e7e34;
                border-radius: 8px;
                font-weight: 500;
                margin: 15px 0;
            }
            
            /* Info Message */
            .info-badge {
                display: inline-flex;
                align-items: center;
                padding: 10px 20px;
                background: #DDEBFF;
                color: #004085;
                border-radius: 8px;
                font-weight: 500;
                margin: 15px 0;
            }
            
            /* Section Headers */
            .section-header {
                font-size: 1.4rem;
                font-weight: 600;
                color: #1C2D4A;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
            }
            
            .section-icon {
                margin-right: 10px;
                font-size: 1.5rem;
            }
            
            /* Metrics Grid */
            div[data-testid="metric-container"] {
                background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                border: 1px solid #e8eaed;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            }
            
            div[data-testid="metric-container"] > label {
                color: #5F6C7B !important;
                font-weight: 500 !important;
                font-size: 0.9rem !important;
            }
            
            div[data-testid="metric-container"] > div {
                color: #1C2D4A !important;
                font-weight: 700 !important;
                font-size: 2rem !important;
            }
            
            /* Buttons */
            .stButton > button {
                background: linear-gradient(135deg, #1C2D4A 0%, #2d4a6e 100%);
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 1.05rem;
                font-weight: 600;
                border-radius: 10px;
                transition: all 0.3s ease;
                box-shadow: 0 4px 12px rgba(28, 45, 74, 0.2);
            }
            
            .stButton > button:hover {
                background: linear-gradient(135deg, #0f1c2e 0%, #1C2D4A 100%);
                box-shadow: 0 6px 16px rgba(28, 45, 74, 0.3);
                transform: translateY(-2px);
            }
            
            .stDownloadButton > button {
                background: white;
                color: #1C2D4A;
                border: 2px solid #1C2D4A;
                padding: 12px 24px;
                font-size: 0.95rem;
                font-weight: 600;
                border-radius: 8px;
                transition: all 0.3s ease;
            }
            
            .stDownloadButton > button:hover {
                background: #1C2D4A;
                color: white;
            }
            
            /* Progress Bar */
            .stProgress > div > div {
                background-color: #1C2D4A;
            }
            
            /* Expander */
            .streamlit-expanderHeader {
                font-weight: 600;
                color: #1C2D4A;
                background: #f8f9fa;
                border-radius: 8px;
                padding: 12px;
            }
            
            /* Footer */
            .footer {
                text-align: center;
                padding: 30px 0 10px 0;
                margin-top: 50px;
                border-top: 1px solid #e8eaed;
                color: #9ca3af;
                font-size: 0.9rem;
            }
            
            /* Sidebar Styling */
            .css-1d391kg, [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0f172a 0%, #1C2D4A 60%, #111827 100%);
                color: #e5e7eb;
            }

            [data-testid="stSidebar"] * {
                color: #e5e7eb !important;
            }

            [data-testid="stSidebar"] hr {
                border-color: #1f2937 !important;
            }

            [data-testid="stSidebar"] .stRadio label {
                color: #e5e7eb !important;
            }

            [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
                background: transparent !important;
            }
            
            /* Status Messages */
            .status-processing {
                padding: 15px;
                background: #FFF3CD;
                border-left: 4px solid #FFC107;
                border-radius: 6px;
                margin: 10px 0;
                font-weight: 500;
            }
            
            .status-success {
                padding: 15px;
                background: #DAF5DB;
                border-left: 4px solid #28a745;
                border-radius: 6px;
                margin: 10px 0;
                font-weight: 500;
            }
            
            /* File Badge */
            .file-badge {
                display: inline-flex;
                align-items: center;
                padding: 12px 20px;
                background: #DDEBFF;
                border-radius: 8px;
                margin: 10px 0;
                font-weight: 500;
                color: #004085;
            }
            
            /* Recommendation Text */
            .recommendation {
                font-size: 0.9rem;
                color: #6c757d;
                font-style: italic;
                margin-top: 10px;
            }
        </style>
        """, 
        unsafe_allow_html=True
    )
    logger.debug("Custom CSS injected.")

inject_custom_css()

# ------------------- Sidebar Configuration ------------------- #
def config_sidebar():
    with st.sidebar:
        st.markdown("### ⚙️ Configuration Panel")
        st.markdown("---")
        
        st.markdown("**Output Format**")
        output_format = st.radio(
            "Select export format:",
            ("Excel", "CSV"),
            help="Choose how you want to download the extracted data"
        )
        
        st.markdown("---")
        st.markdown("**About**")
        st.info(
            "This tool uses advanced OCR and AI to extract Repair Orders and Bates Numbers from legal documents with high accuracy."
        )
        
    logger.info(f"User selected output format: {output_format}")
    return output_format

output_format = config_sidebar()

# ------------------- Step Indicator Component ------------------- #
def render_step_indicator(current_stage):
    step1_class = "complete" if current_stage > 1 else ("active" if current_stage == 1 else "")
    step2_class = "complete" if current_stage > 2 else ("active" if current_stage == 2 else "")
    step3_class = "complete" if current_stage > 3 else ("active" if current_stage == 3 else "")
    step4_class = "active" if current_stage == 4 else ""
    
    st.markdown(
        f"""
        <div class="step-indicator">
            <div class="step {step1_class}">
                <span style="margin-right: 8px;">📄</span>
                Step 1 — Upload PDF
            </div>
            <div class="step-arrow">→</div>
            <div class="step {step2_class}">
                <span style="margin-right: 8px;">🔍</span>
                Step 2 — Detect Document Type
            </div>
            <div class="step-arrow">→</div>
            <div class="step {step3_class}">
                <span style="margin-right: 8px;">🧩</span>
                Step 3 — Run Processing Pipeline
            </div>
            <div class="step-arrow">→</div>
            <div class="step {step4_class}">
                <span style="margin-right: 8px;">📊</span>
                Step 4 — Export Results & Summary
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ------------------- Header Component ------------------- #
def render_header():
    st.markdown(
    """
        <div class="main-header">
            <div class="main-title">⚖️ Repair Order & Bates Extraction Console</div>
            <div class="main-subtitle">
                Upload Bates-stamped legal PDFs and automatically extract Repair Orders, Bates Numbers, 
                and Page Numbers using high-accuracy OCR. Download a structured Excel index ready for 
                legal briefs, discovery responses, and evidence mapping.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    logger.info("Displayed app header.")

# ------------------- Upload Section ------------------- #
def render_upload_section():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header"><span class="section-icon">📁</span>Document Upload</div>',
        unsafe_allow_html=True
    )
    
    uploaded_file = st.file_uploader(
        "Upload PDF File",
        type=["pdf"],
        help="Maximum file size: 200MB. Recommended: Bates-stamped court PDFs",
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        logger.info(f"File uploaded: {uploaded_file.name}, size: {uploaded_file.size} bytes")
        
        # Display success message
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.markdown(
            f"""
            <div class="success-badge">
                ✅ PDF Uploaded Successfully
            </div>
            <div class="file-badge">
                📄 {uploaded_file.name} — {file_size_mb:.2f} MB
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Store in session state
        if (
            'pdf_bytes' not in st.session_state 
            or st.session_state.get('pdf_filename') != uploaded_file.name
        ):
            uploaded_file.seek(0)
            st.session_state.pdf_bytes = uploaded_file.read()
            st.session_state.pdf_filename = uploaded_file.name
            st.session_state.processing_stage = 1
            st.session_state.extraction_complete = False
            logger.info(f"Stored {uploaded_file.name} in session_state.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        return True
    else:
        st.markdown(
            """
            <div class="upload-zone">
                <div class="upload-icon">📤</div>
                <h3 style="color: #1C2D4A; margin-bottom: 10px;">Drag and drop your PDF here</h3>
                <p style="color: #5F6C7B; margin-bottom: 20px;">or click to browse</p>
                <p class="recommendation">✨ Recommended: Bates-stamped court-ready PDF documents</p>
                <p style="color: #9ca3af; font-size: 0.85rem; margin-top: 15px;">Maximum file size: 200MB</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        logger.debug("Waiting for user to upload a PDF document.")
        return False

# ------------------- Processing Section ------------------- #
def render_processing_section():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header"><span class="section-icon">🚀</span>OCR Processing Engine</div>',
        unsafe_allow_html=True
    )
    
    st.markdown(
        """
        <p style="color: #5F6C7B; margin-bottom: 20px;">
            Click the button below to start the Processing engine. The system will automatically identify the document type,
            run a custom processing pipeline for that document, extract Bates Numbers and Repair Order Numbers,
            and then prepare an indexed sheet in the output format selected in the configuration panel on the left.
        </p>
        """,
        unsafe_allow_html=True
    )
    
    process_clicked = st.button(
        "🚀 Process Document",
        use_container_width=True,
        type="primary"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    return process_clicked

# ------------------- PDF Processing Function ------------------- #
def process_pdf(pdf_bytes):
    try:
        # OCR Status
        st.markdown(
            '<div class="status-processing">🔄 Analyzing the document type</div>',
            unsafe_allow_html=True
        )

        # Router TO BE IMPLEMENTED TO IDENTIFY THE DOCUMENT TYPE
        # For now, we assume a text-based PDF that we process with the structured OCR logic.
        extracted_res = extraction_service.is_text_based_pdf(pdf_bytes)

        # Process per-page text to extract Bates Numbers and Repair Order Numbers
        bate_dict, pages_with_issues = extraction_service.process_structured_ocr_pdf(extracted_res)
        if not bate_dict:
            logger.error("Processing returned no response dictionary.")
            st.error("❌ Processing failed. Please try again.", icon="❌")
            return None

        logger.info("Processing completed successfully.")
        st.markdown(
            '<div class="status-success">✅ Processing complete!</div>',
            unsafe_allow_html=True
        )

        # Formatting the data as per the Excel or CSV output
        formatted_data, export_bytes = extraction_service.format_data_for_excel_or_csv(
            bate_dict, output_format
        )

        # Build a results object compatible with the summary & download panels
        total_pages = extracted_res.get("Total pages", 0)
        responses = formatted_data  # list of row dicts

        st.session_state.extraction_results = {
            "total_pages": total_pages,
            "num_chunks": 1,  # single-pass processing for now
            "responses": responses,
            "pages_with_issues": pages_with_issues,
            "export_bytes": export_bytes,
            "export_format": output_format,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        st.session_state.extraction_complete = True
        st.session_state.processing_stage = 4

        return formatted_data

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        st.error(f"❌ Error processing PDF: {str(e)}", icon="❌")
        return None

# ------------------- Extraction Summary Section ------------------- #
def render_extraction_summary():
    if not st.session_state.extraction_complete or not st.session_state.extraction_results:
        return
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header"><span class="section-icon">📊</span>Extraction Summary</div>',
        unsafe_allow_html=True
    )
    
    results = st.session_state.extraction_results
    responses = results.get("responses", [])

    # Calculate metrics based on structured extraction results
    total_pages = results.get("total_pages", 0)
    num_chunks = results.get("num_chunks", 1)

    # Count repair orders (non-empty repair_order_number values)
    repair_orders_found = sum(
        1 for row in responses
        if str(row.get("repair_order_number", "")).strip()
    )

    # Count unique Bates Numbers
    bates_numbers = {
        row.get("bate_number")
        for row in responses
        if row.get("bate_number")
    }
    bates_found = len(bates_numbers)

    # Errors = pages where Bates numbers were missing/ambiguous
    errors_detected = len(results.get("pages_with_issues", []))

    # Estimated accuracy: based on alignment between total pages and Bates Numbers
    # If every page has exactly one Bates Number, accuracy = 100%.
    if total_pages > 0:
        missing_or_extra = abs(total_pages - bates_found)
        accuracy = max(0.0, 100.0 * (1.0 - missing_or_extra / total_pages))
    else:
        accuracy = 0.0
    
    # Display metrics in 2 rows
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📄 Total Pages Processed", f"{total_pages:,}")
    with col2:
        st.metric("🔧 Repair Orders Extracted", f"{repair_orders_found:,}")
    with col3:
        st.metric("📋 Bates Numbers Found", f"{bates_found:,}")
    
    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("⚠️ Errors Detected", f"{errors_detected}")
    with col5:
        st.metric("✅ Estimated Accuracy", f"{accuracy}%")
    with col6:
        st.metric("📦 Chunks Processed", f"{num_chunks}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------- Download Section ------------------- #
def render_download_section():
    if not st.session_state.extraction_complete or not st.session_state.extraction_results:
        return
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-header"><span class="section-icon">⬇️</span>Download Results</div>',
        unsafe_allow_html=True
    )
    
    results = st.session_state.extraction_results
    responses = results.get("responses", [])
    export_bytes = results.get("export_bytes", b"")
    export_format = results.get("export_format", "Excel")

    # Choose filename and mime based on export format
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if export_bytes and export_format == "CSV":
        index_filename = f"extraction_results_{timestamp}.csv"
        index_mime = "text/csv"
    else:
        index_filename = f"extraction_results_{timestamp}.xlsx"
        index_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            label="📊 Download Index Sheet",
            data=export_bytes,
            file_name=index_filename,
            mime=index_mime,
            use_container_width=True
        )
    
    with col2:
        # Generate JSON download
        json_data = json.dumps(results['responses'], indent=2)
        st.download_button(
            label="📄 Download Raw JSON",
            data=json_data,
            file_name=f"extraction_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col3:
        # Generate Error Log (placeholder)
        error_log = "No errors detected during processing.\n"
        st.download_button(
            label="📋 Download Error Log",
            data=error_log,
            file_name=f"error_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    # Detailed logs expander
    with st.expander("🔍 View Detailed Extraction Logs"):
        st.markdown("**Processing Timestamp:**")
        st.code(results['timestamp'])
        
        st.markdown("**Raw JSON Response:**")
        st.json(results['responses'])
        
        st.markdown("**Processing Statistics:**")
        st.write(f"- Total Pages: {results['total_pages']}")
        st.write(f"- Total Chunks: {results['num_chunks']}")
        st.write(f"- Responses Received: {len(results['responses'])}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------- Footer ------------------- #
def render_footer():
    st.markdown(
        """
        <div class="footer">
            Built for Litigation Workflows — OCR + Bates Indexing Automation<br>
            Powered by Streamlit • PyMuPDF • OpenAI GPT-4
        </div>
        """,
        unsafe_allow_html=True
    )

# ------------------- Main Application Flow ------------------- #
render_header()
render_step_indicator(st.session_state.processing_stage)

# Upload Section
pdf_uploaded = render_upload_section()

# Processing Section
if pdf_uploaded:
    st.session_state.processing_stage = max(st.session_state.processing_stage, 1)
    
    process_clicked = render_processing_section()
    
    if process_clicked and 'pdf_bytes' in st.session_state:
        logger.info("User pressed process button. Starting OCR pipeline...")
        st.session_state.processing_stage = 2
        
        formatted_data = process_pdf(st.session_state.pdf_bytes)
        
        if formatted_data:
            logger.info(f"Successfully processed document.")
            st.balloons()

# Results Sections
if st.session_state.extraction_complete:
    render_extraction_summary()
    render_download_section()

# Footer
render_footer()

logger.info("App ready. UI rendered.")
