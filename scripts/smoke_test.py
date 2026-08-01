import argparse
import sys
from pathlib import Path

# Add apps/api to path
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "api"))

from app.config import settings
from app.providers.capcut_provider import CapCutProvider

def main():
    parser = argparse.ArgumentParser(description="CapVoice Studio Live Provider Smoke Test")
    parser.add_argument("--voice", default="BV421_vivn_streaming", help="Voice type identifier")
    parser.add_argument("--text", default="Xin chào, đây là bài kiểm tra giọng đọc.", help="Text content to synthesize")
    args = parser.parse_args()

    print(f"[+] Initializing provider with catalog: {settings.capcut_catalog_path}")
    provider = CapCutProvider(catalog_path=settings.capcut_catalog_path)
    
    voices = provider.list_voices()
    print(f"[+] Loaded catalog voices: {len(voices)}")
    
    target_voice = next((v for v in voices if v.voice_type == args.voice), None)
    if not target_voice:
        print(f"[!] Error: Voice '{args.voice}' not found in catalog.")
        sys.exit(1)
        
    print(f"[+] Found voice: {target_voice.display_name} ({target_voice.voice_type})")
    print(f"[+] Requesting synthesis for: '{args.text}'...")

    try:
        res = provider.synthesize(
            text=args.text,
            voice_type=target_voice.voice_type,
            resource_id=target_voice.resource_id,
            rate=1.0,
        )
        print(f"[+] Raw Response Keys: {list(res.raw_response.keys())}")
        print(f"[+] Extracted Audio URLs: {res.audio_urls}")
        if res.audio_urls:
            print(f"[✓] SMOKE TEST SUCCESS: Extracted playable audio URL: {res.audio_urls[0]}")
        else:
            print("[!] Warning: No audio URLs extracted from response.")
    except Exception as e:
        print(f"[!] Provider synthesis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
