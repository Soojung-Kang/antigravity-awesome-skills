"""
notebooklm_agent.py
-------------------
NotebookLM Agent: notebooklm MCP 서버를 활용하여
당일 digest를 NotebookLM에 소스로 추가하고
Audio Overview(팟캐스트)를 생성 후 다운로드합니다.

NotebookLM MCP 서버가 실행 중이어야 합니다.
(nlm 또는 antigravity의 notebooklm MCP)
"""

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def load_config(config_path: str = "config.json") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_nlm(command: list[str], capture: bool = True) -> subprocess.CompletedProcess:
    """nlm CLI 커맨드를 실행합니다."""
    try:
        result = subprocess.run(
            ["nlm"] + command,
            capture_output=capture,
            text=True,
            timeout=300
        )
        return result
    except FileNotFoundError:
        print("❌ nlm CLI가 설치되어 있지 않습니다.")
        print("   설치: pip install notebooklm-cli")
        sys.exit(1)


def create_notebook(title: str) -> str | None:
    """새 NotebookLM 노트북을 생성하고 notebook ID를 반환합니다."""
    print(f"  📓 노트북 생성 중: '{title}'")
    result = run_nlm(["notebook", "create", "--title", title])

    if result.returncode != 0:
        print(f"  ❌ 노트북 생성 실패: {result.stderr[:300]}")
        return None

    # nlm 출력에서 notebook ID 파싱
    for line in result.stdout.splitlines():
        if "notebook_id" in line.lower() or "id:" in line.lower():
            parts = line.split()
            for part in parts:
                # UUID 패턴 감지 (8-4-4-4-12)
                if len(part) == 36 and part.count("-") == 4:
                    print(f"  ✅ 노트북 생성됨: {part}")
                    return part

    # 파싱 실패 시 전체 출력 표시
    print(f"  ℹ️  노트북 생성 출력:\n{result.stdout}")
    return None


def add_source_text(notebook_id: str, text: str, title: str) -> bool:
    """텍스트를 NotebookLM 소스로 추가합니다."""
    print(f"  📎 소스 추가 중: '{title[:50]}'")

    # 임시 파일로 저장 후 추가
    tmp_path = Path("logs") / "_tmp_source.txt"
    tmp_path.parent.mkdir(exist_ok=True)
    tmp_path.write_text(text, encoding="utf-8")

    result = run_nlm([
        "source", "add",
        "--notebook-id", notebook_id,
        "--file", str(tmp_path),
        "--title", title
    ])

    tmp_path.unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"  ⚠️  소스 추가 실패: {result.stderr[:200]}")
        return False

    print(f"  ✅ 소스 추가됨")
    return True


def create_audio_overview(notebook_id: str, fmt: str = "deep_dive") -> str | None:
    """Audio Overview(팟캐스트)를 생성하고 artifact ID를 반환합니다."""
    print(f"  🎙️  Audio Overview 생성 중 (format: {fmt})...")

    result = run_nlm([
        "studio", "create",
        "--notebook-id", notebook_id,
        "--type", "audio",
        "--format", fmt
    ])

    if result.returncode != 0:
        print(f"  ❌ Audio Overview 생성 실패: {result.stderr[:300]}")
        return None

    # artifact ID 파싱
    for line in result.stdout.splitlines():
        if "artifact_id" in line.lower() or "id:" in line.lower():
            parts = line.split()
            for part in parts:
                if len(part) == 36 and part.count("-") == 4:
                    print(f"  ✅ 생성 시작됨: {part}")
                    return part

    print(f"  ℹ️  Audio Overview 출력:\n{result.stdout}")
    return None


def wait_and_download(notebook_id: str, artifact_id: str, output_path: str, max_wait: int = 300) -> bool:
    """
    Audio Overview 생성 완료를 기다린 후 MP3를 다운로드합니다.
    """
    print(f"  ⏳ 팟캐스트 생성 대기 중 (최대 {max_wait}초)...")
    start = time.time()

    while time.time() - start < max_wait:
        result = run_nlm([
            "studio", "status",
            "--notebook-id", notebook_id
        ])

        if "completed" in result.stdout.lower():
            break

        remaining = int(max_wait - (time.time() - start))
        print(f"    ⏳ 생성 중... ({remaining}초 남음)")
        time.sleep(30)
    else:
        print("  ⚠️  타임아웃: 팟캐스트 생성이 완료되지 않았습니다.")
        return False

    # 다운로드
    print(f"  ⬇️  다운로드 중: {output_path}")
    result = run_nlm([
        "download",
        "--notebook-id", notebook_id,
        "--artifact-id", artifact_id,
        "--type", "audio",
        "--output", output_path
    ])

    if result.returncode != 0:
        print(f"  ❌ 다운로드 실패: {result.stderr[:200]}")
        return False

    print(f"  ✅ 팟캐스트 저장됨: {output_path}")
    return True


def run(digest_text: str, digest_path: str, config: dict) -> str | None:
    """
    NotebookLM Agent 메인 실행 함수.
    digest를 NotebookLM에 올리고 팟캐스트를 생성한 후 경로를 반환합니다.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_compact = datetime.now(timezone.utc).strftime("%Y%m%d")
    title = f"{config.get('notebook_title_prefix', 'AI Daily Digest')} — {today}"
    output_dir = config.get("output_dir", "output")
    output_path = str(Path(output_dir) / f"podcast_{today_compact}.mp4")
    podcast_format = config.get("podcast_format", "deep_dive")

    print(f"\n🤖 NotebookLM Agent 시작\n")

    # 1. 노트북 생성
    notebook_id = create_notebook(title)
    if not notebook_id:
        print("❌ 노트북 ID를 얻지 못했습니다. NLM CLI 출력을 확인하세요.")
        return None

    # 2. Digest 전체를 하나의 소스로 추가
    source_title = f"Daily Digest {today}"
    if not add_source_text(notebook_id, digest_text, source_title):
        print("⚠️  소스 추가에 실패했지만 계속 진행합니다...")

    # 소스 인덱싱 대기
    print("  ⏳ 소스 인덱싱 대기 중 (30초)...")
    time.sleep(30)

    # 3. Audio Overview 생성
    artifact_id = create_audio_overview(notebook_id, podcast_format)
    if not artifact_id:
        print("❌ Audio Overview 생성에 실패했습니다.")
        return None

    # 4. 완료 대기 후 다운로드
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    success = wait_and_download(notebook_id, artifact_id, output_path)

    if success:
        print(f"\n🎉 팟캐스트 완성: {output_path}\n")
        return output_path
    else:
        return None


if __name__ == "__main__":
    config = load_config()
    # 테스트: 오늘 digest 파일 읽어서 실행
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    digest_path = Path(config.get("output_dir", "output")) / f"daily_digest_{today}.txt"

    if not digest_path.exists():
        print(f"❌ Digest 파일 없음: {digest_path}")
        print("   먼저 research_agent.py를 실행하세요.")
        sys.exit(1)

    digest_text = digest_path.read_text(encoding="utf-8")
    podcast_path = run(digest_text, str(digest_path), config)

    if podcast_path:
        print(f"✅ 팟캐스트: {podcast_path}")
    else:
        print("❌ 팟캐스트 생성 실패")
        sys.exit(1)
