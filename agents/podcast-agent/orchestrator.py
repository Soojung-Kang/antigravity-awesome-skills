"""
orchestrator.py
---------------
메인 오케스트레이터: 두 에이전트를 순서대로 실행하여
유튜브 최신 영상 → NotebookLM 팟캐스트 파이프라인을 완성합니다.

실행 방법:
    python orchestrator.py

Windows 작업 스케줄러에서 매일 오전 8시에 run_daily.bat으로 자동 실행됩니다.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import fetch_recent_videos
import notebooklm_agent
import research_agent


def load_config(config_path: str = "config.json") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def setup_logging(logs_dir: str) -> logging.Logger:
    """날짜별 로그 파일 설정."""
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    log_file = Path(logs_dir) / f"run_{today}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("orchestrator")


def print_banner():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print("=" * 60)
    print("  🎙️  AI Daily Podcast Generator")
    print(f"  📅 {now}")
    print("=" * 60)


def main():
    config = load_config()
    logs_dir = config.get("logs_dir", "logs")
    output_dir = config.get("output_dir", "output")
    logger = setup_logging(logs_dir)

    print_banner()
    logger.info("=== Orchestrator 시작 ===")

    # ──────────────────────────────────────────
    # Step 1: 최신 영상 수집 (Research Agent Phase 1)
    # ──────────────────────────────────────────
    logger.info("Step 1: 유튜브 최신 영상 수집 중...")
    videos = fetch_recent_videos.fetch_all_recent_videos(config)

    if not videos:
        logger.warning("⚠️  새로운 영상이 없습니다. 오늘은 팟캐스트를 생성하지 않습니다.")
        print("\n⚠️  오늘은 수집된 영상이 없어 종료합니다.\n")
        sys.exit(0)

    logger.info(f"  → {len(videos)}개 영상 수집 완료")

    # ──────────────────────────────────────────
    # Step 2: 트랜스크립트 추출 & Digest 생성 (Research Agent Phase 2)
    # ──────────────────────────────────────────
    logger.info("Step 2: 트랜스크립트 추출 및 Digest 생성 중...")
    digest_text = research_agent.run(videos, config)

    if not digest_text:
        logger.error("❌ Digest 생성 실패 — 유효한 트랜스크립트가 없습니다.")
        sys.exit(1)

    digest_path = research_agent.save_digest(digest_text, output_dir)
    logger.info(f"  → Digest 저장됨: {digest_path}")

    # ──────────────────────────────────────────
    # Step 3: NotebookLM 팟캐스트 생성
    # ──────────────────────────────────────────
    logger.info("Step 3: NotebookLM 팟캐스트 생성 중...")
    podcast_path = notebooklm_agent.run(digest_text, digest_path, config)

    if not podcast_path:
        logger.error("❌ 팟캐스트 생성 실패")
        sys.exit(1)

    logger.info(f"  → 팟캐스트 완성: {podcast_path}")

    # ──────────────────────────────────────────
    # 완료 요약
    # ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  ✅ 오늘의 AI 팟캐스트가 완성되었습니다!")
    print(f"  📁 파일: {podcast_path}")
    print(f"  📄 Digest: {digest_path}")
    print("=" * 60 + "\n")

    logger.info("=== Orchestrator 완료 ===")


if __name__ == "__main__":
    main()
