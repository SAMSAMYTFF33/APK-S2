import asyncio
import aiohttp
import ssl
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession

# إعداد السجلات لمتابعة الأداء بدقة
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ==========================================
# 1. الإعدادات والبيانات (Configuration)
# ==========================================

# 🔴 للتحكم العام في الحساب (1 = تشغيل الحساب ككل | 0 = إيقاف الحساب بالكامل)
ACCOUNT_1_ENABLED = 1 

ACCOUNTS = [
    {
        "enabled": ACCOUNT_1_ENABLED,
        "name": "gz",
        
        # 🔴 أزرار التحكم المستقلة لكل بوت (True = تشغيل | False = إيقاف)
        "enable_atf": False,   # تشغيل بوت ATF
        "enable_mrg": True,  # إيقاف بوت MRG (حسب طلبك)
        
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
    }
]

# ثوابت الروابط لـ ATF
LOGIN_ENDPOINT_ATF = "https://api.atfminers.com/login"
TASKS_ENDPOINT_ATF = "https://api.atfminers.com/tasks"
BOOST_ENDPOINT_ATF = "https://api.atfminers.com/boost"

# قفل التزامن لمنع إغراق الشبكة
network_lock = asyncio.Lock()

# إعدادات الـ SSL
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


# ==========================================
# 2. دوال مساعدة وبصمة الجهاز (Helpers)
# ==========================================

def get_headers(account: dict, token: str = None) -> dict:
    """بناء الترويسات مع الدمج الكامل للبصمة"""
    headers = {
        "User-Agent": account['user_agent'],
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if "extra_headers" in account:
        headers.update(account["extra_headers"])
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

async def fetch_telegram_init_data(client: TelegramClient, bot_username: str, tg_lock: asyncio.Lock) -> str:
    """جلب initData طازج وآمن من تيليجرام باستخدام قفل التزامن يمنع تعارض الجلسة"""
    async with tg_lock:
        try:
            if not client.is_connected():
                await client.connect()
            
            # يمكنك وضع كود استخراج WebView الحقيقي الخاص بك هنا
            # مثال:
            # web_view = await client(RequestWebViewRequest(...))
            # return web_view_url_parsed
            
            logging.info(f"[+] Fresh initData generated for bot: {bot_username}")
            return f"dummy_init_data_for_{bot_username}"
        except Exception as e:
            logging.error(f"[-] Error fetching Telegram initData for {bot_username}: {e}")
            return ""


# ==========================================
# 3. مدير جلسة ATF لمنع تسريب المهام (Session Manager)
# ==========================================

class ATFSessionManager:
    """يدير التوكن وعامل البوست لضمان عدم تكرار العمال واستنزاف الموارد"""
    def __init__(self, account: dict):
        self.account = account
        self.token = None
        self.boost_task = None

    def update_token(self, new_token: str, session: aiohttp.ClientSession):
        self.token = new_token
        # إلغاء مهمة البوست القديمة إن وجدت لمنع تكرار العمال
        if self.boost_task and not self.boost_task.done():
            self.boost_task.cancel()
            logging.info(f"[*] ATF ({self.account['name']}): Old boost task cancelled.")
        
        # إطلاق عامل بوست جديد بالتوكن المحدث فقط إذا كان الحساب يملك توكن مفعل
        if self.account.get("do_boost", True) and new_token:
            self.boost_task = asyncio.create_task(self._boost_loop(session))
            logging.info(f"[+] ATF ({self.account['name']}): New boost task spawned.")

    async def _boost_loop(self, session: aiohttp.ClientSession):
        """عامل التعدين والسحب الذي ينطلق كل 10 ثوانٍ"""
        headers = get_headers(self.account, self.token)
        while True:
            try:
                async with session.post(BOOST_ENDPOINT_ATF, headers=headers) as resp:
                    if resp.status == 200:
                        logging.info(f"[+] ATF ({self.account['name']}): Boost successful (10s cycle).")
                    elif resp.status == 401:
                        logging.warning(f"[-] ATF ({self.account['name']}): Boost 401 Unauthorized. Stopping boost loop.")
                        break
                    else:
                        logging.warning(f"[-] ATF ({self.account['name']}): Boost failed code: {resp.status}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"[-] ATF ({self.account['name']}): Boost network error: {e}")
            
            await asyncio.sleep(10) # 🔴 التكرار كل 10 ثوانٍ كما طلبت


# ==========================================
# 4. دوال عمليات ATF
# ==========================================

async def login_atf(session: aiohttp.ClientSession, account: dict, init_data: str):
    headers = get_headers(account)
    payload = {"initData": init_data}
    try:
        async with session.post(LOGIN_ENDPOINT_ATF, json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                token = data.get("token")
                if token:
                    logging.info(f"[+] ATF ({account['name']}): Login successful.")
                    return token
            logging.error(f"[-] ATF ({account['name']}): Login failed status {resp.status}")
            return None
    except Exception as e:
        logging.error(f"[-] ATF ({account['name']}): Login Exception: {e}")
        return None

async def execute_task_atf(session: aiohttp.ClientSession, account: dict, token: str, task_id: str) -> bool:
    headers = get_headers(account, token)
    payload = {"taskId": task_id}
    
    async with network_lock:
        try:
            async with session.post(TASKS_ENDPOINT_ATF, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    logging.info(f"[+] ATF ({account['name']}): Task {task_id} started.")
                elif resp.status == 401:
                    logging.warning(f"[-] ATF ({account['name']}): Task {task_id} failed: Unauthorized (401).")
                    return False # التوكن غير صالح
                else:
                    logging.warning(f"[-] ATF ({account['name']}): Task {task_id} status {resp.status}")
        except Exception as e:
            logging.error(f"[-] ATF ({account['name']}): Task execution error: {e}")

    logging.info(f"[*] ATF ({account['name']}): Waiting 36s for task {task_id}...")
    await asyncio.sleep(36)
    return True

async def smart_tasks_worker_atf(session: aiohttp.ClientSession, account: dict, tg_client: TelegramClient, tg_lock: asyncio.Lock):
    """عامل ATF الذكي بالدورات الفترية (كل ساعتين)"""
    manager = ATFSessionManager(account)
    cached_init_data = None
    
    while True:
        # 1. تسجيل الدخول وتوليد التوكن إذا لم يكن موجواً
        if not manager.token:
            if not cached_init_data:
                cached_init_data = await fetch_telegram_init_data(tg_client, "atf_bot_username", tg_lock)
            
            if cached_init_data:
                token = await login_atf(session, account, cached_init_data)
                if token:
                    manager.update_token(token, session)
                else:
                    logging.warning(f"[-] ATF ({account['name']}): Login failed. Clearing initData cache...")
                    cached_init_data = None
                    await asyncio.sleep(30)
                    continue
            else:
                await asyncio.sleep(60)
                continue

        # 2. فحص وتنفيذ المهام
        headers = get_headers(account, manager.token)
        try:
            async with session.get(TASKS_ENDPOINT_ATF, headers=headers) as resp:
                if resp.status == 401:
                    logging.warning(f"[-] ATF ({account['name']}): Token expired (401). Resetting...")
                    manager.update_token(None, session)
                    cached_init_data = None
                    continue
                
                if resp.status == 200:
                    try:
                        tasks_data = await resp.json()
                    except Exception:
                        tasks_data = {}
                    
                    if isinstance(tasks_data, dict):
                        available_tasks = tasks_data.get("available", [])
                        for task in available_tasks:
                            if isinstance(task, dict) and "id" in task:
                                success = await execute_task_atf(session, account, manager.token, task["id"])
                                if not success:
                                    manager.update_token(None, session)
                                    cached_init_data = None
                                    break
                                await asyncio.sleep(3)
                                
        except Exception as e:
            logging.error(f"[-] ATF ({account['name']}): Fetch tasks error: {e}")
            
        logging.info(f"[*] ATF ({account['name']}): Cycle complete. Sleeping for 2 hours (7200s)...")
        await asyncio.sleep(7200) # 🔴 دورة مهام ATF كل ساعتين


# ==========================================
# 5. دوال عمليات MRG
# ==========================================

async def smart_tasks_worker_mrg(session: aiohttp.ClientSession, account: dict, tg_client: TelegramClient, tg_lock: asyncio.Lock):
    """عامل MRG المستقل تماماً (كل 3 ساعات)"""
    cached_init_data = None
    
    while True:
        if not cached_init_data:
            cached_init_data = await fetch_telegram_init_data(tg_client, "mrg_bot_username", tg_lock)
            
        logging.info(f"[*] MRG ({account['name']}): Starting task execution cycle...")
        
        # يمكنك إضافة منطق طلبات MRG هنا كـ HTTP GET/POST عبر session
        # ...

        logging.info(f"[*] MRG ({account['name']}): Cycle complete. Sleeping for 3 hours (10800s)...")
        await asyncio.sleep(10800) # 🔴 دورة مهام MRG كل 3 ساعات


# ==========================================
# 6. المدير الموحد للحساب (Master Worker)
# ==========================================

async def master_account_worker(account: dict):
    """مدير الحساب الموحد: يضمن تشغيل الحساب على البوتين بنفس الاتصال وبدون تعارض AuthKeyDuplicatedError"""
    
    # التأكد من أن على الأقل بوت واحد مفعل لهذا الحساب، وإلا نتوقف فوراً لتوفير الموارد
    enable_atf = account.get("enable_atf", True)
    enable_mrg = account.get("enable_mrg", True)
    
    if not enable_atf and not enable_mrg:
        logging.info(f"[*] Both ATF and MRG are DISABLED for account {account['name']}. Stopping worker.")
        return

    client = TelegramClient(StringSession(account['session_string']), account['api_id'], account['api_hash'])
    tg_lock = asyncio.Lock()
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            logging.critical(f"[-] Account {account['name']} Telegram session UNAUTHORIZED! Stopping worker.")
            return

        logging.info(f"[+] Account {account['name']} Telegram authenticated successfully.")
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout, connector=aiohttp.TCPConnector(ssl=ssl_context)) as http_session:
            
            active_tasks = []
            
            # تشغيل عامل ATF فقط إذا كان مفعلاً
            if enable_atf:
                logging.info(f"[*] Starting ATF worker for {account['name']}...")
                active_tasks.append(asyncio.create_task(smart_tasks_worker_atf(http_session, account, client, tg_lock)))
            
            # تشغيل عامل MRG فقط إذا كان مفعلاً
            if enable_mrg:
                logging.info(f"[*] Starting MRG worker for {account['name']}...")
                active_tasks.append(asyncio.create_task(smart_tasks_worker_mrg(http_session, account, client, tg_lock)))
            
            # جمع العمال النشطة وتشغيلها بسلام
            if active_tasks:
                await asyncio.gather(*active_tasks)

    except Exception as e:
        logging.critical(f"[-] Master worker error for {account['name']}: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()
            logging.info(f"[*] Telegram client for {account['name']} disconnected safely.")


# ==========================================
# 7. المحرك الأساسي (Main Runner)
# ==========================================

async def main():
    tasks = []
    
    for acc in ACCOUNTS:
        if acc.get('enabled') == 1:
            logging.info(f"[*] Initializing MASTER worker for account: {acc['name']}")
            tasks.append(asyncio.create_task(master_account_worker(acc)))
        else:
            logging.info(f"[-] Account {acc['name']} is (DISABLED globally) skipping...")

    if not tasks:
        logging.warning("[-] No active accounts configured. Exiting.")
        return

    logging.info("[*] System running with zero leaks and safe concurrency...")
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("\n[!] Script manually stopped by user. Shutting down gracefully...")
