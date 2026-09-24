import asyncio
import aiohttp
import ssl
from telethon import TelegramClient
from telethon.sessions import StringSession

# ==========================================
# 1. الإعدادات والبيانات (Configuration)
# ==========================================

# تم دمج بيانات حساب "gz" الكاملة مع الترويسات الإضافية لضمان تطابق البصمة 100%
ATF_ACCOUNTS = [
    {
        "name": "gz",
        "session_string": "1BJWap1wBu3SWNB8JFOdcM2T6cVu0o4dv7iybgtIqrRmUZYzkmWRkmBjFbGaovA7tyqfsozceWzvd9SuhsKsW1a9cle_PXkM_THwP_65_PYfO9w3aHVUvN_sIcfbnyQHz4AaVJhCyNEbwaRaZjShJvpZscoU_JLc0xD0rvE5wGQjEHZJkmL4OLsqoxZn0DgKqRtjLFX6KeQZinHJQeaFQQTqMdelSWmtE3diSNAV3JETvf7X2Llfb4dhVYbOAcMxm3ZRhRtv5uE9RjmMkS2OHOA8Dmr1OYn_E1r-xup8d2FifOMmI8QHcAS0ucEUwtgf5fS9AxtrLOS-JimS6tTNiiPcc7jZzRUU=",
        "api_id": 38197378,
        "api_hash": "1efeb1db162150616801ae759799ca97",
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

# حسابات MRG (متروكة فارغة أو يُمكن إضافتها لاحقاً)
MRG_ACCOUNTS = []

# ثوابت الروابط (EndPoints)
LOGIN_ENDPOINT_ATF = "https://api.atfminers.com/login"
TASKS_ENDPOINT_ATF = "https://api.atfminers.com/tasks"
BOOST_ENDPOINT_ATF = "https://api.atfminers.com/boost"

# قفل التزامن لإرسال الطلبات المتزامنة
network_lock = asyncio.Lock()

# إعدادات SSL
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


# ==========================================
# 2. دوال MRG
# ==========================================

async def api_mrg(session: aiohttp.ClientSession, url: str, headers: dict, payload: dict = None):
    """دالة موحدة لاتصالات MRG باستخدام aiohttp السريع"""
    try:
        if payload:
            async with session.post(url, json=payload, headers=headers) as response:
                return await response.json()
        else:
            async with session.get(url, headers=headers) as response:
                return await response.json()
    except Exception as e:
        print(f"[-] MRG API Error: {e}")
        return None

async def get_mrg_data_and_disconnect(account: dict):
    """إدارة جلسة MRG وجمع البيانات"""
    client = TelegramClient(StringSession(account['session_string']), account['api_id'], account['api_hash'])
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print(f"[-] MRG Account {account['name']} is unauthorized. Skipping.")
            return

        print(f"[+] MRG Account {account['name']} connected successfully.")
        
    except Exception as e:
        print(f"[-] Error in MRG {account['name']}: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()


# ==========================================
# 3. دوال ATF لحساب gz (المهام، البوست، تسجيل الدخول)
# ==========================================

def get_base_headers(account: dict, token: str = None) -> dict:
    """توليد الترويسات مع الدمج الكامل للبصمة والـ Extra Headers"""
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

async def login_atf(session: aiohttp.ClientSession, account: dict, init_data: str):
    """تسجيل الدخول بذكاء للحصول على التوكن مع الحفاظ على بصمة الجهاز"""
    headers = get_base_headers(account)
    payload = {"initData": init_data}
    
    try:
        async with session.post(LOGIN_ENDPOINT_ATF, json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"[+] ATF ({account['name']}): Login successful.")
                return data.get("token")
            else:
                print(f"[-] ATF ({account['name']}): Login failed with status {resp.status}")
                return None
    except asyncio.TimeoutError:
        print(f"[-] ATF ({account['name']}): Login Timeout.")
        return None
    except Exception as e:
        print(f"[-] ATF ({account['name']}): Login Error: {e}")
        return None

async def execute_task_atf(session: aiohttp.ClientSession, account: dict, token: str, task_id: str):
    """تنفيذ مهمة واحدة دون تجميد باقي النظام"""
    headers = get_base_headers(account, token)
    payload = {"taskId": task_id}
    
    async with network_lock:
        try:
            async with session.post(TASKS_ENDPOINT_ATF, json=payload, headers=headers) as resp:
                result = await resp.json()
                print(f"[+] ATF ({account['name']}): Task {task_id} started.")
        except Exception as e:
            print(f"[-] ATF ({account['name']}): Task trigger error: {e}")
            return

    # الانتظار يقع خارج القفل تماماً لعدم تعطيل الحسابات والمهام الأخرى
    print(f"[*] ATF ({account['name']}): Waiting 36 seconds for task {task_id} to complete...")
    await asyncio.sleep(36)
    print(f"[+] ATF ({account['name']}): Task {task_id} completed.")

async def atf_boost_worker(session: aiohttp.ClientSession, account: dict, token: str):
    """عامل البوست المستقل يعمل بالخلفية"""
    headers = get_base_headers(account, token)
    while True:
        try:
            async with session.post(BOOST_ENDPOINT_ATF, headers=headers) as resp:
                if resp.status == 200:
                    print(f"[+] ATF ({account['name']}): Boost successful.")
                else:
                    print(f"[-] ATF ({account['name']}): Boost failed.")
        except Exception as e:
            pass
        
        await asyncio.sleep(7200) # النوم ساعتين خارج القفل

async def smart_tasks_worker(session: aiohttp.ClientSession, account: dict, init_data: str):
    """المحرك الذكي للمهام وتجديد التوكن تلقائياً عند انتهاء صلاحيته"""
    current_token = None
    
    while True:
        if not current_token:
            current_token = await login_atf(session, account, init_data)
            if not current_token:
                await asyncio.sleep(60)
                continue
            
            asyncio.create_task(atf_boost_worker(session, account, current_token))
        
        headers = get_base_headers(account, current_token)
        try:
            async with session.get(TASKS_ENDPOINT_ATF, headers=headers) as resp:
                if resp.status == 401:
                    print(f"[-] ATF ({account['name']}): Token expired. Relogging...")
                    current_token = None
                    continue
                
                if resp.status == 200:
                    tasks = await resp.json()
                    for task in tasks.get("available", []):
                        await execute_task_atf(session, account, current_token, task["id"])
                        await asyncio.sleep(3)
                        
        except Exception as e:
            print(f"[-] ATF ({account['name']}): Tasks fetch error: {e}")
            
        print(f"[*] ATF ({account['name']}): Cycle complete. Sleeping for 3 hours.")
        await asyncio.sleep(10800)

async def account_worker_atf(account: dict):
    """مدير جلسة التليجرام والشبكة للحساب"""
    client = TelegramClient(StringSession(account['session_string']), account['api_id'], account['api_hash'])
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print(f"[-] ATF Account {account['name']} is UNAUTHORIZED! Stopping worker.")
            return

        print(f"[+] ATF Account {account['name']} successfully authenticated via Telegram.")
        
        # استبدل هذا المتغير بناتج استخراج init_data الحقيقي من البوت
        init_data = "dummy_init_data_from_telegram_webview"
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout, connector=aiohttp.TCPConnector(ssl=ssl_context)) as http_session:
            await smart_tasks_worker(http_session, account, init_data)

    except Exception as e:
        print(f"[-] Critical Error in ATF {account['name']}: {e}")
    finally:
        if client.is_connected():
            await client.disconnect()


# ==========================================
# 4. المحرك الأساسي (Main Runner)
# ==========================================

async def main():
    tasks = []
    
    # تشغيل حساب gz المطابق للإعدادات
    for atf_acc in ATF_ACCOUNTS:
        if atf_acc['name'] == 'gz':
            tasks.append(asyncio.create_task(account_worker_atf(atf_acc)))
            print(f"[+] Initialized ATF worker for: {atf_acc['name']}")

    for mrg_acc in MRG_ACCOUNTS:
        tasks.append(asyncio.create_task(get_mrg_data_and_disconnect(mrg_acc)))
        print(f"[+] Initialized MRG worker for: {mrg_acc['name']}")
        
    if not tasks:
        print("[-] No active accounts configured. Exiting.")
        return

    print("[*] All workers initialized. System running asynchronously with zero lock-bottlenecks...")
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Process terminated by user. Shutting down gracefully...")
