---
description: [YouTube to NotebookLM Podcast Automation]
---
# YouTube to NotebookLM Podcast Automation Workflow

지정된 유튜브 채널의 최신 영상을 수집하여 NotebookLM을 통해 고품질 팟캐스트(Audio Overview)를 자동 생성하는 워크플로우입니다.

## 📋 사전 요구 사항
- **Python 3.10+** (v1.2.4+ `youtube-transcript-api` 대응 필요)
- **nlm CLI (NotebookLM MCP)**: `nlm login`으로 인증 완료 상태
- **공통 스킬**: `youtube-summarizer`, `notebooklm`

## 🚀 실행 단계

### 1. 환경 준비 및 의존성 설치
워크스페이스 내 `agents/podcast-agent/` 폴더를 생성하고 필수 라이브러리를 설치합니다.
// turbo
```powershell
pip install yt-dlp youtube-transcript-api
```

### 2. 채널 및 동작 설정 (`config.json`)
수집할 채널 URL과 팟캐스트 포맷(`deep_dive` 또는 `brief`), 그리고 영상 조회 기간(`lookback_hours`)을 설정합니다.

### 3. 영상 수집 (`fetch_recent_videos.py`)
`yt-dlp`를 사용하여 채널의 비디오 피드를 크롤링합니다. 
> [!IMPORTANT]
> `--flat-playlist` 모드에서는 `upload_date`가 정상적으로 표시되지 않으므로, `--dateafter` 필터를 직접 사용하고 탭(`\t`) 구분자로 파싱하는 것이 안정적입니다.

### 4. 트랜스크립트 추출 및 분석 (`research_agent.py`)
`youtube-transcript-api`를 활용합니다.
> [!NOTE]
> v1.2.4 이상에서는 `YouTubeTranscriptApi()` 인스턴스를 생성한 후 `api.fetch(video_id)`를 호출해야 하며, 결과물은 `.text` 속성을 가진 스니펫들의 이터러블입니다.

### 5. NotebookLM 연동 및 생성 (`notebooklm_agent.py`)
1. `mcp_notebooklm_notebook_create` 툴로 새 노트북 생성
2. `mcp_notebooklm_source_add` 툴로 생성된 `daily_digest.txt` 업로드
3. `mcp_notebooklm_studio_create(artifact_type="audio")`로 팟캐스트 생성 요청
4. `mcp_notebooklm_studio_status`를 폴링하며 완료 대기

### 6. 자동화 스케줄링 (`run_daily.bat`)
Windows 작업 스케줄러에 등록하여 매일 정해진 시간에 `orchestrator.py`를 실행합니다.

## 🛠️ 문제 해결 (Troubleshooting)
- **트랜스크립트 오류**: 일부 채널은 자막이 비활성화되어 있을 수 있습니다. `CouldNotRetrieveTranscript` 예외 처리를 반드시 포함하세요.
- **NotebookLM 오디오 생성 지연**: 30만 자 이상의 방대한 데이터의 경우 인코딩에 10분 이상 소요될 수 있습니다. 폴링 주기를 30~60초로 넉넉히 설정하세요.
- **다운로드 실패**: `studio_status`에서 `status`가 `completed`이거나 `audio_url`이 존재할 때 `nlm download` 또는 `mcp_notebooklm_download_artifact`를 호출하세요.
