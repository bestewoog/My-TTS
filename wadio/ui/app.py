import gradio as gr
import requests
import json

API_BASE = "http://localhost:8000"

def get_token(email, password):
    try:
        resp = requests.post(
            f"{API_BASE}/api/auth/login",
            data={"username": email, "password": password}
        )
        if resp.status_code == 200:
            return resp.json()["access_token"]
    except:
        pass
    return None

def register_user(email, password):
    try:
        resp = requests.post(
            f"{API_BASE}/api/auth/register",
            json={"email": email, "password": password}
        )
        return resp.status_code in [200, 201, 400]
    except:
        return False

def api_headers(token):
    return {"Authorization": f"Bearer {token}"}

def build_ui():
    with gr.Blocks(title="Wadio - Voice Platform") as demo:
        gr.Markdown("# 🎤 Wadio - Voice Management Platform")
        
        token_state = gr.State("")
        
        with gr.Tab("🔐 Login / Register"):
            with gr.Row():
                with gr.Column():
                    email_in = gr.Textbox(label="Email")
                    pass_in = gr.PasswordBox(label="Password")
                    login_btn = gr.Button("Login", variant="primary")
                    reg_btn = gr.Button("Register")
                    
                    login_msg = gr.Textbox(label="Status", interactive=False)
                    
                    def do_login(e, p):
                        token = get_token(e, p)
                        if token:
                            return token, "Login successful!"
                        return "", "Login failed - check credentials"
                    
                    login_btn.click(do_login, inputs=[email_in, pass_in], outputs=[token_state, login_msg])
                    
                    def do_register(e, p):
                        ok = register_user(e, p)
                        if ok:
                            return "Registered! Now login."
                        return "Registration failed"
                    
                    reg_btn.click(do_register, inputs=[email_in, pass_in], outputs=[login_msg])
        
        with gr.Tab("🎤 My Voice Files"):
            gr.Markdown("### Upload Voice Files")
            
            with gr.Row():
                upload_file = gr.File(label="WAV File", file_types=[".wav"])
                transcript_in = gr.Textbox(label="Transcript (대사)", lines=2)
                upload_btn = gr.Button("Upload", variant="primary")
            
            upload_result = gr.Textbox(label="Result", interactive=False)
            
            file_list = gr.Dataframe(
                headers=["ID", "Filename", "Duration", "Transcript"],
                label="My Voice Files"
            )
            
            def upload_voice(token, f, transcript):
                if not token:
                    return "Please login first", []
                
                files = {"file": (f.name, open(f.name, "rb"), "audio/wav")}
                data = {"transcript": transcript}
                headers = api_headers(token)
                
                try:
                    resp = requests.post(
                        f"{API_BASE}/api/voice-files/upload",
                        files=files,
                        data=data,
                        headers=headers
                    )
                    if resp.status_code == 200:
                        return "Uploaded!", list_files(token)
                except Exception as e:
                    return str(e), []
                return "Upload failed", []
            
            upload_btn.click(upload_voice, inputs=[token_state, upload_file, transcript_in], outputs=[upload_result, file_list])
            
            def list_files(token):
                if not token:
                    return []
                headers = api_headers(token)
                try:
                    resp = requests.get(f"{API_BASE}/api/voice-files/", headers=headers)
                    if resp.status_code == 200:
                        files = resp.json()
                        return [[f["id"], f["filename"], f"{f.get('duration', 0):.1f}s", f.get("transcript", "")[:50]] for f in files]
                except:
                    pass
                return []
            
            def refresh_files(token):
                return list_files(token)
        
        with gr.Tab("🔧 Fine-tuning"):
            gr.Markdown("### Create New Speaker")
            
            with gr.Row():
                with gr.Column():
                    speaker_name = gr.Textbox(label="Speaker Name")
                    files_check = gr.CheckboxGroup(label="Select Voice Files")
                    epochs = gr.Slider(minimum=1, maximum=10, value=3, step=1, label="Epochs")
                    batch_size = gr.Slider(minimum=1, maximum=8, value=2, step=1, label="Batch Size")
                    lr = gr.Textbox(label="Learning Rate", value="2e-5")
                    
                    start_btn = gr.Button("Start Training", variant="primary")
                    
                    train_result = gr.Textbox(label="Status", interactive=False)
                
                with gr.Column():
                    job_list = gr.Dataframe(
                        headers=["ID", "Speaker", "Status", "Created"],
                        label="Training Jobs"
                    )
            
            def start_training(token, name, file_ids, ep, batch, lr_val):
                if not token:
                    return "Please login first", []
                
                headers = api_headers(token)
                data = {
                    "speaker_name": name,
                    "voice_file_ids": file_ids,
                    "epochs": ep,
                    "batch_size": batch,
                    "lr": float(lr_val)
                }
                
                try:
                    resp = requests.post(f"{API_BASE}/api/finetune/start", json=data, headers=headers)
                    if resp.status_code == 200:
                        return "Training started!", list_jobs(token)
                except Exception as e:
                    return str(e), []
                return "Failed to start", []
            
            start_btn.click(start_training, inputs=[token_state, speaker_name, files_check, epochs, batch_size, lr], outputs=[train_result, job_list])
            
            def list_jobs(token):
                if not token:
                    return []
                headers = api_headers(token)
                try:
                    resp = requests.get(f"{API_BASE}/api/finetune/jobs", headers=headers)
                    if resp.status_code == 200:
                        jobs = resp.json()
                        return [[j["id"], j["speaker_name"], j["status"], j["created_at"][:19]] for j in jobs]
                except:
                    pass
                return []
        
        with gr.Tab("📚 Speakers"):
            gr.Markdown("### My Speakers")
            
            speaker_grid = gr.Dataframe(
                headers=["ID", "Name", "Speaker ID", "Default", "Created"],
                label="My Speakers"
            )
            
            refresh_speakers_btn = gr.Button("Refresh")
            
            def list_speakers(token):
                if not token:
                    return []
                headers = api_headers(token)
                try:
                    resp = requests.get(f"{API_BASE}/api/speakers/", headers=headers)
                    if resp.status_code == 200:
                        speakers = resp.json()
                        return [[s["id"], s["name"], s["speaker_id"], s["is_default"], s["created_at"][:19]] for s in speakers]
                except:
                    pass
                return []
            
            refresh_speakers_btn.click(list_speakers, inputs=[token_state], outputs=[speaker_grid])
        
        with gr.Tab("🔊 TTS Generate"):
            gr.Markdown("### Generate Speech")
            
            with gr.Row():
                with gr.Column():
                    tts_text = gr.Textbox(label="Text to Synthesize", lines=4)
                    speaker_dropdown = gr.Dropdown(label="Select Speaker", choices=[])
                    lang_dropdown = gr.Dropdown(label="Language", choices=["auto", "ko", "en", "zh", "ja"], value="auto")
                    instruct_in = gr.Textbox(label="Style Instruction (optional)", lines=2)
                    
                    generate_btn = gr.Button("Generate", variant="primary")
                
                with gr.Column():
                    audio_out = gr.Audio(label="Generated Audio")
                    gen_status = gr.Textbox(label="Status", interactive=False)
            
            def load_speakers(token):
                if not token:
                    return []
                headers = api_headers(token)
                try:
                    resp = requests.get(f"{API_BASE}/api/speakers/", headers=headers)
                    if resp.status_code == 200:
                        speakers = resp.json()
                        return [s["name"] for s in speakers]
                except:
                    pass
                return []
            
            def generate_speech(token, text, speaker, lang, instruct):
                if not token:
                    return None, "Please login first"
                
                headers = api_headers(token)
                data = {
                    "text": text,
                    "speaker": speaker,
                    "language": lang,
                    "instruction": instruct if instruct else None
                }
                
                try:
                    resp = requests.post(f"{API_BASE}/api/tts/synthesize", json=data, headers=headers)
                    if resp.status_code == 200:
                        result = resp.json()
                        audio_file = result.get("audio_filename")
                        return f"{API_BASE}/api/tts/audio/{audio_file}", "Generated!"
                except Exception as e:
                    return None, str(e)
                return None, "Failed"
            
            generate_btn.click(generate_speech, inputs=[token_state, tts_text, speaker_dropdown, lang_dropdown, instruct_in], outputs=[audio_out, gen_status])
    
    return demo

if __name__ == "__main__":
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860)
