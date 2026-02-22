import threading
import subprocess
import json
import os
from pathlib import Path
from wadio.config import MODEL_DIR

finetune_threads = {}

def run_finetune_thread(job_id: int, speaker_name: str, voice_file_data: list, config: dict, db_session):
    from datetime import datetime
    from wadio.models import FineTuneJob, Speaker
    
    job = db_session.query(FineTuneJob).filter(FineTuneJob.id == job_id).first()
    if not job:
        return
    
    try:
        job.status = "running"
        db_session.commit()
        
        user_dir = MODEL_DIR / str(job.user_id) / speaker_name
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Create raw training JSONL
        raw_jsonl_path = user_dir / "train_raw.jsonl"
        with open(raw_jsonl_path, "w", encoding="utf-8") as f:
            for vf in voice_file_data:
                line = json.dumps({
                    "audio": vf["file_path"],
                    "text": vf["transcript"],
                    "ref_audio": vf["file_path"]  # Use same audio as reference
                }, ensure_ascii=False)
                f.write(line + "\n")
        
        # Step 2: Run prepare_data.py to generate audio_codes
        train_jsonl_path = user_dir / "train_with_codes.jsonl"
        prepare_cmd = [
            "python", "-m", "finetuning.prepare_data",
            "--device", "cuda:0",
            "--tokenizer_model_path", "Qwen/Qwen3-TTS-Tokenizer-12Hz",
            "--input_jsonl", str(raw_jsonl_path),
            "--output_jsonl", str(train_jsonl_path),
        ]
        
        prepare_result = subprocess.run(prepare_cmd, capture_output=True, text=True)
        
        if prepare_result.returncode != 0:
            job.status = "failed"
            job.config = {"error": f"prepare_data failed: {prepare_result.stderr}"}
            db_session.commit()
            return
        
        # Step 3: Run fine-tuning
        output_path = user_dir / "checkpoints"
        output_path.mkdir(parents=True, exist_ok=True)
        
        ft_cmd = [
            "python", "-m", "finetuning.sft_12hz",
            "--init_model_path", "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
            "--output_model_path", str(output_path),
            "--train_jsonl", str(train_jsonl_path),
            "--speaker_name", speaker_name,
            "--batch_size", str(config.get("batch_size", 2)),
            "--lr", str(config.get("lr", "2e-5")),
            "--num_epochs", str(config.get("epochs", 3)),
        ]
        
        ft_result = subprocess.run(ft_cmd, capture_output=True, text=True)
        
        if ft_result.returncode == 0:
            job.status = "completed"
            job.checkpoint_path = str(output_path)
            job.completed_at = datetime.utcnow()
            
            existing_speakers = db_session.query(Speaker).filter(
                Speaker.user_id == job.user_id,
                Speaker.name == speaker_name
            ).first()
            
            if not existing_speakers:
                next_speaker_id = 3000 + db_session.query(Speaker).filter(
                    Speaker.user_id == job.user_id
                ).count()
                
                speaker = Speaker(
                    user_id=job.user_id,
                    name=speaker_name,
                    speaker_id=next_speaker_id,
                    model_path=str(output_path),
                    is_default=False
                )
                db_session.add(speaker)
        else:
            job.status = "failed"
            job.config = {"error": ft_result.stderr}
        
        db_session.commit()
        
    except Exception as e:
        job.status = "failed"
        job.config = {"error": str(e)}
        db_session.commit()
    finally:
        if job_id in finetune_threads:
            del finetune_threads[job_id]

def start_finetune_job(job_id: int, speaker_name: str, voice_file_data: list, config: dict, db_session):
    thread = threading.Thread(
        target=run_finetune_thread,
        args=(job_id, speaker_name, voice_file_data, config, db_session)
    )
    finetune_threads[job_id] = thread
    thread.start()
    return thread
