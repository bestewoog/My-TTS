# Wadio API 가이드

Base URL: `http://<SERVER_IP>:21302/api`

---

## 🔊 TTS API

### POST /tts/synthesize
텍스트를 음성으로 변환합니다.

**Request Body:**
```json
{
  "text": "안녕하세요, 테스트입니다.",
  "speaker": "vivian",
  "language": "korean",
  "instruction": "부드럽게"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| text | string | ✓ | 변환할 텍스트 |
| speaker | string | ✓ | 스피커 이름 (vivian, serena, ryan, aiden, sohee 등) |
| language | string | | 언어 (auto, korean, english, chinese, japanese 등) |
| instruction | string | | 스타일 지시 (cheerful, sad, angry 등) |

**Response:**
```json
{
  "audio_filename": "uuid.wav",
  "message": "Audio generated successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:21302/api/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "안녕하세요", "speaker": "vivian", "language": "korean"}'
```

---

### GET /tts/audio/{filename}
생성된 오디오 파일을 다운로드합니다.

**Response:** WAV 파일 (24000 Hz, 16-bit mono)

**Example:**
```bash
curl http://localhost:21302/api/tts/audio/uuid.wav -o output.wav
```

---

### GET /tts/default-speakers
기본 제공 스피커 목록을 조회합니다.

**Response:**
```json
{
  "speakers": ["vivian", "serena", "ryan", "aiden", "sohee", ...]
}
```

---

## 🎤 Voice Files API

### POST /voice-files/upload
음성 파일을 업로드합니다. (파인튜닝용)

**Request:** multipart/form-data
- `file`: WAV 파일
- `transcript`: 음성 내용 (선택)

**Response:**
```json
{
  "id": 1,
  "filename": "voice.wav",
  "duration": 10.5
}
```

**Example:**
```bash
curl -X POST http://localhost:21302/api/voice-files/upload \
  -F "file=@voice.wav" \
  -F "transcript=안녕하세요"
```

---

### GET /voice-files/
업로드한 음성 파일 목록을 조회합니다.

**Response:**
```json
[
  {"id": 1, "filename": "voice.wav", "duration": 10.5, "transcript": "안녕하세요"}
]
```

---

### DELETE /voice-files/{file_id}
음성 파일을 삭제합니다.

---

## 🔧 Finetune API

### POST /finetune/start
파인튜닝 작업을 시작합니다.

**Request Body:**
```json
{
  "speaker_name": "my_voice",
  "voice_file_ids": [1, 2, 3],
  "epochs": 3,
  "batch_size": 2,
  "lr": 2e-5
}
```

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| speaker_name | string | - | 새 스피커 이름 (영문, 공백 없이) |
| voice_file_ids | array | - | 학습할 음성 파일 ID 목록 |
| epochs | int | 3 | 반복 횟수 (1-10) |
| batch_size | int | 2 | 배치 크기 (1-8) |
| lr | float | 2e-5 | 학습률 (1e-5 ~ 1e-4) |

**Response:**
```json
{
  "job_id": 1,
  "status": "queued"
}
```

---

### GET /finetune/jobs
파인튜닝 작업 목록을 조회합니다.

---

### GET /finetune/jobs/{job_id}
특정 작업의 상세 정보를 조회합니다.

---

### DELETE /finetune/jobs/{job_id}
진행 중인 작업을 취소합니다.

---

## 📚 Speakers API

### GET /speakers/
사용 가능한 스피커 목록을 조회합니다.

**Response:**
```json
[
  {
    "id": 1,
    "name": "vivian",
    "speaker_id": 0,
    "model_path": null,
    "is_default": true,
    "created_at": "2026-02-22T13:12:33"
  }
]
```

---

### DELETE /speakers/{speaker_id}
커스텀 스피커를 삭제합니다.

---

### POST /speakers/{speaker_id}/set-default
기본 스피커로 설정합니다.

---

## 🌐 지원 언어

| 코드 | 언어 |
|------|------|
| auto | 자동 감지 |
| korean | 한국어 |
| english | 영어 |
| chinese | 중국어 |
| japanese | 일본어 |
| german | 독일어 |
| french | 프랑스어 |
| spanish | 스페인어 |
| italian | 이탈리아어 |
| russian | 러시아어 |

---

## 🎭 기본 스피커

| 이름 | 특징 |
|------|------|
| vivian | 기본 여성 목소리 |
| serena | 부드러운 여성 목소리 |
| ryan | 남성 목소리 |
| aiden | 또 다른 남성 목소리 |
| sohee | 한국어 여성 목소리 |
| uncle_fu | 중국어 남성 목소리 |
| ono_anna | 일본어 여성 목소리 |
| eric | 영어 남성 목소리 |
| dylan | 영어 남성 목소리 |
