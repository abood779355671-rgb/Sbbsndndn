import asyncio
import yt_dlp
from tenacity import retry, stop_after_attempt, wait_exponential
from config import config
from database.redis_cache import cache_get, cache_set

_QUALITY_FORMATS = {
    "high": "bestaudio/best",
    "medium": "bestaudio[abr<=128]/best",
    "low": "bestaudio[abr<=64]/worstaudio",
}


# #1: تُبنى عند الطلب لتعكس أي تغيير في الإعدادات
def _build_opts() -> dict:
    opts = {
        "format": _QUALITY_FORMATS.get(config.DEFAULT_QUALITY, "bestaudio/best"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch",
        "geo_bypass": True,
        "nocheckcertificate": True,
        "skip_download": True,
    }
    if config.COOKIES_FILE:
        opts["cookiefile"] = config.COOKIES_FILE
    return opts


def _duration(sec):
    # #16: المدة صفر/غير متوفرة تُعرض 0:00 بدل "غير معروف" إلا إن كانت None
    if sec is None:
        return "غير معروف"
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _search(query: str):
    with yt_dlp.YoutubeDL(_build_opts()) as ydl:
        info = ydl.extract_info(query, download=False)
        if "entries" in info:
            if not info["entries"]:
                return None
            info = info["entries"][0]
        return {
            "video_id": info["id"],
            "title": info.get("title", "غير معروف"),
            "duration": _duration(info.get("duration")),
            "thumb": info.get("thumbnail", ""),
            "url": info.get("webpage_url", ""),
        }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def _stream_url(video_id: str) -> str:
    url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL(_build_opts()) as ydl:
        info = ydl.extract_info(url, download=False)
        return info["url"]


async def search(query: str):
    cached = await cache_get(f"yt:{query}")
    if cached:
        return dict(cached)
    result = await asyncio.to_thread(_search, query)
    if result:
        await cache_set(f"yt:{query}", result, config.SEARCH_CACHE_TTL)
        return dict(result)
    return None


async def stream_url(video_id: str):
    return await asyncio.to_thread(_stream_url, video_id)
