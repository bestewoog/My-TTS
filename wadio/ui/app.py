import gradio as gr
import requests

API_BASE = "http://localhost:21302"

def get_token(email, password):
    try:
        resp = requests.post(
            f"{API_BASE}/api/auth/login",
            data={"username": email, "password": password}
        )
        if resp.status_code == 200:
            return resp.json()["access_token"]
    except Exception as e:
        print(f"Login error: {e}")
    return None

def register_user(email, password):
    try:
        resp = requests.post(
            f"{API_BASE}/api/auth/register",
            json={"email": email, "password": password}
        )
        return resp.status_code in [200, 201, 400]
    except Exception as e:
        print(f"Register error: {e}")
        return False

def api_headers(token):
    return {"Authorization": f"Bearer {token}"}

def build_ui():
    with gr.Blocks(title="Wadio - Voice Platform") as demo:
        gr.Markdown("# 🎤 Wadio - Voice Management Platform")
        gr.Markdown("**Voice cloning and TTS generation platform using Qwen3-TTS**")
        
        token_state = gr.State(value=None)
        
        with gr.Row():
            login_col = gr.Column(scale=1)
            with login_col:
                gr.Markdown("### 🔐 Login")
                email_in = gr.Textbox(label="Email", placeholder="your@email.com")
                pass_in = gr.Textbox(label="Password", type="password")
                with gr.Row():
                    login_btn = gr.Button("Login", variant="primary")
                    reg_btn = gr.Button("Register")
                login_msg = gr.Textbox(label="Status", interactive=False)
        
        with gr.Row(visible=False, equal_height=False) as main_content:
            with gr.Column(scale=1):
                gr.Markdown("### 🎤 Voice Files")
                with gr.Row():
                    upload_file = gr.File(label="WAV Audio", file_types=[".wav"])
                transcript_in = gr.Textbox(label="Transcript (대사)", lines=2, placeholder="음성 파일의 대사를 입력하세요")
                upload_btn = gr.Button("Upload", variant="primary")
                upload_result = gr.Textbox(label="Result", interactive=False)
                file_list = gr.Dataframe(
                    headers=["ID", "Filename", "Duration", "Transcript"],
                    label="My Voice Files"
                )
                refresh_files_btn = gr.Button("🔄 Refresh Files")
            
            with gr.Column(scale=1):
                gr.Markdown("### 🔧 Fine-tuning")
                speaker_name = gr.Textbox(label="Speaker Name", placeholder="my_speaker")
                files_check = gr.CheckboxGroup(label="Select Voice Files for Training")
                with gr.Row():
                    epochs = gr.Slider(minimum=1, maximum=10, value=3, step=1, label="Epochs")
                    batch_size = gr.Slider(minimum=1, maximum=8, value=2, step=1, label="Batch Size")
                lr = gr.Textbox(label="Learning Rate", value="2e-5")
                start_btn = gr.Button("Start Training", variant="primary")
                train_result = gr.Textbox(label="Status", interactive=False)
                job_list = gr.Dataframe(
                    headers=["ID", "Speaker", "Status", "Created"],
                    label="Training Jobs"
                )
                refresh_jobs_btn = gr.Button("🔄 Refresh Jobs")
            
            with gr.Column(scale=1):
                gr.Markdown("### 📚 Speakers")
                speaker_grid = gr.Dataframe(
                    headers=["ID", "Name", "Speaker ID", "Default", "Created"],
                    label="My Speakers"
                )
                refresh_speakers_btn = gr.Button("🔄 Refresh Speakers")
                
                gr.Markdown("### 🔊 TTS Generate")
                tts_text = gr.Textbox(label="Text to Synthesize", lines=4, placeholder="생성할 텍스트를 입력하세요")
                speaker_dropdown = gr.Dropdown(label="Select Speaker", choices=[])
                lang_dropdown = gr.Dropdown(label="Language", choices=["auto", "ko", "en", "zh", "ja", "de", "fr", "es", "it", "ru"], value="ko")
                instruct_in = gr.Textbox(label="Style Instruction (선택)", lines=2, placeholder="예: cheerful, sad, angry...")
                generate_btn = gr.Button("Generate", variant="primary")
                audio_out = gr.Audio(label="Generated Audio")
                gen_status = gr.Textbox(label="Status", interactive=False)
        
        def do_login(email, password):
            token = get_token(email, password)
            if token:
                return token, "✅ Login successful!", gr.update(visible=True), gr.update(visible=False)
            return None, "❌ Login failed - check credentials", gr.update(visible=False), gr.update(visible=True)
        
        def do_register(email, password):
            ok = register_user(email, password)
            if ok:
                return "✅ Registered! Please login."
            return "❌ Registration failed"
        
        def upload_voice(token, f, transcript):
            if not token:
                return "❌ Please login first", []
            if not f:
                return "❌ Please select a file", []
            
            files = {"file": (f.name, open(f.name, "rb"), "audio/wav")}
            data = {"transcript": transcript or ""}
            headers = api_headers(token)
            
            try:
                resp = requests.post(
                    f"{API_BASE}/api/voice-files/upload",
                    files=files,
                    data=data,
                    headers=headers
                )
                if resp.status_code == 200:
                    return "✅ Uploaded!", list_files(token)
                else:
                    return f"❌ Upload failed: {resp.text}", []
            except Exception as e:
                return f"❌ Error: {str(e)}", []
        
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
        
        def start_training(token, name, file_ids, ep, batch, lr_val):
            if not token:
                return "❌ Please login first", []
            if not name:
                return "❌ Please enter speaker name", []
            if not file_ids:
                return "❌ Please select voice files", []
            
            headers = api_headers(token)
            data = {
                "speaker_name": name,
                "voice_file_ids": list(file_ids) if file_ids else [],
                "epochs": ep,
                "batch_size": batch,
                "lr": float(lr_val) if lr_val else 2e-5
            }
            
            try:
                resp = requests.post(f"{API_BASE}/api/finetune/start", json=data, headers=headers)
                if resp.status_code == 200:
                    return "✅ Training started!", list_jobs(token)
                else:
                    return f"❌ Failed: {resp.text}", []
            except Exception as e:
                return f"❌ Error: {str(e)}", []
        
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
        
        def load_speakers_for_dropdown(token):
            if not token:
                return gr.update(choices=[])
            headers = api_headers(token)
            try:
                resp = requests.get(f"{API_BASE}/api/speakers/", headers=headers)
                if resp.status_code == 200:
                    speakers = resp.json()
                    return gr.update(choices=[s["name"] for s in speakers])
            except:
                pass
            return gr.update(choices=[])
        
        def load_files_for_checkbox(token):
            if not token:
                return gr.update(choices=[])
            headers = api_headers(token)
            try:
                resp = requests.get(f"{API_BASE}/api/voice-files/", headers=headers)
                if resp.status_code == 200:
                    files = resp.json()
                    return gr.update(choices=[(f"{f['filename']} ({f.get('duration', 0):.1f}s)", f["id"]) for f in files])
            except:
                pass
            return gr.update(choices=[])
        
        def generate_speech(token, text, speaker, lang, instruct):
            if not token:
                return None, "❌ Please login first"
            if not text:
                return None, "❌ Please enter text"
            if not speaker:
                return None, "❌ Please select a speaker"
            
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
                    return f"{API_BASE}/api/tts/audio/{audio_file}", "✅ Generated!"
                else:
                    return None, f"❌ Failed: {resp.text}"
            except Exception as e:
                return None, f"❌ Error: {str(e)}"
        
        login_btn.click(do_login, inputs=[email_in, pass_in], outputs=[token_state, login_msg, main_content, login_col])
        reg_btn.click(do_register, inputs=[email_in, pass_in], outputs=[login_msg])
        
        upload_btn.click(upload_voice, inputs=[token_state, upload_file, transcript_in], outputs=[upload_result, file_list])
        refresh_files_btn.click(list_files, inputs=[token_state], outputs=[file_list])
        
        start_btn.click(start_training, inputs=[token_state, speaker_name, files_check, epochs, batch_size, lr], outputs=[train_result, job_list])
        refresh_jobs_btn.click(list_jobs, inputs=[token_state], outputs=[job_list])
        
        refresh_speakers_btn.click(list_speakers, inputs=[token_state], outputs=[speaker_grid])
        
        generate_btn.click(generate_speech, inputs=[token_state, tts_text, speaker_dropdown, lang_dropdown, instruct_in], outputs=[audio_out, gen_status])
        
        token_state.change(load_speakers_for_dropdown, inputs=[token_state], outputs=[speaker_dropdown])
        token_state.change(load_files_for_checkbox, inputs=[token_state], outputs=[files_check])
        token_state.change(list_speakers, inputs=[token_state], outputs=[speaker_grid])
        token_state.change(list_files, inputs=[token_state], outputs=[file_list])
        token_state.change(list_jobs, inputs=[token_state], outputs=[job_list])
    
    return demo

if __name__ == "__main__":
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860)
