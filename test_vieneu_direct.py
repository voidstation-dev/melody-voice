import asyncio
from app.providers.vieneu_provider import VieneuProvider

async def main():
    provider = VieneuProvider()
    print("Voices:", await provider.list_voices())
    
    res = await provider.synthesize(
        text="Xin chào, hệ thống Vieneu hoạt động rất tốt.",
        voice_type="v3_tu_nhien_nam", # We'll see if it crashes or defaults to default_voice
        resource_id=None,
        rate=1.0,
    )
    print("Result:", res)

if __name__ == "__main__":
    asyncio.run(main())
