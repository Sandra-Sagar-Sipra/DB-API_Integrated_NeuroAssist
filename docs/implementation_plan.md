# AI Service Integration Plan

## Goal
Integrate the existing `stt_service.py` (AssemblyAI) and `llm_service.py` (Gemini) into the `consultation_processor.py` workflow to enable real-time audio processing and SOAP note generation.

## Proposed Changes

### AI Services Layer
#### [MODIFY] [stt_service.py](file:///Users/sindhu/Projects/DB-API_Integrated_NeuroAssist/app/services/stt_service.py)
- Ensure `transcribe_audio_async` correctly offloads the synchronous API call to a thread executor to prevent blocking the event loop.

#### [MODIFY] [llm_service.py](file:///Users/sindhu/Projects/DB-API_Integrated_NeuroAssist/app/services/llm_service.py)
- Add an async wrapper `generate_soap_note_async` (similar to STT service) to offload the synchronous `model.generate_content` call.

### Business Logic Layer
#### [MODIFY] [consultation_processor.py](file:///Users/sindhu/Projects/DB-API_Integrated_NeuroAssist/app/services/consultation_processor.py)
- Remove `AssemblyAIMock` and `GeminiMock` classes.
- Import `AssemblyAIService` and `GeminiService`.
- Update `process_consultation_flow` to:
    - Call `AssemblyAIService.transcribe_audio_async`.
    - Call `GeminiService.generate_soap_note_async` (new method).
    - Update `consultation.status` to `COMPLETED` upon successful SOAP generation (fixing the current bug where it stays `IN_PROGRESS`).
    - Add basic error handling to set status so it doesn't get stuck if it fails (optional: add `FAILED` status if model supports it, otherwise log error).

## Verification Plan

### Automated/Manual Verification
1.  **Environment Setup**: User must ensure `ASSEMBLYAI_API_KEY` and `GEMINI_API_KEY` are set in `.env`.
2.  **Test Script**: I will create a script `verify_process.py` that:
    - Creates a dummy consultation.
    - Calls `process_consultation_flow` directly (or via a mock background task trigger).
    - Checks if `soap_note` is created and `consultation.status` is `COMPLETED`.
    *Note: This requires actual API keys. If keys are missing, we will verify the code structure.*
