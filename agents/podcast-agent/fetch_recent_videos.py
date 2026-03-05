"""
fetch_recent_videos.py
----------------------
지정된 유튜브 채널에서 최근 N시간 이내에 업로드된 영상 URL을 수집합니다.
yt-dlp를 사용해 채널 메타데이터를 조회하고 업로드 시간 기준으로 필터링합니다.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


def load_config(config_path: str = "config.json") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_recent_videos_from_channel(channel_url: str, lookback_hours: int = 24) -> list[dict]:
    """
    yt-dlp로 채널의 최신 영상 목록을 가져와 lookback_hours 이내 영상만 반환합니다.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    dateafter = cutoff.strftime("%Y%m%d")

    print(f"  📡 조회 중: {channel_url} (기준일: {dateafter}~)")

    try:
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--playlist-end", "30",
            "--dateafter", dateafter,
            "--print", "%(id)s\t%(title)s\t%(upload_date>%Y%m%d,NA)s\t%(channel,Unknown)s",
            "--no-warnings",
            "--quiet",
            f"{channel_url}/videos",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)

        if result.returncode != 0 and not result.stdout.strip():
            print(f"  ⚠️  채널 조회 실패: {channel_url}")
            if result.stderr:
                print(f"     오류: {result.stderr[:200]}")
            return []

        videos = []
        for line in result.stdout.strip().splitlines():
            if not line or "\t" not in line:
                continue
            parts = line.split("\t", 3)
            if len(parts) < 2:
                continue

            video_id = parts[0].strip()
            title = parts[1].strip()
            upload_date_str = parts[2].strip() if len(parts) > 2 else "NA"
            channel_name = parts[3].strip() if len(parts) > 3 else channel_url.split("@")[-1]

            if not video_id or video_id == "NA":
                continue

            # upload_date가 NA이면 URL만으로 추가 (날짜 필터가 --dateafter로 이미 적용됨)
            videos.append({
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "title": title,
                "channel": channel_name if channel_name != "NA" else channel_url.split("@")[-1],
                "upload_date": upload_date_str if upload_date_str != "NA" else dateafter,
            })
            print(f"  ✅ 발견: [{channel_name}] {title[:60]}")

        return videos

    except subprocess.TimeoutExpired:
        print(f"  ⚠️  타임아웃: {channel_url}")
        return []
    except FileNotFoundError:
        print("  ❌ yt-dlp가 설치되어 있지 않습니다. 'pip install yt-dlp' 실행 후 재시도하세요.")
        sys.exit(1)



def fetch_all_recent_videos(config: dict) -> list[dict]:
    """
    config에 지정된 모든 채널에서 최신 영상을 수집합니다.
    """
    channels = config.get("channels", [])
    lookback_hours = config.get("lookback_hours", 24)
    all_videos = []

    print(f"\n🔍 {len(channels)}개 채널에서 최근 {lookback_hours}시간 이내 영상 탐색 중...\n")

    for channel_url in channels:
        videos = fetch_recent_videos_from_channel(channel_url, lookback_hours)
        all_videos.extend(videos)

    print(f"\n📊 총 {len(all_videos)}개 신규 영상 발견\n")
    return all_videos


if __name__ == "__main__":
    config = load_config()
    videos = fetch_all_recent_videos(config)

    for v in videos:
        print(f"  [{v['channel']}] {v['title']} → {v['url']}")
