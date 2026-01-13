"""
CKSEARCH - Username Search Module (Ultimate Edition)
======================================================
Multi-platform username search with 300+ sites support.
Includes: Global, Indonesia, Asia, Dating, Gaming, Professional, etc.
"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

import config
from core.scanner import BaseScanner

console = Console()

# =============================================================================
# PLATFORM DATABASE - 300+ Sites
# =============================================================================

# Format: {"name": "Site", "url": "URL with {}", "check_type": "status/content", "category": "Category"}

# -------------------------------------------
# SOCIAL MEDIA GLOBAL
# -------------------------------------------
SOCIAL_GLOBAL = [
    {"name": "Instagram", "url": "https://www.instagram.com/{}", "check_type": "status", "category": "Social"},
    {"name": "Facebook", "url": "https://www.facebook.com/{}", "check_type": "status", "category": "Social"},
    {"name": "Twitter/X", "url": "https://twitter.com/{}", "check_type": "status", "category": "Social"},
    {"name": "TikTok", "url": "https://www.tiktok.com/@{}", "check_type": "status", "category": "Social"},
    {"name": "Pinterest", "url": "https://www.pinterest.com/{}/", "check_type": "status", "category": "Social"},
    {"name": "Reddit", "url": "https://www.reddit.com/user/{}", "check_type": "status", "category": "Social"},
    {"name": "Tumblr", "url": "https://{}.tumblr.com", "check_type": "status", "category": "Social"},
    {"name": "VK", "url": "https://vk.com/{}", "check_type": "status", "category": "Social"},
    {"name": "OK.ru", "url": "https://ok.ru/{}", "check_type": "status", "category": "Social"},
    {"name": "Snapchat", "url": "https://www.snapchat.com/add/{}", "check_type": "status", "category": "Social"},
    {"name": "Threads", "url": "https://www.threads.net/@{}", "check_type": "status", "category": "Social"},
    {"name": "Mastodon.social", "url": "https://mastodon.social/@{}", "check_type": "status", "category": "Social"},
    {"name": "Bluesky", "url": "https://bsky.app/profile/{}.bsky.social", "check_type": "status", "category": "Social"},
    {"name": "Truth Social", "url": "https://truthsocial.com/@{}", "check_type": "status", "category": "Social"},
    {"name": "Gab", "url": "https://gab.com/{}", "check_type": "status", "category": "Social"},
    {"name": "Parler", "url": "https://parler.com/user/{}", "check_type": "status", "category": "Social"},
    {"name": "MeWe", "url": "https://mewe.com/i/{}", "check_type": "status", "category": "Social"},
    {"name": "Minds", "url": "https://www.minds.com/{}", "check_type": "status", "category": "Social"},
    {"name": "Gettr", "url": "https://gettr.com/user/{}", "check_type": "status", "category": "Social"},
    {"name": "Quora", "url": "https://www.quora.com/profile/{}", "check_type": "status", "category": "Social"},
    {"name": "Ask.fm", "url": "https://ask.fm/{}", "check_type": "status", "category": "Social"},
    {"name": "CuriousCat", "url": "https://curiouscat.live/{}", "check_type": "status", "category": "Social"},
    {"name": "Tellonym", "url": "https://tellonym.me/{}", "check_type": "status", "category": "Social"},
    {"name": "NGL", "url": "https://ngl.link/{}", "check_type": "status", "category": "Social"},
]

# -------------------------------------------
# INDONESIA & SOUTHEAST ASIA
# -------------------------------------------
INDONESIA_ASIA = [
    # Indonesia
    {"name": "Kaskus", "url": "https://www.kaskus.co.id/profile/{}", "check_type": "status", "category": "Indonesia"},
    {"name": "Kompasiana", "url": "https://www.kompasiana.com/{}", "check_type": "status", "category": "Indonesia"},
    {"name": "Brainly ID", "url": "https://brainly.co.id/profil/{}", "check_type": "status", "category": "Indonesia"},
    {"name": "IDN Times", "url": "https://www.idntimes.com/author/{}", "check_type": "status", "category": "Indonesia"},
    {"name": "Hipwee", "url": "https://www.hipwee.com/author/{}", "check_type": "status", "category": "Indonesia"},
    {"name": "Tokopedia", "url": "https://www.tokopedia.com/{}", "check_type": "status", "category": "Indonesia"},
    {"name": "Shopee ID", "url": "https://shopee.co.id/{}", "check_type": "status", "category": "Indonesia"},
    {"name": "Bukalapak", "url": "https://www.bukalapak.com/u/{}", "check_type": "status", "category": "Indonesia"},
    {"name": "Bibli", "url": "https://www.blibli.com/merchant/{}", "check_type": "status", "category": "Indonesia"},
    {"name": "OLX ID", "url": "https://www.olx.co.id/profile/{}", "check_type": "status", "category": "Indonesia"},
    {"name": "Detik Forum", "url": "https://forum.detik.com/member/{}", "check_type": "status", "category": "Indonesia"},
    {"name": "Liputan6", "url": "https://www.liputan6.com/author/{}", "check_type": "status", "category": "Indonesia"},
    {"name": "1Cak", "url": "https://1cak.com/users/{}", "check_type": "status", "category": "Indonesia"},
    {"name": "Kincir", "url": "https://www.kincir.com/user/{}", "check_type": "status", "category": "Indonesia"},
    
    # Malaysia
    {"name": "Lowyat.net", "url": "https://forum.lowyat.net/user/{}", "check_type": "status", "category": "Malaysia"},
    {"name": "Shopee MY", "url": "https://shopee.com.my/{}", "check_type": "status", "category": "Malaysia"},
    {"name": "Mudah.my", "url": "https://www.mudah.my/profile/{}", "check_type": "status", "category": "Malaysia"},
    {"name": "Cari Forum", "url": "https://forum.cari.com.my/home.php?mod=space&username={}", "check_type": "status", "category": "Malaysia"},
    
    # Singapore
    {"name": "HardwareZone SG", "url": "https://forums.hardwarezone.com.sg/members/{}", "check_type": "status", "category": "Singapore"},
    {"name": "Carousell SG", "url": "https://www.carousell.sg/{}", "check_type": "status", "category": "Singapore"},
    {"name": "Shopee SG", "url": "https://shopee.sg/{}", "check_type": "status", "category": "Singapore"},
    
    # Thailand
    {"name": "Pantip", "url": "https://pantip.com/profile/{}", "check_type": "status", "category": "Thailand"},
    {"name": "Sanook", "url": "https://www.sanook.com/profile/{}", "check_type": "status", "category": "Thailand"},
    {"name": "Shopee TH", "url": "https://shopee.co.th/{}", "check_type": "status", "category": "Thailand"},
    
    # Vietnam
    {"name": "Tinhte", "url": "https://tinhte.vn/members/{}", "check_type": "status", "category": "Vietnam"},
    {"name": "VoZ", "url": "https://voz.vn/u/{}", "check_type": "status", "category": "Vietnam"},
    {"name": "Shopee VN", "url": "https://shopee.vn/{}", "check_type": "status", "category": "Vietnam"},
    
    # Philippines
    {"name": "Shopee PH", "url": "https://shopee.ph/{}", "check_type": "status", "category": "Philippines"},
    {"name": "PinoyExchange", "url": "https://www.pinoyexchange.com/profile/{}", "check_type": "status", "category": "Philippines"},
]

# -------------------------------------------
# EAST ASIA (China, Japan, Korea)
# -------------------------------------------
EAST_ASIA = [
    # China
    {"name": "Weibo", "url": "https://weibo.com/n/{}", "check_type": "status", "category": "China"},
    {"name": "Douyin", "url": "https://www.douyin.com/user/{}", "check_type": "status", "category": "China"},
    {"name": "Bilibili", "url": "https://space.bilibili.com/{}", "check_type": "status", "category": "China"},
    {"name": "Xiaohongshu", "url": "https://www.xiaohongshu.com/user/profile/{}", "check_type": "status", "category": "China"},
    {"name": "Zhihu", "url": "https://www.zhihu.com/people/{}", "check_type": "status", "category": "China"},
    {"name": "Douban", "url": "https://www.douban.com/people/{}", "check_type": "status", "category": "China"},
    {"name": "Baidu Tieba", "url": "https://tieba.baidu.com/home/main?un={}", "check_type": "status", "category": "China"},
    {"name": "QQ", "url": "https://user.qzone.qq.com/{}", "check_type": "status", "category": "China"},
    
    # Japan
    {"name": "Pixiv", "url": "https://www.pixiv.net/users/{}", "check_type": "status", "category": "Japan"},
    {"name": "Niconico", "url": "https://www.nicovideo.jp/user/{}", "check_type": "status", "category": "Japan"},
    {"name": "Note.com", "url": "https://note.com/{}", "check_type": "status", "category": "Japan"},
    {"name": "Ameba", "url": "https://ameblo.jp/{}", "check_type": "status", "category": "Japan"},
    {"name": "Hatena", "url": "https://profile.hatena.ne.jp/{}", "check_type": "status", "category": "Japan"},
    {"name": "Mercari JP", "url": "https://jp.mercari.com/user/profile/{}", "check_type": "status", "category": "Japan"},
    
    # Korea
    {"name": "Naver Blog", "url": "https://blog.naver.com/{}", "check_type": "status", "category": "Korea"},
    {"name": "Naver Cafe", "url": "https://cafe.naver.com/{}", "check_type": "status", "category": "Korea"},
    {"name": "Daum", "url": "https://blog.daum.net/{}", "check_type": "status", "category": "Korea"},
    {"name": "DCInside", "url": "https://gallog.dcinside.com/{}", "check_type": "status", "category": "Korea"},
    {"name": "Tistory", "url": "https://{}.tistory.com", "check_type": "status", "category": "Korea"},
    {"name": "KakaoStory", "url": "https://story.kakao.com/{}", "check_type": "status", "category": "Korea"},
    
    # Taiwan
    {"name": "PTT", "url": "https://www.ptt.cc/bbs/user/{}", "check_type": "status", "category": "Taiwan"},
    {"name": "Dcard", "url": "https://www.dcard.tw/@{}", "check_type": "status", "category": "Taiwan"},
    {"name": "Shopee TW", "url": "https://shopee.tw/{}", "check_type": "status", "category": "Taiwan"},
]

# -------------------------------------------
# DATING & RELATIONSHIP APPS
# -------------------------------------------
DATING_SITES = [
    {"name": "Tinder", "url": "https://tinder.com/@{}", "check_type": "status", "category": "Dating"},
    {"name": "Badoo", "url": "https://badoo.com/profile/{}", "check_type": "status", "category": "Dating"},
    {"name": "OkCupid", "url": "https://www.okcupid.com/profile/{}", "check_type": "status", "category": "Dating"},
    {"name": "Bumble", "url": "https://bumble.com/en/profile/{}", "check_type": "status", "category": "Dating"},
    {"name": "Plenty of Fish", "url": "https://www.pof.com/viewprofile.aspx?profile_id={}", "check_type": "status", "category": "Dating"},
    {"name": "Hinge", "url": "https://hinge.co/{}", "check_type": "status", "category": "Dating"},
    {"name": "Coffee Meets Bagel", "url": "https://coffeemeetsbagel.com/user/{}", "check_type": "status", "category": "Dating"},
    {"name": "Match.com", "url": "https://www.match.com/profile/{}", "check_type": "status", "category": "Dating"},
    {"name": "eHarmony", "url": "https://www.eharmony.com/member/{}", "check_type": "status", "category": "Dating"},
    {"name": "Zoosk", "url": "https://www.zoosk.com/personals/{}", "check_type": "status", "category": "Dating"},
    {"name": "Tantan", "url": "https://tantanapp.com/u/{}", "check_type": "status", "category": "Dating"},
    {"name": "Grindr", "url": "https://grindr.com/{}", "check_type": "status", "category": "Dating"},
    {"name": "Her", "url": "https://weareher.com/@{}", "check_type": "status", "category": "Dating"},
    {"name": "Feeld", "url": "https://feeld.co/{}", "check_type": "status", "category": "Dating"},
    {"name": "Happn", "url": "https://www.happn.com/user/{}", "check_type": "status", "category": "Dating"},
    {"name": "Once", "url": "https://www.once.com/u/{}", "check_type": "status", "category": "Dating"},
]

# -------------------------------------------
# GAMING PLATFORMS
# -------------------------------------------
GAMING = [
    {"name": "Steam", "url": "https://steamcommunity.com/id/{}", "check_type": "status", "category": "Gaming"},
    {"name": "Twitch", "url": "https://www.twitch.tv/{}", "check_type": "status", "category": "Gaming"},
    {"name": "Xbox", "url": "https://account.xbox.com/en-us/profile?gamertag={}", "check_type": "status", "category": "Gaming"},
    {"name": "PlayStation", "url": "https://psnprofiles.com/{}", "check_type": "status", "category": "Gaming"},
    {"name": "Roblox", "url": "https://www.roblox.com/user.aspx?username={}", "check_type": "status", "category": "Gaming"},
    {"name": "Minecraft", "url": "https://namemc.com/profile/{}", "check_type": "status", "category": "Gaming"},
    {"name": "Epic Games", "url": "https://fortnitetracker.com/profile/all/{}", "check_type": "status", "category": "Gaming"},
    {"name": "Origin/EA", "url": "https://www.ea.com/ea-app/profile/{}", "check_type": "status", "category": "Gaming"},
    {"name": "Ubisoft", "url": "https://www.ubisoft.com/en-us/account/player/{}", "check_type": "status", "category": "Gaming"},
    {"name": "Battle.net", "url": "https://playoverwatch.com/en-us/career/pc/{}", "check_type": "status", "category": "Gaming"},
    {"name": "Riot Games", "url": "https://tracker.gg/valorant/profile/riot/{}", "check_type": "status", "category": "Gaming"},
    {"name": "League of Legends", "url": "https://www.op.gg/summoners/na/{}", "check_type": "status", "category": "Gaming"},
    {"name": "Dota 2", "url": "https://www.dotabuff.com/players/{}", "check_type": "status", "category": "Gaming"},
    {"name": "Chess.com", "url": "https://www.chess.com/member/{}", "check_type": "status", "category": "Gaming"},
    {"name": "Lichess", "url": "https://lichess.org/@/{}", "check_type": "status", "category": "Gaming"},
    {"name": "osu!", "url": "https://osu.ppy.sh/users/{}", "check_type": "status", "category": "Gaming"},
    {"name": "Roblox", "url": "https://www.roblox.com/user.aspx?username={}", "check_type": "status", "category": "Gaming"},
    {"name": "Kongregate", "url": "https://www.kongregate.com/accounts/{}", "check_type": "status", "category": "Gaming"},
    {"name": "Newgrounds", "url": "https://{}.newgrounds.com", "check_type": "status", "category": "Gaming"},
    {"name": "Itch.io", "url": "https://{}.itch.io", "check_type": "status", "category": "Gaming"},
    {"name": "Speedrun.com", "url": "https://www.speedrun.com/user/{}", "check_type": "status", "category": "Gaming"},
    {"name": "RetroAchievements", "url": "https://retroachievements.org/user/{}", "check_type": "status", "category": "Gaming"},
    {"name": "Tabletopia", "url": "https://tabletopia.com/users/{}", "check_type": "status", "category": "Gaming"},
    {"name": "Board Game Arena", "url": "https://boardgamearena.com/player?id={}", "check_type": "status", "category": "Gaming"},
]

# -------------------------------------------
# PROFESSIONAL & BUSINESS
# -------------------------------------------
PROFESSIONAL = [
    {"name": "LinkedIn", "url": "https://www.linkedin.com/in/{}", "check_type": "status", "category": "Professional"},
    {"name": "AngelList", "url": "https://angel.co/u/{}", "check_type": "status", "category": "Professional"},
    {"name": "Crunchbase", "url": "https://www.crunchbase.com/person/{}", "check_type": "status", "category": "Professional"},
    {"name": "Glassdoor", "url": "https://www.glassdoor.com/member/profile/{}", "check_type": "status", "category": "Professional"},
    {"name": "Indeed", "url": "https://my.indeed.com/p/{}", "check_type": "status", "category": "Professional"},
    {"name": "Xing", "url": "https://www.xing.com/profile/{}", "check_type": "status", "category": "Professional"},
    {"name": "About.me", "url": "https://about.me/{}", "check_type": "status", "category": "Professional"},
    {"name": "Linktree", "url": "https://linktr.ee/{}", "check_type": "status", "category": "Professional"},
    {"name": "Carrd", "url": "https://{}.carrd.co", "check_type": "status", "category": "Professional"},
    {"name": "Jobstreet", "url": "https://www.jobstreet.co.id/candidate/{}", "check_type": "status", "category": "Professional"},
    {"name": "Behance", "url": "https://www.behance.net/{}", "check_type": "status", "category": "Professional"},
    {"name": "Dribbble", "url": "https://dribbble.com/{}", "check_type": "status", "category": "Professional"},
    {"name": "99designs", "url": "https://99designs.com/profiles/{}", "check_type": "status", "category": "Professional"},
    {"name": "Fiverr", "url": "https://www.fiverr.com/{}", "check_type": "status", "category": "Professional"},
    {"name": "Upwork", "url": "https://www.upwork.com/freelancers/~{}", "check_type": "status", "category": "Professional"},
    {"name": "Freelancer", "url": "https://www.freelancer.com/u/{}", "check_type": "status", "category": "Professional"},
    {"name": "Toptal", "url": "https://www.toptal.com/resume/{}", "check_type": "status", "category": "Professional"},
    {"name": "PeoplePerHour", "url": "https://www.peopleperhour.com/freelancer/{}", "check_type": "status", "category": "Professional"},
]

# -------------------------------------------
# TECH & DEVELOPER
# -------------------------------------------
TECH_DEV = [
    {"name": "GitHub", "url": "https://github.com/{}", "check_type": "status", "category": "Tech"},
    {"name": "GitLab", "url": "https://gitlab.com/{}", "check_type": "status", "category": "Tech"},
    {"name": "Bitbucket", "url": "https://bitbucket.org/{}", "check_type": "status", "category": "Tech"},
    {"name": "SourceForge", "url": "https://sourceforge.net/u/{}", "check_type": "status", "category": "Tech"},
    {"name": "CodePen", "url": "https://codepen.io/{}", "check_type": "status", "category": "Tech"},
    {"name": "Replit", "url": "https://replit.com/@{}", "check_type": "status", "category": "Tech"},
    {"name": "StackOverflow", "url": "https://stackoverflow.com/users/{}", "check_type": "status", "category": "Tech"},
    {"name": "Dev.to", "url": "https://dev.to/{}", "check_type": "status", "category": "Tech"},
    {"name": "Hashnode", "url": "https://hashnode.com/@{}", "check_type": "status", "category": "Tech"},
    {"name": "HackerRank", "url": "https://www.hackerrank.com/{}", "check_type": "status", "category": "Tech"},
    {"name": "LeetCode", "url": "https://leetcode.com/{}", "check_type": "status", "category": "Tech"},
    {"name": "Codeforces", "url": "https://codeforces.com/profile/{}", "check_type": "status", "category": "Tech"},
    {"name": "TopCoder", "url": "https://www.topcoder.com/members/{}", "check_type": "status", "category": "Tech"},
    {"name": "Kaggle", "url": "https://www.kaggle.com/{}", "check_type": "status", "category": "Tech"},
    {"name": "HackerNews", "url": "https://news.ycombinator.com/user?id={}", "check_type": "status", "category": "Tech"},
    {"name": "ProductHunt", "url": "https://www.producthunt.com/@{}", "check_type": "status", "category": "Tech"},
    {"name": "Docker Hub", "url": "https://hub.docker.com/u/{}", "check_type": "status", "category": "Tech"},
    {"name": "NPM", "url": "https://www.npmjs.com/~{}", "check_type": "status", "category": "Tech"},
    {"name": "PyPI", "url": "https://pypi.org/user/{}", "check_type": "status", "category": "Tech"},
    {"name": "RubyGems", "url": "https://rubygems.org/profiles/{}", "check_type": "status", "category": "Tech"},
    {"name": "Packagist", "url": "https://packagist.org/packages/{}", "check_type": "status", "category": "Tech"},
    {"name": "Codesandbox", "url": "https://codesandbox.io/u/{}", "check_type": "status", "category": "Tech"},
    {"name": "Glitch", "url": "https://glitch.com/@{}", "check_type": "status", "category": "Tech"},
    {"name": "Observable", "url": "https://observablehq.com/@{}", "check_type": "status", "category": "Tech"},
    {"name": "Codewars", "url": "https://www.codewars.com/users/{}", "check_type": "status", "category": "Tech"},
    {"name": "Exercism", "url": "https://exercism.org/profiles/{}", "check_type": "status", "category": "Tech"},
    {"name": "Keybase", "url": "https://keybase.io/{}", "check_type": "status", "category": "Tech"},
    {"name": "Pastebin", "url": "https://pastebin.com/u/{}", "check_type": "status", "category": "Tech"},
    {"name": "Gist", "url": "https://gist.github.com/{}", "check_type": "status", "category": "Tech"},
    {"name": "Launchpad", "url": "https://launchpad.net/~{}", "check_type": "status", "category": "Tech"},
]

# -------------------------------------------
# VIDEO & STREAMING
# -------------------------------------------
VIDEO_STREAMING = [
    {"name": "YouTube", "url": "https://www.youtube.com/@{}", "check_type": "status", "category": "Video"},
    {"name": "Vimeo", "url": "https://vimeo.com/{}", "check_type": "status", "category": "Video"},
    {"name": "DailyMotion", "url": "https://www.dailymotion.com/{}", "check_type": "status", "category": "Video"},
    {"name": "Rumble", "url": "https://rumble.com/user/{}", "check_type": "status", "category": "Video"},
    {"name": "BitChute", "url": "https://www.bitchute.com/channel/{}", "check_type": "status", "category": "Video"},
    {"name": "Odysee", "url": "https://odysee.com/@{}", "check_type": "status", "category": "Video"},
    {"name": "PeerTube", "url": "https://peertube.fr/accounts/{}", "check_type": "status", "category": "Video"},
    {"name": "Dtube", "url": "https://d.tube/#!/c/{}", "check_type": "status", "category": "Video"},
    {"name": "Kick", "url": "https://kick.com/{}", "check_type": "status", "category": "Video"},
    {"name": "Trovo", "url": "https://trovo.live/{}", "check_type": "status", "category": "Video"},
]

# -------------------------------------------
# MUSIC & AUDIO
# -------------------------------------------
MUSIC_AUDIO = [
    {"name": "Spotify", "url": "https://open.spotify.com/user/{}", "check_type": "status", "category": "Music"},
    {"name": "SoundCloud", "url": "https://soundcloud.com/{}", "check_type": "status", "category": "Music"},
    {"name": "Bandcamp", "url": "https://bandcamp.com/{}", "check_type": "status", "category": "Music"},
    {"name": "Last.fm", "url": "https://www.last.fm/user/{}", "check_type": "status", "category": "Music"},
    {"name": "Mixcloud", "url": "https://www.mixcloud.com/{}/", "check_type": "status", "category": "Music"},
    {"name": "ReverbNation", "url": "https://www.reverbnation.com/{}", "check_type": "status", "category": "Music"},
    {"name": "Audiomack", "url": "https://audiomack.com/{}", "check_type": "status", "category": "Music"},
    {"name": "Genius", "url": "https://genius.com/artists/{}", "check_type": "status", "category": "Music"},
    {"name": "DistroKid", "url": "https://distrokid.com/hyperfollow/{}", "check_type": "status", "category": "Music"},
    {"name": "Deezer", "url": "https://www.deezer.com/profile/{}", "check_type": "status", "category": "Music"},
    {"name": "Apple Music", "url": "https://music.apple.com/profile/{}", "check_type": "status", "category": "Music"},
    {"name": "Tidal", "url": "https://tidal.com/browse/artist/{}", "check_type": "status", "category": "Music"},
    {"name": "Anchor", "url": "https://anchor.fm/{}", "check_type": "status", "category": "Podcast"},
    {"name": "Podbean", "url": "https://{}.podbean.com", "check_type": "status", "category": "Podcast"},
]

# -------------------------------------------
# PHOTO & ART
# -------------------------------------------
PHOTO_ART = [
    {"name": "Flickr", "url": "https://www.flickr.com/people/{}", "check_type": "status", "category": "Photo"},
    {"name": "500px", "url": "https://500px.com/{}", "check_type": "status", "category": "Photo"},
    {"name": "Unsplash", "url": "https://unsplash.com/@{}", "check_type": "status", "category": "Photo"},
    {"name": "Pexels", "url": "https://www.pexels.com/@{}", "check_type": "status", "category": "Photo"},
    {"name": "SmugMug", "url": "https://{}.smugmug.com", "check_type": "status", "category": "Photo"},
    {"name": "DeviantArt", "url": "https://www.deviantart.com/{}", "check_type": "status", "category": "Art"},
    {"name": "ArtStation", "url": "https://www.artstation.com/{}", "check_type": "status", "category": "Art"},
    {"name": "Pixiv", "url": "https://www.pixiv.net/users/{}", "check_type": "status", "category": "Art"},
    {"name": "Newgrounds", "url": "https://{}.newgrounds.com", "check_type": "status", "category": "Art"},
    {"name": "Imgur", "url": "https://imgur.com/user/{}", "check_type": "status", "category": "Photo"},
    {"name": "VSCO", "url": "https://vsco.co/{}", "check_type": "status", "category": "Photo"},
    {"name": "EyeEm", "url": "https://www.eyeem.com/u/{}", "check_type": "status", "category": "Photo"},
    {"name": "PhotoBucket", "url": "https://photobucket.com/user/{}", "check_type": "status", "category": "Photo"},
    {"name": "Giphy", "url": "https://giphy.com/channel/{}", "check_type": "status", "category": "Photo"},
    {"name": "Tenor", "url": "https://tenor.com/users/{}", "check_type": "status", "category": "Photo"},
]

# -------------------------------------------
# BLOG & WRITING
# -------------------------------------------
BLOG_WRITING = [
    {"name": "Medium", "url": "https://medium.com/@{}", "check_type": "status", "category": "Blog"},
    {"name": "Substack", "url": "https://{}.substack.com", "check_type": "status", "category": "Blog"},
    {"name": "WordPress", "url": "https://{}.wordpress.com", "check_type": "status", "category": "Blog"},
    {"name": "Blogger", "url": "https://{}.blogspot.com", "check_type": "status", "category": "Blog"},
    {"name": "Ghost", "url": "https://{}.ghost.io", "check_type": "status", "category": "Blog"},
    {"name": "Wattpad", "url": "https://www.wattpad.com/user/{}", "check_type": "status", "category": "Writing"},
    {"name": "AO3", "url": "https://archiveofourown.org/users/{}", "check_type": "status", "category": "Writing"},
    {"name": "FanFiction.net", "url": "https://www.fanfiction.net/u/{}", "check_type": "status", "category": "Writing"},
    {"name": "Royal Road", "url": "https://www.royalroad.com/profile/{}", "check_type": "status", "category": "Writing"},
    {"name": "Webnovel", "url": "https://www.webnovel.com/profile/{}", "check_type": "status", "category": "Writing"},
    {"name": "Goodreads", "url": "https://www.goodreads.com/{}", "check_type": "status", "category": "Book"},
    {"name": "Scribd", "url": "https://www.scribd.com/{}", "check_type": "status", "category": "Book"},
    {"name": "SlideShare", "url": "https://www.slideshare.net/{}", "check_type": "status", "category": "Work"},
    {"name": "Issuu", "url": "https://issuu.com/{}", "check_type": "status", "category": "Work"},
    {"name": "Telegraph", "url": "https://telegra.ph/{}", "check_type": "status", "category": "Blog"},
]

# -------------------------------------------
# SHOPPING & E-COMMERCE
# -------------------------------------------
SHOPPING = [
    {"name": "eBay", "url": "https://www.ebay.com/usr/{}", "check_type": "status", "category": "Shopping"},
    {"name": "Etsy", "url": "https://www.etsy.com/shop/{}", "check_type": "status", "category": "Shopping"},
    {"name": "Poshmark", "url": "https://poshmark.com/closet/{}", "check_type": "status", "category": "Shopping"},
    {"name": "Mercari", "url": "https://www.mercari.com/u/{}", "check_type": "status", "category": "Shopping"},
    {"name": "Depop", "url": "https://www.depop.com/{}", "check_type": "status", "category": "Shopping"},
    {"name": "Vinted", "url": "https://www.vinted.com/member/{}", "check_type": "status", "category": "Shopping"},
    {"name": "Gumroad", "url": "https://gumroad.com/{}", "check_type": "status", "category": "Shopping"},
    {"name": "Redbubble", "url": "https://www.redbubble.com/people/{}", "check_type": "status", "category": "Shopping"},
    {"name": "Society6", "url": "https://society6.com/{}", "check_type": "status", "category": "Shopping"},
    {"name": "Teepublic", "url": "https://www.teepublic.com/user/{}", "check_type": "status", "category": "Shopping"},
    {"name": "Zazzle", "url": "https://www.zazzle.com/mbr/{}", "check_type": "status", "category": "Shopping"},
    {"name": "TeeSpring", "url": "https://teespring.com/stores/{}", "check_type": "status", "category": "Shopping"},
]

# -------------------------------------------
# FINANCE & CRYPTO
# -------------------------------------------
FINANCE_CRYPTO = [
    {"name": "PayPal.me", "url": "https://paypal.me/{}", "check_type": "status", "category": "Finance"},
    {"name": "CashApp", "url": "https://cash.app/${}", "check_type": "status", "category": "Finance"},
    {"name": "Venmo", "url": "https://venmo.com/{}", "check_type": "status", "category": "Finance"},
    {"name": "Ko-fi", "url": "https://ko-fi.com/{}", "check_type": "status", "category": "Finance"},
    {"name": "BuyMeACoffee", "url": "https://www.buymeacoffee.com/{}", "check_type": "status", "category": "Finance"},
    {"name": "Patreon", "url": "https://www.patreon.com/{}", "check_type": "status", "category": "Finance"},
    {"name": "OpenSea", "url": "https://opensea.io/{}", "check_type": "status", "category": "Crypto"},
    {"name": "Rarible", "url": "https://rarible.com/{}", "check_type": "status", "category": "Crypto"},
    {"name": "Foundation", "url": "https://foundation.app/@{}", "check_type": "status", "category": "Crypto"},
    {"name": "Gitcoin", "url": "https://gitcoin.co/{}", "check_type": "status", "category": "Crypto"},
]

# -------------------------------------------
# COMMUNICATION & MESSAGING
# -------------------------------------------
COMMUNICATION = [
    {"name": "Telegram", "url": "https://t.me/{}", "check_type": "status", "category": "Chat"},
    {"name": "Discord", "url": "https://discord.com/users/{}", "check_type": "status", "category": "Chat"},
    {"name": "Slack", "url": "https://{}.slack.com", "check_type": "status", "category": "Chat"},
    {"name": "Skype", "url": "https://join.skype.com/invite/{}", "check_type": "status", "category": "Chat"},
    {"name": "Line", "url": "https://line.me/ti/p/{}", "check_type": "status", "category": "Chat"},
    {"name": "KakaoTalk", "url": "https://open.kakao.com/o/{}", "check_type": "status", "category": "Chat"},
    {"name": "WeChat", "url": "https://wx.qq.com/{}", "check_type": "status", "category": "Chat"},
    {"name": "Viber", "url": "https://viber.com/{}", "check_type": "status", "category": "Chat"},
]

# -------------------------------------------
# ADULT (Optional - separated for control)
# -------------------------------------------
ADULT_SITES = [
    {"name": "OnlyFans", "url": "https://onlyfans.com/{}", "check_type": "status", "category": "Adult"},
    {"name": "Fansly", "url": "https://fansly.com/{}", "check_type": "status", "category": "Adult"},
    {"name": "Pornhub", "url": "https://www.pornhub.com/users/{}", "check_type": "status", "category": "Adult"},
    {"name": "XVideos", "url": "https://www.xvideos.com/profiles/{}", "check_type": "status", "category": "Adult"},
    {"name": "XHamster", "url": "https://xhamster.com/users/{}", "check_type": "status", "category": "Adult"},
    {"name": "Chaturbate", "url": "https://chaturbate.com/{}/", "check_type": "status", "category": "Adult"},
    {"name": "MyFreeCams", "url": "https://profiles.myfreecams.com/{}", "check_type": "status", "category": "Adult"},
    {"name": "CamSoda", "url": "https://www.camsoda.com/{}", "check_type": "status", "category": "Adult"},
    {"name": "BongaCams", "url": "https://bongacams.com/{}", "check_type": "status", "category": "Adult"},
    {"name": "FetLife", "url": "https://fetlife.com/users/{}", "check_type": "status", "category": "Adult"},
]

# -------------------------------------------
# OTHER / MISC
# -------------------------------------------
MISC_SITES = [
    {"name": "Gravatar", "url": "https://en.gravatar.com/{}", "check_type": "status", "category": "Other"},
    {"name": "Wikipedia", "url": "https://en.wikipedia.org/wiki/User:{}", "check_type": "status", "category": "Other"},
    {"name": "Archive.org", "url": "https://archive.org/search.php?query=creator:{}", "check_type": "status", "category": "Other"},
    {"name": "Disqus", "url": "https://disqus.com/by/{}", "check_type": "status", "category": "Other"},
    {"name": "TripAdvisor", "url": "https://www.tripadvisor.com/members/{}", "check_type": "status", "category": "Travel"},
    {"name": "Yelp", "url": "https://www.yelp.com/user_details?userid={}", "check_type": "status", "category": "Travel"},
    {"name": "Foursquare", "url": "https://foursquare.com/user/{}", "check_type": "status", "category": "Travel"},
    {"name": "Untappd", "url": "https://untappd.com/user/{}", "check_type": "status", "category": "Food"},
    {"name": "Vivino", "url": "https://www.vivino.com/users/{}", "check_type": "status", "category": "Food"},
    {"name": "AllRecipes", "url": "https://www.allrecipes.com/cook/{}", "check_type": "status", "category": "Food"},
    {"name": "MyFitnessPal", "url": "https://www.myfitnesspal.com/profile/{}", "check_type": "status", "category": "Health"},
    {"name": "Strava", "url": "https://www.strava.com/athletes/{}", "check_type": "status", "category": "Health"},
    {"name": "Fitbit", "url": "https://www.fitbit.com/user/{}", "check_type": "status", "category": "Health"},
]

# =============================================================================
# BUILD SITE LISTS
# =============================================================================

# QUICK SCAN: Essential platforms only (~75 sites)
QUICK_SITES = (
    SOCIAL_GLOBAL[:15] +
    TECH_DEV[:10] +
    GAMING[:10] +
    VIDEO_STREAMING[:5] +
    MUSIC_AUDIO[:5] +
    PHOTO_ART[:10] +
    BLOG_WRITING[:10] +
    PROFESSIONAL[:10]
)

# DEEP SCAN: All platforms (~300 sites)
DEEP_SITES = (
    SOCIAL_GLOBAL +
    INDONESIA_ASIA +
    EAST_ASIA +
    DATING_SITES +
    GAMING +
    PROFESSIONAL +
    TECH_DEV +
    VIDEO_STREAMING +
    MUSIC_AUDIO +
    PHOTO_ART +
    BLOG_WRITING +
    SHOPPING +
    FINANCE_CRYPTO +
    COMMUNICATION +
    ADULT_SITES +
    MISC_SITES
)


# =============================================================================
# SCANNER CLASS
# =============================================================================

class UsernameSearch(BaseScanner):
    """Ultimate Multi-platform username searcher with 300+ sites."""
    
    def __init__(self, language: str = "id"):
        super().__init__("Username Search", language)
    
    def scan(self, username: str, **options) -> Dict[str, Any]:
        """
        Scan for username across platforms.
        
        Args:
           username: Username target
           scan_mode: 'quick' (75 sites) or 'deep' (300+ sites)
           include_adult: Include adult sites in deep scan (default: True)
        """
        self._start()
        
        scan_mode = options.get("scan_mode", "quick")
        include_adult = options.get("include_adult", True)
        
        if not username:
            return {"error": "Username empty"}
        
        # Select sites based on scan mode
        if scan_mode == "deep":
            sites_to_check = DEEP_SITES.copy()
            if not include_adult:
                sites_to_check = [s for s in sites_to_check if s.get("category") != "Adult"]
        else:
            sites_to_check = QUICK_SITES.copy()
        
        console.print(f"[cyan]→ Scanning {len(sites_to_check)} sites ({scan_mode.upper()} Mode)...[/cyan]")
        if scan_mode == "deep":
            console.print("[dim]  This may take 2-5 minutes...[/dim]")
        
        results = {
            "target": username,
            "scan_mode": scan_mode,
            "total_sites": len(sites_to_check),
            "found": [],
            "categories": {},
        }
        
        # Async Scan
        found_data = asyncio.run(self._scan_sites(username, sites_to_check))
        results["found"] = found_data
        results["count"] = len(found_data)
        
        # Categorize results
        for item in found_data:
            cat = item.get("category", "Other")
            if cat not in results["categories"]:
                results["categories"][cat] = []
            results["categories"][cat].append(item)
        
        self._finish()
        results["metadata"] = self.get_metadata()
        
        return results
    
    async def _scan_sites(self, username: str, site_list: List[Dict]) -> List[Dict]:
        found_results = []
        
        timeout = aiohttp.ClientTimeout(total=10)
        connector = aiohttp.TCPConnector(limit=100, ssl=False)  # High concurrency
        
        headers = {
            "User-Agent": config.DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers=headers) as session:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                BarColumn(bar_width=40),
                TaskProgressColumn(),
                TextColumn("[green]Found: {task.fields[found_count]}[/green]"),
                console=console
            ) as progress:
                
                found_count = 0
                task = progress.add_task("Scanning...", total=len(site_list), found_count=0)
                
                # Create all tasks
                tasks = [self._check_site(session, site, username) for site in site_list]
                
                # Execute with progress updates
                for future in asyncio.as_completed(tasks):
                    result = await future
                    if result:
                        found_results.append(result)
                        found_count += 1
                    progress.update(task, advance=1, found_count=found_count)
        
        return found_results

    async def _check_site(self, session: aiohttp.ClientSession, site: Dict, username: str) -> Optional[Dict]:
        url = site["url"].format(username)
        
        try:
            async with session.get(url, allow_redirects=True) as resp:
                # Status code check
                if resp.status == 200:
                    # Optional content check for sites with custom 404
                    check_type = site.get("check_type", "status")
                    
                    if check_type == "content":
                        text = await resp.text()
                        error_msg = site.get("error_msg", "not found")
                        if error_msg.lower() in text.lower():
                            return None
                    
                    return {
                        "site": site["name"],
                        "url": url,
                        "category": site.get("category", "Other"),
                    }
        except:
            pass
        return None


def scan_username(username: str, scan_mode: str = "quick") -> Dict[str, Any]:
    return UsernameSearch().scan(username, scan_mode=scan_mode)
