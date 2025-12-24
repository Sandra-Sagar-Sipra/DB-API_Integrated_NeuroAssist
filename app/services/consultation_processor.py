from sqlmodel import Session, select
from app.core.db import engine
from app.models.base import Consultation, ConsultationStatus, AudioFile, SOAPNote, PatientProfile
from app.services.stt_service import AssemblyAIService
from app.services.llm_service import GeminiService
from uuid import UUID
import asyncio

async def process_consultation_flow(consultation_id: UUID):
    """
    Orchestrates the AI processing flow:
    1. Transcribe Audio (AssemblyAI)
    2. Generate SOAP Note (Gemini)
    3. Update Database
    """
    print(f"Starting processing for consultation {consultation_id}")
    
    # We use a new session per background task execution
    with Session(engine) as session:
        consultation = session.get(Consultation, consultation_id)
        if not consultation:
            print(f"Consultation {consultation_id} not found.")
            return
        
        # 1. Update Status: Transcribing
        consultation.status = ConsultationStatus.IN_PROGRESS
        session.add(consultation)
        session.commit()
        
        # 2. Get Audio File
        audio_file = session.exec(select(AudioFile).where(AudioFile.consultation_id == consultation_id)).first()
        if not audio_file:
            print("Audio file missing.")
            # We treat this as a failure state, but keep it in IN_PROGRESS or move to CANCELLED?
            # For now, let's leave it but log it.
            return

        # Fetch Patient Context
        patient_profile = session.exec(select(PatientProfile).where(PatientProfile.user_id == consultation.patient_id)).first()
        patient_context = {}
        if patient_profile:
            # Calculate Age (Rough approx is fine for now)
            age = "N/A"
            if patient_profile.date_of_birth:
                from datetime import datetime
                today = datetime.now()
                dob = patient_profile.date_of_birth
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            patient_context = {
                "first_name": patient_profile.first_name,
                "last_name": patient_profile.last_name,
                "age": age,
                "gender": patient_profile.gender,
                "notes": f"Address: {patient_profile.city}, {patient_profile.state}" # Add more history if available in DB
            }

        try:
            # 3. Transcribe (AssemblyAI)
            print("Starting transcription...")
            transcript_result = await AssemblyAIService.transcribe_audio_async(audio_file.file_url)
            transcript_text = transcript_result["text"]
            utterances = transcript_result.get("utterances", [])
            
            # Update AudioFile with transcription
            audio_file.transcription = transcript_text
            session.add(audio_file)
            session.commit() # Commit intermediate progress
            print("Transcription complete.")
            
            # 4. Generate SOAP (Gemini) - ENABLED
            print("Generating SOAP note...")
            soap_data = await GeminiService.generate_soap_note_async(transcript_text, utterances, patient_context)
            
            soap_content = soap_data.get("soap_note", {})
            risk_flags = soap_data.get("risk_flags", [])
            
            # 5. Create SOAP Note Record
            soap_note = SOAPNote(
                consultation_id=consultation.id,
                soap_json=soap_content,
                risk_flags={"flags": risk_flags}, # Wrap in dict as risk_flags is JSON type
                confidence=transcript_result.get("confidence"), # Use STT confidence as proxy or from LLM if available
                generated_by_ai=True
            )
            session.add(soap_note)
            
            # 6. Update Final Status
            consultation.status = ConsultationStatus.COMPLETED
            session.add(consultation)
            session.commit()
            
            print(f"Processing successfully completed for {consultation_id}")
            
        except Exception as e:
            print(f"Processing failed: {e}")
            # Set status to FAILED so we can track errors in DB
            consultation.status = ConsultationStatus.FAILED
            # Optionally store the error message in notes or a separate column if available. 
            # For now, just marking as FAILED is sufficient for the test.
            session.add(consultation)
            session.commit()

