import os
import time
import asyncio
import json
import re
import ssl
import sys
import random
import urllib.request
import urllib.error
import urllib.parse
import subprocess
from datetime import datetime, timezone

from telethon import TelegramClient, functions, types, errors
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest

# =============================================================================
# 🟥 إعدادات وثوابت MRG Claimer
# ==============================================================================
API_ID_MRG = int(os.environ.get("API_ID_MRG", 38197378))
API_HASH_MRG = os.environ.get("API_HASH_MRG", "1efeb1db162150616801ae759799ca97")

# قراءة الجلسة حصراً من بيئة المتغيرات دون تضمين قيمتها في الكود
SESSION_MRG = os.environ.get("SESSION_MRG")

BOT_MRG = "@mrgminerbot"
BASE_MRG = "https://mrg.up.railway.app"

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

G, R, Y, C, D, X = "\033[92m", "\033[91m", "\033[93m", "\033[96m", "\033[2m", "\033[0m"
MEM_MRG = {}

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
    for _ in range(3): # زيادة محاولات الاتصال الصامتة
        try:
            req = urllib.request.Request(BASE_MRG+ep, data=json.dumps(payload).encode(),
                headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0",
                         "Origin":"https://app.mrgtoken.xyz"}, method="POST")
            with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())
        except: 
            time.sleep(random.uniform(2, 4)) # تأخير عشوائي
    return None, {}

async def api_mrg(ep, p): 
    return await asyncio.to_thread(http_mrg, ep, p)

async def wv_mrg(cli, bot, url=None, sn=None, sp=None):
    try:
        if sn: return (await cli(functions.messages.RequestAppWebViewRequest(
            peer=bot, app=types.InputBotAppShortName(bot, sn), platform="android", start_param=sp))).url
        return (await cli(functions.messages.RequestWebViewRequest(
            peer=bot, bot=bot, platform="android", url=url, start_param=sp))).url
    except Exception as e: 
        return None

async def get_init_mrg(cli, bot):
    full = None

    # 1. المحاولة الأولى: طلب التطبيق مباشرة بصمت عبر الأسماء الشائعة (الأكثر أماناً)
    for sn in ["app", "start", "game"]:
        full = await wv_mrg(cli, bot, sn=sn)
        if full: break

    # 2. المحاولة الثانية: البحث في الرسائل القديمة إذا لم ينجح الطلب المباشر
    if not full:
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

    if not full: return None

    # استخراج initData الصحيح
    raw = full.split("#tgWebAppData=")[-1].split("&tgWebAppVersion")[0] if "#tgWebAppData=" in full \
          else full.split("tgWebAppData=")[-1].split("&tgWebAppVersion")[0]
    return urllib.parse.unquote(raw)

async def get_mrg_data_and_disconnect():
    global SESSION_MRG
    SESSION_MRG = os.environ.get("SESSION_MRG")
    
    if not SESSION_MRG:
        print(f"{Y}⚠️ لم يتم العثور على متغير البيئة SESSION_MRG. السكربت يدخل في سبات لمدة 5 دقائق...{X}")
        return None, None

    cli = TelegramClient(StringSession(SESSION_MRG), API_ID_MRG, API_HASH_MRG)
    try:
        await cli.connect()
        if not await cli.is_user_authorized():
            print(f"{R}❌ الجلسة غير مصرحة. يرجى استخراج كود Session جديد.{X}")
            return None, None

        me = await cli.get_me()
        bot = await cli.get_input_entity(BOT_MRG)

        # ⚠️ تم حذف إرسال /start لتفادي السبام وحماية الحساب

        init_data = await get_init_mrg(cli, bot)
        return me, init_data

    except errors.FloodWaitError as e:
        print(f"{R}⚠️ تيليجرام يطلب الانتظار (FloodWait): {e.seconds} ثانية. حمايةً لحسابك، سيتم الانتظار.{X}")
        await asyncio.sleep(e.seconds + 5)
        return None, None
    except Exception as e:
        print(f"{R}❌ [خطأ في تيليجرام]: {e}{X}")
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

        # انتظار عشوائي بين المهام كالمستخدم البشري
        if i < len(try_list): await asyncio.sleep(random.uniform(3, 6))

    await asyncio.sleep(2)
    _, f = await api_mrg("/api/auth/verify", {"initData":init, "startParam":"ref"})
    b1 = f.get("user",{}).get("inAppBalance", b0)
    return (b0, b1, tasks, txs), auth_fail

async def mrg_main_worker():
    print(f"\n{C}{'═'*95}\n{C}🎯 MRG Claimer — بدء النظام الذكي الآمن{X}\n{C}{'═'*95}{X}")

    me, init = await get_mrg_data_and_disconnect()
    if not init: 
        print(f"{R}❌ فشل جلب البيانات الأولية أو عدم وجود الجلسة. يدخل السكربت في سبات لمدة 5 دقائق...{X}")
        await asyncio.sleep(300) # سبات لمدة 5 دقائق
    else:
        print(f"{G}✅ الحساب: {me.first_name} (@{me.username or me.id}) - تم الاستخراج بسلام{X}")
        print(f"{G}   ✅ تم قطع الاتصال بتيليجرام بنجاح لحماية الجلسة{X}")

    n = 0
    try:
        while True:
            n += 1
            print(f"\n{C}{'═'*95}\n{C}🔄 [دورة #{n}] — {now().strftime('%H:%M:%S')} UTC{X}\n{C}{'═'*95}{X}")

            if not init:
                me, init = await get_mrg_data_and_disconnect()
                if not init:
                    print(f"⚠️ يتعذر الاتصال (عدم وجود الجلسة أو تعذر الاتصال بتيليجرام). يدخل السكربت في السبات لمدة 5 دقائق...")
                    await asyncio.sleep(300) # سبات لمدة 5 دقائق
                    continue

            try:
                res, auth_fail = await cycle_mrg(init)

                if auth_fail or res is None:
                    print(f"{Y}⚠️ انتهت صلاحية الجلسة في خوادم MRG.{X}")
                    print(f"{Y}🛡️ حماية للحساب: ننتظر 5 دقائق قبل فتح اتصال جديد مع تيليجرام...{X}")
                    await asyncio.sleep(300) # تأخير ذكي يمنع سبام تيليجرام (5 دقائق)
                    init = None # تصفير المتغير لجلبه في الدورة القادمة
                    continue

                if res:
                    b0, b1, tasks, txs = res
                    d = b1 - b0
                    print(f"\n💰 الرصيد الحالي: {b0:.4f} → {b1:.4f} MRG  ({G if d>0 else D}{d:+.4f}{X})")

                    earliest = None
                    for t in tasks:
                        if (t.get("taskType") or "").startswith("recurring"):
                            rem, _ = remaining_mrg(t, txs)
                            if rem and rem > 0 and (earliest is None or rem < earliest):
                                earliest = rem

                    # الاستيقاظ العشوائي الذكي (+ 15 لـ 45 ثانية عشوائية)
                    wait = int(earliest) + random.randint(15, 45) if earliest else 3600
                    hrs, mins = divmod(wait, 3600)
                    mins = mins // 60

                    print(f"😴 [النوم الذكي] إراحة السكربت واستيقاظه بعد: {int(hrs)} ساعة و {int(mins)} دقيقة ({wait} ثانية)...")
                    await asyncio.sleep(wait)

            except Exception as e:
                print(f"{R}❌ [حدث خطأ غير متوقع]: {e}{X}")
                await asyncio.sleep(60)

    except asyncio.CancelledError:
        pass

def run_bot():
    while True:
        try: 
            asyncio.run(mrg_main_worker())
        except KeyboardInterrupt: 
            sys.exit(0)
        except Exception as e:
            print(f"{R}⚠️ خطأ عام في النظام: {type(e).__name__}{X}")
            time.sleep(10)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child": 
        run_bot()
    else:
        while True:
            print(f"{C}🚀 تشغيل المراقب الآمن לבوت MRG...{X}")
            try:
                result = subprocess.run([sys.executable, __file__, "--child"])
                if result.returncode == 0: break
            except KeyboardInterrupt: 
                break
            except Exception: 
                pass
            time.sleep(10)

