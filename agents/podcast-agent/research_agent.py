"""
research_agent.py
-----------------
Research Agent: youtube-summarizer 스킬을 활용하여
각 영상의 트랜스크립트를 추출하고 채널별 요약 digest를 생성합니다.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from youtube_transcript_api import YouTubeTranscriptApi, CouldNotRetrieveTranscript
    _YT_API = YouTubeTranscriptApi()
except ImportError:
    print("❌ youtube-transcript-api가 설치되어 있지 않습니다.")
    print("   실행: pip install youtube-transcript-api")
    sys.exit(1)


def load_config(config_path: str = "config.json") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_transcript(video_id: str, language: str = "en") -> str | None:
    """
    유튜브 영상의 트랜스크립트를 추출합니다. (youtube-transcript-api v1.2.4+)
    우선순위: 지정 언어 → 영어 → 첫 번째 사용 가능 언어
    """
    try:
        # v1.2.4: 인스턴스 기반 API
        transcript = _YT_API.fetch(video_id, languages=[language, "en"])
        # FetchedTranscript는 이터러블: 각 snippet에 .text 속성
        full_text = " ".join(snippet.text for snippet in transcript)
        return full_text.strip()

    except CouldNotRetrieveTranscript:
        return None
    except Exception as e:
        # 첫 번째 시도 실패 시 언어 제한 없이 재시도
        try:
            transcript = _YT_API.fetch(video_id)
            full_text = " ".join(snippet.text for snippet in transcript)
            return full_text.strip()
        except Exception:
            print(f"    ⚠️  트랜스크립트 추출 오류 ({video_id}): {e}")
            return None



def summarize_video(video: dict, transcript: str) -> str:
    """
    영상 메타데이터와 트랜스크립트로 단일 영상 요약 텍스트를 생성합니다.
    """
    return (
        f"### {video['title']}\n"
        f"- **Channel**: {video['channel']}\n"
        f"- **URL**: {video['url']}\n"
        f"- **Uploaded**: {video['upload_date']}\n\n"
        f"**Transcript:**\n{transcript[:8000]}\n"  # NotebookLM 소스 크기 제한 고려
    )


def run(videos: list[dict], config: dict) -> str:
    """
    Research Agent 메인 실행 함수.
    모든 영상 트랜스크립트를 추출하고 daily digest 텍스트를 반환합니다.
    """
    language = config.get("language", "en")
    min_length = config.get("min_transcript_length", 100)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    print(f"\n🔬 Research Agent 시작 — {len(videos)}개 영상 처리 중...\n")

    digest_sections = []
    success_count = 0
    skip_count = 0

    for i, video in enumerate(videos, 1):
        print(f"  [{i}/{len(videos)}] {video['title'][:60]}...")
        transcript = extract_transcript(video["video_id"], language)

        if not transcript or len(transcript) < min_length:
            print(f"    ⏭️  트랜스크립트 없음 또는 너무 짧음 — 건너뜀")
            skip_count += 1
            continue

        summary = summarize_video(video, transcript)
        digest_sections.append(summary)
        success_count += 1
        print(f"    ✅ 추출 완료 ({len(transcript):,} chars)")

    if not digest_sections:
        print("\n⚠️  유효한 트랜스크립트가 없습니다.")
        return ""

    header = (
        f"# AI Daily Digest — {today}\n\n"
        f"**수집 채널**: {len(set(v['channel'] for v in videos))}개\n"
        f"**처리 영상**: {success_count}개 성공 / {skip_count}개 건너뜀\n\n"
        f"---\n\n"
    )

    full_digest = header + "\n\n---\n\n".join(digest_sections)

    print(f"\n✅ Research Agent 완료: {success_count}개 영상 처리됨\n")
    return full_digest


def save_digest(digest: str, output_dir: str = "output") -> str:
    """
    Digest를 파일로 저장하고 경로를 반환합니다.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    digest_path = Path(output_dir) / f"daily_digest_{today}.txt"
    digest_path.write_text(digest, encoding="utf-8")
    print(f"💾 Digest 저장됨: {digest_path}")
    return str(digest_path)


if __name__ == "__main__":
    # 단독 실행 시 테스트 (fetch_recent_videos 없이 직접 실행)
    from fetch_recent_videos import fetch_all_recent_videos
    config = load_config()
    videos = fetch_all_recent_videos(config)

    if not videos:
        print("⚠️  수집된 영상이 없습니다.")
        sys.exit(0)

    digest = run(videos, config)
    if digest:
        path = save_digest(digest, config.get("output_dir", "output"))
        print(f"\n📄 Digest 파일: {path}")
