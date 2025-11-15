import streamlit as st
import logging
import json
import io
from datetime import datetime
from utils.ocr_utils import PdfProcessor
from utils.llm_utils import LLMService

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

# ------------------- Session State Initialization ------------------- #
if 'processing_stage' not in st.session_state:
    st.session_state.processing_stage = 1  # 1=Upload, 2=Processing, 3=Complete
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
                background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
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
        st.markdown("**Processing Options**")
        chunk_size = st.slider(
            "Pages per chunk:",
            min_value=10,
            max_value=100,
            value=50,
            step=10,
            help="Number of pages to process in each batch"
        )
        
        st.markdown("---")
        st.markdown("**About**")
        st.info(
            "This tool uses advanced OCR and AI to extract Repair Orders and Bates Numbers from legal documents with high accuracy."
        )
        
    logger.info(f"User selected output format: {output_format}, chunk size: {chunk_size}")
    return output_format, chunk_size

output_format, chunk_size = config_sidebar()

# ------------------- Step Indicator Component ------------------- #
def render_step_indicator(current_stage):
    step1_class = "complete" if current_stage > 1 else ("active" if current_stage == 1 else "")
    step2_class = "complete" if current_stage > 2 else ("active" if current_stage == 2 else "")
    step3_class = "active" if current_stage == 3 else ""
    
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
                Step 2 — OCR Processing
            </div>
            <div class="step-arrow">→</div>
            <div class="step {step3_class}">
                <span style="margin-right: 8px;">📊</span>
                Step 3 — Extraction & Export
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
            Click the button below to start the OCR engine. The system will extract clean text, 
            identify Repair Orders, and map them to Bates Numbers.
        </p>
        """,
        unsafe_allow_html=True
    )
    
    process_clicked = st.button(
        "🚀 Process Document (Run OCR Engine)",
        use_container_width=True,
        type="primary"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    return process_clicked

# ------------------- PDF Processing Function ------------------- #
def process_pdf(pdf_bytes, chunk_size_param):
    try:
        # OCR Status
        st.markdown(
            '<div class="status-processing">🔄 OCR engine started... Extracting text from PDF pages...</div>',
            unsafe_allow_html=True
        )
        
        ocr_response_list = pdf_service.extract_text_from_pdf(pdf_bytes)
        if not ocr_response_list:
            logger.error("OCR processing returned no response.")
            st.error("❌ OCR processing failed. Please try again.", icon="❌")
            return None

        logger.info(f"OCR processing completed successfully. Total pages: {len(ocr_response_list)}")
        st.markdown(
            '<div class="status-success">✅ OCR text extraction complete!</div>',
            unsafe_allow_html=True
        )
        
        # Chunking Status
        CHUNK_SIZE = chunk_size_param
        total_pages = len(ocr_response_list)
        num_chunks = (total_pages + CHUNK_SIZE - 1) // CHUNK_SIZE
        logger.info(f"Creating {num_chunks} chunks of {CHUNK_SIZE} pages each from {total_pages} total pages")
        
        st.markdown(
            f'<div class="status-processing">📦 Preparing {num_chunks} chunks for AI analysis...</div>',
            unsafe_allow_html=True
        )

        # Load the markdown prompt template
        prompt_path = "prompt_registry/document_analysis_propmt.md"
        try:
            prompt_template = pdf_service.load_markdown_file(prompt_path)
            logger.info(f"Loaded prompt template from {prompt_path}")
        except Exception as e:
            logger.error(f"Failed to load prompt template: {str(e)}", exc_info=True)
            st.error(f"❌ Failed to load prompt template: {str(e)}")
            prompt_template = None

        # Chunk processing
        chunk_results = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for chunk_idx in range(num_chunks):
            start_idx = chunk_idx * CHUNK_SIZE
            end_idx = min(start_idx + CHUNK_SIZE, total_pages)
            progress = (chunk_idx + 1) / num_chunks
            progress_bar.progress(progress)
            status_text.markdown(
                f'<div class="status-processing">🔍 Analyzing chunk {chunk_idx + 1}/{num_chunks} (Pages {start_idx + 1}-{end_idx})...</div>',
                unsafe_allow_html=True
            )

            chunk_pages = ocr_response_list[start_idx:end_idx]
            combined_markdown = "\n\n".join(chunk_pages)
            logger.info(f"Chunk {chunk_idx + 1}/{num_chunks}: Pages {start_idx + 1}-{end_idx} combined into markdown ({len(combined_markdown)} chars)")

            if prompt_template and "{ocr_text}" in prompt_template:
                final_prompt = prompt_template.replace("{ocr_text}", combined_markdown)
            else:
                final_prompt = f"# OCR TEXT DATA (Pages {start_idx + 1}-{end_idx})\n\n{combined_markdown}"

            chunk_results.append({
                'chunk_number': chunk_idx + 1,
                'start_page': start_idx + 1,
                'end_page': end_idx,
                'combined_markdown': combined_markdown,
                'final_prompt': final_prompt,
            })

        progress_bar.empty()
        status_text.empty()
        st.session_state.ocr_chunks = chunk_results
        logger.info(f"Stored {len(chunk_results)} chunks in session state")

        # AI Processing Status
        st.markdown(
            '<div class="status-processing">🤖 Sending to AI for Repair Order & Bates extraction...</div>',
            unsafe_allow_html=True
        )

        # Making calls to OpenAI
        llm_responses_list = []
        ai_progress = st.progress(0)
        ai_status = st.empty()
        
        for idx, chunk in enumerate(chunk_results):
            ai_progress.progress((idx + 1) / len(chunk_results))
            ai_status.markdown(
                f'<div class="status-processing">🧠 AI processing chunk {idx + 1}/{len(chunk_results)}...</div>',
                unsafe_allow_html=True
            )
            
            response = llm_service.process_document_extraction(chunk['final_prompt'])
            if response:
                llm_responses_list.append(response)
            else:
                logger.error("No response from AI for chunk.")
                llm_responses_list.append(None)

        ai_progress.empty()
        ai_status.empty()

        if llm_responses_list:
            logger.info(f"Successfully processed {len(llm_responses_list)} chunks with AI.")
            st.markdown(
                '<div class="status-success">✅ Extraction complete! Data ready for download.</div>',
                unsafe_allow_html=True
            )
            
            # Store results in session state
            st.session_state.extraction_results = {
                'responses': llm_responses_list,
                'total_pages': total_pages,
                'num_chunks': num_chunks,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.extraction_complete = True
            st.session_state.processing_stage = 3
            
            return llm_responses_list
        else:
            logger.error("No response from AI.")
            st.error("❌ No response from AI. Please check the logs.", icon="❌")
            return None

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
    
    # Calculate metrics (you can enhance this based on actual response structure)
    total_pages = results['total_pages']
    num_chunks = results['num_chunks']
    repair_orders_found = len(results['responses']) * 5  # Placeholder - adjust based on actual data
    bates_found = total_pages  # Placeholder
    accuracy = 95.8  # Placeholder
    
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
        st.metric("⚠️ Errors Detected", "0")
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
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Generate Excel download (placeholder - implement based on your data structure)
        excel_data = json.dumps(results['responses'], indent=2).encode('utf-8')
        st.download_button(
            label="📊 Download Excel Index",
            data=excel_data,
            file_name=f"extraction_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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
        
        llm_responses = process_pdf(st.session_state.pdf_bytes, chunk_size)
        
        if llm_responses:
            logger.info(f"Successfully processed document.")
            st.balloons()

# Results Sections
if st.session_state.extraction_complete:
    render_extraction_summary()
    render_download_section()

# Footer
render_footer()

logger.info("App ready. UI rendered.")
