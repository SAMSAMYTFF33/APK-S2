#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 Comprehensive Combined Bo.t (MRG Claimer v8 + ATF Bot)
تمت ترقية الكود بنظام (Connect ➔ Fetch ➔ Disconnect) لمنع أخطاء 409 وتعارض الجلسات بالكامل.
"""

import time
import asyncio
import json
import re
import ssl
import sys
import random
import subprocess
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone
import aiohttp

from telethon import TelegramClient, functions, types
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest

# ==============================================================================
# 🔒 قفل المزامنة العالمي لمنع التداخل بين الطلبات
# ==============================================================================
system_task_lock = asyncio.Lock()

# ==============================================================================
# ⚙️ مفاتيح التحكم بحسابات ATF (1 = يعمل | 0 = متوقف)
# =============================================================================
ATF_ACCOUNT_1   = 1    
ATF_ACCOUNT_2   = 0    
ATF_ACCOUNT_3   = 0    
ATF_ACCOUNT_4   = 0    
ATF_ACCOUNT_5   = 0    

# ==============================================================================
# 🟩 إعدادات حسابات ATF
# ==============================================================================
ACCOUNTS_CONFIG_ATF = [
    {
        "atf_enabled": ATF_ACCOUNT_1 == 1,
        "account_name": "الحساب الأول (gz)",
        "do_boost": True,
        "api_id": 38197378,
        "api_hash": "1efeb1db162150616801ae759799ca97",
        "session_string": "1BJWap1wBu3SWNB8JFOdcM2T6cVu0o4dv7iybgtIqrRmUZYzkmWRkmBjFbGaovA7tyqfsozceWzvd9SuhsKsW1a9cle_PXkM_THwP_65_PYfO9w3aHVUvN_sIcfbnyQHz4AaVJhCyNEbwaRaZjShJvpZscoU_JLc0xD0rvE5wGQjEHZJkmL4OLsqoxZn0DgKqRtjLFX6KeQZinHJQeaFQQTqMdelSWmtE3diSNAV3JETvf7X2Llfb4dhVYbOAcMxm3ZRhRtv5uE9RjmMkS2OHOA8Dmr1OYn_E1r-xup8d2FifOMmI8QHcAS0ucEUwtgf5fS9AxtrLOS-JimS6tTNiiPcc7jZzRUU=",
        "device_prefix": "dev-B",
        "user_agent": "Mozilla/5.0 (Linux; Android 14; SM-A155F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.122 Mobile Safari/537.36",
        "extra_headers": {
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "accept-language": "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7"
        }
    },
    {
        "atf_enabled": ATF_ACCOUNT_2 == 1,
        "account_name": "الحساب الثاني",
        "do_boost": True,
        "api_id": 38197378,
        "api_hash": "1efeb1db162150616801ae759799ca97",
        "session_string": "1BJWap1sBu2AYJJY6BirfGnzglAB8ppxWTbWSqjEvsAjT01QZCU-_LkiLVzmOJcpiD4NsR2UeXCb6Ujl9wuvUl7diZMgaNoV3L-RnfwKIkJFUzQ2F6txstq0gxgyjfPwQnoYhFLJGWV-8RI4bCDikGqmAzSYtwaJ7YYBP0UWPBEAAUT6cby6QAZfYAO6IXTLktrR7E48X9j5dXApa1wh8T_WPZKP5IRE8njO53kiN9_NfrBqLEz_7vogPGcDxDo9XU3S4wQ-DZTB4iEmXzzZ3dxcYrWUqpmtGLho0Uc_uS3amDa7hlg3tzo6ngvXiygMVkf8xjkxI6lAcC63gt527D43ePyRvLxY=",
        "device_prefix": "dev-D",
        "user_agent": "Mozilla/5.0 (Linux; Android 14; 23124RA7EO) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36",
        "extra_headers": {
            "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not=A?Brand";v="24"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "accept-language": "ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7"
        }
    },
    {
        "atf_enabled": ATF_ACCOUNT_3 == 1,
        "account_name": "الحساب الثالث (SKATE)",
        "do_boost": True,
        "api_id": 38197378,
        "api_hash": "1efeb1db162150616801ae759799ca97",
        "session_string": "1BJWap1sBu3uWEMwOhx78ucgVfqr0pS4dqY-ZoadziQ2tr6oMiXKg7fJJZ1HFL2VJBIe8Krw0LJZCbFO9dczyhhdwZ1OL0sX8zwTwuSxoxWzM12cF9okgymz3b7RPMBqthYhMxZQ-ivjAiqSW3yEyUG6-roO6OpdG2ydmiFXqd8-vJxKBYpVXu1VQtqRrNEaZl9wRSWJ0U-hBypmPsvjXzo1JPfX0sqkTPB-E86AHZOqCBHzq9xFkoTyPiS60cFFpOHN8kP7Q33qnmU49Khq9YTVo-kKgxlXXys8mL_H5H-Hke_wO4skgG8j5qDmrpRKZo5guTczEOOAsxXNL7XOo8X7a_eyNAgM=",
        "device_prefix": "dev-Oppo",
        "user_agent": "Mozilla/5.0 (Linux; Android 13; CPH2565) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.119 Mobile Safari/537.36",
        "extra_headers": {
            "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "accept-language": "ar-MA,ar;q=0.9,en-US;q=0.8,en;q=0.7"
        }
    },
    {
        "atf_enabled": ATF_ACCOUNT_4 == 1,
        "account_name": "الحساب الرابع",
        "do_boost": True,
        "api_id": 38197378,
        "api_hash": "1efeb1db162150616801ae759799ca97",
        "session_string": "1BJWap1sBu3E3ixVfR8ae3yJnPtwfAjXfmbV9o_ud-zFiEbSr1ir2RUOjO2qf0jaP6P5Dpzh7sz607dhyDJX26eEo3dm-YZW0DzXKGkiOI6E7VHnMplSf1S15aKcekSHXoZ6U614I_Irx0AeoSkU12iPqy6PY5slRUUrz3D1k5MIROVwrm0Sn61yWRPJPQ-T8PAMyRjxsZHM5fuGFTz2sZRjSIpTKaleHybBFwuWRbCg3ADiYaPYsxEozXuyGmIT_dggv6gDQ6agIVkrDHUHDdzyOctKWs7UyAgSOxtrSunbtks2yEX_hvRjh5EIA9gejGO9G3sg72sbBDBCYSXXwyo2f8A4vEj8=",
        "device_prefix": "dev-E",
        "user_agent": "Mozilla/5.0 (Linux; Android 13; 2310FPCA4G) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.118 Mobile Safari/537.36",
        "extra_headers": {
            "sec-ch-ua": '"Not:A-Brand";v="8", "Chromium";v="123", "Google Chrome";v="123"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "accept-language": "ar-DZ,ar;q=0.9,en-US;q=0.8,en;q=0.7"
        }
    },
    {
        "atf_enabled": ATF_ACCOUNT_5 == 1,
        "account_name": "الحساب الخامس (ZAMASO)",
        "do_boost": True,
        "api_id": 31514497,
        "api_hash": "98d779341dd063307994de23cfd9796d",
        "session_string": "1BJWap1wBu4nVoNbxlJjeimChDuFtJFf-DIOl0cQE-sdurr6DuG3MLi23QOlaAmdHcU4k6lvqYt0Cn9Edehg8jApjS7Hhus2LNpBPotjpyNNWSWISgWMmBA-_GV0aPcXCcL8NTNjwAvaQCPptkQ02560D2UM5iunpN7kEIkwWNa-mMRFfMmwldrK81tc7CQf2QqkGLBijcNJsw-1-7h-UZ1A1Y75gk3BaLXrM-upajdg89y9Ka-vVsiUw4CZL8gMWU2CcxkPSjoxWBA-7bzG-HPnWduIyY6G__IDUsVua9ZTCFYywMkNccpNfwdXLAPEAjtFQ-bawSyWEM9uzM2pVlfE1Nxg2Nww=",
        "device_prefix": "dev-F",
        "user_agent": "Mozilla/5.0 (Linux; Android 13; RMX3710) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.122 Mobile Safari/537.36",
        "extra_headers": {
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "accept-language": "ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7"
        }
    }
]

# ==============================================================================
# 🟥 إعدادات وثوابت MRG Claimer v8
# ==============================================================================
API_ID_MRG, API_HASH_MRG = 38197378, "1efeb1db162150616801ae759799ca97"
SESSION_MRG = "1BJWap1sBu2EWCgdPwWR7Wv_6tcilC6U5ISSgbQGDPQKSz7YcWmZ9xOgswV5fgW5HI_I1ADtBWtdlRcSrIwprzgv7Ru7TjF7O_tRJo7Zk0CoSs6ZnEbRsbwnQ3-w1OzvechQt5LI-_i0eYgKJZqn_vw_iOxpE7qA92MRklYrM1M1EWKQESkCHMqgdPMZq7ZkAaw4Q6_o4qOHo9dasf4kDSUsqvHYAZjEMiiPOGZZYofdiVgiJF787cSABfraMbAvxZKaN6W-Ves_s8IXzIsjayYEfAQUP-wKpJzyIaAVWvVLusLltXjfG1ZLMW_iZ3nHz6nuMEPf7g3JRst5E3SlsJejFshYy2wA="
BOT_MRG, BASE_MRG = "@mrgminerbot", "https://mrg.up.railway.app"
SSL_CTX = ssl.create_default_context(); SSL_CTX.check_hostname = False; SSL_CTX.verify_mode = ssl.CERT_NONE

G, R, Y, C, D, X = "\033[92m", "\033[91m", "\033[93m", "\033[96m", "\033[2m", "\033[0m"
MEM_MRG = {}

# ==============================================================================
# 🟨 إعدادات وثوابت ATF Bot
# ==============================================================================
TARGET_BOT_USERNAME_ATF = "ATF_AIRDROP_bot"
WEB_APP_URL_ATF = "https://atfminers.asloni.online/miner/index.html"
BASE_URL_ATF = "https://atfminers.asloni.online"

LOGIN_ENDPOINT_ATF = f"{BASE_URL_ATF}/miner/index.php?action=login"
START_MINE_ENDPOINT_ATF = f"{BASE_URL_ATF}/miner/index.php?action=start_mine"
ACTIVATE_BOOST_ENDPOINT_ATF = f"{BASE_URL_ATF}/miner/index.php?action=activate_boost"
START_TASK_ENDPOINT_ATF = f"{BASE_URL_ATF}/miner/index.php?action=start_task"
CLAIM_TASK_ENDPOINT_ATF = f"{BASE_URL_ATF}/miner/index.php?action=claim_task"

TASKS_ATF = [
    {"id": "website_visit", "wait": 3, "name": "Website"},
    {"id": "youtube_like_comment", "wait": 33, "name": "YouTube"},
    {"id": "twitter_retweet", "wait": 33, "name": "Twitter"},
    {"id": "telegram_react_latest", "wait": 23, "name": "React"}
]

# ==============================================================================
# 🛠️ أدوات MRG الأساسية
# ==============================================================================
def hms(s):
    s = int(max(0, s)); h, r = divmod(s, 3600); m, x = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{x:02d}"

def now(): return datetime.now(timezone.utc)

def iso(s):
    if not s: return None
    try:
        if s.endswith("Z"): s = s[:-1] + "+00:00"
        d = datetime.fromisoformat(s)
        return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d
    except: return None

def http_mrg(ep, payload):
    for _ in range(2):
        try:
            req = urllib.request.Request(BASE_MRG+ep, data=json.dumps(payload).encode(),
                headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0",
                         "Origin":"https://app.mrgtoken.xyz"}, method="POST")
            with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())
        except: time.sleep(2)
    return None, {}

async def api_mrg(ep, p): return await asyncio.to_thread(http_mrg, ep, p)

async def wv_mrg(cli, bot, url=None, sn=None, sp=None):
    try:
        if sn: return (await cli(functions.messages.RequestAppWebViewRequest(
            peer=bot, app=types.InputBotAppShortName(bot, sn), platform="android", start_param=sp))).url
        return (await cli(functions.messages.RequestWebViewRequest(
            peer=bot, bot=bot, platform="android", url=url, start_param=sp))).url
    except: return None

async def get_init_mrg(cli, bot):
    full = None
    async for m in cli.iter_messages(BOT_MRG, limit=5):
        if not (m.reply_markup and hasattr(m.reply_markup, "rows")): continue
        for row in m.reply_markup.rows:
            for b in row.buttons:
                if isinstance(b, (types.KeyboardButtonWebView, types.KeyboardButtonSimpleWebView)):
                    full = await wv_mrg(cli, bot, url=b.url); break
                if isinstance(b, types.KeyboardButtonUrl) and not any(x in b.url for x in ["x.com","twitter.com"]):
                    mm = re.search(r't\.me/[^/]+/([^/?#]+)', b.url)
                    if mm and mm.group(1) not in ["start","join"]:
                        full = await wv_mrg(cli, bot, sn=mm.group(1)); break
            if full: break
        if full: break
    if not full:
        for sn in ["app","start","game"]:
            full = await wv_mrg(cli, bot, sn=sn)
            if full: break
    if not full: return None
    raw = full.split("#tgWebAppData=")[-1].split("&tgWebAppVersion")[0] if "#tgWebAppData=" in full \
          else full.split("tgWebAppData=")[-1].split("&tgWebAppVersion")[0]
    return urllib.parse.unquote(raw)

async def get_mrg_data_and_disconnect():
    """الاتصال مؤقتاً لجلب بيانات MRG ثم قطع الاتصال فوراً لتجنب الأخطاء."""
    cli = TelegramClient(StringSession(SESSION_MRG), API_ID_MRG, API_HASH_MRG)
    try:
        await cli.connect()
        if not await cli.is_user_authorized():
            return None, None
        me = await cli.get_me()
        bot = await cli.get_input_entity(BOT_MRG)
        try: 
            await cli.send_message(BOT_MRG, "/start")
            await asyncio.sleep(2)
        except: pass
        init_data = await get_init_mrg(cli, bot)
        return me, init_data
    except Exception as e:
        print(f"{R}❌ [MRG Telegram Error]: {e}{X}")
        return None, None
    finally:
        if cli.is_connected():
            await cli.disconnect()

def cd_sec_mrg(tt):
    tt = (tt or "").lower()
    return 3600 if tt == "recurring_1h" else 10800 if tt.startswith("recurring") else None

def remaining_mrg(task, txs):
    cd = cd_sec_mrg(task.get("taskType"))
    if not cd: return None, "—"
    tid = task.get("taskId")

    if tid in MEM_MRG:
        return max(0.0, cd - (now() - MEM_MRG[tid]).total_seconds()), "جلسة"

    rw = float(task.get("reward", 0))
    best = None
    for tx in txs:
        if tx.get("type") != "Task Reward": continue
        try: amt = float(tx.get("amount", 0))
        except: continue
        if abs(amt - rw) < 0.01:
            d = iso(tx.get("createdAt"))
            if d and (best is None or d > best): best = d
    if best:
        return max(0.0, cd - (now() - best).total_seconds()), "دقيق"
    return None, "?"

def show_mrg(tasks, done, txs):
    print(f"\n{C}{'═'*95}{X}\n{C}📋 مهام MRG{X}\n{C}{'═'*95}{X}")
    print(f"{'#':<3}{'ID':<28}{'العنوان':<36}{'MRG':<7}{'النوع':<10}{'المتبقي':<12}{'القرار'}")
    print("─"*95)
    for i, t in enumerate(tasks, 1):
        tid = t.get("taskId"); tt = t.get("taskType","")
        rem, q = remaining_mrg(t, txs) if tt.startswith("recurring") else (None,"—")
        if tid in done and tt == "one_time": dec = f"{G}✓ منجزة{X}"
        elif t.get("isPaused"): dec = f"{R}✗ متوقفة{X}"
        elif rem and rem > 0: dec = f"{Y}⏳ {hms(rem)}{X}"
        else: dec = f"{C}▶ سيُجرَّب{X}"
        rs = hms(rem) if rem and rem > 0 else "—" if rem is None else f"{G}جاهز{X}"
        ts = {"one_time":"once","recurring_1h":"1h","recurring_3h":"3h"}.get(tt, tt[:6])
        print(f"{i:<3}{tid:<28}{(t.get('title') or '')[:34]:<36}{Y}+{t.get('reward',0):<6}{X}{ts:<10}{rs:<12}{dec}")
    print("─"*95)

async def cycle_mrg(init):
    async with system_task_lock:
        st, data = await api_mrg("/api/auth/verify", {"initData":init, "startParam":"ref"})
        if st != 200 or not data.get("success"): 
            return None, True 

        tasks, done = data.get("tasks", []), set(data.get("completedTaskIds", []))
        txs, b0 = data.get("transactions", []), data.get("user",{}).get("inAppBalance",0)
        show_mrg(tasks, done, txs)

        try_list = []
        for t in tasks:
            tid, tt = t.get("taskId"), t.get("taskType","")
            if tid in done and tt == "one_time": continue
            if t.get("isPaused"): continue
            if tt.startswith("recurring"):
                rem, _ = remaining_mrg(t, txs)
                if rem and rem > 0: continue
            try_list.append(t)

        if try_list:
            print(f"\n{C}🎯 [MRG] محاولة {len(try_list)} مهمة{X}\n")
        auth_fail = False
        for i, t in enumerate(try_list, 1):
            tid = t.get("taskId")
            print(f"[MRG] [{i}/{len(try_list)}] {(t.get('title') or '')[:55]}")
            st, body = await api_mrg("/api/user/claim-task", {"initData":init, "taskId":tid})
            err = (body.get("error") or "").lower()

            if st == 200 and body.get("success"):
                MEM_MRG[tid] = now()
                print(f"   {G}✅ +{t.get('reward',0)} MRG{X}")
            elif "cooldown" in err:
                rem, _ = remaining_mrg(t, txs)
                print(f"   {Y}⏳ cooldown — متبقي {hms(rem) if rem else '?'}{X}")
            elif "region" in err: print(f"   {R}🚫 محجوبة جغرافياً{X}")
            elif "already" in err: print(f"   {D}✓ منجزة{X}")
            elif st == 429: print(f"   {Y}⚠️ Rate limit{X}"); break
            else:
                e = (body.get("error") or "?")[:60]
                print(f"   {R}❌ {e}{X}")
                if "hmac" in e.lower() or "initdata" in e.lower(): auth_fail = True; break
            if i < len(try_list): await asyncio.sleep(4)

        await asyncio.sleep(2)
        _, f = await api_mrg("/api/auth/verify", {"initData":init, "startParam":"ref"})
        b1 = f.get("user",{}).get("inAppBalance", b0)
        return (b0, b1, tasks, txs), auth_fail

async def mrg_main_worker():
    print(f"\n{C}{'═'*95}\n{C}🎯 MRG Claimer v8 — بدء الخدمة الذكية (مزامنة الموارد){X}\n{C}{'═'*95}{X}")

    me, init = await get_mrg_data_and_disconnect()
    if not init: 
        print(f"{R}❌ جلسة MRG غير صالحة أو فشل جلب البيانات{X}")
        return

    print(f"{G}✅ MRG: {me.first_name} (@{me.username or me.id}) - بيانات مستخرجة بنجاح{X}")
    print(f"{G}   ✅ تم قطع الاتصال لحماية الجلسة من التعارض{X}")

    n = 0
    try:
        while True:
            n += 1
            print(f"\n{C}{'═'*95}\n{C}🔄 [MRG] دورة #{n} — {now().strftime('%H:%M:%S')} UTC{X}\n{C}{'═'*95}{X}")
            try:
                res, auth_fail = await cycle_mrg(init)

                if auth_fail or res is None:
                    print(f"⚠️ [MRG] الجلسة انتهت صلاحيتها، سيتم إعادة الاتصال لجلب بيانات جديدة...")
                    me, init = await get_mrg_data_and_disconnect()
                    if not init: 
                        await asyncio.sleep(30)
                    continue

                if res:
                    b0, b1, tasks, txs = res
                    d = b1 - b0
                    print(f"\n💰 MRG Balance: {b0:.4f} → {b1:.4f} MRG  ({G if d>0 else D}{d:+.4f}{X})")

                    earliest = None
                    for t in tasks:
                        if (t.get("taskType") or "").startswith("recurring"):
                            rem, _ = remaining_mrg(t, txs)
                            if rem and rem > 0 and (earliest is None or rem < earliest):
                                earliest = rem

                    wait = int(earliest) + 10 if earliest else 3600
                    hrs, mins = divmod(wait, 3600)
                    mins = mins // 60

                    print(f"😴 [MRG] إراحة السكربت والاستيقاظ بعد: {int(hrs)} ساعة و {int(mins)} دقيقة ({wait} ثانية)...")
                    await asyncio.sleep(wait)

            except Exception as e:
                print(f"{R}❌ [MRG Error]: {e}{X}")
                await asyncio.sleep(60)

    except asyncio.CancelledError:
        pass

# ==============================================================================
# 🟩 دوال وتدفق بوت ATF
# ==============================================================================
async def get_init_data_atf(client, bot, acc_name):
    try:
        web_view = await client(RequestWebViewRequest(
            peer=bot, bot=bot, platform="android", from_bot_menu=True, url=WEB_APP_URL_ATF
        ))
        raw_url = web_view.url
        if "#tgWebAppData=" in raw_url: return urllib.parse.unquote(raw_url.split("#tgWebAppData=")[1].split("&")[0])
        elif "tgWebAppData=" in raw_url: return urllib.parse.unquote(raw_url.split("tgWebAppData=")[1].split("&")[0])
    except Exception as e:
        print(f"❌ [{acc_name}] خطأ أثناء جلب initData: {e}")
    return None

async def login_atf(session, init_data, tg_id, username, acc_config):
    headers = {
        "User-Agent": acc_config["user_agent"],
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "Origin": BASE_URL_ATF,
        "Referer": f"{BASE_URL_ATF}/miner/index.html",
        "X-Requested-With": "XMLHttpRequest",
        "X-Telegram-Init-Data": init_data,
        **acc_config.get("extra_headers", {})
    }
    payload = {
        "initData": init_data,
        "tg_id": tg_id,
        "username": username or "",
        "request_id": f"rq-{int(time.time()*1000)}-{tg_id}",
        "device_id": f"{acc_config['device_prefix']}-{tg_id}-{int(time.time())}"
    }
    async with session.post(LOGIN_ENDPOINT_ATF, json=payload, headers=headers) as resp:
        if resp.status == 200:
            data = await resp.json()
            if data.get("status") == "success":
                headers["X-ATF-TMA-Session"] = data.get("tma_session_token")
                return data, headers
    return None, None

async def execute_task_atf(session, headers, tg_id, init_data, device_prefix, task, is_started, acc_name):
    now_ts = int(time.time())
    if not is_started:
        print(f"👉 [{acc_name}] [GO] بدء مهمة: {task['name']}")
        start_payload = {
            "tg_id": tg_id, "task_id": task["id"], "client_started_at": now_ts,
            "initData": init_data, "device_id": f"{device_prefix}-{tg_id}-{now_ts}",
            "request_id": f"rq-{now_ts}-{tg_id}"
        }
        try:
            async with session.post(START_TASK_ENDPOINT_ATF, json=start_payload, headers=headers) as resp:
                s_data = await resp.json()
                if s_data.get("status") != "success":
                    print(f"❌ [{acc_name}] فشل البدء للمهمة {task['name']}: {s_data.get('message')}")
                    return False
        except Exception as e:
            return False

        wait_sec = task.get('wait', 5) + 3
        print(f"⏳ [{acc_name}] انتظار {wait_sec} ثانية لإنهاء المهمة...")
        await asyncio.sleep(wait_sec)

    now_claim = int(time.time())
    print(f"🟩 [{acc_name}] [CLAIM] المطالبة بمكافأة: {task['name']}")
    claim_payload = {
        "tg_id": tg_id, "task_id": task["id"], "client_started_at": now_claim,
        "initData": init_data, "device_id": f"{device_prefix}-{tg_id}-{now_claim}",
        "request_id": f"rq-{now_claim}-{tg_id}"
    }
    try:
        async with session.post(CLAIM_TASK_ENDPOINT_ATF, json=claim_payload, headers=headers) as resp:
            c_data = await resp.json()
            if c_data.get("status") == "success":
                print(f"✅ [{acc_name}] تم جمع مهمة {task['name']} بنجاح! المكافأة: +{c_data.get('reward', 3)} ATF")
                return True
    except Exception as e:
        return False

async def atf_boost_worker(session, headers, me_id, me_username, init_data, device_prefix):
    await asyncio.sleep(2)
    while True:
        try:
            async with system_task_lock:
                payload = {
                    "initData": init_data, 
                    "tg_id": me_id, 
                    "username": me_username or "",
                    "request_id": f"rq-{int(time.time()*1000)}-{me_id}",
                    "device_id": f"{device_prefix}-{me_id}-{int(time.time())}",
                    "display_preview": "0.0000"
                }
                async with session.post(START_MINE_ENDPOINT_ATF, json=payload, headers=headers): pass
                async with session.post(ACTIVATE_BOOST_ENDPOINT_ATF, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        res = await resp.json()
                        if res.get("status") == "success":
                            print(f"🚀 [{me_id}] تم إرسال تسريع التعدين (BOOST) بنجاح!")
        except Exception:
            pass
        await asyncio.sleep(round(random.uniform(9, 10), 2))

async def smart_tasks_worker(acc_config, session, me_id, me_username, init_data):
    acc_name = acc_config["account_name"]
    device_prefix = acc_config["device_prefix"]

    while True:
        async with system_task_lock:
            print("\n" + "="*50)
            print(f"🔍 [{acc_name}] بدء دورة تنفيذ المهام...")

            login_data, headers = await login_atf(session, init_data, me_id, me_username, acc_config)

            if not login_data:
                print(f"⚠️ [{acc_name}] انتهت صلاحية الجلسة/الرابط (Token Expired). سيتم جلب رابط جديد...")
                return  

            cooldowns = login_data.get("task_cooldowns", {})
            task_starts = login_data.get("task_starts", {})
            current_time = int(time.time())
            pending_waits = []

            for task in TASKS_ATF:
                task_id = task["id"]
                cd_time = cooldowns.get(task_id, 0)
                is_started = task_id in task_starts

                if cd_time > current_time and not is_started:
                    remaining = cd_time - current_time
                    pending_waits.append(remaining)
                    mins, secs = divmod(remaining, 60)
                    hrs, mins = divmod(mins, 60)
                    print(f"⏳ [{acc_name}] [{task['name']}]: غير جاهزة ({hrs}h {mins}m {secs}s)")
                else:
                    await execute_task_atf(session, headers, me_id, init_data, device_prefix, task, is_started, acc_name)
                    await asyncio.sleep(3)

        next_wake_up = min(pending_waits) + 10 if pending_waits else 7200 
        hrs, mins = divmod(next_wake_up // 60, 60)
        print(f"😴 [{acc_name}] استيقاظ بعد: {hrs} ساعة و {mins} دقيقة ({next_wake_up} ثانية)...")
        await asyncio.sleep(next_wake_up)

async def account_worker_atf(acc_config):
    acc_name = acc_config["account_name"]

    while True:
        client = TelegramClient(StringSession(acc_config["session_string"]), acc_config["api_id"], acc_config["api_hash"])

        try:
            await client.connect()
            if not await client.is_user_authorized():
                print(f"🛑 [{acc_name}] الجلسة غير مصرّحة - يلزم session جديد")
                await client.disconnect()
                await asyncio.sleep(300)
                continue

            me = await client.get_me()
            bot = await client.get_input_entity(TARGET_BOT_USERNAME_ATF)

            init_data = await get_init_data_atf(client, bot, acc_name)
            await client.disconnect()
            print(f"🔗 [{acc_name}] تم جلب البيانات بنجاح، وقطع اتصال تيليجرام للحماية.")

            if not init_data:
                print(f"🛑 [{acc_name}] فشل جلب initData الأولي")
                await asyncio.sleep(15)
                continue

            async with aiohttp.ClientSession() as http_session:
                login_data, headers = await login_atf(http_session, init_data, me.id, me.username, acc_config)
                if not headers:
                    await asyncio.sleep(15)
                    continue

                tasks_task = asyncio.create_task(smart_tasks_worker(acc_config, http_session, me.id, me.username, init_data))
                boost_task = None
                if acc_config.get("do_boost", True):
                    boost_task = asyncio.create_task(atf_boost_worker(http_session, headers, me.id, me.username, init_data, acc_config["device_prefix"]))

                await tasks_task

                if boost_task: boost_task.cancel()

        except Exception as e:
            print(f"🛑 [{acc_name}] توقف في ATF: {type(e).__name__}")
        finally:
            try:
                if client.is_connected(): await client.disconnect()
            except Exception: pass

        print(f"🔄 [{acc_name}] جاري إعادة تهيئة الحساب لجلب بيانات جديدة...")
        await asyncio.sleep(10)

async def main_atf_app():
    active_accounts = [acc for acc in ACCOUNTS_CONFIG_ATF if acc.get("atf_enabled", True)]
    if not active_accounts:
        print("⚠️ ATF: كل الحسابات متوقفة")
        return

    print(f"🚀 ATF: تشغيل {len(active_accounts)} حسابات بنظام التحقق الذكي...")
    await asyncio.gather(*(account_worker_atf(acc) for acc in active_accounts), return_exceptions=True)

# ==============================================================================
# 🟨 المنسق الرئيسي والنظام الشامل المدمج
# ==============================================================================
async def main_system():
    print("⚡ تشغيل النظام الشامل (MRG Claimer + ATF Bot)...")
    await asyncio.gather(mrg_main_worker(), main_atf_app())

def run_bot():
    while True:
        try: asyncio.run(main_system())
        except KeyboardInterrupt: sys.exit(0)
        except Exception as e:
            print(f"⚠️ خطأ عام: {type(e).__name__}")
            time.sleep(5)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child": run_bot()
    else:
        while True:
            print("🚀 تشغيل المراقب للنظام الشامل...")
            try:
                result = subprocess.run([sys.executable, __file__, "--child"])
                if result.returncode == 0: break
            except KeyboardInterrupt: break
            except Exception: pass
            time.sleep(10)
