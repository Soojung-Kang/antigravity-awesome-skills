# AI Daily Podcast Generator

매일 오전 8시, 지정된 유튜브 채널의 최신 영상을 NotebookLM으로 종합 팟캐스트를 자동 생성하는 멀티에이전트 시스템입니다.

## 구조

```
podcast-agent/
├── orchestrator.py          # 메인 실행 파일 (여기서 시작)
├── fetch_recent_videos.py   # YouTube 최신 영상 수집 (yt-dlp)
├── research_agent.py        # 트랜스크립트 추출 (youtube-summarizer 스킬)
├── notebooklm_agent.py      # NotebookLM 팟캐스트 생성 (notebooklm 스킬)
├── config.json              # 채널 목록 및 설정
├── run_daily.bat            # Windows 스케줄러용 배치 파일
├── output/                  # 생성된 팟캐스트 및 digest 저장
└── logs/                    # 실행 로그
```

## 의존성 설치

```powershell
cd agents\podcast-agent
pip install -r requirements.txt
```

## 채널 설정

`config.json`에서 채널 목록과 설정을 변경할 수 있습니다:

```json
{
  "channels": [
    "https://www.youtube.com/@nateherk",
    "https://www.youtube.com/@nicksaraev",
    "https://www.youtube.com/@Itssssss_Jack",
    "https://www.youtube.com/@Chase-H-AI"
  ],
  "lookback_hours": 24,
  "podcast_format": "deep_dive"
}
```

## 수동 실행

```powershell
cd agents\podcast-agent
python orchestrator.py
```

각 단계별 단독 테스트:
```powershell
python fetch_recent_videos.py    # 영상 목록 확인
python research_agent.py         # 트랜스크립트 추출 테스트
python notebooklm_agent.py       # NotebookLM 연동 테스트
```

## Windows 작업 스케줄러 설정 (매일 오전 8시 자동 실행)

1. **작업 스케줄러 열기**: `Win + R` → `taskschd.msc`
2. **작업 만들기** 클릭
3. **일반 탭**: 이름 → `AI Daily Podcast`
4. **트리거 탭**: 새로 만들기 → 매일 → 시작: `오전 8:00`
5. **동작 탭**: 새로 만들기 →
   - 프로그램: `C:\Users\0115a\Projects\ggdd012_20270306_AntiGravity\agents\podcast-agent\run_daily.bat`
6. **확인** 클릭

또는 PowerShell로 자동 등록:
```powershell
$trigger = New-ScheduledTaskTrigger -Daily -At "08:00"
$action = New-ScheduledTaskAction -Execute "C:\Users\0115a\Projects\ggdd012_20270306_AntiGravity\agents\podcast-agent\run_daily.bat"
Register-ScheduledTask -TaskName "AI Daily Podcast" -Trigger $trigger -Action $action
```

## 사전 요구 사항

- Python 3.10+
- `yt-dlp` (pip install yt-dlp)
- `youtube-transcript-api` (pip install youtube-transcript-api)
- `nlm` CLI (NotebookLM MCP) - 인증 완료 상태

## 출력 결과

매일 실행 후 `output/` 폴더에 저장됩니다:
- `daily_digest_YYYYMMDD.txt` — 채널별 영상 transcript digest
- `podcast_YYYYMMDD.mp4` — NotebookLM Audio Overview 팟캐스트
