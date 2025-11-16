import re
import logging
import fitz
import io
import csv
from typing import List, Dict, Any, Tuple
from openpyxl import Workbook

# Setting up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFTextExtractor:
    def __init__(self):
        # Precompile regex patterns for efficiency
        self.aaron_code_pattern = re.compile(r"\bAARON\d{8,}\b")
        self.ro_pattern_structured_ocr_pdf = re.compile(r"\b\d{5}\b")
    
    def extract_aaron_code(self, text: str) -> List[str]:
        """
        Extract Bate codes in the format AARON followed by 8 or more digits.

        Args:
            text (str): Input text to search.

        Returns:
            List[str]: List of detected codes.
        """
        if not isinstance(text, str):
            raise ValueError("Input text must be a string.")
        return self.aaron_code_pattern.findall(text)
    
    def extract_repair_order_numbers_structred_ocr_pdf(self, text: str) -> List[str]:
        """
        Extract all 5-digit repair order numbers (standalone numbers).

        Args:
            text (str): Input text to search.

        Returns:
            List[str]: List of 5-digit numbers as strings.
        """
        if not isinstance(text, str):
            raise ValueError("Input text must be a string.")
        return self.ro_pattern_structured_ocr_pdf.findall(text)
    
    def process_structured_ocr_pdf(self, extracted_res: dict):
        """
        Process each page's text to extract Bate numbers and Repair Order numbers.
        Logs pages with issues (no/multiple Bate numbers).
        Returns a dictionary mapping page numbers to Bate numbers and repair order numbers.
        """
        pages_with_issues = []
        bate_dict = {}

        for i, text in enumerate(extracted_res["Text"]):
            page_num = i + 1
            try:
                # Extract the Bate Number (should be exactly one per page)
                bate_number_list = self.extract_aaron_code(text)
                if len(bate_number_list) != 1:
                    # Log the issue and store page number
                    pages_with_issues.append(page_num)
                    logger.warning(
                        f"Page {page_num} has {'no' if len(bate_number_list)==0 else 'multiple'} Bate numbers: {bate_number_list}"
                    )

                # Extract the Repair Order Number(s)
                repair_order_numbers = self.extract_repair_order_numbers_structred_ocr_pdf(text)
                
                # Add to dictionary only if Bate number is found
                bate_dict[page_num] = {}
                if bate_number_list:
                    bate_dict[page_num][bate_number_list[0]] = repair_order_numbers
                else:
                    # Optionally store None or an empty string if no Bate number found
                    bate_dict[page_num][None] = repair_order_numbers
            except Exception as e:
                logger.error(f"Error processing page {page_num}: {e}")
                pages_with_issues.append(page_num)

        return bate_dict, pages_with_issues

    def format_data_for_excel_or_csv(
        self,
        data: Dict[int, Dict[str, List[str]]],
        output_format: str,
    ) -> Tuple[List[Dict[str, Any]], bytes]:
        """
        Format the data for Excel or CSV.

        For each repair order number on a page, create a separate row with the same page number and bate number.
        If there are no repair order numbers, generate a row with repair_order_number as empty.
        """
        formatted_data_list: List[Dict[str, Any]] = []

        # First build a normalized list of row dicts
        for page_num, bate_number_dict in data.items():
            for bate_number, repair_order_numbers in bate_number_dict.items():
                if repair_order_numbers and len(repair_order_numbers) > 0:
                    for ro in repair_order_numbers:
                        formatted_data_list.append(
                            {
                                "page_number": page_num,
                                "bate_number": bate_number,
                                "repair_order_number": ro,
                            }
                        )
                else:
                    # No repair order -- create one row with empty repair_order_number
                    formatted_data_list.append(
                        {
                            "page_number": page_num,
                            "bate_number": bate_number,
                            "repair_order_number": "",
                        }
                    )

        # Build binary export (CSV or Excel) with consistent headers
        headers = ["Bate Number", "Repair Order Number", "Page Number"]
        normalized_output_format = (output_format or "").strip().upper()

        if normalized_output_format == "CSV":
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            writer.writerow(headers)
            for row in formatted_data_list:
                writer.writerow(
                    [
                        row.get("bate_number", ""),
                        row.get("repair_order_number", ""),
                        row.get("page_number", ""),
                    ]
                )
            export_bytes = buffer.getvalue().encode("utf-8")
        else:
            # Default to Excel (.xlsx) using openpyxl
            wb = Workbook()
            ws = wb.active
            ws.title = "Index"
            # Write headers
            ws.append(headers)
            # Write rows
            for row in formatted_data_list:
                ws.append(
                    [
                        row.get("bate_number", ""),
                        row.get("repair_order_number", ""),
                        row.get("page_number", ""),
                    ]
                )
            bytes_buffer = io.BytesIO()
            wb.save(bytes_buffer)
            export_bytes = bytes_buffer.getvalue()

        return formatted_data_list, export_bytes

    def is_text_based_pdf(self,pdf_bytes: bytes) -> dict:
        """
        Returns information about the number of text pages and total pages, as well as a list of text per page.
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        text_list = []
        for page in doc:
            text = page.get_text()
            if text.strip():
                text_list.append(text)
        return {
            "Total pages": total_pages,
            "Text pages": len(text_list),
            "Text": text_list
        }

# Usage example
# pdf_path = "your_pdf_path_here.pdf"
# with open(pdf_path, "rb") as f:
#     pdf_bytes = f.read()
# extracted_res = is_text_based_pdf(pdf_bytes)
# extractor = PDFTextExtractor()
# bate_dict, issue_pages = extractor.process_structured_ocr_pdf(extracted_res)
