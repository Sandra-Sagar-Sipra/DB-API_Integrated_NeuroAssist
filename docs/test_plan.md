# NeuroAssist Phase 1 Verification Plan

**Current System State:** STT-Only (LLM Disabled), Word Boost Enabled.

## 1. Automated Regression Suite (The "To-Do" List)

### A. Data Flow & Orchestration
*   **Test Case 1.1: Happy Path (End-to-End)**
    *   **Goal:** Verify audio moves from Upload -> DB -> AssemblyAI -> DB Update -> Status COMPLETED.
    *   **Constraint:** Assert `soap_note` is NOT created (LLM disabled).
    *   **Script:** `tests/test_live_chain.py`

### B. Accuracy & "Ears" Testing
*   **Test Case 2.1: Medical Terminology Recognition**
    *   **Goal:** Inputs audio with "Levetiracetam" and "Donepezil".
    *   **Metric:** Word Error Rate (WER) on specific keywords.
    *   **Script:** `tests/test_live_stt.py` (Manual verification of output logs).

### C. Resilience & Security
*   **Test Case 3.1: Corrupt File Handling**
    *   **Goal:** Upload random bytes.
    *   **Expected Result:** Status `FAILED` in DB. Server stays alive.
    *   **Script:** `tests/test_live_chain.py::test_corrupt_file_upload`
*   **Test Case 3.2: Environment Security**
    *   **Goal:** Ensure no tests run if API keys are stripped.
    *   **Script:** `tests/conftest_live.py` (Implicit).

## 2. Metrics to Collect
1.  **Pass/Fail Rate:** Number of automated tests passed.
2.  **Transcription Latency:** Time taken from Upload to `stt_status=COMPLETED`.
3.  **Keyword Hit Rate:** Did the STT engine catch the medical drugs?
