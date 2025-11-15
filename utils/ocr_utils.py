import os
import logging
import base64
from mistralai import Mistral
from dotenv import load_dotenv
import traceback
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
load_dotenv()

# Setting up the logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Getting the Mistral API key from the environment variables
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    raise ValueError("Please set the MISTRAL_API_KEY environment variable.")


class PdfProcessor:
    def __init__(self):
        # You can set the API key via argument or environment variable
        self.api_key = MISTRAL_API_KEY
        self.client = Mistral(api_key=self.api_key)

    def validate_ocr_response(self, ocr_response):
        """
        Simple validation of OCR response, with page number injected:
        - If no response, raise error.
        - If response has 'pages', and it's not empty, return a list of markdown with prepended page number.
        - If no pages, raise error.
        """
        if not ocr_response:
            raise ValueError("OCR response is empty or None.")

        if hasattr(ocr_response, 'pages'):
            pages = ocr_response.pages
            if not pages or len(pages) == 0:
                raise ValueError("OCR response does not contain any pages.")
            
            markdown_pages = []
            for idx, page in enumerate(pages):
                if hasattr(page, 'markdown'):
                    page_num = idx + 1  # 1-based indexing
                    page_markdown_with_number = f"**PAGE {page_num}**\n\n{page.markdown}"
                    markdown_pages.append(page_markdown_with_number)
            return markdown_pages

        else:
            raise ValueError("OCR response does not have pages attribute.")
            return None

    def load_markdown_file(self,prompt_path:str):
        try:
            with open(prompt_path, "r") as file:
                markdown = file.read()
            return markdown
        except Exception as e:
            logger.error(f"Failed to load markdown file: {str(e)}", exc_info=True)
            raise e


    @retry(stop=stop_after_attempt(5), wait=wait_exponential_jitter(initial=1, max=10))
    def extract_text_from_pdf(self, pdf_bytes):
        """
        Extracts text from a local PDF using Mistral OCR.
        
        Args:
            pdf_bytes: Raw PDF file bytes to be processed
            
        Returns:
            OCR response object containing extracted text (markdown format)
            
        Raises:
            ValueError: If pdf_bytes is None or empty
        """
        try:
            # Validate PDF bytes
            if not pdf_bytes:
                raise ValueError("PDF bytes are empty or None. Please ensure the PDF file was read correctly.")
            
            if len(pdf_bytes) == 0:
                raise ValueError("PDF bytes length is 0. Please check the uploaded file.")
            
            # Validate PDF header (PDF files should start with %PDF)
            if not pdf_bytes.startswith(b'%PDF'):
                raise ValueError("Invalid PDF format. File does not appear to be a valid PDF.")
            
            # Encode PDF bytes to base64 for Mistral OCR API
            base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

            ocr_response = self.client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{base64_pdf}"
                },
                include_image_base64=False  # Set to True if you need embedded images
            )

            validated_ocr_response = self.validate_ocr_response(ocr_response)
            return validated_ocr_response
        except Exception as e:
            logger.error(f"Error during OCR extraction: {str(e)}")
            logger.error(traceback.format_exc())
            raise e


if __name__ == "__main__":
    pdf_processor = PdfProcessor()
    ocr_response = pdf_processor.extract_text_from_pdf("testing/Purewick_Resupply_Agreement_OHS.pdf")
    print(ocr_response)
