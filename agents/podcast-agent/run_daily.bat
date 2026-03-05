@echo off
:: AI Daily Podcast Generator - Windows Task Scheduler용 배치 파일
:: 매일 오전 8시에 실행되도록 Windows 작업 스케줄러에 등록하세요.

cd /d C:\Users\0115a\Projects\ggdd012_20270306_AntiGravity\agents\podcast-agent

echo [%date% %time%] Starting AI Daily Podcast Generator >> logs\scheduler.log 2>&1
python orchestrator.py >> logs\scheduler.log 2>&1
echo [%date% %time%] Finished >> logs\scheduler.log 2>&1
