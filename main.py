import os
import time
import asyncio
import json
import sys
import random
import subprocess
import urllib.parse
import aiohttp

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest

# ==============================================================================
# 🎨 ألوان التنسيق للترمينال
# ==============================================================================
G, R, Y, C, D, X = "\033[92m", "\033[91m", "\033[93m", "\033[96m", "\033[2m", "\033[0m"

# ==============================================================================
# 🔒 قفل المزامنة لمنع تداخل الطلبات
# ==============================================================================
system_task_lock = asyncio.Lock()

# ==============================================================================
# ⚙️ مفتاح التحكم بالحساب الأول ATF (1 = يعمل | 0 = متوقف)
# ==============================================================================
ATF_ACCOUNT_1   = 1    

# ==============================================================================
# 🟩 إعدادات الحساب الأول (ATF Account 1) - القراءة من متغيرات البيئة
# ==============================================================================
ACCOUNTS_CONFIG_ATF = [
    {
        "atf_enabled": ATF_ACCOUNT_1 == 1,
        "account_name": "الحساب الأول (gz)",
        "do_boost": True,
        "api_id": int(os.environ.get("API_ID_1", 38197378)),
        "api_hash": os.environ.get("API_HASH_1", "1efeb1db162150616801ae759799ca97"),
        "session_string": os.environ.get("SESSION_STRING_1", ""),  # يتم جلبها تلقائياً من Railway
        "device_prefix": "redmi-note9s",
        "user_agent": "Mozilla/5.0 (Linux; Android 12; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.8010.36 Mobile Safari/537.36 Telegram-Android/12.10.1.1 (Xiaomi Redmi Note 9S; Android 12; SDK 31; AVERAGE)",
        "extra_headers": {
            "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="153", "Google Chrome";v="153"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "accept-language": "ar"
        }
    }
]

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
# ⚙️ دوال وتدفق العمل لبوت ATF
# ==============================================================================
async def get_init_data_atf(client, bot, acc_name):
    try:
        web_view = await client(RequestWebViewRequest(
            peer=bot, bot=bot, platform="android", from_bot_menu=True, url=WEB_APP_URL_ATF
        ))
        raw_url = web_view.url
        if "#tgWebAppData=" in raw_url:
            return urllib.parse.unquote(raw_url.split("#tgWebAppData=")[1].split("&")[0])
        elif "tgWebAppData=" in raw_url:
            return urllib.parse.unquote(raw_url.split("tgWebAppData=")[1].split("&")[0])
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
        except Exception:
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
    except Exception:
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
    session_str = acc_config.get("session_string", "").strip()

    if not session_str:
        print(f"🛑 [{acc_name}] خطأ: لم يتم العثور على SESSION_STRING_1 في متغيرات البيئة (Variables) الخاص بـ Railway!")
        await asyncio.sleep(60)
        return

    while True:
        client = TelegramClient(StringSession(session_str), acc_config["api_id"], acc_config["api_hash"])

        try:
            await client.connect()
            if not await client.is_user_authorized():
                print(f"🛑 [{acc_name}] الجلسة غير مصرّحة أو منتهية الصلاحية - تحقق من SESSION_STRING_1")
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

                if boost_task:
                    boost_task.cancel()

        except Exception as e:
            print(f"🛑 [{acc_name}] توقف في ATF: {type(e).__name__}")
        finally:
            try:
                if client.is_connected():
                    await client.disconnect()
            except Exception:
                pass

        print(f"🔄 [{acc_name}] جاري إعادة تهيئة الحساب لجلب بيانات جديدة...")
        await asyncio.sleep(10)

async def main_atf_app():
    active_accounts = [acc for acc in ACCOUNTS_CONFIG_ATF if acc.get("atf_enabled", False)]
    if not active_accounts:
        print("⚠️ ATF: الحساب متوقف (ATF_ACCOUNT_1 = 0)")
        return

    print(f"🚀 ATF: تشغيل الحساب الأول ({active_accounts[0]['account_name']}) بنظام التحقق الذكي...")
    await asyncio.gather(*(account_worker_atf(acc) for acc in active_accounts), return_exceptions=True)

# ==============================================================================
# 🚀 نقطة التشغيل الرئيسية مع المراقب
# ==============================================================================
def run_bot():
    while True:
        try:
            asyncio.run(main_atf_app())
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print(f"⚠️ خطأ عام: {type(e).__name__}")
            time.sleep(5)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        run_bot()
    else:
        while True:
            print("🚀 تشغيل المراقب الخاص ببوت ATF (الحساب الأول)...")
            try:
                result = subprocess.run([sys.executable, __file__, "--child"])
                if result.returncode == 0:
                    break
            except KeyboardInterrupt:
                break
            except Exception:
                pass
            time.sleep(10)
