# # ------------------- PDF Processing Function ------------------- #
# def process_pdf(pdf_bytes, chunk_size_param):
#     try:
#         # OCR Status
#         st.markdown(
#             '<div class="status-processing">🔄 OCR engine started... Extracting text from PDF pages...</div>',
#             unsafe_allow_html=True
#         )
        
#         ocr_response_list = pdf_service.extract_text_from_pdf(pdf_bytes)
#         if not ocr_response_list:
#             logger.error("OCR processing returned no response.")
#             st.error("❌ OCR processing failed. Please try again.", icon="❌")
#             return None

#         logger.info(f"OCR processing completed successfully. Total pages: {len(ocr_response_list)}")
#         st.markdown(
#             '<div class="status-success">✅ OCR text extraction complete!</div>',
#             unsafe_allow_html=True
#         )
        
#         # Chunking Status
#         CHUNK_SIZE = chunk_size_param
#         total_pages = len(ocr_response_list)
#         num_chunks = (total_pages + CHUNK_SIZE - 1) // CHUNK_SIZE
#         logger.info(f"Creating {num_chunks} chunks of {CHUNK_SIZE} pages each from {total_pages} total pages")
        
#         st.markdown(
#             f'<div class="status-processing">📦 Preparing {num_chunks} chunks for AI analysis...</div>',
#             unsafe_allow_html=True
#         )

#         # Load the markdown prompt template
#         prompt_path = "prompt_registry/document_analysis_propmt.md"
#         try:
#             prompt_template = pdf_service.load_markdown_file(prompt_path)
#             logger.info(f"Loaded prompt template from {prompt_path}")
#         except Exception as e:
#             logger.error(f"Failed to load prompt template: {str(e)}", exc_info=True)
#             st.error(f"❌ Failed to load prompt template: {str(e)}")
#             prompt_template = None

#         # Chunk processing
#         chunk_results = []
#         progress_bar = st.progress(0)
#         status_text = st.empty()

#         for chunk_idx in range(num_chunks):
#             start_idx = chunk_idx * CHUNK_SIZE
#             end_idx = min(start_idx + CHUNK_SIZE, total_pages)
#             progress = (chunk_idx + 1) / num_chunks
#             progress_bar.progress(progress)
#             status_text.markdown(
#                 f'<div class="status-processing">🔍 Analyzing chunk {chunk_idx + 1}/{num_chunks} (Pages {start_idx + 1}-{end_idx})...</div>',
#                 unsafe_allow_html=True
#             )

#             chunk_pages = ocr_response_list[start_idx:end_idx]
#             combined_markdown = "\n\n".join(chunk_pages)
#             logger.info(f"Chunk {chunk_idx + 1}/{num_chunks}: Pages {start_idx + 1}-{end_idx} combined into markdown ({len(combined_markdown)} chars)")

#             if prompt_template and "{ocr_text}" in prompt_template:
#                 final_prompt = prompt_template.replace("{ocr_text}", combined_markdown)
#             else:
#                 final_prompt = f"# OCR TEXT DATA (Pages {start_idx + 1}-{end_idx})\n\n{combined_markdown}"

#             chunk_results.append({
#                 'chunk_number': chunk_idx + 1,
#                 'start_page': start_idx + 1,
#                 'end_page': end_idx,
#                 'combined_markdown': combined_markdown,
#                 'final_prompt': final_prompt,
#             })

#         progress_bar.empty()
#         status_text.empty()
#         st.session_state.ocr_chunks = chunk_results
#         logger.info(f"Stored {len(chunk_results)} chunks in session state")

#         # AI Processing Status
#         st.markdown(
#             '<div class="status-processing">🤖 Sending to AI for Repair Order & Bates extraction...</div>',
#             unsafe_allow_html=True
#         )

#         # Making calls to OpenAI
#         llm_responses_list = []
#         ai_progress = st.progress(0)
#         ai_status = st.empty()
        
#         for idx, chunk in enumerate(chunk_results):
#             ai_progress.progress((idx + 1) / len(chunk_results))
#             ai_status.markdown(
#                 f'<div class="status-processing">🧠 AI processing chunk {idx + 1}/{len(chunk_results)}...</div>',
#                 unsafe_allow_html=True
#             )
            
#             response = llm_service.process_document_extraction(chunk['final_prompt'])
#             if response:
#                 llm_responses_list.append(response)
#             else:
#                 logger.error("No response from AI for chunk.")
#                 llm_responses_list.append(None)

#         ai_progress.empty()
#         ai_status.empty()

#         if llm_responses_list:
#             logger.info(f"Successfully processed {len(llm_responses_list)} chunks with AI.")
#             st.markdown(
#                 '<div class="status-success">✅ Extraction complete! Data ready for download.</div>',
#                 unsafe_allow_html=True
#             )
            
#             # Store results in session state
#             st.session_state.extraction_results = {
#                 'responses': llm_responses_list,
#                 'total_pages': total_pages,
#                 'num_chunks': num_chunks,
#                 'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             }
#             st.session_state.extraction_complete = True
#             st.session_state.processing_stage = 3
            
#             return llm_responses_list
#         else:
#             logger.error("No response from AI.")
#             st.error("❌ No response from AI. Please check the logs.", icon="❌")
#             return None

#     except Exception as e:
#         logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
#         st.error(f"❌ Error processing PDF: {str(e)}", icon="❌")
#         return None