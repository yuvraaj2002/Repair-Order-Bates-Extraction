from openai import OpenAI
import os
import json
import logging
import traceback
from dotenv import load_dotenv
from rich import print
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

load_dotenv()

# Setting up the logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Getting the OpenAI API key from the environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
OPENAI_TEMPERATURE = os.getenv("OPENAI_TEMPERATURE", "0.7")  # Default to 0.7 if not set

# Validate required environment variables
if not OPENAI_API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")
if not OPENAI_MODEL:
    raise ValueError("Please set the OPENAI_MODEL environment variable.")
if not OPENAI_TEMPERATURE:
    raise ValueError("Please set the OPENAI_TEMPERATURE environment variable.")


class LLMService:
    def __init__(self):
        self.llm_client = OpenAI(api_key=OPENAI_API_KEY)
        self.logger = logging.getLogger(__name__)

    def validate_response():
        """
        This function will validate the response from the OPENAI and return back the response if it is valid.
        """


    @retry(stop=stop_after_attempt(5), wait=wait_exponential_jitter(initial=1, max=10))
    def process_document_extraction(self, prompt: str):
        """
        Processes a document and returns a structured JSON of the document.
        
        Args:
            prompt: The prompt text to send to the LLM
            
        Returns:
            str: The extracted text/JSON response from the LLM, or None if an error occurred
        """
        try:
            # Validate prompt
            if not prompt or not prompt.strip():
                raise ValueError("Prompt cannot be empty.")
            
            self.logger.info(f"Calling OpenAI API with model: {OPENAI_MODEL}")
            
            # Use chat.completions.create() for GPT-4 models
            response = self.llm_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a high-precision extraction engine that returns only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=float(OPENAI_TEMPERATURE),
                response_format={"type": "json_object"}  # Ensure JSON response
            )
            
            # Extract the response text
            if response.choices and len(response.choices) > 0:
                response_text = response.choices[0].message.content
                print(response_text)
                self.logger.info(f"Successfully received response from OpenAI API (length: {len(response_text)} chars)")
                return response_text
            else:
                self.logger.error("No choices in OpenAI API response")
                return None
                
        except Exception as e:
            self.logger.error(f"Error processing document extraction: {str(e)}")
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            raise  # Re-raise to allow tenacity to retry

# if __name__ == "__main__":
#     llm_service = LLMService()
#     response = llm_service.process_document_extraction("What is the main idea of the document?")
#     print(response)