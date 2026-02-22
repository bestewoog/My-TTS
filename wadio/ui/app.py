import gradio as gr
import requests
import os
import socket
from pathlib import Path

def get_local_ip():
    """로컬 IP 주소 가져오기"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# API_BASE 우선순위: 환경변수 > localhost (SSRF 보호 우회)
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:21302")
print(f"[Wadio UI] API_BASE: {API_BASE}")

# 출력 디렉토리
OUTPUT_DIR = Path(__file__).parent / "data" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def build_ui():
    with gr.Blocks(title="Wadio - 음성 플랫폼") as demo:
        # 상단 헤더
        with gr.Row():
            gr.Markdown("# 🎤 Wadio - 음성 플랫폼")
            gr.HTML('<div style="text-align: right; padding-top: 10px;"><a href="/api-guide" target="_blank" style="font-size: 18px; text-decoration: none; background: #4CAF50; color: white; padding: 8px 16px; border-radius: 5px;">📖 API 가이드</a></div>')
        gr.Markdown("**Qwen3-TTS 기반 음성 클로닝 및 TTS 생성 플랫폼**")
        
        # 사용 가이드
        gr.Markdown("""
        ---
        ## 📖 사용 가이드
        **사용 순서:**
        1. **음성 파일 업로드** → 2. **파인튜닝(선택)** → 3. **스피커 확인** → 4. **TTS 생성**
        
        - 기본 제공 스피커(Vivian, Ryan, Sohee 등)를 바로 사용 가능
        - 나만의 음성을 학습시키려면 파인튜닝 필요
        """)
        
        # ========== 섹션 1: 음성 파일 업로드 ==========
        with gr.Column(scale=1):
            gr.Markdown("### 🎤 1. 음성 파일 업로드")
            gr.Markdown("""
            **설명:** 나만의 음성 클로닝을 위한 음성 파일을 업로드합니다.
            
            - WAV 형식의 오디오 파일만 지원됩니다
            - 파일당 최대 3분 권장 (길수록 학습 시간 증가)
            """)
            with gr.Row():
                upload_file = gr.File(
                    label="음성 파일",
                    file_types=[".wav"],
                    type="filepath"
                )
            transcript_in = gr.Textbox(
                label="대사 (텍스트)",
                lines=3,
                placeholder="이 음성 파일에 해당하는 텍스트를 입력하세요.\n예: 안녕하세요, 저는 학생입니다.",
                info="음성 파일의 내용을 텍스트로 입력하세요"
            )
            upload_btn = gr.Button("업로드", variant="primary")
            upload_result = gr.Textbox(label="업로드 결과", interactive=False)
            file_list = gr.Dataframe(
                headers=["ID", "파일명", "길이", "대사"],
                label="내 음성 파일 목록"
            )
            refresh_files_btn = gr.Button("새로고침")
        
        # ========== 섹션 2: 파인튜닝 ==========
        with gr.Column(scale=1):
            gr.Markdown("### 🔧 2. 파인튜닝 (선택사항)")
            gr.Markdown("""
            **설명:** 업로드한 음성 파일로 나만의 커스텀 스피커를 학습시킵니다.
            
            **파라미터 설명:**
            | 파라미터 | 설명 | 권장값 |
            |---------|------|--------|
            | Epochs | 데이터 반복 학습 횟수 | 3~5 |
            | Batch Size | 한 번에 학습하는 샘플 수 | 2~4 |
            | Learning Rate | 가중치 업데이트 속도 | 2e-5 |
            """)
            speaker_name = gr.Textbox(
                label="스피커 이름",
                placeholder="my_voice (영문, 띄어쓰기 없이)",
                info="새로 만들 스피커의 이름을 입력하세요"
            )
            files_check = gr.CheckboxGroup(
                label="학습시킬 음성 파일",
                info="학습에 사용할 음성 파일을 선택하세요"
            )
            with gr.Row():
                epochs = gr.Slider(
                    minimum=1, maximum=10, value=3, step=1,
                    label="에포크 (반복 횟수)",
                    info="데이터를 몇 번 반복해서 학습할지"
                )
                batch_size = gr.Slider(
                    minimum=1, maximum=8, value=2, step=1,
                    label="배치 크기",
                    info="한 번에 학습하는 샘플 수"
                )
            lr = gr.Dropdown(
                label="학습률 (Learning Rate)",
                choices=["1e-5", "2e-5", "3e-5", "5e-5", "1e-4"],
                value="2e-5",
                info="1e-5(느림/안전) ~ 5e-5(빠름/불안정), 기본값: 2e-5"
            )
            start_btn = gr.Button("학습 시작", variant="primary")
            train_result = gr.Textbox(label="학습 상태", interactive=False)
            job_list = gr.Dataframe(
                headers=["ID", "스피커", "상태", "생성일"],
                label="학습 작업 목록"
            )
            refresh_jobs_btn = gr.Button("새로고침")
        
        # ========== 섹션 3: 스피커 목록 ==========
        with gr.Column(scale=1):
            gr.Markdown("### 📚 3. 스피커 목록")
            gr.Markdown("""
            **설명:** 사용 가능한 스피커 목록을 확인합니다.
            - **기본 스피커:** Vivian, Serena, Ryan, Aiden, Sohee 등
            - **커스텀 스피커:** 파인튜닝으로 생성한 스피커
            """)
            speaker_grid = gr.Dataframe(
                headers=["ID", "이름", "스피커ID", "기본여부", "생성일"],
                label="스피커 목록"
            )
            refresh_speakers_btn = gr.Button("새로고침")
            
        # ========== 섹션 4: TTS 생성 ==========
        with gr.Column(scale=1):
            gr.Markdown("### 🔊 4. TTS 생성 (텍스트 → 음성)")
            gr.Markdown("""
            **설명:** 텍스트를 음성으로 변환합니다.
            
            **지원 언어:** auto(자동), korean, english, chinese, japanese, german, french, spanish, italian, russian
            
            **스타일 지시 예시:** cheerful(밝게), sad(슬프게), angry(화나게), 빠르게, 부드럽게
            """)
            tts_text = gr.Textbox(
                label="변환할 텍스트",
                lines=4,
                placeholder="안녕하세요, 오늘 날씨가 좋네요.",
                info="음성으로 변환할 텍스트를 입력하세요"
            )
            # 기본 스피커 목록
            DEFAULT_SPEAKERS = ["vivian", "serena", "ryan", "aiden", "sohee", "uncle_fu", "ono_anna", "eric", "dylan"]
            speaker_dropdown = gr.Dropdown(
                label="스피커",
                choices=DEFAULT_SPEAKERS,
                value="vivian",
                info="사용할 스피커를 선택하세요"
            )
            lang_dropdown = gr.Dropdown(
                label="언어",
                choices=["auto", "korean", "english", "chinese", "japanese", "german", "french", "spanish", "italian", "russian"],
                value="korean",
                info="텍스트의 언어를 선택하세요 (auto: 자동 감지)"
            )
            instruct_in = gr.Textbox(
                label="스타일 지시 (선택)",
                lines=2,
                placeholder="예: cheerful, sad, angry, 빠르게, 부드럽게...",
                info="말하기 스타일을 지정하세요 (선택사항)"
            )
            generate_btn = gr.Button("음성 생성", variant="primary")
            audio_out = gr.Audio(label="생성된 음성")
            gen_status = gr.Textbox(label="생성 상태", interactive=False)
        
        # ========== 이벤트 핸들러 ==========
        def upload_voice(f, transcript):
            """음성 파일 업로드"""
            if not f:
                return "❌ 파일을 선택해 주세요", []
            
            files = {"file": (os.path.basename(f), open(f, "rb"), "audio/wav")}
            data = {"transcript": transcript or ""}
            
            try:
                resp = requests.post(
                    f"{API_BASE}/api/voice-files/upload",
                    files=files,
                    data=data
                )
                if resp.status_code == 200:
                    return "✅ 업로드 완료!", list_files()
                else:
                    return f"❌ 업로드 실패: {resp.text}", []
            except Exception as e:
                return f"❌ 오류: {str(e)}", []
        
        def list_files():
            """음성 파일 목록 조회"""
            try:
                resp = requests.get(f"{API_BASE}/api/voice-files/")
                if resp.status_code == 200:
                    files = resp.json()
                    return [[f["id"], f["filename"], f"{f.get('duration', 0):.1f}s", f.get("transcript", "")[:50]] for f in files]
            except:
                pass
            return []
        
        def start_training(name, file_ids, ep, batch, lr_val):
            """파인튜닝 시작"""
            if not name:
                return "❌ 스피커 이름을 입력해 주세요", []
            if not file_ids:
                return "❌ 음성 파일을 선택해 주세요", []
            
            data = {
                "speaker_name": name,
                "voice_file_ids": list(file_ids) if file_ids else [],
                "epochs": ep,
                "batch_size": batch,
                "lr": float(lr_val) if lr_val else 2e-5
            }
            
            try:
                resp = requests.post(f"{API_BASE}/api/finetune/start", json=data)
                if resp.status_code == 200:
                    return "✅ 학습 시작됨!", list_jobs()
                else:
                    return f"❌ 실패: {resp.text}", []
            except Exception as e:
                return f"❌ 오류: {str(e)}", []
        
        def list_jobs():
            """학습 작업 목록 조회"""
            try:
                resp = requests.get(f"{API_BASE}/api/finetune/jobs")
                if resp.status_code == 200:
                    jobs = resp.json()
                    return [[j["id"], j["speaker_name"], j["status"], j["created_at"][:19]] for j in jobs]
            except:
                pass
            return []
        
        def list_speakers():
            """스피커 목록 조회"""
            try:
                resp = requests.get(f"{API_BASE}/api/speakers/")
                if resp.status_code == 200:
                    speakers = resp.json()
                    return [[s["id"], s["name"], s["speaker_id"], s["is_default"], s["created_at"][:19]] for s in speakers]
            except:
                pass
            return []
        
        def load_speakers_for_dropdown():
            """드롭다운용 스피커 목록 로드"""
            try:
                resp = requests.get(f"{API_BASE}/api/speakers/")
                if resp.status_code == 200:
                    speakers = resp.json()
                    return gr.update(choices=[s["name"] for s in speakers])
            except:
                pass
            return gr.update(choices=[])
        
        def load_files_for_checkbox():
            """체크박스용 파일 목록 로드"""
            try:
                resp = requests.get(f"{API_BASE}/api/voice-files/")
                if resp.status_code == 200:
                    files = resp.json()
                    return gr.update(choices=[(f"{f['filename']} ({f.get('duration', 0):.1f}s)", f["id"]) for f in files])
            except:
                pass
            return gr.update(choices=[])
        
        def generate_speech(text, speaker, lang, instruct):
            """TTS 음성 생성"""
            if not text:
                return None, "❌ 텍스트를 입력해 주세요"
            if not speaker:
                return None, "❌ 스피커를 선택해 주세요"
            
            data = {
                "text": text,
                "speaker": speaker,
                "language": lang,
                "instruction": instruct if instruct else None
            }
            
            url = f"{API_BASE}/api/tts/synthesize"
            print(f"[TTS] 요청 URL: {url}")
            print(f"[TTS] 요청 데이터: {data}")
            
            try:
                resp = requests.post(url, json=data, timeout=120)
                print(f"[TTS] 응답 상태: {resp.status_code}")
                print(f"[TTS] 응답 내용: {resp.text[:500] if resp.text else 'empty'}")
                
                if resp.status_code == 200:
                    result = resp.json()
                    audio_file = result.get("audio_filename")
                    
                    # 로컬 파일 경로 반환
                    local_path = OUTPUT_DIR / audio_file
                    print(f"[TTS] 로컬 파일 경로: {local_path}")
                    
                    if local_path.exists():
                        return str(local_path), "✅ 생성 완료!"
                    else:
                        # 파일이 없으면 API에서 다운로드
                        audio_url = f"{API_BASE}/api/tts/audio/{audio_file}"
                        audio_resp = requests.get(audio_url, timeout=30)
                        if audio_resp.status_code == 200:
                            with open(local_path, 'wb') as f:
                                f.write(audio_resp.content)
                            return str(local_path), "✅ 생성 완료!"
                        else:
                            return None, "❌ 오디오 다운로드 실패"
                else:
                    error_msg = f"❌ 실패 (HTTP {resp.status_code}): {resp.text[:200]}"
                    print(f"[TTS] 에러: {error_msg}")
                    return None, error_msg
            except requests.exceptions.Timeout:
                return None, "❌ 오류: 요청 시간 초과 (120초)"
            except requests.exceptions.ConnectionError as e:
                return None, "❌ 연결 오류: API 서버에 연결할 수 없습니다"
            except Exception as e:
                print(f"[TTS] 예외 발생: {type(e).__name__}: {str(e)}")
                return None, f"❌ 오류: {str(e)}"
        
        # ========== 이벤트 연결 ==========
        upload_btn.click(
            upload_voice,
            inputs=[upload_file, transcript_in],
            outputs=[upload_result, file_list],
            api_name="음성파일_업로드"
        )
        refresh_files_btn.click(list_files, outputs=[file_list], api_name="음성파일_목록")
        
        start_btn.click(
            start_training,
            inputs=[speaker_name, files_check, epochs, batch_size, lr],
            outputs=[train_result, job_list],
            api_name="파인튜닝_시작"
        )
        refresh_jobs_btn.click(list_jobs, outputs=[job_list], api_name="학습작업_목록")
        
        refresh_speakers_btn.click(list_speakers, outputs=[speaker_grid], api_name="스피커_목록")
        
        generate_btn.click(
            generate_speech,
            inputs=[tts_text, speaker_dropdown, lang_dropdown, instruct_in],
            outputs=[audio_out, gen_status],
            api_name="음성생성"
        )
        
        # 페이지 로드 시 데이터 초기화
        demo.load(load_speakers_for_dropdown, outputs=[speaker_dropdown])
        demo.load(load_files_for_checkbox, outputs=[files_check])
        demo.load(list_speakers, outputs=[speaker_grid])
        demo.load(list_files, outputs=[file_list])
        demo.load(list_jobs, outputs=[job_list])
    
    return demo

if __name__ == "__main__":
    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        allowed_paths=[str(OUTPUT_DIR)]
    )
