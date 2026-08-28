import os
TOKEN = "8872823199:AAGlOZmzYOb9C3esalQBsWW9I32HkV5BBkI"
BOT_USERNAME = "NOP3bot"

ADMIN_IDS = [123456789]
POINTS_ADMIN_ID = 7638322813

OWNER_IDS = [POINTS_ADMIN_ID, 8676850552]


def is_owner(user_id: int) -> bool:
    """يتحقق مما إذا كان المستخدم أحد مالكي البوت (OWNER_IDS)."""
    return user_id in OWNER_IDS


REQUIRED_CHANNEL_USERNAME = "e_ggf"
REQUIRED_CHANNEL_URL = "https://t.me/e_ggf"
REQUIRED_CHANNEL_BUTTON_TEXT = "VORTEX  𓏺"
REQUIRED_CHANNEL_DEFAULT_TARGET = "1000"

FIREBASE_PROJECT_ID = "wep-app-1771a"
FIREBASE_PRIVATE_KEY_ID = "4e6f499aee9cf5a54366a87c45b3760782f43b41"
FIREBASE_CLIENT_EMAIL = "firebase-adminsdk-fbsvc@wep-app-1771a.iam.gserviceaccount.com"
FIREBASE_CLIENT_ID = "105199268649045240747"
FIREBASE_CLIENT_CERT_URL = (
    "https://www.googleapis.com/robot/v1/metadata/x509/"
    "firebase-adminsdk-fbsvc%40wep-app-1771a.iam.gserviceaccount.com"
)

_raw_private_key = os.environ.get("FIREBASE_PRIVATE_KEY", "")
if "\\n" in _raw_private_key and "\n" not in _raw_private_key:
    _raw_private_key = _raw_private_key.replace("\\n", "\n")

FIREBASE_SERVICE_ACCOUNT = {
    "type": "service_account",
    "project_id": FIREBASE_PROJECT_ID,
    "private_key_id": FIREBASE_PRIVATE_KEY_ID,
    "private_key": _raw_private_key,
    "client_email": FIREBASE_CLIENT_EMAIL,
    "client_id": FIREBASE_CLIENT_ID,
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": FIREBASE_CLIENT_CERT_URL,
    "universe_domain": "googleapis.com",
}


import asyncio
import json
import logging
import random
import secrets
import sqlite3
import threading
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
_boot_logger = logging.getLogger("contest_bot.bootstrap")

try:
    import apscheduler
except ImportError:
    _boot_logger.warning("مكتبة JobQueue غير مثبّتة — جارٍ تثبيتها تلقائيًا الآن (مرة واحدة فقط)...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--quiet",
            "python-telegram-bot[job-queue]",
        ])
        _boot_logger.warning(
            "تم تثبيت المكتبة بنجاح! سيتابع البوت الإقلاع الآن مباشرة بدون الحاجة لإعادة "
            "التشغيل يدويًا (وإن ظهر خطأ JobQueue رغم هذا، أعد تشغيل السكربت مرة واحدة)."
        )
    except Exception as _exc:
        _boot_logger.error(
            "فشل التثبيت التلقائي (%s). ثبّت يدويًا عبر: "
            "pip install \"python-telegram-bot[job-queue]\" ثم أعد التشغيل.",
            _exc,
        )

try:
    import firebase_admin
except ImportError:
    _boot_logger.warning("مكتبة firebase-admin غير مثبّتة — جارٍ تثبيتها تلقائيًا الآن (مرة واحدة فقط)...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--quiet", "firebase-admin",
        ])
        _boot_logger.warning("تم تثبيت firebase-admin بنجاح! يتابع البوت الإقلاع الآن مباشرة.")
    except Exception as _exc:
        _boot_logger.error(
            "فشل التثبيت التلقائي لـ firebase-admin (%s). ثبّت يدويًا عبر: "
            "pip install firebase-admin ثم أعد التشغيل.",
            _exc,
        )

import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger("contest_bot")

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQueryResultArticle,
    InputTextMessageContent,
    SwitchInlineQueryChosenChat,
    MessageEntity,
    CopyTextButton,
    LabeledPrice,
    BotCommand,
    LinkPreviewOptions,
)
from telegram.error import RetryAfter
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    InlineQueryHandler,
    ChosenInlineResultHandler,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    PreCheckoutQueryHandler,
    filters,
)
from telegram.request import HTTPXRequest

DEFAULT_POINTS_TITLE = "🎁 ربح من البوت"
DEFAULT_POINTS_CONDITIONS = (
    "الربح يكون فقط من قسم «إنشاء سحب».\n"
    "كل مستخدم جديد يجتاز منع الرشق ويشارك في السحب يمنح صاحب السحب نقاطًا مرة واحدة فقط."
)
TECH_SUPPORT_USERNAME = "y66vlBOT"
SUPPORT_BOT_STARS_AMOUNT = 5

BRAND_NAME = "𝚁𝙾𝚄𝙻𝙴𝚃𝚃𝙴 𝚅𝙾𝚁𝚃𝙴𝚇"
BRAND_URL = "https://t.me/e_ggf"

GIVEAWAYS_LINK_TEXT = "السحوبات"
GIVEAWAYS_CHANNEL_URL = "https://t.me/n_bbo"

ANNOUNCE_CHANNEL_USERNAME = "n_bbo"
ANNOUNCE_CHANNEL_URL = "https://t.me/n_bbo"
ANNOUNCE_CHANNEL_CHAT_ID = f"@{ANNOUNCE_CHANNEL_USERNAME}"


ROULETTE_COUNTS = [5, 10, 15, 20, 25, 30, 50, 100]

DEFAULT_HIDE_PARTICIPANTS = "1"
DEFAULT_GAME_CLICHE = f"أهلا وسهلا بكم في {BRAND_NAME}"

ROULETTE_THUMBS = {
    n: f"https://wsrv.nl/?url=raw.githubusercontent.com/SAMSAMYTFF33/WEB/main/assets/Number{n}.png&w=100&h=100&output=jpg&q=60&v=2" for n in ROULETTE_COUNTS
}

EMOJI = {
    "trophy_create_draw": "5429387503129875330",
    "roulette": "5102856631562011824",
    "draws_check": "5843596438373667352",
    "chart": "5940378308003762340",
    "doc": "5334882760735598374",
    "remind_check": "5954244021508380732",
    "star": "5346309121794659890",
    "tech": "5814558770075803439",
    "trophy_contest": "5789577921727307070",
    "gear": "5341715473882955310",
    "hand": "5940774295398521609",
    "buoy": "6008036485436022431",
    "arrow_down": "5208903445729266755",
    "remind_on": "5206607081334906820",
    "remind_off": "5210952531676504517",
    "hide_participants_btn": "5332724926216428039",
    "cliche_btn": "5841360920781002031",
    "restore_defaults_btn": "6012661228910939253",
    "back_section_btn": "6039539366177541657",
    "register_plus": "5226945370684140473",
    "target_pin": "5310278924616356636",
    "num_one": "5260562728249996728",
    "num_two": "5260273822979863490",
    "pin_note": "5769520351440540688",
    "arrow_left": "5769534112515756980",
    "envelope_klesha": "5406631276042002796",
    "new_badge": "5895669571058142797",
    "end_question": "5208748474719293821",
    "alarm_clock": "5208413342716153772",
    "votes_chart_btn": "5429651785352501917",
    "alarm_clock_btn": "6217487596486922033",
    "people": "5769289664452104963",
    "bullet_point": "5769338979266597469",
    "target": "5965522064461799191",
    "party": "5370870691140737817",
    "medal": "5789703004059868939",
    "trophy_win": "5789577921727307070",
    "alarm_clock_title": "5215394081911351762",
    "time_option_btn": "5764762214871343251",
    "time_manual_btn": "6046294958892129907",
    "time_custom_btn": "5850317551090800862",
    "back_time_menu_btn": "5390885122775985914",
    "trophy_winners_title": "5429387503129875330",
    "back_winners_btn": "6039539366177541657",
    "confirm_check": "5429381339851796035",
    "notify_win_btn": "5458603043203327669",
    "no_btn": "5954244021508380732",
    "announce_results_btn": "5789428375261023681",
    "approve_participants_label_btn": "6026257381678124710",
    "yes_btn": "5852544431504234283",
    "premium_vote_btn": "5942584147372413048",
    "publish_btn": "5258332798409783582",
    "join_accept_btn": "5767193595857606245",
    "withdraw_btn": "5967594648175121607",
    "sub_laptop": "5769469013696451511",
    "sub_alert": "5769630100739854545",
    "sub_check": "5767193595857606245",
    "recent_contests_btn": "5213334816891631245",
    "seats_change_btn": "5429651785352501917",
    "pause_toggle_btn": "5852544431504234283",
    "edit_settings_refresh_btn": "6012661228910939253",
    "remove_contestant_btn": "5967594648175121607",
    "delete_all_btn": "5913597928487784523",
    "cross_flag_off": "5954244021508380732",
    "check_flag_on": "5429381339851796035",
    "num_three": "5260650672000348972",
    "num_four": "5260544569128269433",
    "num_five": "5260655426529146332",
    "num_six": "5260604105964926035",
    "gw_condition_channel": "6039381989985882045",
    "gw_vote_icon": "5895428924040548238",
    "gw_new_participant": "6032994772321309200",
    "gw_view_profile": "5904630315946611415",
    "gw_kick_btn": "5240241223632954241",
    "gw_atime_lightning": "5965286318001889755",
    "gw_atime_clock": "5852614259082530343",
}

CAPTCHA_EMOJIS = [
    "5402477260982731644",
    "5449449325434266744",
    "5438496463044752972",
    "5456140674028019486",
    "5447410659077661506",
    "5453976908159016299",
    "5454206993852029667",
    "5253984341591076047",
    "5253861243533406038",
    "5408850391154569842",
    "5019726470101075726",
    "5145427681680032825",
]

CAPTCHA_OPTIONS_COUNT = 3
CAPTCHA_SESSION_TTL_SECONDS = 10 * 60

CONTEST_TIME_OPTIONS = [
    [(5, "بعد 5 دقايق"), (1, "بعد 1 دقيقة")],
    [(30, "بعد 30 دقيقة"), (60, "بعد 1 ساعة")],
    [(120, "بعد 2 ساعات"), (180, "بعد 3 ساعات")],
    [(240, "بعد 4 ساعات"), (300, "بعد 5 ساعات")],
    [(360, "بعد 6 ساعات"), (720, "بعد 12 ساعات")],
    [(1440, "بعد 24 ساعة"), (2880, "بعد 48 ساعات")],
    [(4320, "بعد 3 ايام"), (10080, "بعد 1 اسبوع")],
]

def _build_single_back_keyboard(text: str, callback_data: str, style: str, emoji_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text, callback_data=callback_data,
            style=style, **emoji_kwargs(emoji_key),
        )],
    ])


def build_text_with_emojis(parts) -> tuple:
    """
    تقوم ببناء النص والكيانات (entities) لدعم التنسيقات المتداخلة:
    - كيان CUSTOM_EMOJI للإيموجيات المخصصة.
    - كيان TEXT_MENTION للإشارة إلى مستخدم (عبر user object).
    - كيان TEXT_LINK لإنشاء اسم أزرق قابل للضغط (باستخدام tg://user?id=).
    - كيان BOLD للخط العريض.
    - كيان BLOCKQUOTE للاقتباس الجانبي مع علامة ”.
    جميع الكيانات يمكن دمجها داخل بعضها (مثلاً اسم أزرق داخل اقتباس).
    """
    text = ""
    entities = []

    def add_bold(start_offset: int, end_offset: int):
        """إضافة كيان عريض للنص مع الحفاظ على الكيانات المتداخلة."""
        if end_offset > start_offset:
            entities.append(MessageEntity(
                type=MessageEntity.BOLD,
                offset=start_offset,
                length=end_offset - start_offset,
            ))

    def append_text(value: str, make_bold: bool = True):
        nonlocal text
        start_offset = len(text.encode("utf-16-le")) // 2
        text += str(value)
        end_offset = len(text.encode("utf-16-le")) // 2
        if make_bold:
            add_bold(start_offset, end_offset)

    def process_part(p, inside_bold: bool = False):
        nonlocal text, entities
        if isinstance(p, tuple):
            if len(p) == 3 and p[1] == "mention":
                display_name, _, user_obj = p
                offset = len(text.encode("utf-16-le")) // 2
                length = len(display_name.encode("utf-16-le")) // 2
                entities.append(MessageEntity(type=MessageEntity.TEXT_MENTION, offset=offset, length=length, user=user_obj))
                text += display_name
                if not inside_bold:
                    add_bold(offset, offset + length)
            elif len(p) == 3 and p[1] == "mention_id":
                display_name, _, user_id = p
                offset = len(text.encode("utf-16-le")) // 2
                length = len(display_name.encode("utf-16-le")) // 2
                entities.append(MessageEntity(type=MessageEntity.TEXT_LINK, offset=offset, length=length, url=f"tg://user?id={user_id}"))
                text += display_name
                if not inside_bold:
                    add_bold(offset, offset + length)
            elif len(p) == 2:
                placeholder, custom_emoji_id = p
                offset = len(text.encode("utf-16-le")) // 2
                length = len(placeholder.encode("utf-16-le")) // 2
                entities.append(MessageEntity(type=MessageEntity.CUSTOM_EMOJI, offset=offset, length=length, custom_emoji_id=custom_emoji_id))
                text += placeholder
            elif len(p) == 3 and p[1] in ["bold", "blockquote", "italic", "spoiler"]:
                content, ent_type, _ = p
                start_offset = len(text.encode("utf-16-le")) // 2
                if isinstance(content, list):
                    for sub in content:
                        process_part(sub, inside_bold or ent_type == "bold")
                else:
                    append_text(content, make_bold=inside_bold or ent_type != "bold")
                end_offset = len(text.encode("utf-16-le")) // 2
                length = end_offset - start_offset
                t_type = {
                    "bold": MessageEntity.BOLD,
                    "blockquote": MessageEntity.BLOCKQUOTE,
                    "italic": MessageEntity.ITALIC,
                    "spoiler": MessageEntity.SPOILER,
                }[ent_type]
                entities.append(MessageEntity(type=t_type, offset=start_offset, length=length))
            elif len(p) == 3 and p[1] == "link":
                content, _, url = p
                start_offset = len(text.encode("utf-16-le")) // 2
                if isinstance(content, list):
                    for sub in content:
                        process_part(sub, inside_bold)
                else:
                    append_text(content, make_bold=not inside_bold)
                end_offset = len(text.encode("utf-16-le")) // 2
                length = end_offset - start_offset
                entities.append(MessageEntity(type=MessageEntity.TEXT_LINK, offset=start_offset, length=length, url=url))
            else:
                append_text(p, make_bold=not inside_bold)
        else:
            append_text(p, make_bold=not inside_bold)

    for part in parts:
        process_part(part)

    return text, entities


def build_brand_giveaways_parts(prefix: str = "• "):
    """يبني جزء الجملة الموحّد: «BRAND_NAME < السحوبات» — يُستخدم في القائمة
    الرئيسية وفي منشورات السحوبات والمسابقات. اسم العلامة رابط أزرق يفتح
    {BRAND_URL}، وكلمة «السحوبات» رابط أزرق عريض يفتح {GIVEAWAYS_CHANNEL_URL}.
    كلا الرابطين يُنشئان معاينة رابط صغيرة تلقائيًا من تيليجرام (صورة القناة)."""
    parts = []
    if prefix:
        parts.append(prefix)
    parts.append((BRAND_NAME, "link", BRAND_URL))
    parts.append(" < ")
    parts.append((GIVEAWAYS_LINK_TEXT, "link", GIVEAWAYS_CHANNEL_URL))
    return parts


def bold_notice(message: str) -> tuple:
    """يبني رسالة تنبيه/تأكيد قصيرة بخط عريض — يُستخدم لتوحيد شكل رسائل النظام في البوت."""
    return build_text_with_emojis([([message], "bold", None)])


def emoji_kwargs(key: str) -> dict:
    value = EMOJI.get(key, "0")
    if value and value != "0":
        return {"icon_custom_emoji_id": value}
    return {}

def build_welcome_message(user) -> tuple:
    """
    رسالة الترحيب بالقائمة الرئيسية.

    كلمة VORTEX داخل الجملة الأولى رابط نصي أزرق قابل للضغط يفتح قناة
    العلامة (BRAND_URL)، وكلمة «السحوبات» رابط نصي أزرق قابل للضغط يفتح
    قناة السحوبات المحددة مسبقًا (GIVEAWAYS_CHANNEL_URL) — مدمجتان داخل
    نص الجملة نفسها بدل عرضهما كسطر منفصل («• ROULETTE VORTEX < السحوبات»)
    أعلى الجملتين. الجملتان قريبتان من بعضهما (سطر واحد بينهما) لتظهرا
    متلاصقتين كما في الصورة المرجعية.
    """
    user_name = user.first_name or user.username or "صديقنا"
    vortex_word = BRAND_NAME.split(" ", 1)[-1]  # "𝚅𝙾𝚁𝚃𝙴𝚇"
    parts = [
        ([
            ("👋", EMOJI["hand"]),
            " : أهلاً بك - ",
            (user_name, "mention", user),
            "\n\n",
            ([
                "روليت ", (vortex_word, "link", BRAND_URL),
                " لإنشاء ", (GIVEAWAYS_LINK_TEXT, "link", GIVEAWAYS_CHANNEL_URL),
                " والمسابقات والروليت السريع",
            ], "blockquote", None),
            "\n",
            ([
                "استمتع وابدأ الآن بالاختيار من القائمة أدناه ",
                ("⏬", EMOJI["arrow_down"]),
            ], "blockquote", None),
        ], "bold", None),
    ]
    return build_text_with_emojis(parts)


def build_terms_message() -> tuple:
    """
    رسالة «سياسة الاستخدام والخصوصية»:
    - كامل النص بخط عريض (Bold).
    - السطرين الأخيرين («أي مخالفة = حظر دائم» / «ثقتكم هي أولويتنا») داخل
      اقتباس وردي (Blockquote) منتهي بعلامة ”، تمامًا كما في الصورة المرفقة.
    """
    parts = [
        ([
            ("📜", EMOJI["doc"]),
            " : سياسة الاستخدام والخصوصية",
            "\n\n",
            "ثقتكم هي أولويتنا",
            "\n\n",
            "✅ : المسموح به:\n",
            "├ تنظيم سحوبات حقيقية وواضحة\n",
            "├ تقديم جوائز حقيقية وموثوقة\n",
            "└ احترام جميع المشاركين",
            "\n\n",
            "❌ : الممنوع:\n",
            "├ سحوبات وهمية أو مضللة\n",
            "├ خداع المستخدمين\n",
            "└ التلاعب بالنتائج",
            "\n\n",
            ([
                "🚨 : أي مخالفة = حظر دائم\n",
                "ثقتكم هي أولويتنا",
            ], "blockquote", None),
        ], "bold", None),
    ]
    return build_text_with_emojis(parts)


def build_terms_keyboard() -> InlineKeyboardMarkup:
    """كيبورد رسالة الشروط والأحكام: زر «رجوع» أحمر يعيد للقائمة الرئيسية."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "رجوع", callback_data="back_main_menu",
            style="danger", **emoji_kwargs("back_section_btn"),
        )],
    ])


def build_support_bot_message() -> tuple:
    """رسالة قائمة «دعم البوت» — نفس نص وتنسيق الصورة المرفقة."""
    parts = [
        ([
            ("⭐", EMOJI["star"]),
            " دعم البوت",
        ], "bold", None),
        "\n\n",
        f"ادفع {SUPPORT_BOT_STARS_AMOUNT} نجوم تيليجرام لدعم تطوير البوت 💖",
        "\n\n",
        "كل نجمة تساعدنا في الاستمرار وتطوير ميزات جديدة!",
        "\n\n",
        "👇 اضغط على الزر أدناه للدفع:",
    ]
    return build_text_with_emojis(parts)


def build_support_bot_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"ادفع {SUPPORT_BOT_STARS_AMOUNT} نجوم", callback_data="support_pay_stars",
            style="success", **emoji_kwargs("star"),
        )],
        [InlineKeyboardButton(
            "رجوع", callback_data="back_main_menu",
            style="danger", **emoji_kwargs("back_section_btn"),
        )],
    ])


def get_required_channel_username() -> str:
    """اسم يوزر قناة الاشتراك الإجباري الحالية (بدون @) — قابل للتغيير من قسم المالك."""
    return (get_setting("required_channel_username") or REQUIRED_CHANNEL_USERNAME).lstrip("@")


def get_required_channel_url() -> str:
    """رابط قناة الاشتراك الإجباري الحالية."""
    custom_url = get_setting("required_channel_url")
    if custom_url:
        return custom_url
    return f"https://t.me/{get_required_channel_username()}"


def get_required_channel_next_username() -> str:
    """اسم يوزر القناة التالية (بدون @) التي سيتم التحويل إليها تلقائيًا، أو فارغ إن لم تُحدَّد."""
    return (get_setting("required_channel_next_username") or "").lstrip("@")


def get_required_channel_auto_target() -> int:
    """عدد المشتركين المطلوب للتحويل التلقائي للقناة التالية."""
    raw = get_setting("required_channel_auto_target") or REQUIRED_CHANNEL_DEFAULT_TARGET
    try:
        return int(raw)
    except (TypeError, ValueError):
        return int(REQUIRED_CHANNEL_DEFAULT_TARGET)


def _normalize_channel_username(raw: str) -> str:
    """يستخرج اسم اليوزر من نص قد يكون @username أو t.me/username أو مجرد username."""
    value = (raw or "").strip()
    for prefix in ("https://t.me/", "http://t.me/", "t.me/", "@"):
        if value.lower().startswith(prefix):
            value = value[len(prefix):]
            break
    value = value.strip().strip("/")
    return value


def build_subscription_required_message() -> tuple:
    """رسالة تطلب من المستخدم الاشتراك في القناة قبل استخدام البوت."""
    parts = [
        "عليك الأشتراك في القناة اولاً",
        "\n",
        "- لتتمكن من أستخدام البوت : ",
        ("💻", EMOJI["sub_laptop"]),
        "\n",
        ([
            ("‼️", EMOJI["sub_alert"]),
            " | اشترك ثم اضغط تحقق",
            ("✅", EMOJI["sub_check"]),
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_subscription_required_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(REQUIRED_CHANNEL_BUTTON_TEXT, url=get_required_channel_url())],
        [InlineKeyboardButton("تحقق من الاشتراك", callback_data="check_sub_status")],
    ])


_SUBSCRIPTION_CACHE = {}
SUBSCRIPTION_CACHE_TTL = 60
SUBSCRIPTION_NEGATIVE_CACHE_TTL = 3


async def is_user_subscribed(
    context: ContextTypes.DEFAULT_TYPE, user_id: int, force_refresh: bool = False
) -> bool:
    """يتحقق مما إذا كان المستخدم عضوًا في قناة الاشتراك الإجباري، مع كاش مؤقت
    لكل مستخدم لتجنب نداء تليجرام (get_chat_member) في كل ضغطة/فتح رابط —
    وهو السبب الرئيسي لبطء رد الأزرار وتأخر ظهور الكابتشا بعد إعادة التوجيه."""
    cached = _SUBSCRIPTION_CACHE.get(user_id)
    if not force_refresh and cached is not None:
        age = time.time() - cached["ts"]
        ttl = SUBSCRIPTION_CACHE_TTL if cached["value"] else SUBSCRIPTION_NEGATIVE_CACHE_TTL
        if age < ttl:
            return cached["value"]
    channel_username = get_required_channel_username()
    result = False
    for attempt in range(2):
        try:
            member = await context.bot.get_chat_member(
                chat_id=f"@{channel_username}", user_id=user_id
            )
            result = (
                member.status in ("member", "administrator", "creator")
                or (member.status == "restricted" and bool(getattr(member, "is_member", False)))
            )
            break
        except RetryAfter as exc:
            if attempt == 0 and exc.retry_after <= 5:
                logger.warning(
                    "تيليجرام حدّد عدد الطلبات أثناء التحقق من اشتراك %s في @%s — "
                    "إعادة محاولة واحدة بعد %s ثانية بدل رفض المستخدم فورًا",
                    user_id, channel_username, exc.retry_after,
                )
                await asyncio.sleep(exc.retry_after)
                continue
            logger.warning(
                "تيليجرام حدّد عدد الطلبات أثناء التحقق من اشتراك %s في @%s "
                "(retry_after=%s) — تعذّر إعادة المحاولة الآن، سيُعامَل كغير مشترك مؤقتًا",
                user_id, channel_username, exc.retry_after,
            )
            result = False
            break
        except Exception:
            logger.exception(
                "تعذّر التحقق من اشتراك المستخدم %s في القناة @%s",
                user_id, channel_username,
            )
            result = False
            break
    _SUBSCRIPTION_CACHE[user_id] = {"value": result, "ts": time.time()}
    return result


_GW_CONDITION_SUB_CACHE = {}


async def is_user_subscribed_to_chat(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    chat_ref,
    force_refresh: bool = False,
) -> bool:
    """يتحقق من اشتراك المستخدم في أي قناة يتم تمريرها (chat_ref: يوزر بصيغة
    "@username" أو معرّف الشات الرقمي)، بنفس منطق/كاش is_user_subscribed لكن
    لقنوات «شرط السحب» الديناميكية بدل قناة الاشتراك الإجباري الثابتة. تُستخدم
    هذه الدالة للتحقق الداخلي دون تحويل المستخدم لأي بوت آخر."""
    cache_key = (user_id, str(chat_ref))
    cached = _GW_CONDITION_SUB_CACHE.get(cache_key)
    if not force_refresh and cached is not None:
        age = time.time() - cached["ts"]
        ttl = SUBSCRIPTION_CACHE_TTL if cached["value"] else SUBSCRIPTION_NEGATIVE_CACHE_TTL
        if age < ttl:
            return cached["value"]

    result = False
    for attempt in range(2):
        try:
            member = await context.bot.get_chat_member(chat_id=chat_ref, user_id=user_id)
            result = (
                member.status in ("member", "administrator", "creator")
                or (member.status == "restricted" and bool(getattr(member, "is_member", False)))
            )
            break
        except RetryAfter as exc:
            if attempt == 0 and exc.retry_after <= 5:
                await asyncio.sleep(exc.retry_after)
                continue
            result = False
            break
        except Exception:
            logger.exception(
                "تعذّر التحقق من اشتراك المستخدم %s في قناة الشرط %s", user_id, chat_ref,
            )
            result = False
            break
    _GW_CONDITION_SUB_CACHE[cache_key] = {"value": result, "ts": time.time()}
    return result


async def check_giveaway_condition_channels(
    context: ContextTypes.DEFAULT_TYPE, user_id: int, giveaway,
) -> bool:
    """يتحقق من اشتراك المستخدم في جميع قنوات شرط السحب (واحدة أو قناتين).
    يُعيد True فقط إذا لم توجد قنوات شرط أصلاً، أو كان مشتركًا في جميعها."""
    channels = giveaway.get("condition_channels") or []
    for channel in channels:
        ref = channel.get("ref")
        if not ref:
            continue
        if not await is_user_subscribed_to_chat(context, user_id, ref):
            return False
    return True


async def check_giveaway_boost(
    context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int,
) -> bool:
    """يتحقق مما إذا كان المستخدم قد عزّز (Boost) قناة السحب فعليًا، عبر
    استدعاء getUserChatBoosts الأصلي في تيليجرام (يُستخدم عند تفعيل خيار
    «تعزيز القناة» — Image A1/A2). يُعيد True فقط إذا كانت لدى المستخدم
    تعزيزة واحدة على الأقل مسجّلة على هذه القناة تحديدًا (Image A4/A5)."""
    try:
        result = await context.bot.get_user_chat_boosts(chat_id=chat_id, user_id=user_id)
        return bool(result.boosts)
    except Exception:
        logger.exception(
            "تعذّر التحقق من تعزيز المستخدم %s للقناة %s", user_id, chat_id,
        )
        return False


async def check_giveaway_requirements(context: ContextTypes.DEFAULT_TYPE, user, giveaway) -> tuple:
    """يتحقق من جميع شروط الدخول في السحب (بريميوم / قنوات الاشتراك / تعزيز /
    تصويت لمتسابق) بترتيب واحد موحّد، ويُستخدم في كل نقاط الدخول (زر المشاركة
    المباشر، بوابة الاشتراك قبل الكابتشا، والتحقق النهائي بعد الكابتشا) حتى لا
    تتكرر نفس الشروط بصيغ مختلفة في أكثر من مكان.
    يُعيد (True, "") عند اجتياز كل الشروط، أو (False, نص التنبيه المناسب لأول شرط لم يتحقق)."""
    if giveaway.get("premium_only") and not user.is_premium:
        return False, "💎 هذا السحب للأشخاص المفعلين مميز فقط!"

    if not await check_giveaway_condition_channels(context, user.id, giveaway):
        return False, build_giveaway_condition_subscribe_alert()

    if giveaway.get("boost_required") and not await check_giveaway_boost(
        context, user.id, giveaway["chat_id"],
    ):
        return False, "❌ يجب عليك تعزيز القناة اولا"

    vote_contest_code = giveaway.get("vote_contest_code")
    vote_participant_id = giveaway.get("vote_participant_id")
    if vote_contest_code and vote_participant_id and not has_voted_for(
        vote_contest_code, user.id, vote_participant_id,
    ):
        return False, "❌ يجب عليك التصويت للمتسابق أولاً قبل المشاركة في السحب"

    return True, ""


async def build_giveaway_gate_links(context: ContextTypes.DEFAULT_TYPE, giveaway) -> tuple:
    """يبني رابط التعزيز (إن كان السحب يتطلب Boost) ورابط التصويت (إن كان
    مشروطًا بالتصويت لمتسابق)، لعرضهما كأزرار داخل بوابة شروط السحب."""
    boost_link = (
        await build_giveaway_boost_link(context, giveaway["chat_id"])
        if giveaway.get("boost_required") else ""
    )
    vote_contest_code = giveaway.get("vote_contest_code")
    vote_participant_id = giveaway.get("vote_participant_id")
    vote_link = (
        build_giveaway_vote_condition_link(vote_contest_code, vote_participant_id)
        if vote_contest_code and vote_participant_id else ""
    )
    return boost_link, vote_link


async def _check_bot_can_verify_channel(context: ContextTypes.DEFAULT_TYPE, username: str) -> str:
    """يتحقق من أن البوت نفسه مُضاف كمشرف (Admin) في قناة الاشتراك الإجباري
    الجديدة. هذا شرط ضروري لعمل get_chat_member بشكل صحيح — إن لم يكن البوت
    مشرفًا هناك، ستفشل عملية التحقق من الاشتراك لكل المستخدمين (حتى المشتركين
    الحقيقيين فعليًا)، وهو ما يظهر للمستخدم كخطأ "لم يتم العثور على اشتراكك"
    رغم أنه مشترك فعلاً. تُعيد نص تحذير جاهزًا للإرسال للمالكين، أو '' إن كان
    كل شيء سليمًا."""
    try:
        me = await context.bot.get_chat_member(chat_id=f"@{username}", user_id=context.bot.id)
    except Exception as exc:
        return (
            f"⚠️ تنبيه: تعذّر على البوت الوصول إلى @{username} ({exc}).\n"
            f"على الأغلب البوت غير مُضاف لهذه القناة إطلاقًا. أضِف البوت إليها كمشرف "
            f"(Admin) فورًا، وإلا فسيفشل التحقق من اشتراك جميع المستخدمين ويظهر لهم "
            f"خطأ «لم يتم العثور على اشتراكك» حتى لو كانوا مشتركين بالفعل."
        )
    if me.status not in ("administrator", "creator"):
        return (
            f"⚠️ تنبيه: البوت عضو في @{username} لكنه ليس مشرفًا (Admin) فيها.\n"
            f"يجب ترقية البوت إلى مشرف في هذه القناة الآن، وإلا فسيفشل التحقق من "
            f"اشتراك جميع المستخدمين ويظهر لهم خطأ «لم يتم العثور على اشتراكك» حتى "
            f"لو كانوا مشتركين بالفعل."
        )
    return ""


async def check_required_channel_auto_switch(context: ContextTypes.DEFAULT_TYPE):
    """
    مهمة دورية: تتحقق من عدد مشتركي قناة الاشتراك الإجباري الحالية، وإن وصلت
    (أو تجاوزت) العدد المطلوب وكانت هناك قناة تالية محددة من المالك، يتم تبديل
    قناة الاشتراك الإجباري تلقائيًا إليها. إن لم تُحدَّد قناة تالية فلا يحدث أي
    تغيير أبدًا مهما بلغ عدد المشتركين.
    """
    next_username = get_required_channel_next_username()
    if not next_username:
        return

    target = get_required_channel_auto_target()
    current_username = get_required_channel_username()
    try:
        count = await context.bot.get_chat_member_count(chat_id=f"@{current_username}")
    except Exception:
        logger.exception(
            "تعذّر جلب عدد مشتركي قناة الاشتراك الإجباري @%s للتحقق من التغيير التلقائي",
            current_username,
        )
        return

    if count < target:
        return

    set_setting("required_channel_username", next_username)
    set_setting("required_channel_url", f"https://t.me/{next_username}")
    set_setting("required_channel_next_username", "")
    _SUBSCRIPTION_CACHE.clear()
    logger.info(
        "تم تغيير قناة الاشتراك الإجباري تلقائيًا من @%s إلى @%s بعد وصول عدد المشتركين إلى %s",
        current_username, next_username, count,
    )
    warning = await _check_bot_can_verify_channel(context, next_username)
    for owner_id in OWNER_IDS:
        try:
            await context.bot.send_message(
                chat_id=owner_id,
                text=(
                    f"✅ تم تغيير قناة الاشتراك الإجباري تلقائيًا\n"
                    f"من: @{current_username}\n"
                    f"إلى: @{next_username}\n"
                    f"(بعد وصولها إلى {count} مشترك)"
                    + (f"\n\n{warning}" if warning else "")
                ),
            )
        except Exception:
            pass


def build_contest_section_message() -> tuple:
    """
    رسالة قسم إنشاء المسابقات:
    - العنوان بخط عريض (Bold) + إيموجي الكأس.
    - سطر التوجيه داخل اقتباس وردي (Blockquote) منتهي بعلامة ” + إيموجي السهم.
    """
    parts = [
        ([
            ("🏆", EMOJI["trophy_create_draw"]),
            " قسم إنشاء المسابقات",
        ], "bold", None),
        "\n\n",
        ([
            "• اختر ما تريدمن القائمة أدناه ",
            ("⏬", EMOJI["arrow_down"]),
            "  ”",
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_contest_section_keyboard() -> InlineKeyboardMarkup:
    """
    كيبورد قسم إنشاء المسابقات بنفس ألوان الصورة:
    - أخضر (success) لزر «انشاء مسابقة».
    - أزرق/سماوي (primary) لزري «تسجيل قروب» و«تسجيل قناة».
    - أحمر (danger) لزر «رجوع».
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "انشاء مسابقة", callback_data="comp_start_create",
            style="success", **emoji_kwargs("trophy_contest"),
        )],
        [
            InlineKeyboardButton(
                "تسجيل قروب", callback_data="comp_reg_group",
                style="primary", **emoji_kwargs("register_plus"),
            ),
            InlineKeyboardButton(
                "تسجيل قناة", callback_data="comp_reg_channel",
                style="primary", **emoji_kwargs("register_plus"),
            ),
        ],
        [InlineKeyboardButton(
            "المسابقات الحديثة", callback_data="comp_recent",
            style="primary", **emoji_kwargs("recent_contests_btn"),
        )],
        [InlineKeyboardButton(
            "رجوع", callback_data="back_main_menu",
            style="danger", **emoji_kwargs("back_section_btn"),
        )],
    ])


def build_contest_target_message() -> tuple:
    """
    شاشة «يرجى تحديد القناة أو القروب لـ المسابقة»:
    - العنوان بخط عريض (Bold) + إيموجي الهدف.
    - الجملتين التوجيهيتين داخل اقتباس وردي (Blockquote) — نفس نظام التلوين
      المستخدم سابقًا (تليجرام بيرسم كيان الـ blockquote بلون وردي/أحمر فاتح تلقائيًا
      مع علامة ” الجانبية، فهو نفس اللون المطلوب).
    """
    parts = [
        ([
            "يرجى تحديد القناة أو القروب لـ المسابقة ",
            ("🎯", EMOJI["target_pin"]),
        ], "bold", None),
        "\n\n",
        ([
            "تأكد أولا انك مشرف في القناة او القروب وان البوت أيضا مشرف",
        ], "blockquote", None),
        "\n\n",
        ([
            "إذا لم تظهر القناة أو الجروب وتأكدت ان البوت بها كمشرف وأنت كمشرف إذا يمكنك تسجيله يدويا من الأسفل",
            ("⏬", EMOJI["arrow_down"]),
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_contest_target_keyboard(owner_id: int = None) -> InlineKeyboardMarkup:
    """
    كيبورد شاشة تحديد القناة/القروب:
    - زر شفاف (بدون لون/بدون إيموجي) لكل قناة أو جروب تمت إضافة البوت كمشرف
      فيه لنفس صاحب الطلب — يظهر تلقائيًا فوق صف التسجيل، تمامًا مثل شكل
      الزر الشفاف في الصورة المرفقة.
    - أزرق/سماوي (primary) لزري «تسجيل قروب» و«تسجيل قناة» بجانب بعض.
    - أحمر (danger) لزر «رجوع» اللي بيرجّع لقسم إنشاء المسابقات.
    """
    rows = []

    if owner_id is not None:
        for chat in get_registered_chats(owner_id):
            title = chat["chat_title"] or str(chat["chat_id"])
            rows.append([InlineKeyboardButton(
                title, callback_data=f"comp_pick_chat_{chat['chat_id']}",
            )])

    rows.append([
        InlineKeyboardButton(
            "تسجيل قروب", callback_data="comp_reg_group",
            style="primary", **emoji_kwargs("register_plus"),
        ),
        InlineKeyboardButton(
            "تسجيل قناة", callback_data="comp_reg_channel",
            style="primary", **emoji_kwargs("register_plus"),
        ),
    ])
    rows.append([InlineKeyboardButton(
        "رجوع", callback_data="section_competition",
        style="danger", **emoji_kwargs("back_section_btn"),
    )])
    return InlineKeyboardMarkup(rows)


def build_back_to_competition_keyboard() -> InlineKeyboardMarkup:
    """كيبورد موحّد لزر «رجوع» اللي بيرجّع لقسم إنشاء المسابقات."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "رجوع", callback_data="section_competition",
            style="danger", **emoji_kwargs("back_section_btn"),
        )],
    ])


def build_recent_contests_list_message() -> tuple:
    """شاشة اختيار القناة عند وجود أكثر من مسابقة جارية."""
    parts = [
        ([
            "📢 اختر القناة التي تريد التعديل على مسابقتها :",
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_recent_contests_list_keyboard(contests) -> InlineKeyboardMarkup:
    """أزرار شفافة (بدون لون/إيموجي مخصص) بعدد المسابقات الجارية، باسم كل قناة."""
    rows = []
    for c in contests:
        title = get_chat_title_by_id(c["chat_id"])
        rows.append([InlineKeyboardButton(
            f"📢 {title}", callback_data=f"comp_detail:{c['contest_code']}",
        )])
    rows.append([InlineKeyboardButton(
        "رجوع", callback_data="section_competition",
        style="danger", **emoji_kwargs("back_section_btn"),
    )])
    return InlineKeyboardMarkup(rows)


def build_contest_detail_message(contest, channel_title: str, post_link, participants_count: int) -> tuple:
    """شاشة إعدادات مسابقة واحدة — تطابق تنسيق الصورة المرفقة."""
    name = contest_display_name(contest)
    status_line = "🟢 نشطة" if contest["status"] == "open" else "🔴 متوقفة"

    def flag(value):
        return ("✅", EMOJI["check_flag_on"]) if value else ("❌", EMOJI["cross_flag_off"])

    channel_line = ["📢 القناة : ", channel_title, " | "]
    if post_link:
        channel_line.append(("رابط منشور المسابقة", "link", post_link))
    else:
        channel_line.append("رابط منشور المسابقة")

    parts = [
        ([
            "📋 المسابقة :\n",
            name,
            "\n\n",
            *channel_line,
            "\n\n",
            f"📊 الحالة : {status_line}",
            "\n\n",
            f"👥 المتسابقون : {participants_count} / {contest['target_count']}",
            "\n\n",
            "⚙️ إعدادات المسابقة :",
            "\n\n",
            "🔔 تنبيه الفوز | ", flag(contest["notify_win"]), "\n",
            "📣 إعلان النتائج | ", flag(contest["announce_results"]), "\n",
            "🧩 موافقة المشاركات | ", flag(contest["approve_participants"]), "\n",
            "💎 تصويت بريميوم | ", flag(contest["premium_only"]),
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_contest_detail_keyboard(contest) -> InlineKeyboardMarkup:
    code = contest["contest_code"]
    toggle_label = "⏸ إيقاف المسابقة" if contest["status"] == "open" else "▶️ استئناف المسابقة"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "تغيير عدد المقاعد", callback_data=f"comp_change_seats:{code}",
            style="primary", **emoji_kwargs("seats_change_btn"),
        )],
        [InlineKeyboardButton(
            toggle_label, callback_data=f"comp_toggle_active:{code}",
            style="primary", **emoji_kwargs("pause_toggle_btn"),
        )],
        [InlineKeyboardButton(
            "تغيير إعدادات المسابقة", callback_data=f"comp_edit_settings:{code}",
            style="primary", **emoji_kwargs("edit_settings_refresh_btn"),
        )],
        [InlineKeyboardButton(
            "إزالة متسابق", callback_data=f"comp_remove_contestant:{code}",
            style="danger", **emoji_kwargs("remove_contestant_btn"),
        )],
        [InlineKeyboardButton(
            "حذف المسابقة بالكامل", callback_data=f"comp_delete_all:{code}",
            style="danger", **emoji_kwargs("delete_all_btn"),
        )],
        [InlineKeyboardButton(
            "رجوع", callback_data="section_competition",
            style="danger", **emoji_kwargs("back_section_btn"),
        )],
    ])


def build_channel_registration_message() -> tuple:
    """

    شاشة «لـ اضافة قناة اتبع الخطوات التالية»:
    - العنوان الرئيسي وعنوان «ملاحظة» بخط عريض (Bold).
    - الخطوتين بأرقام مخصصة (1️⃣ / 2️⃣) كنص عادي.
    - جملة الملاحظة داخل اقتباس وردي (Blockquote) منتهية بعلامة ”.
    """
    parts = [
        ("لـ اضافة قناة اتبع الخطوات التالية:", "bold", None),
        "\n\n",
        ("1️⃣", EMOJI["num_one"]),
        f"أضف البوت @{BOT_USERNAME} كمشرف في قناتك.",
        "\n\n",
        ("2️⃣", EMOJI["num_two"]),
        "قم بإعادة توجيه أي رسالة من قناتك إلى البوت",
        "\n\n",
        ([("📌", EMOJI["pin_note"]), "ملاحظة:"], "bold", None),
        "\n",
        ([
            "جميع المشرفين الآخرين في القناة سيتمكنون أيضًا من استخدام البوت بعد إضافته  ”",
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_group_registration_message() -> tuple:
    """
    شاشة «لـ اضافة جروب اتبع الخطوات التالية»:
    - العنوان الرئيسي بخط عريض (Bold).
    - الخطوتين بأرقام مخصصة (1️⃣ / 2️⃣) كنص عادي.
    """
    parts = [
        ("لـ اضافة جروب اتبع الخطوات التالية:", "bold", None),
        "\n\n",
        ("1️⃣", EMOJI["num_one"]),
        f"أضف البوت @{BOT_USERNAME} كمشرف في الجروب الخاص بك",
        "\n\n",
        ("2️⃣", EMOJI["num_two"]),
        "إذهب للجروب الخاص بك بعد إضافة البوت و اكتب ",
        ("◀️", EMOJI["arrow_left"]),
        "تفعيل روليت",
    ]
    return build_text_with_emojis(parts)


def build_contest_cliche_message() -> tuple:
    """
    شاشة «أرسل كليشة المسابقة»:
    - العنوان بخط عريض (Bold) + إيموجي الظرف.
    - أمثلة توضيحية فعلية لتنسيقات تيليجرام (عريض/مائل/مشوش/رابط).
    - سطر ختامي داخل اقتباس وردي (Blockquote) بعلامة ” كنموذج «نص مقتبس».
    """
    parts = [
        ([
            ("📨", EMOJI["envelope_klesha"]),
            " أرسل كليشة المسابقة",
        ], "bold", None),
        "\n\n",
        "اكتب نص المسابقة الذي تريد نشره في القناة.\n"
        "يمكنك استخدام تنسيقات تيليجرام، مثل:\n",
        "• ", ("نص عريض", "bold", None), "\n",
        "• ", ("نص مائل", "italic", None), "\n",
        "• ", ("نص مشوش", "spoiler", None), "\n",
        ([("🆕", EMOJI["new_badge"]), " يمكنك وضع رابط داخل النص"], "link", "https://t.me"),
        "\n",
        (["نص مقتبس  ”"], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_contest_cliche_keyboard() -> InlineKeyboardMarkup:
    return _build_single_back_keyboard("رجوع", "comp_start_create", "danger", "back_section_btn")


def build_contest_count_message() -> tuple:
    """شاشة «أرسل عدد المتسابقين المطلوب 🎯:» — عنوان واحد بخط عريض."""
    parts = [
        ([
            "أرسل عدد المتسابقين المطلوب ",
            ("🎯", EMOJI["target_pin"]),
            ":",
        ], "bold", None),
    ]
    return build_text_with_emojis(parts)


def build_contest_count_keyboard() -> InlineKeyboardMarkup:
    return _build_single_back_keyboard("رجوع", "comp_back_to_klesha", "danger", "back_section_btn")


def build_contest_end_method_message() -> tuple:
    """
    شاشة «اختر طريقة انتهاء المسابقة»:
    - العنوان بخط عريض.
    - كل خيار داخل اقتباس وردي (Blockquote) منفصل.
    """
    parts = [
        ([" اختر طريقة انتهاء المسابقة:", ("❓", EMOJI["end_question"])], "bold", None),
        "\n\n",
        ([
            ("🎯", EMOJI["target_pin"]),
            "   عدد اصوات محدده: تنتهي المسابقة عند وصول المتسابقين عدد الاصوات الذي تحددها",
        ], "blockquote", None),
        "\n\n",
        ([
            ("⏰", EMOJI["alarm_clock"]),
            "   وقت محدد : تنتهي المسابقة تلقائياً عند انقضاء الوقت الذي تحدده ويفوز صاحب الاصوات الأعلى",
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_contest_end_method_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "عدد اصوات محدده", callback_data="comp_end_votes",
                style="primary", **emoji_kwargs("votes_chart_btn"),
            ),
            InlineKeyboardButton(
                "وقت محدد", callback_data="comp_end_time",
                style="primary", **emoji_kwargs("alarm_clock_btn"),
            ),
        ],
        [InlineKeyboardButton(
            "رجوع", callback_data="comp_back_to_count",
            style="danger", **emoji_kwargs("back_section_btn"),
        )],
    ])


def build_contest_time_menu_message(selected_label: str = "غير محدد") -> tuple:
    """
    شاشة «⏰ وقت محدد للمسابقة»:
    - العنوان بخط عريض (Bold) + إيموجي الساعة.
    - القيمة الحالية في سطر مستقل.
    - جملة التوجيه.
    """
    parts = [
        ([
            ("⏰", EMOJI["alarm_clock_title"]),
            "وقت محدد للمسابقة",
        ], "bold", None),
        f"\nالوقت المختار: {selected_label}",
        "\n\n",
        "استخدم الأزرار أدناه لتحديد الوقت المطلوب لانتهاء المسابقة تلقائياً:",
    ]
    return build_text_with_emojis(parts)


def build_contest_time_menu_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for row in CONTEST_TIME_OPTIONS:
        rows.append([
            InlineKeyboardButton(
                label, callback_data=f"comp_atime_set_{minutes}",
                style="primary", **emoji_kwargs("time_option_btn"),
            )
            for minutes, label in row
        ])
    rows.append([
        InlineKeyboardButton(
            "وقت مخصص", callback_data="comp_atime_show_custom",
            style="primary", **emoji_kwargs("time_manual_btn"),
        ),
    ])
    rows.append([
        InlineKeyboardButton(
            "رجوع", callback_data="comp_back_to_end_type",
            style="danger", **emoji_kwargs("back_time_menu_btn"),
        )
    ])
    return InlineKeyboardMarkup(rows)


CONTEST_TIME_CUSTOM_STEPS = [
    [(-1, "- 1 دقيقة"), (1, "+ 1 دقيقة")],
    [(-5, "- 5 دقيقة"), (5, "+ 5 دقيقة")],
    [(-10, "- 10 دقايق"), (10, "+ 10 دقايق")],
    [(-60, "- 1 ساعة"), (60, "+ 1 ساعة")],
    [(-1440, "- 1 يوم"), (1440, "+ 1 يوم")],
]


def build_contest_time_custom_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for row in CONTEST_TIME_CUSTOM_STEPS:
        rows.append([
            InlineKeyboardButton(
                label, callback_data=f"comp_atime_custom_delta:{delta}",
                style="primary", **emoji_kwargs("time_option_btn"),
            )
            for delta, label in row
        ])
    rows.append([InlineKeyboardButton(
        "تأكيد الوقت", callback_data="comp_atime_custom_confirm",
        style="success", **emoji_kwargs("yes_btn"),
    )])
    rows.append([
        InlineKeyboardButton(
            "إعادة تعيين", callback_data="comp_atime_custom_reset",
            style="success", **emoji_kwargs("restore_defaults_btn"),
        ),
        InlineKeyboardButton(
            "رجوع للخيارات", callback_data="comp_back_to_end_type",
            style="danger", **emoji_kwargs("back_section_btn"),
        ),
    ])
    return InlineKeyboardMarkup(rows)


def build_contest_votes_target_message() -> tuple:
    """شاشة «أرسل عدد الأصوات المطلوب» لتفعيل إنهاء المسابقة تلقائيًا عند وصول
    أحد المتسابقين لعدد الأصوات المحدد."""
    parts = [
        ([
            ("🎯", EMOJI["votes_chart_btn"]), " عدد أصوات محدد",
        ], "bold", None),
        "\n\n",
        "أرسل عدد الأصوات المطلوب لإنهاء المسابقة تلقائيًا عند وصول أحد المتسابقين إليه",
        "\n\n",
        ([
            "مثال: إذا أردت إنهاء المسابقة عند وصول أحد المتسابقين إلى 100 صوت "
            "أرسل الرقم 100",
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_contest_votes_target_keyboard() -> InlineKeyboardMarkup:
    return _build_single_back_keyboard("رجوع", "comp_back_to_end_type", "danger", "back_section_btn")


def build_contest_winners_message() -> tuple:
    """شاشة «أرسل عدد الفائزين المطلوب 🏆:»."""
    parts = [
        ([
            "أرسل عدد الفائزين المطلوب ",
            ("🏆", EMOJI["trophy_winners_title"]),
            ":",
        ], "bold", None),
    ]
    return build_text_with_emojis(parts)


def build_contest_winners_keyboard() -> InlineKeyboardMarkup:
    return _build_single_back_keyboard("رجوع", "comp_back_to_end_type", "danger", "back_winners_btn")


def build_contest_winners_confirm_message() -> tuple:
    """رسالة تأكيد «✅ تم تحديد عدد الفائزين» — تُرسل قبل شاشة إعدادات المسابقة."""
    parts = [
        ([
            ("✅", EMOJI["confirm_check"]),
            " تم تحديد عدد الفائزين",
        ], "bold", None),
    ]
    return build_text_with_emojis(parts)


CONTEST_SETTINGS_DEFAULTS = {
    "contest_notify_win": False,
    "contest_announce_results": False,
    "contest_approve_participants": True,
    "contest_premium_only": False,
}


def build_contest_settings_message() -> tuple:
    """
    شاشة «• اعدادات المسابقة الحالية:»:
    - عنوان بخط عريض.
    - كل إعداد: تسمية بخط عريض + شرح عادي.
    - سطر ختامي داخل اقتباس وردي (Blockquote).
    """
    parts = [
        (["• اعدادات المسابقة الحالية:"], "bold", None),
        "\n\n",
        (["- تنبيه الفوز"], "bold", None),
        " : ارسال اشعار تلقائي عند فوز احد المتسابقين",
        "\n\n",
        (["- اعلان النتائج"], "bold", None),
        " : اعلان نتائج المتسابقين وعدد اصواتهم",
        "\n\n",
        (["- موافقة المشاركات"], "bold", None),
        " : نشر أسماء المشاركين تلقائيا أو مراجعتها قبل الموافقة",
        "\n\n",
        (["- اصوات لـ المميزين"], "bold", None),
        " : التصويت متاحا فقط لمستخدمي تيليجرام المميز Premium.",
        "\n\n",
        ([
            ("✅", EMOJI["confirm_check"]),
            " الميزات المفعّلة تظهر بعلامة  ”",
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_contest_settings_keyboard(user_data: dict) -> InlineKeyboardMarkup:
    def yn_button(flag: bool, callback_data: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            "نعم" if flag else "لا",
            callback_data=callback_data,
            style="success" if flag else "danger",
            **emoji_kwargs("yes_btn" if flag else "no_btn"),
        )

    notify = user_data.get("contest_notify_win", CONTEST_SETTINGS_DEFAULTS["contest_notify_win"])
    announce = user_data.get("contest_announce_results", CONTEST_SETTINGS_DEFAULTS["contest_announce_results"])
    approve = user_data.get("contest_approve_participants", CONTEST_SETTINGS_DEFAULTS["contest_approve_participants"])
    premium = user_data.get("contest_premium_only", CONTEST_SETTINGS_DEFAULTS["contest_premium_only"])

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("تنبيه الفوز", callback_data="comp_toggle_notify_win",
                                  style="primary", **emoji_kwargs("notify_win_btn")),
            yn_button(notify, "comp_toggle_notify_win"),
        ],
        [
            InlineKeyboardButton("اعلان النتائج", callback_data="comp_toggle_announce_results",
                                  style="primary", **emoji_kwargs("announce_results_btn")),
            yn_button(announce, "comp_toggle_announce_results"),
        ],
        [
            InlineKeyboardButton("موافقة المشاركات", callback_data="comp_toggle_approve_participants",
                                  style="primary", **emoji_kwargs("approve_participants_label_btn")),
            yn_button(approve, "comp_toggle_approve_participants"),
        ],
        [
            InlineKeyboardButton("تصويت بريميوم", callback_data="comp_toggle_premium_only",
                                  style="primary", **emoji_kwargs("premium_vote_btn")),
            yn_button(premium, "comp_toggle_premium_only"),
        ],
        [InlineKeyboardButton(
            "نشر المسابقة", callback_data="comp_publish",
            style="primary", **emoji_kwargs("publish_btn"),
        )],
        [InlineKeyboardButton(
            "رجوع", callback_data="comp_back_to_winners",
            style="danger", **emoji_kwargs("back_section_btn"),
        )],
    ])


def build_publish_success_message() -> tuple:
    """رسالة «✅ تم نشر المسابقة بنجاح!» — تحل محل قائمة الإعدادات فورًا عند الضغط على نشر."""
    parts = [
        (["✅ تم نشر المسابقة بنجاح !"], "bold", None),
    ]
    return build_text_with_emojis(parts)


def format_minutes_label(minutes: int) -> str:
    """يحوّل عدد الدقائق إلى تسمية عربية مقروءة (يوم/ساعة/دقيقة)."""
    if minutes >= 1440 and minutes % 1440 == 0:
        days = minutes // 1440
        if days == 1:
            return "يوم واحد"
        if days == 2:
            return "يومين"
        if days <= 10:
            return f"{days} أيام"
        return f"{days} يوم"
    if minutes >= 60 and minutes % 60 == 0:
        hours = minutes // 60
        if hours == 1:
            return "ساعة واحدة"
        if hours == 2:
            return "ساعتين"
        if hours <= 10:
            return f"{hours} ساعات"
        return f"{hours} ساعة"
    if minutes == 1:
        return "دقيقة واحدة"
    if minutes == 2:
        return "دقيقتين"
    if minutes <= 10:
        return f"{minutes} دقائق"
    return f"{minutes} دقيقة"


def _duration_unit_label(n: int, one: str, two: str, few: str, many: str) -> str:
    """صيغة عربية مختصرة لوحدة زمنية ضمن تسمية مركّبة (يوم/ساعة/دقيقة معًا) —
    بدون «واحد/واحدة» كي لا تتكرر عبر كل وحدة (مثال: «يوم و ساعة و 11 دقيقة»)."""
    if n == 1:
        return one
    if n == 2:
        return two
    if n <= 10:
        return f"{n} {few}"
    return f"{n} {many}"


def format_duration_label(total_minutes) -> str:
    """يحوّل عدد الدقائق المتراكم (من قائمة «وقت مخصص» التراكمية) إلى تسمية عربية
    مقروءة. عند وجود وحدة واحدة فقط (مثلاً 60 دقيقة بالضبط) تُستخدم نفس صيغة
    format_minutes_label الكاملة («ساعة واحدة»)، وعند تركيب أكثر من وحدة تُستخدم
    صيغة مختصرة متسلسلة بـ«و» (مثال: «يوم و ساعة و 11 دقيقة»)، مطابقةً لتصميم
    قائمة «وقت مخصص» (Image 7/8)."""
    if not total_minutes or total_minutes <= 0:
        return "غير محدد"
    total_minutes = int(total_minutes)
    days, rem = divmod(total_minutes, 1440)
    hours, minutes = divmod(rem, 60)
    units_present = sum(1 for x in (days, hours, minutes) if x)
    if units_present <= 1:
        return format_minutes_label(total_minutes)
    parts = []
    if days:
        parts.append(_duration_unit_label(days, "يوم", "يومين", "أيام", "يوم"))
    if hours:
        parts.append(_duration_unit_label(hours, "ساعة", "ساعتين", "ساعات", "ساعة"))
    if minutes:
        parts.append(_duration_unit_label(minutes, "دقيقة", "دقيقتين", "دقائق", "دقيقة"))
    return " و ".join(parts)


def utf16_len(s: str) -> int:
    return len(s.encode("utf-16-le")) // 2


def shift_entities(entities, shift: int):
    shifted = []
    for e in entities or []:
        shifted.append(MessageEntity(
            type=e.type,
            offset=e.offset + shift,
            length=e.length,
            url=getattr(e, "url", None),
            user=getattr(e, "user", None),
            language=getattr(e, "language", None),
            custom_emoji_id=getattr(e, "custom_emoji_id", None),
        ))
    return shifted


def build_brand_footer() -> tuple:
    """يبني تذييل العلامة التجارية (اسم أزرق قابل للضغط + رابط «السحوبات» بجانبه)
    المستخدم في نهاية منشورات القناة (السحب والمسابقة)."""
    return build_text_with_emojis([
        "\n\n",
        *build_brand_giveaways_parts(),
    ])


def build_contest_channel_message(cliche_text: str, cliche_entities, target_count: int,
                                   end_type: str, time_minutes: int, votes_target: int = None) -> tuple:
    """
    منشور المسابقة الذي يُنشر في القناة/القروب المحدد (صورة image 2):
    - كليشة المسابقة كما أرسلها صاحب المسابقة (بتنسيقاتها الأصلية).
    - عدد المشاركين المسموح بخط عريض.
    - تعليمات التسجيل داخل اقتباس ملوّن منفصل.
    - وقت انتهاء المسابقة تلقائيًا داخل اقتباس ملوّن منفصل (إذا كان معتمدًا على الوقت)،
      أو عدد الأصوات الذي تنتهي عنده المسابقة (إذا كان معتمدًا على عدد الأصوات).
    - تذييل باسم العلامة التجارية بلون أزرق قابل للضغط.
    """
    extra_parts = [
        "\n\n",
        ([f"عدد المشاركين المسموح : {target_count}"], "bold", None),
        "\n\n",
        (["لتسجيل اسمك في المسابقة اضغط على زر المشاركة في المسابقة بأسفل المنشور  ”"], "blockquote", None),
    ]
    if end_type == "time" and time_minutes:
        extra_parts.append("\n\n")
        extra_parts.append(([f"سيتم انتهاء المسابقة بعد {format_minutes_label(time_minutes)}  ”"], "blockquote", None))
    elif end_type == "votes" and votes_target:
        extra_parts.append("\n\n")
        extra_parts.append(([
            f"ستنتهي المسابقة عند وصول أحد المتسابقين إلى {votes_target} صوت  ”",
        ], "blockquote", None))

    extra_text, extra_entities = build_text_with_emojis(extra_parts)
    footer_text, footer_entities = build_brand_footer()

    base_text = cliche_text or ""
    base_entities = list(cliche_entities or [])
    shift = utf16_len(base_text)
    footer_shift = utf16_len(base_text + extra_text)

    combined_text = base_text + extra_text + footer_text
    combined_entities = (
        base_entities
        + shift_entities(extra_entities, shift)
        + shift_entities(footer_entities, footer_shift)
    )
    return combined_text, combined_entities


def build_contest_channel_keyboard(contest_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "✅ المشاركة في المسابقة",
            url=f"https://t.me/{BOT_USERNAME}?start=compjoin_{contest_code}",
            style="success",
        )],
    ])


ARABIC_ORDINALS = [
    "الأول", "الثاني", "الثالث", "الرابع", "الخامس",
    "السادس", "السابع", "الثامن", "التاسع", "العاشر",
]

MEDAL_EMOJI_BY_RANK = {1: EMOJI["medal"], 2: EMOJI["medal"], 3: EMOJI["medal"]}


def format_votes_label(votes: int) -> str:
    return f"{votes} صوت"


def build_contest_ended_message(cliche_text: str, cliche_entities, winners: list) -> tuple:
    """
    رسالة نهاية المسابقة — تُنشر كمنشور جديد منفصل (لا تُستبدل الرسالة القديمة):
    - عنوان «🏆 انتهت المسابقة!» داخل اقتباس (بخط عريض).
    - سطر لكل فائز: «الفائز 🥇 : [الاسم بلون أزرق قابل للضغط]  (X صوت)» — كل شيء بخط عريض،
      واسم الفائز رابط أزرق (TEXT_LINK) يشير إلى حساب الفائز الفعلي (وليس @يوزرنيم).
    winners: قائمة (user_id, display_name, participant_code, votes).
    """
    parts = [
        ([("🏆", EMOJI["trophy_win"]), " انتهت المسابقة!  ”"], "blockquote", None),
    ]

    if not winners:
        parts.append("\n\n")
        parts.append((["⚠️ لم يشارك أحد في هذه المسابقة، لم يتم اختيار فائز."], "bold", None))
    elif len(winners) == 1:
        user_id, name, _, votes = winners[0]
        parts.append("\n\n")
        parts.append(([
            "الفائز ",
            ("🥇", EMOJI["medal"]),
            " : ",
            (name, "mention_id", user_id),
            f"  ({format_votes_label(votes)})",
        ], "bold", None))
    else:
        for i, (user_id, name, _, votes) in enumerate(winners):
            ordinal = ARABIC_ORDINALS[i] if i < len(ARABIC_ORDINALS) else f"رقم {i + 1}"
            parts.append("\n\n")
            parts.append(([
                f"الفائز {ordinal} ",
                ("🥇", EMOJI["medal"]),
                " : ",
                (name, "mention_id", user_id),
                f"  ({format_votes_label(votes)})",
            ], "bold", None))

    combined_text, combined_entities = build_text_with_emojis(parts)
    return combined_text, combined_entities


def build_contest_ended_keyboard(contest_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "عرض النتائج", callback_data=f"comp_view_results:{contest_code}",
            style="success",
        )],
    ])


def build_contest_results_message(leaderboard: list, winners_count: int) -> tuple:
    """رسالة النتائج الكاملة (ترتيب جميع المتسابقين) — تُعرض عند الضغط على «عرض النتائج»."""
    parts = [
        ([("📊", EMOJI["chart"]), " النتائج الكاملة للمسابقة"], "bold", None),
    ]
    if not leaderboard:
        parts.append("\n\n")
        parts.append((["⚠️ لا يوجد أي متسابق مسجّل في هذه المسابقة."], "bold", None))
    else:
        bq_parts = []
        for i, (user_id, name, _, votes) in enumerate(leaderboard):
            rank = i + 1
            crown = "🏆 " if rank <= winners_count else ""
            bq_parts.append(f"{crown}({rank}) ")
            bq_parts.append((name, "mention_id", user_id))
            bq_parts.append(f" — {format_votes_label(votes)}")
            if i == 0:
                bq_parts.append("  ”\n")
            elif i != len(leaderboard) - 1:
                bq_parts.append("\n")
        parts.append("\n\n")
        parts.append(([(bq_parts, "bold", None)], "blockquote", None))
    return build_text_with_emojis(parts)


def build_contest_join_confirm_message(display_name: str) -> tuple:
    """رسالة «🎯 تأكيد المشاركة في المسابقة» (صورة image 3)."""
    parts = [
        ([("🎯", EMOJI["target_pin"]), " تأكيد المشاركة في المسابقة"], "bold", None),
        "\n\n",
        f"تريد المشاركة في المسابقة باسم: {display_name}",
        "\n\n",
        "هل أنت متأكد؟",
    ]
    return build_text_with_emojis(parts)


def build_contest_join_confirm_keyboard(contest_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "رفض", callback_data=f"comp_reject_join:{contest_code}",
                style="danger", **emoji_kwargs("remind_off"),
            ),
            InlineKeyboardButton(
                "قبول", callback_data=f"comp_confirm_join:{contest_code}",
                style="success", **emoji_kwargs("join_accept_btn"),
            ),
        ],
    ])


def build_contest_registered_message(display_name: str, participant_code: str) -> tuple:
    """رسالة تأكيد التسجيل مع كود المتسابق (صورة image 4) — عناوين الأقسام داخل اقتباس ملوّن."""
    parts = [
        ([("✅", EMOJI["confirm_check"]), f" تم تسجيل مشاركتك في المسابقة بإسم : {display_name}"], "bold", None),
        "\n\n",
        (["🎟 كود المتسابق الخاص بك:"], "bold", None),
        f"\n{participant_code}",
        "\n\n",
        (["كيفية استخدام كود المتسابق:  ”"], "blockquote", None),
        "\n\n",
        ("❶", EMOJI["num_one"]),
         " افتح بوت ",
         (BRAND_NAME, "link", BRAND_URL),
         f" @{BOT_USERNAME} وأنشئ روليت جديد.",
        "\n\n",
        ("❷", EMOJI["num_two"]),
        " اختر شرط السحب: التصويت للمتسابق ثم أدخل الكود الخاص بك.",
        "\n\n",
        (["مميزات الكود :  ”"], "blockquote", None),
        "\n\n",
        ("✅", EMOJI["confirm_check"]),
        " يمنع أي شخص من المشاركة في السحب قبل أن يصوّت لك وهذا يزيد عدد المصوتين لصالحك.",
        "\n\n",
        ("✅", EMOJI["confirm_check"]),
        " يمكنك إعطاء الكود لصديق وسيتمكن من عمل سحب في قناته بشرط التصويت لك وسيُسجَّل التصويت باسمك.",
        "\n\n",
        ("✅", EMOJI["confirm_check"]),
        " كل استخدام للكود يرفع فرصك في الفوز بالمسابقة وجميع السحوبات المرتبطة بها.",
    ]
    return build_text_with_emojis(parts)


def build_contest_registered_keyboard(contest_code: str, user_id: int, participant_code: str) -> InlineKeyboardMarkup:
    try:
        copy_btn = InlineKeyboardButton(
            "انسخ كود المسابقة",
            copy_text=CopyTextButton(text=participant_code),
            style="success",
        )
    except Exception:
        copy_btn = InlineKeyboardButton("🎟 كودك: " + participant_code, callback_data="noop")
    return InlineKeyboardMarkup([
        [copy_btn],
        [InlineKeyboardButton(
            "سحب اسمي من المسابقه", callback_data=f"comp_withdraw:{contest_code}:{user_id}",
            style="danger", **emoji_kwargs("withdraw_btn"),
        )],
    ])


def build_contest_vote_post_message(display_name: str) -> tuple:
    """المنشور الذي يُنشر في القناة/القروب عند تسجيل متسابق جديد (صورة image 5)."""
    parts = [f"{display_name} : المتسابق"]
    return build_text_with_emojis(parts)


def build_contest_vote_keyboard(contest_code: str, participant_id: int, votes: int,
                                 participant_code: str) -> InlineKeyboardMarkup:
    try:
        copy_btn = InlineKeyboardButton(
            "نسخ كود المتسابق",
            copy_text=CopyTextButton(text=participant_code),
            style="success",
        )
    except Exception:
        copy_btn = InlineKeyboardButton("🎟 كود المتسابق: " + participant_code, callback_data="noop")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"🤍 {votes}",
            url=f"https://t.me/{BOT_USERNAME}?start=compvote_{contest_code}_{participant_id}",
            style="primary",
        )],
        [copy_btn],
    ])


def build_contest_vote_premium_blocked_message() -> tuple:
    """رسالة تُعرض لمستخدم غير مفعّل بريميوم عند محاولته التصويت في مسابقة
    مخصّصة حصريًا لمصوّتي تيليجرام بريميوم."""
    parts = [
        ([("💎", EMOJI.get("premium_vote_btn", "💎")),
          " هذه المسابقة تتيح التصويت فقط لمستخدمي تيليجرام المميز Premium."],
         "bold", None),
    ]
    return build_text_with_emojis(parts)


def build_contest_vote_gate_message() -> tuple:
    """رسالة بوابة الشرط الإلزامي قبل احتساب أي تصويت: يجب الاشتراك في
    القناة الإلزامية أولاً، ثم الضغط على زر «تحقق» لإكمال التصويت."""
    parts = [
        "للتصويت في هذه المسابقة عليك أولاً:",
        "\n\n",
        ([
            (" 1️⃣ ", None), "الاشتراك في القناة الإلزامية أدناه", "\n",
            (" 2️⃣ ", None), "ثم الضغط على زر «تحقق ✅» لإتمام تصويتك",
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_contest_vote_gate_keyboard(contest_code: str, participant_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(REQUIRED_CHANNEL_BUTTON_TEXT, url=get_required_channel_url())],
        [InlineKeyboardButton(
            "تحقق ✅", callback_data=f"compcond:{contest_code}:{participant_id}", style="success",
        )],
    ])


def build_vote_captcha_message(target_emoji_id: str) -> tuple:
    """رسالة الكابتشا التي تُعرض للمستخدم عند محاولة التصويت لمتسابق (تحقق أنك لست روبوت)."""
    parts = [
        "🤖 للتحقق انك لست روبوت للتصويت اضغط على الرمز:",
        "\n\n",
        ("🔘", target_emoji_id),
    ]
    return build_text_with_emojis(parts)


def build_vote_captcha_keyboard(token: str, option_ids: list, correct_index: int,
                                 prefix: str = "compcap") -> InlineKeyboardMarkup:
    """
    يبني صف واحد من 3 أزرار إيموجي عشوائية (مطابق تمامًا لشكل كابتشا تيليجرام)،
    حيث يمثّل كل زر رمزًا مختلفًا وزر واحد فقط (عند correct_index) هو الرمز الصحيح.

    ملاحظة مهمة: هذه الدالة تُستخدم لبناء كابتشا التصويت في المسابقات (compcap)
    وأيضًا كابتشا منع الرشق في السحوبات (gwcap). كانت تُبنى دائمًا ببادئة "compcap"
    ثابتة بغض النظر عن السياق، فكانت أزرار كابتشا السحب تُرسل بيانات "compcap:..."
    فتُعالَج بواسطة hander كابتشا التصويت (الذي يبحث عن الجلسة في
    context.user_data["vote_captchas"]) بدل هاندلر كابتشا السحب (الذي يخزّن
    الجلسة في context.user_data["gw_captchas"]) — فتُعتبر الجلسة "غير موجودة"
    فورًا ويظهر خطأ "انتهت صلاحية هذا التحقق" حتى لو كانت الكابتشا جديدة تمامًا.
    الحل: تمرير بادئة مختلفة (prefix) حسب السياق حتى تُطابق كل كابتشا الهاندلر
    الصحيح الخاص بها.
    """
    row = [
        InlineKeyboardButton(
            "◻️",
            callback_data=f"{prefix}:{token}:{idx}",
            icon_custom_emoji_id=emoji_id,
        )
        for idx, emoji_id in enumerate(option_ids)
    ]
    return InlineKeyboardMarkup([row])


def build_vote_captcha_success_message() -> tuple:
    parts = [
        ([("✅", EMOJI["confirm_check"]), " تم التحقق وتسجيل تصويتك بنجاح!"], "bold", None),
    ]
    return build_text_with_emojis(parts)


def build_vote_captcha_wrong_alert() -> str:
    return "❌ رمز غير صحيح، حاول اختيار الرمز الصحيح مرة أخرى."


QUICK_ROULETTE_TEXT = (
    "🎡 قسم روليت سريع\n\n"
    "• انشاء روليت: انشاء روليت سريع\n"
    "• الاعدادات: تحكم في اعدادة اللعبة\n\n"
    "• اختر ماتريد من الازرار ادناه ⬇️"
)

def _roulette_progress_bar(current: int, target: int, length: int = 10) -> str:
    """يبني شريط تقدّم مرئي بسيط (مربعات ملوّنة) لعدد المشاركين الحاليين
    مقابل العدد المطلوب، يُستخدم في منشور «روليت سريع» ليبدو أكثر احترافية."""
    if target <= 0:
        return ""
    ratio = min(1.0, current / target)
    filled = min(length, round(length * ratio))
    return "🟩" * filled + "⬜️" * (length - filled)


def build_quick_roulette_channel_message(target: int, current: int) -> tuple:
    """رسالة «روليت سريع» الاحترافية التي تُنشر عبر الوضع المضمّن (inline) في
    القناة/القروب، وتُحدَّث في نفس الرسالة عند كل مشاركة جديدة. تتضمّن كليشة
    اللعبة، عداد المشاركين مع شريط تقدّم داخل اقتباس مميّز، وتذييل العلامة
    التجارية الموحّد (نفس تذييل منشورات السحب/المسابقة)."""
    cliche = get_setting("game_cliche") or DEFAULT_GAME_CLICHE
    bar = _roulette_progress_bar(current, target)
    parts = [
        ([("🎡", EMOJI["roulette"]), " روليت سريع"], "bold", None),
        "\n\n",
        cliche,
        "\n\n",
        ([
            ("👥", EMOJI["people"]),
            f" المشاركين: {current}/{target}",
            "\n",
            bar,
        ], "blockquote", None),
    ]
    base_text, base_entities = build_text_with_emojis(parts)
    footer_text, footer_entities = build_brand_footer()
    shift = utf16_len(base_text)
    combined_text = base_text + footer_text
    combined_entities = base_entities + shift_entities(footer_entities, shift)
    return combined_text, combined_entities


def build_quick_roulette_join_notify_message(display_name: str) -> tuple:
    """رسالة مختصرة تُرسل لمالك الروليت السريع فقط عند انضمام مشارك جديد —
    الاسم فقط دون أي تفاصيل إضافية (آيدي/يوزر/عدد المشاركين)."""
    parts = [
        ([("🎡", EMOJI["roulette"]), f" قام شخص بالاشتراك في روليتك: {display_name}"], "bold", None),
    ]
    return build_text_with_emojis(parts)



def build_waiting_spin_message(target: int, current: int, participants: list) -> tuple:
    """
    participants: قائمة من tuples (user_id, display_name)
    """
    hide = get_setting("hide_participants") == "1"
    parts = [
        ("⧉ اكتمل العدد\n\n", "bold", None),
        ([
            ("👥", EMOJI["people"]),
            f" المشاركين: {current}/{target}  ”"
        ], "blockquote", None),
        "\n\n"
    ]

    if not hide and participants:
        parts.append(("🫧 قائمة المشاركين:\n", "bold", None))
        bq_parts = []
        for i, (uid, name) in enumerate(participants):
            suffix = '  ”\n' if i == 0 else '\n'
            if i == len(participants) - 1:
                suffix = suffix.rstrip('\n')
            bq_parts.append(f"- المشارك ({i + 1}) : ")
            bq_parts.append((name, "mention_id", uid))
            bq_parts.append(suffix)
        parts.append((bq_parts, "blockquote", None))
        parts.append("\n\n")

    parts.append(([
        ("🎯", EMOJI["target"]),
        " في انتظار تدوير الروليت  ”"
    ], "blockquote", None))

    return build_text_with_emojis(parts)

def build_result_message(winner_id: int, winner_name: str, participants: list) -> tuple:
    hide = get_setting("hide_participants") == "1"
    parts = [
        ("• تم اختيار الفائز ", "bold", None), ("🥳", EMOJI["party"]), "\n\n",
        ([
            ("🏆", EMOJI["trophy_win"]),
            " الفائز : ",
            (winner_name, "mention_id", winner_id),
            " ",
            ("🥇", EMOJI["medal"]),
            "  ”"
        ], "blockquote", None),
        "\n\n"
    ]

    if not hide and participants:
        parts.append((f"🔹 جميع المشاركين ({len(participants)}):\n", "bold", None))
        bq_parts = []
        for i, (uid, name) in enumerate(participants):
            suffix = '  ”\n' if i == 0 else '\n'
            if i == len(participants) - 1:
                suffix = suffix.rstrip('\n')
            bq_parts.append(f"- المشارك ({i + 1}) : ")
            bq_parts.append((name, "mention_id", uid))
            bq_parts.append(suffix)
        parts.append((bq_parts, "blockquote", None))
        parts.append("\n\n")

    parts += build_brand_giveaways_parts()
    return build_text_with_emojis(parts)

def waiting_spin_keyboard(roulette_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔷 تدوير الروليت 🔷", callback_data=f"rr_spin_{roulette_id}", style="danger")],
    ])

def result_keyboard(roulette_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↻ اختيار فائز آخر", callback_data=f"rr_respin_{roulette_id}", style="danger")],
        [InlineKeyboardButton("↻ لعب مره اخرى", switch_inline_query="", style="success")],
    ])

def build_giveaway_target_message() -> tuple:
    """شاشة «يرجى تحديد القناة أو القروب للسحب» (Image 1)."""
    parts = [
        ([
            "يرجى تحديد القناة أو القروب للسحب ",
            ("🎯", EMOJI["target_pin"]),
        ], "bold", None),
        "\n\n",
        ([
            "تأكد أولاً أنك مشرف في القناة أو الجروب وأن البوت أيضاً مشرف.",
        ], "blockquote", None),
        "\n\n",
        ([
            "إذا لم تظهر القناة أو الجروب وتأكدت أن البوت موجود كـ «مشرف» وأنت كذلك، يمكنك تسجيله يدوياً من الأسفل ",
            ("⏬", EMOJI["arrow_down"]),
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_giveaway_target_keyboard(owner_id: int = None) -> InlineKeyboardMarkup:
    rows = []
    if owner_id is not None:
        for chat in get_registered_chats(owner_id):
            title = chat["chat_title"] or str(chat["chat_id"])
            rows.append([InlineKeyboardButton(
                title, callback_data=f"gw_sel:{chat['chat_id']}",
            )])
    rows.append([
        InlineKeyboardButton(
            "تسجيل قناة", callback_data="gw_reg_channel",
            style="primary", **emoji_kwargs("register_plus"),
        ),
        InlineKeyboardButton(
            "تسجيل جروب", callback_data="gw_reg_group",
            style="primary", **emoji_kwargs("register_plus"),
        ),
    ])
    rows.append([InlineKeyboardButton(
        "حذف قناة", callback_data="gw_del_channels",
        style="danger", **emoji_kwargs("delete_all_btn"),
    )])
    rows.append([InlineKeyboardButton(
        "رجوع", callback_data="back_main_menu",
        style="danger", **emoji_kwargs("back_section_btn"),
    )])
    return InlineKeyboardMarkup(rows)


def build_giveaway_delete_message() -> tuple:
    parts = [
        (["🗑️ حذف قناة أو مجموعة"], "bold", None),
        "\n\n",
        "اضغط على 🗑️ لحذف:",
    ]
    return build_text_with_emojis(parts)


def build_giveaway_delete_keyboard(owner_id: int) -> InlineKeyboardMarkup:
    rows = []
    for chat in get_registered_chats(owner_id):
        title = chat["chat_title"] or str(chat["chat_id"])
        rows.append([
            InlineKeyboardButton(title, callback_data="gw_noop"),
            InlineKeyboardButton("🗑️", callback_data=f"gw_delc:{chat['chat_id']}"),
        ])
    rows.append([InlineKeyboardButton(
        "رجوع", callback_data="gw_start_create",
        style="danger", **emoji_kwargs("back_section_btn"),
    )])
    return InlineKeyboardMarkup(rows)


def build_back_to_giveaway_keyboard() -> InlineKeyboardMarkup:
    return _build_single_back_keyboard("رجوع", "gw_start_create", "danger", "back_section_btn")


GW_LIST_PAGE_SIZE = 8


def build_my_giveaways_list_message(page: int, total_pages: int) -> tuple:
    """شاشة «سحوباتي»: تعرض رقم الصفحة الحالية من إجمالي الصفحات."""
    parts = [
        ([("🎁", EMOJI["draws_check"]), " سحوباتي"], "bold", None),
        "\n\n",
        ([
            f"كل سحوباتك • صفحة {page}/{total_pages}", "\n",
            "اختر سحبًا لعرض تفاصيله:",
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_my_giveaways_list_keyboard(giveaways, page: int, total_pages: int) -> InlineKeyboardMarkup:
    """
    أزرار مرقّمة (زر لكل سحب) مع نقطة ملوّنة تدل على حالته (🟢 نشط / 🔴 متوقف).
    عند كثرة السحوبات تُقسَّم تلقائيًا إلى صفحات (GW_LIST_PAGE_SIZE في كل صفحة)
    مع صف تنقّل «السابق / التالي» حتى لا تتكدّس القائمة.
    """
    start = (page - 1) * GW_LIST_PAGE_SIZE
    page_items = giveaways[start:start + GW_LIST_PAGE_SIZE]

    rows = []
    for offset, gw in enumerate(page_items):
        index = start + offset + 1
        dot = "🟢" if gw["status"] == "open" else "🔴"
        rows.append([InlineKeyboardButton(
            f"{dot} #{index}", callback_data=f"gwmy_detail:{gw['gw_code']}:{page}",
        )])

    if total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton("◀️ السابق", callback_data=f"gwmy_page:{page - 1}"))
        nav_row.append(InlineKeyboardButton(f"صفحة {page}/{total_pages}", callback_data="gw_noop"))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton("التالي ▶️", callback_data=f"gwmy_page:{page + 1}"))
        rows.append(nav_row)

    rows.append([InlineKeyboardButton(
        "رجوع", callback_data="back_main_menu",
        style="danger", **emoji_kwargs("back_section_btn"),
    )])
    return InlineKeyboardMarkup(rows)


def build_my_giveaway_detail_message(giveaway, index: int, channel_title: str,
                                      participants_total: int, new_rewarded_count: int) -> tuple:
    """شاشة تفاصيل سحب واحد من «سحوباتي»."""
    status_line = "🟢 نشط" if giveaway["status"] == "open" else "🔴 متوقف"
    parts = [
        ([
            f"🎁 السحب #{index}",
            "\n\n",
            f"👥 عدد المشاركين الكلي : {participants_total}", "\n",
            f"🏆 عدد الفائزين : {giveaway['winners_count']}", "\n",
            f"📊 الحالة : {status_line}", "\n",
            f"✨ مشاركون جدد احتُسبت نقاطهم : {new_rewarded_count}", "\n",
            f"📢 القناة : {channel_title}",
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_my_giveaway_detail_keyboard(page: int) -> InlineKeyboardMarkup:
    """زر «رجوع» فقط، يعيد المستخدم لنفس صفحة القائمة التي جاء منها."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "رجوع", callback_data=f"gwmy_page:{page}",
            style="danger", **emoji_kwargs("back_section_btn"),
        )],
    ])


def build_giveaway_cliche_message() -> tuple:
    parts = [
        ([
            ("📨", EMOJI["envelope_klesha"]),
            " أرسل كليشة السحب",
        ], "bold", None),
        "\n\n",
        "اكتب نص السحب الذي تريد نشره في القناة.\n"
        "يمكنك استخدام تنسيقات تيليجرام مثل:\n",
        "• ", ("نص عريض", "bold", None), "\n",
        "• ", ("نص مائل", "italic", None), "\n",
        "• ", ("نص مشوش", "spoiler", None), "\n",
        ([("🆕", EMOJI["new_badge"]), " يمكنك وضع رابط داخل النص"], "link", "https://t.me"),
        "\n",
        (["نص مقتبس  ”"], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_giveaway_cliche_keyboard() -> InlineKeyboardMarkup:
    return build_back_to_giveaway_keyboard()


GIVEAWAY_SETTINGS_DEFAULTS = {
    "gw_boost": False,
    "gw_premium": False,
    "gw_antispam": False,
    "gw_vote_contest_code": None,
    "gw_vote_participant_id": None,
    "gw_vote_participant_code": None,
    "gw_vote_display_name": None,
    "gw_condition_channels": [],
    "gw_autospin_mode": None,
    "gw_autospin_target": None,
    "gw_autospin_minutes": None,
}

GW_CONDITION_CHANNELS_MAX = 2
GW_CONDITION_CIRCLE_NUMS = ["❶", "❷", "❸"]


def build_giveaway_settings_message() -> tuple:
    parts = [
        ([("⚙️", EMOJI["target"]), " إعدادات السحب"], "bold", None),
        "\n\n",
        (["اختر شرطًا لتحسين السحب:"], "blockquote", None),
        "\n\n",
        ("1️⃣", EMOJI["num_one"]), " قناة شرط: الاشتراك في قناة محددة", "\n",
        ("2️⃣", EMOJI["num_two"]), " تعزيز القناة: تعزيز قناتك", "\n",
        ("3️⃣", EMOJI["num_three"]), " التصويت: التصويت لمتسابق معين", "\n",
        ("4️⃣", EMOJI["num_four"]), " مشتركون مميزون: للمشتركين المميزين", "\n",
        ("5️⃣", EMOJI["num_five"]), " منع الرشق: حماية السحب من الرشق", "\n",
        ("6️⃣", EMOJI["num_six"]), " سحب تلقائي: عند اكتمال العدد أو انتهاء الوقت",
        "\n\n",
        ([
            "• اختر الشرط الذي تريده من الأزرار أدناه ",
            ("⏬", EMOJI["arrow_down"]),
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_giveaway_settings_keyboard(user_data: dict) -> InlineKeyboardMarkup:
    def toggle_btn(label: str, flag: bool, callback_data: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(
            f"{label} : {'نعم' if flag else 'لا'}",
            callback_data=callback_data,
            style="success" if flag else "danger",
            **emoji_kwargs("yes_btn" if flag else "no_btn"),
        )

    boost = user_data.get("gw_boost", GIVEAWAY_SETTINGS_DEFAULTS["gw_boost"])
    premium = user_data.get("gw_premium", GIVEAWAY_SETTINGS_DEFAULTS["gw_premium"])
    antispam = user_data.get("gw_antispam", GIVEAWAY_SETTINGS_DEFAULTS["gw_antispam"])

    vote_contest_code = user_data.get("gw_vote_contest_code")
    vote_participant_id = user_data.get("gw_vote_participant_id")
    if vote_contest_code and vote_participant_id:
        vote_display_name = user_data.get("gw_vote_display_name") or "متسابق"
        votes = get_participant_votes(vote_contest_code, vote_participant_id)
        vote_btn = InlineKeyboardButton(
            f"🤍 {votes}   {vote_display_name}", callback_data="gw_opt_vote",
            style="success", **emoji_kwargs("gw_vote_icon"),
        )
    else:
        vote_btn = InlineKeyboardButton("تصويت متسابق", callback_data="gw_opt_vote",
                                         style="primary", **emoji_kwargs("gw_vote_icon"))

    condition_channels = user_data.get("gw_condition_channels") or []
    if condition_channels:
        label = condition_channels[0]["title"]
        extra = len(condition_channels) - 1
        if extra > 0:
            label = f"{label} +{extra}"
        condition_btn = InlineKeyboardButton(
            label, callback_data="gw_opt_condition",
            style="success", **emoji_kwargs("gw_condition_channel"),
        )
    else:
        condition_btn = InlineKeyboardButton(
            "قناة شرط", callback_data="gw_opt_condition",
            style="primary", **emoji_kwargs("gw_condition_channel"),
        )

    autospin_mode = user_data.get("gw_autospin_mode", GIVEAWAY_SETTINGS_DEFAULTS["gw_autospin_mode"])
    if autospin_mode == "count" and user_data.get("gw_autospin_target"):
        autospin_label = f"سحب تلقائي: {user_data['gw_autospin_target']} مشترك"
        autospin_btn = InlineKeyboardButton(
            autospin_label, callback_data="gw_opt_autospin",
            style="success", **emoji_kwargs("target_pin"),
        )
    elif autospin_mode == "time" and user_data.get("gw_autospin_minutes"):
        autospin_label = f"سحب تلقائي: {format_duration_label(user_data['gw_autospin_minutes'])}"
        autospin_btn = InlineKeyboardButton(
            autospin_label, callback_data="gw_opt_autospin",
            style="success", **emoji_kwargs("gw_atime_clock"),
        )
    else:
        autospin_btn = InlineKeyboardButton(
            "سحب تلقائي", callback_data="gw_opt_autospin",
            style="primary", **emoji_kwargs("draws_check"),
        )

    return InlineKeyboardMarkup([
        [
            toggle_btn("تعزيز القناة", boost, "gw_toggle_boost"),
            condition_btn,
        ],
        [
            toggle_btn("مشتركين المميز", premium, "gw_toggle_premium"),
            vote_btn,
        ],
        [
            toggle_btn("منع الرشق", antispam, "gw_toggle_antispam"),
            autospin_btn,
        ],
        [InlineKeyboardButton(
            "نشر السحب", callback_data="gw_opt_create",
            style="success", **emoji_kwargs("yes_btn"),
        )],
        [InlineKeyboardButton(
            "رجوع", callback_data="gw_back_main",
            style="danger", **emoji_kwargs("back_section_btn"),
        )],
    ])


def build_giveaway_autospin_end_method_message() -> tuple:
    """شاشة «اختر طريقة انتهاء السحب» الخاصة بالسحب التلقائي (Image 2)."""
    parts = [
        (["اختر طريقة انتهاء السحب", ("❓", EMOJI["end_question"])], "bold", None),
        "\n\n",
        ([
            ("🎯", EMOJI["target_pin"]), " عدد محدد ", ("⚡️", EMOJI["gw_atime_lightning"]),
            " : ينتهي السحب تلقائيًا عند وصول عدد المشاركين إلى الرقم الذي تحدده",
        ], "blockquote", None),
        "\n\n",
        ([
            ("🕖", EMOJI["gw_atime_clock"]), " وقت محدد : ينتهي السحب عند انتهاء الوقت الذي "
            "تحدده ويتم اختيار الفائزين ", ("🏆", EMOJI["trophy_win"]),
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_giveaway_autospin_end_method_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "عدد محدد", callback_data="gw_atime_end_count",
                style="primary", **emoji_kwargs("target_pin"),
            ),
            InlineKeyboardButton(
                "وقت محدد", callback_data="gw_atime_end_time",
                style="primary", **emoji_kwargs("gw_atime_clock"),
            ),
        ],
        [InlineKeyboardButton(
            "رجوع للخيارات", callback_data="gw_back_to_options",
            style="danger", **emoji_kwargs("back_section_btn"),
        )],
    ])


def build_giveaway_autospin_count_message() -> tuple:
    """شاشة «أرسل عدد المشاركين المطلوب» لتفعيل السحب التلقائي لعدد محدد (Image 3)."""
    parts = [
        ([
            ("🎯", EMOJI["target_pin"]), " السحب التلقائي لـ عدد محدد",
        ], "bold", None),
        "\n\n",
        "أرسل عدد المشاركين المطلوب لبدء السحب تلقائياً",
        "\n\n",
        ([
            "مثال: إذا أردت تفعيل السحب التلقائي عند وصول عدد المشاركين إلى 100 "
            "أرسل الرقم 100",
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_giveaway_autospin_count_keyboard() -> InlineKeyboardMarkup:
    return _build_single_back_keyboard("رجوع للخيارات", "gw_atime_back", "danger", "back_section_btn")


def build_giveaway_autospin_time_message(selected_label: str = "غير محدد") -> tuple:
    """شاشة «السحب التلقائي لـ وقت محدود» بعرض قائمة الأوقات الجاهزة (Image 4)."""
    parts = [
        ([
            ("🕖", EMOJI["gw_atime_clock"]), " السحب التلقائي لـ وقت محدود",
        ], "bold", None),
        f"\nالوقت المختار: {selected_label}",
        "\n\n",
        "استخدم الأزرار أدناه لتحديد الوقت المطلوب لبدء السحب تلقائياً:",
    ]
    return build_text_with_emojis(parts)


def build_giveaway_autospin_time_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for row in CONTEST_TIME_OPTIONS:
        rows.append([
            InlineKeyboardButton(
                label, callback_data=f"gw_atime_set_{minutes}",
                style="primary", **emoji_kwargs("time_option_btn"),
            )
            for minutes, label in row
        ])
    rows.append([
        InlineKeyboardButton(
            "وقت مخصص", callback_data="gw_atime_show_custom",
            style="primary", **emoji_kwargs("time_manual_btn"),
        ),
    ])
    rows.append([
        InlineKeyboardButton(
            "رجوع", callback_data="gw_atime_back",
            style="danger", **emoji_kwargs("back_time_menu_btn"),
        )
    ])
    return InlineKeyboardMarkup(rows)


GW_AUTOSPIN_CUSTOM_STEPS = [
    [(-1, "- 1 دقيقة"), (1, "+ 1 دقيقة")],
    [(-5, "- 5 دقيقة"), (5, "+ 5 دقيقة")],
    [(-10, "- 10 دقايق"), (10, "+ 10 دقايق")],
    [(-60, "- 1 ساعة"), (60, "+ 1 ساعة")],
    [(-1440, "- 1 يوم"), (1440, "+ 1 يوم")],
]


def build_giveaway_autospin_custom_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for row in GW_AUTOSPIN_CUSTOM_STEPS:
        rows.append([
            InlineKeyboardButton(
                label, callback_data=f"gw_atime_custom_delta:{delta}",
                style="primary", **emoji_kwargs("time_option_btn"),
            )
            for delta, label in row
        ])
    rows.append([InlineKeyboardButton(
        "تأكيد الوقت", callback_data="gw_atime_custom_confirm",
        style="success", **emoji_kwargs("yes_btn"),
    )])
    rows.append([
        InlineKeyboardButton(
            "إعادة تعيين", callback_data="gw_atime_custom_reset",
            style="success", **emoji_kwargs("restore_defaults_btn"),
        ),
        InlineKeyboardButton(
            "رجوع للخيارات", callback_data="gw_back_to_options",
            style="danger", **emoji_kwargs("back_section_btn"),
        ),
    ])
    return InlineKeyboardMarkup(rows)


def build_giveaway_vote_code_message() -> tuple:
    """شاشة طلب كود المتسابق لجعل التصويت له شرطًا للمشاركة في السحب (Image 2)."""
    parts = [
        ([("📌", EMOJI["pin_note"]), " يرجى ارسال كود المتسابق الذي تريد جعله شرطًا"], "bold", None),
        "\n\n",
        ("📌", EMOJI["pin_note"]), " مثال على الكود: C12345678",
        "\n\n",
        (["⚠️ ملاحظة: لن يتمكن أي شخص من المشاركة في السحب قبل إتمام التصويت للمتسابق المحدد"],
         "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_giveaway_vote_code_keyboard() -> InlineKeyboardMarkup:
    return _build_single_back_keyboard("رجوع", "gw_back_to_options", "danger", "back_section_btn")


def build_giveaway_vote_code_error_message() -> tuple:
    """رسالة الخطأ عند إرسال كود متسابق غير صحيح أو مسابقة منتهية (Image 5)."""
    parts = [
        (["❌ كود المتسابق غير صحيح أو المسابقة انتهت!"], "bold", None),
        "\n\n",
        "تأكد من الكود وحاول مجدداً.",
    ]
    return build_text_with_emojis(parts)


def build_giveaway_vote_code_error_keyboard() -> InlineKeyboardMarkup:
    return build_giveaway_vote_code_keyboard()


def build_giveaway_vote_linked_message(participant_code: str) -> tuple:
    """رسالة تأكيد ربط كود المتسابق بشرط السحب بنجاح (Image 4)."""
    parts = [
        (["✅ تم ربط كود المتسابق:"], "bold", None),
        f"\n{participant_code}",
        "\n\n",
        "كل مشارك سيتحقق من تصويته قبل المشاركة في السحب.",
    ]
    return build_text_with_emojis(parts)


def build_giveaway_condition_type_message() -> tuple:
    """شاشة اختيار نوع «قناة الشرط»: عامة أو خاصة (Image 2)."""
    parts = [
        ([("📢", EMOJI["gw_condition_channel"]), " قناة الشرط"], "bold", None),
        "\n\n",
        "اختر نوع قناة الشرط:",
    ]
    return build_text_with_emojis(parts)


def build_giveaway_condition_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌐 قناة عامة", callback_data="gw_cond_public", style="primary"),
            InlineKeyboardButton("🔒 قناة خاصة", callback_data="gw_cond_private", style="primary"),
        ],
        [InlineKeyboardButton(
            "رجوع للخيارات", callback_data="gw_back_to_options",
            style="danger", **emoji_kwargs("back_section_btn"),
        )],
    ])


def build_giveaway_condition_public_message() -> tuple:
    """شاشة طلب يوزر القناة العامة (أو قناتين) لجعلها شرط اشتراك للمشاركة (Image 3)."""
    parts = [
        ([("📢", EMOJI["gw_condition_channel"]), " قناة الشرط العامة"], "bold", None),
        "\n\n",
        "الان ارسل لي يوزر قناة الشرط", "\n",
        "مثال @e_ggf",
        "\n\n",
        "لا تضف أي نص إضافي مع اليوزر",
        "\n\n",
        (["تأكد من إضافة البوت كمشرف في قناة الشرط مع صلاحية إدارة الأعضاء"],
         "blockquote", None),
        "\n\n",
        ([
            "يمكنك إضافة قناتين كحد أقصى، ويتم إدخال الأسماء بهذا الشكل:", "\n",
            "@e_ggf", "\n",
            "@n_bbo",
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_giveaway_condition_public_keyboard() -> InlineKeyboardMarkup:
    return _build_single_back_keyboard("رجوع للخيارات", "gw_opt_condition", "danger", "back_section_btn")


def build_giveaway_condition_private_message(added_count: int = 0) -> tuple:
    """شاشة طلب توجيه رسالة من القناة الخاصة لجعلها شرط اشتراك للمشاركة.
    عند added_count == 1 (بعد إضافة أول قناة) تتحول الرسالة لعرض إمكانية إضافة
    قناة ثانية اختيارية أو إنهاء الآن بقناة واحدة فقط."""
    if added_count >= 1:
        parts = [
            ([("✅", EMOJI["sub_check"]), f" تم إضافة القناة الخاصة رقم {added_count} بنجاح"], "bold", None),
            "\n\n",
            "يمكنك إعادة توجيه رسالة من قناة خاصة ثانية (اختياري)، أو الضغط على «إنهاء» للاكتفاء بالقناة الحالية.",
        ]
    else:
        parts = [
            ([("📢", EMOJI["gw_condition_channel"]), " قناة الشرط الخاصة"], "bold", None),
            "\n\n",
            "الان قم بإعادة توجيه أي رسالة من قناتك الخاصة إلى هنا",
            "\n\n",
            (["تأكد من إضافة البوت كمشرف في القناة مع صلاحية إدارة الأعضاء، وأن تكون أنت مشرفًا فيها أيضًا"],
             "blockquote", None),
            "\n\n",
            (["يمكنك إضافة قناتين خاصتين كحد أقصى، بتوجيه رسالة من كل قناة على حدة"],
             "blockquote", None),
        ]
    return build_text_with_emojis(parts)


def build_giveaway_condition_private_keyboard(added_count: int = 0) -> InlineKeyboardMarkup:
    if added_count >= 1:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "إنهاء ✅", callback_data="gw_cond_private_done",
                style="success", **emoji_kwargs("yes_btn"),
            )],
            [InlineKeyboardButton(
                "رجوع للخيارات", callback_data="gw_opt_condition",
                style="danger", **emoji_kwargs("back_section_btn"),
            )],
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "رجوع للخيارات", callback_data="gw_opt_condition",
            style="danger", **emoji_kwargs("back_section_btn"),
        )],
    ])


def build_giveaway_condition_error_message() -> tuple:
    """رسالة الخطأ عند تعذّر التحقق من قناة الشرط المُدخلة."""
    parts = [
        (["❌ تعذّر العثور على القناة أو أن البوت ليس مشرفًا فيها!"], "bold", None),
        "\n\n",
        "تأكد من اليوزر وأن البوت مضاف كمشرف بصلاحية إدارة الأعضاء، ثم حاول مجدداً.",
    ]
    return build_text_with_emojis(parts)


def build_giveaway_condition_max_error_message() -> tuple:
    """رسالة الخطأ عند إرسال أكثر من قناتين لشرط السحب."""
    parts = [
        (["❌ يمكنك إضافة قناتين كحد أقصى!"], "bold", None),
        "\n\n",
        "أرسل يوزر قناة واحدة أو قناتين فقط (كل يوزر في سطر منفصل).",
    ]
    return build_text_with_emojis(parts)


def build_giveaway_condition_linked_message(channel_titles) -> tuple:
    """رسالة تأكيد ربط قناة/قنوات الشرط بنجاح (Image 4)."""
    titles_line = "\n".join(channel_titles) if isinstance(channel_titles, (list, tuple)) else str(channel_titles)
    parts = [
        (["✅ تم اضافة قناة الشرط بنجاح"], "bold", None),
        f"\n{titles_line}",
        "\n\n",
        "كل مشارك سيتحقق من اشتراكه في القناة قبل المشاركة في السحب.",
    ]
    return build_text_with_emojis(parts)


def build_giveaway_condition_subscribe_alert() -> str:
    """نص التنبيه الداخلي (show_alert) الذي يظهر عند محاولة المشاركة دون اشتراك في
    قناة/قنوات الشرط (Image 2 — نص عام دون ذكر اسم قناة محددة)."""
    return "❌ يجب عليك الاشتراك في قناة الشرط اولاً"


def build_giveaway_gate_message(giveaway) -> tuple:
    """رسالة «بوابة الشروط» التي تظهر للمستخدم داخل البوت بعد الضغط على زر
    المشاركة في سحب مفعّل عليه «منع الرشق» — تُعرض فقط عندما لا يكون قد
    اجتاز بعد شرط/شروط السحب (اشتراك في القنوات و/أو تعزيز)، وقبل ظهور زر
    التحقق (الكابتشا) الذي يظهر بعد إكمال هذه الشروط."""
    channels = (giveaway.get("condition_channels") or [])[:GW_CONDITION_CHANNELS_MAX]
    lines = [f"• {ch.get('title') or ch.get('ref') or 'القناة'}" for ch in channels]
    if giveaway.get("boost_required"):
        lines.append("• تعزيز القناة (Boost)")
    vote_contest_code = giveaway.get("vote_contest_code")
    vote_participant_id = giveaway.get("vote_participant_id")
    if vote_contest_code and vote_participant_id:
        lines.append("• التصويت للمتسابق المطلوب")

    parts = [
        "عليك إكمال الشروط التالية أولاً", "\n",
        "- لتتمكن من المشاركة في السحب: ", ("🎁", EMOJI["target_pin"]),
    ]
    if lines:
        parts += ["\n", "\n".join(lines)]
    parts += [
        "\n\n",
        ([
            ("‼️", EMOJI["sub_alert"]),
            " | أكمل الشروط ثم اضغط تحقق",
            ("✅", EMOJI["sub_check"]),
        ], "blockquote", None),
    ]
    return build_text_with_emojis(parts)


def build_giveaway_gate_keyboard(gw_code: str, giveaway, is_genuinely_new: bool,
                                  boost_link: str = "", vote_link: str = "") -> InlineKeyboardMarkup:
    """كيبورد بوابة الشروط: زر لكل قناة/تعزيز/تصويت مطلوب، وزر «تحقق ✅» أسفلها.
    عند الضغط على «تحقق» يُعاد فحص الشروط؛ فإن اجتازها المستخدم تتحوّل نفس
    الرسالة إلى كابتشا التحقق منع الرشق الموجودة مسبقًا."""
    rows = []
    channels = (giveaway.get("condition_channels") or [])[:GW_CONDITION_CHANNELS_MAX]
    for ch in channels:
        title = ch.get("title") or "الإشتراك في القناة"
        link = ch.get("url") or f"https://t.me/{str(ch.get('ref', '')).lstrip('@')}"
        rows.append([InlineKeyboardButton(title, url=link)])
    if boost_link:
        rows.append([InlineKeyboardButton("تعزيز القناة (Boost)", url=boost_link)])
    if vote_link:
        rows.append([InlineKeyboardButton("التصويت للمتسابق", url=vote_link)])
    rows.append([
        InlineKeyboardButton(
            "تحقق ✅", callback_data=f"gwcond:{gw_code}:{1 if is_genuinely_new else 0}",
        )
    ])
    return InlineKeyboardMarkup(rows)


def build_giveaway_winners_message() -> tuple:
    parts = [
        ([
            "أرسل عدد الفائزين المطلوب ",
            ("🏆", EMOJI["trophy_winners_title"]),
        ], "bold", None),
    ]
    return build_text_with_emojis(parts)


def build_giveaway_winners_keyboard() -> InlineKeyboardMarkup:
    return _build_single_back_keyboard("رجوع للخيارات", "gw_back_to_options", "danger", "back_section_btn")


def build_giveaway_publish_success_message() -> tuple:
    parts = [
        (["✅ تم نشر السحب بنجاح !"], "bold", None),
    ]
    return build_text_with_emojis(parts)


def build_giveaway_vote_condition_link(vote_contest_code: str, vote_participant_id) -> str:
    """يبني رابط التصويت المخفي (نفس رابط زر 🤍 أسفل منشور المتسابق) الذي تحمله
    كلمة «هنا» داخل اقتباس شرط التصويت في منشور السحب."""
    return f"https://t.me/{BOT_USERNAME}?start=compvote_{vote_contest_code}_{vote_participant_id}"


def build_giveaway_autospin_notice_text(giveaway) -> str:
    """يبني نص عبارة «سحب تلقائي» المزخرفة المضافة أسفل منشور السحب (Image 9)،
    والتي تُحدَّث تلقائيًا كل 10 دقائق في حالة «وقت محدد» حتى وصول العداد للصفر."""
    mode = giveaway.get("autospin_mode")
    if mode == "count":
        target = giveaway.get("autospin_target")
        return f"يُسحب تلقائيًا عند اكتمال {target} مشارك"
    if mode == "time":
        end_at = giveaway_autospin_end_datetime(giveaway)
        remaining_minutes = max(0, (end_at - datetime.now(timezone.utc)).total_seconds() / 60)
        remaining_label = format_duration_label(round(remaining_minutes)) if remaining_minutes >= 1 else "لحظات"
        return f"يُسحب تلقائيًا بعد {remaining_label}"
    return ""


def build_giveaway_channel_message(cliche_text: str, cliche_entities, vote_link: str = None,
                                    condition_channels=None, boost_link: str = None,
                                    autospin: dict = None) -> tuple:
    """منشور السحب الذي يُنشر في القناة/القروب (Image 5).

    إذا كان السحب مشروطًا بالتصويت لمتسابق (vote_link)، يُضاف أعلى تذييل العلامة
    التجارية اقتباس مزخرف «شرط تصويت» تحمل فيه كلمة «هنا» رابطًا مخفيًا يفتح
    نفس مسار التصويت للمتسابق مباشرة عبر البوت (Image 6).

    وإذا كان السحب مشروطًا بالاشتراك في قناة شرط واحدة أو قناتين (condition_channels:
    قائمة عناصر {"title", "url"}) و/أو بتعزيز (Boost) القناة (boost_link)، يُضاف
    اقتباس واحد «الشرط» يحتوي سطرًا مرقّمًا (❶ / ❷ / ❸) لكل بند: قناة/قناتا
    الشرط أولاً ثم بند «تعزيز» إن وُجد، كل سطر تحمل فيه كلمة «هنا» الرابط
    الخاص بذلك البند تحديدًا (Image A3). بند «تعزيز» يفتح نافذة تعزيز القناة
    الأصلية في تيليجرام مباشرة عبر رابط https://t.me/boost/<username> (Image A4)."""
    extra_parts = []
    condition_channels = condition_channels or []
    condition_items = []
    for channel in condition_channels[:GW_CONDITION_CHANNELS_MAX]:
        link = channel.get("url") or f"https://t.me/{str(channel.get('ref', '')).lstrip('@')}"
        condition_items.append(("الإشتراك", link))
    if boost_link:
        condition_items.append(("تعزيز", boost_link))
    if condition_items:
        quote_content = ["• الشرط ", ("⬇️", EMOJI["arrow_down"])]
        for idx, (label, link) in enumerate(condition_items):
            circle = GW_CONDITION_CIRCLE_NUMS[idx] if idx < len(GW_CONDITION_CIRCLE_NUMS) else f"{idx + 1}."
            quote_content += [
                "\n", f"{circle} ",
                ([label], "bold", None),
                " ›› ",
                (["هـــنـــا"], "link", link),
            ]
        extra_parts += ["\n\n", (quote_content, "blockquote", None)]
    if vote_link:
        quote_content = [
            "شرط تصويت", "\n\n",
            "• الشرط ", ("⬇️", EMOJI["arrow_down"]), "\n",
            (["تصويت"], "bold", None),
            " ›› ",
            (["هـــنـــا"], "link", vote_link),
        ]
        extra_parts += ["\n\n", (quote_content, "blockquote", None)]

    if autospin and autospin.get("mode") in ("count", "time"):
        icon = ("🎯", EMOJI["target_pin"]) if autospin["mode"] == "count" else ("🕖", EMOJI["gw_atime_clock"])
        notice_text = autospin.get("notice_text") or ""
        quote_content = [icon, " ", notice_text]
        extra_parts += ["\n\n", (quote_content, "blockquote", None)]

    extra_text, extra_entities = build_text_with_emojis(extra_parts) if extra_parts else ("", [])
    footer_text, footer_entities = build_brand_footer()

    base_text = cliche_text or ""
    base_entities = list(cliche_entities or [])
    shift = utf16_len(base_text)
    footer_shift = utf16_len(base_text + extra_text)

    combined_text = base_text + extra_text + footer_text
    combined_entities = (
        base_entities
        + shift_entities(extra_entities, shift)
        + shift_entities(footer_entities, footer_shift)
    )
    return combined_text, combined_entities


def build_giveaway_channel_keyboard(gw_code: str, current_count: int,
                                     antispam: bool = False,
                                     status: str = "open") -> InlineKeyboardMarkup:
    """يبني كيبورد منشور السحب في القناة/القروب (Image 5)، بنفس تنسيق/ألوان بقية أزرار البوت.

    عند تفعيل «منع الرشق» يتحوّل زر المشاركة إلى زر رابط (url) يفتح البوت مباشرة عبر
    ?start=gwcap_{gw_code} — بنفس آلية زر التصويت 🤍 في المسابقات — بدل إرسال أي رسالة
    خاصة وسيطة تحتوي على الرابط.

    الصف الثالث (أسفل الكيبورد) يتغيّر حسب حالة السحب (status):
    - "open"   : «ايقاف وسحب» (أحمر) لإيقاف استقبال المشاركات مؤقتًا، و
                 «ذكرني اذا فزت» (أخضر).
    - "paused" : بعد الضغط على «ايقاف وسحب» يتحوّل نفس الزر إلى «استئناف
                 المشاركة» (أخضر) لإعادة فتح المشاركة، والزر الآخر يتحوّل إلى
                 «ابدا السحب» (أحمر) الذي يقوم فعليًا باختيار الفائزين عشوائيًا.
    """
    join_text = f"• اضغط لـ المشاركة ({current_count})"
    if antispam:
        join_button = InlineKeyboardButton(
            join_text,
            url=f"https://t.me/{BOT_USERNAME}?start=gwcap_{gw_code}",
            style="primary",
        )
    else:
        join_button = InlineKeyboardButton(
            join_text, callback_data=f"gw_join:{gw_code}",
            style="primary",
        )

    if status == "paused":
        row3 = [
            InlineKeyboardButton(
                "استئناف المشاركة", callback_data=f"gw_resume:{gw_code}",
                style="success",
            ),
            InlineKeyboardButton(
                "ابدا السحب", callback_data=f"gw_draw:{gw_code}",
                style="danger",
            ),
        ]
    else:
        row3 = [
            InlineKeyboardButton(
                "ايقاف وسحب", callback_data=f"gw_pause:{gw_code}",
                style="danger",
            ),
            InlineKeyboardButton(
                "ذكرني اذا فزت",
                url=f"https://t.me/{BOT_USERNAME}?start=gw_remind",
                style="success",
            ),
        ]

    return InlineKeyboardMarkup([
        [join_button],
        [
            InlineKeyboardButton(
                "↻ إعادة نشر", callback_data=f"gw_repost:{gw_code}",
                style="primary",
            ),
            InlineKeyboardButton(
                "مشاركة السحب",
                url=f"https://t.me/{BOT_USERNAME}?start=gwshare_{gw_code}",
                style="success",
            ),
        ],
        row3,
    ])


def build_giveaway_join_notify_message(display_name: str, username: str, user_id: int,
                                        gw_number: str, total_participants: int) -> tuple:
    """رسالة إشعار «مشارك جديد في سحبك» تُرسل لمنشئ السحب فقط (Image 6)."""
    username_line = f"@{username}" if username else "—"
    parts = [
        ([("👤", EMOJI["gw_new_participant"]), " مشارك جديد في سحبك!"], "bold", None),
        "\n\n",
        f"• الاسم: {display_name}", "\n",
        f"• اليوزر: {username_line}", "\n",
        f"• الآيدي: {user_id}", "\n",
        f"• رقم السحب: #{gw_number}", "\n",
        f"• إجمالي المشاركين: {total_participants}",
    ]
    return build_text_with_emojis(parts)


def build_giveaway_join_notify_keyboard(gw_code: str, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "عرض الملف الشخصي", url=f"tg://user?id={user_id}",
            style="success", **emoji_kwargs("gw_view_profile"),
        )],
        [InlineKeyboardButton(
            "استبعاد", callback_data=f"gw_kick:{gw_code}:{user_id}",
            style="danger", **emoji_kwargs("gw_kick_btn"),
        )],
    ])


def build_giveaway_ended_message(cliche_text: str, cliche_entities, winners: list) -> tuple:
    """رسالة إعلان الفائز/الفائزين بعد «ايقاف وسحب»."""
    parts = [
        ([("🏆", EMOJI["trophy_win"]), " انتهى السحب!  ”"], "blockquote", None),
    ]
    if not winners:
        parts.append("\n\n")
        parts.append((["⚠️ لم يشارك أحد في هذا السحب، لم يتم اختيار فائز."], "bold", None))
    elif len(winners) == 1:
        user_id, name = winners[0]
        parts.append("\n\n")
        parts.append(([
            "الفائز ", ("🥇", EMOJI["medal"]), " : ", (name, "mention_id", user_id),
        ], "bold", None))
    else:
        for i, (user_id, name) in enumerate(winners):
            ordinal = ARABIC_ORDINALS[i] if i < len(ARABIC_ORDINALS) else f"رقم {i + 1}"
            parts.append("\n\n")
            parts.append(([
                f"الفائز {ordinal} ", ("🥇", EMOJI["medal"]), " : ", (name, "mention_id", user_id),
            ], "bold", None))
    return build_text_with_emojis(parts)


_FS_CLIENT = None
_FS_LOCK = threading.Lock()


class FSRow(dict):
    """
    يحاكي واجهة sqlite3.Row القديمة: وصول للحقول بالمفتاح row["field"] تمامًا كما
    كانت كل دوال الكود تستخدمها سابقًا مع SQLite، حتى لا يحتاج أي كود خارج طبقة
    قاعدة البيانات هذه إلى أي تعديل.
    """
    pass


def fs_db():
    """يعيد عميل Firestore واحد مشترك (Singleton) بدل تهيئته في كل استدعاء."""
    global _FS_CLIENT
    if _FS_CLIENT is None:
        with _FS_LOCK:
            if _FS_CLIENT is None:
                if not firebase_admin._apps:
                    if not FIREBASE_SERVICE_ACCOUNT.get("private_key"):
                        raise RuntimeError(
                            "متغير البيئة FIREBASE_PRIVATE_KEY غير موجود أو فارغ. "
                            "ضع فيه محتوى private_key من ملف Service Account قبل تشغيل البوت."
                        )
                    cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT)
                    firebase_admin.initialize_app(cred)
                _FS_CLIENT = firestore.client()
    return _FS_CLIENT


def _fs_row_or_none(doc) -> "FSRow | None":
    if doc is None or not doc.exists:
        return None
    return FSRow(doc.to_dict())


def _fs_create_or_integrity_error(doc_ref, data: dict) -> None:
    """يحاكي سلوك INSERT الذي يفشل عند تكرار المفتاح الأساسي (sqlite3.IntegrityError)."""
    from google.api_core.exceptions import AlreadyExists
    try:
        doc_ref.create(data)
    except AlreadyExists:
        raise sqlite3.IntegrityError("duplicate key")


def _fs_bump_counter(doc_ref, field: str, amount: int, extra: dict = None) -> None:
    """يزيد قيمة حقل رقمي بشكل ذري داخل معاملة (transaction) لتفادي تعارض التحديثات المتزامنة.
    القيمة النهائية لا تنزل تحت الصفر أبدًا (مهم عند خصم نقاط ملغاة)."""
    client = fs_db()
    transaction = client.transaction()

    @firestore.transactional
    def _txn(transaction):
        snap = doc_ref.get(transaction=transaction)
        current = (snap.to_dict().get(field, 0) if snap.exists else 0) or 0
        payload = dict(extra or {})
        payload[field] = max(0, current + amount)
        if snap.exists:
            transaction.update(doc_ref, payload)
        else:
            transaction.set(doc_ref, payload)

    _txn(transaction)


def _next_roulette_id() -> int:
    """عدّاد ذري بديل عن AUTOINCREMENT في SQLite، عبر معاملة على مستند عدّاد واحد."""
    client = fs_db()
    counter_ref = client.collection("counters").document("roulettes")
    transaction = client.transaction()

    @firestore.transactional
    def _txn(transaction):
        snap = counter_ref.get(transaction=transaction)
        current = (snap.to_dict().get("next_id", 0) if snap.exists else 0) or 0
        next_id = current + 1
        transaction.set(counter_ref, {"next_id": next_id})
        return next_id

    return _txn(transaction)


def init_db():
    """
    Firestore بدون بنية جداول مسبقة — المجموعات (collections) تُنشأ تلقائيًا عند
    أول عملية كتابة فيها. الشيء الوحيد المطلوب هنا هو ضمان وجود قيم الإعدادات
    الافتراضية إن لم تكن موجودة بعد (بديل INSERT OR IGNORE في SQLite).
    """
    client = fs_db()
    defaults = {
        "points_enabled": "1",
        "points_per_user": "1",
        "points_required": "100",
        "reward_type": "رصيد",
        "reward_value": "10",
        "points_title": DEFAULT_POINTS_TITLE,
        "points_conditions": DEFAULT_POINTS_CONDITIONS,
        "hide_participants": DEFAULT_HIDE_PARTICIPANTS,
        "game_cliche": DEFAULT_GAME_CLICHE,
        "required_channel_username": REQUIRED_CHANNEL_USERNAME,
        "required_channel_url": REQUIRED_CHANNEL_URL,
        "required_channel_next_username": "",
        "required_channel_auto_target": REQUIRED_CHANNEL_DEFAULT_TARGET,
    }
    for k, v in defaults.items():
        ref = client.collection("settings").document(k)
        if not ref.get().exists:
            ref.set({"value": v})

_SETTINGS_CACHE = {}

def get_setting(key: str) -> str:
    if key in _SETTINGS_CACHE:
        return _SETTINGS_CACHE[key]
    doc = fs_db().collection("settings").document(key).get()
    value = doc.to_dict().get("value") if doc.exists else None
    _SETTINGS_CACHE[key] = value
    return value

def set_setting(key: str, value: str):
    fs_db().collection("settings").document(key).set({"value": value})
    _SETTINGS_CACHE[key] = value

def create_roulette(owner_id: int, target_count: int) -> int:
    rid = _next_roulette_id()
    fs_db().collection("roulettes").document(str(rid)).set({
        "roulette_id": rid,
        "owner_id": owner_id,
        "target_count": target_count,
        "inline_message_id": None,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "channel_id": 0,
    })
    return rid

def _next_roulette_ids(count: int) -> list:
    """يحجز عدة معرّفات دفعة واحدة عبر معاملة واحدة فقط (بدل معاملة Firestore منفصلة
    لكل رقم) — هذا هو أحد سببي بطء ظهور خيارات «روليت سريع»."""
    client = fs_db()
    counter_ref = client.collection("counters").document("roulettes")
    transaction = client.transaction()

    @firestore.transactional
    def _txn(transaction):
        snap = counter_ref.get(transaction=transaction)
        current = (snap.to_dict().get("next_id", 0) if snap.exists else 0) or 0
        transaction.set(counter_ref, {"next_id": current + count})
        return list(range(current + 1, current + count + 1))

    return _txn(transaction)


def create_roulettes_batch(owner_id: int, target_counts: list) -> dict:
    """ينشئ كل خيارات «روليت سريع» (لكل الأعداد في ROULETTE_COUNTS) في طلبين فقط
    إلى Firestore (معاملة واحدة لحجز المعرّفات + كتابة دفعية واحدة)، بدل طلبين
    منفصلين لكل عدد (16 طلب سابقًا لـ 8 أعداد) — هذا يسرّع كثيرًا ظهور القائمة
    فور الضغط على «روليت سريع»."""
    ids = _next_roulette_ids(len(target_counts))
    client = fs_db()
    batch = client.batch()
    now_iso = datetime.now(timezone.utc).isoformat()
    result = {}
    for n, rid in zip(target_counts, ids):
        batch.set(client.collection("roulettes").document(str(rid)), {
            "roulette_id": rid,
            "owner_id": owner_id,
            "target_count": n,
            "inline_message_id": None,
            "status": "open",
            "created_at": now_iso,
            "channel_id": 0,
        })
        result[n] = rid
    batch.commit()
    return result

def set_inline_message_id(roulette_id: int, inline_message_id: str):
    ref = fs_db().collection("roulettes").document(str(roulette_id))
    doc = ref.get()
    if doc.exists and doc.to_dict().get("inline_message_id") is None:
        ref.update({"inline_message_id": inline_message_id})

def get_roulette(roulette_id: int):
    doc = fs_db().collection("roulettes").document(str(roulette_id)).get()
    return _fs_row_or_none(doc)

def set_roulette_status(roulette_id: int, status: str):
    fs_db().collection("roulettes").document(str(roulette_id)).update({"status": status})

def _counted_user_doc_id(user_id: int, roulette_id: int) -> str:
    return f"{roulette_id}_{user_id}"

def is_user_counted(user_id: int, roulette_id: int) -> bool:
    doc = fs_db().collection("counted_users").document(_counted_user_doc_id(user_id, roulette_id)).get()
    return doc.exists

def count_user(user_id: int, roulette_id: int, display_name: str = None):
    ref = fs_db().collection("counted_users").document(_counted_user_doc_id(user_id, roulette_id))
    if not ref.get().exists:
        ref.set({
            "user_id": user_id,
            "roulette_id": roulette_id,
            "display_name": display_name,
            "counted_at": datetime.now(timezone.utc).isoformat(),
        })

def count_participants(roulette_id: int) -> int:
    docs = fs_db().collection("counted_users").where("roulette_id", "==", roulette_id).stream()
    return sum(1 for _ in docs)

def get_participants_with_names(roulette_id: int):
    docs = list(fs_db().collection("counted_users").where("roulette_id", "==", roulette_id).stream())
    rows = [d.to_dict() for d in docs]
    rows.sort(key=lambda r: r.get("counted_at") or "")
    return [(r["user_id"], r.get("display_name") or str(r["user_id"])) for r in rows]

def get_points(owner_id: int) -> int:
    doc = fs_db().collection("owner_points").document(str(owner_id)).get()
    if not doc.exists:
        return 0
    return doc.to_dict().get("points", 0) or 0

def get_top_channel_points(limit: int = 5):
    """يعيد أعلى القنوات التي حصلت على نقاط فعلية من سحوبات منع الرشق."""
    client = fs_db()
    docs = client.collection("channel_points").stream()
    candidates = []
    for d in docs:
        data = d.to_dict()
        if (data.get("points") or 0) <= 0:
            continue
        chat_id = data.get("chat_id")
        rc_doc = client.collection("registered_chats").document(str(chat_id)).get()
        if not rc_doc.exists:
            continue
        rc = rc_doc.to_dict()
        if rc.get("chat_type") != "channel":
            continue
        candidates.append(FSRow({
            "chat_id": chat_id,
            "owner_id": data.get("owner_id"),
            "points": data.get("points"),
            "updated_at": data.get("updated_at"),
            "chat_title": rc.get("chat_title") or f"قناة {chat_id}",
        }))
    candidates.sort(key=lambda r: (r.get("points") or 0, r.get("updated_at") or ""), reverse=True)
    return candidates[:max(1, min(int(limit), 5))]



def register_bot_user_and_check_new(user_id: int) -> bool:
    """
    يسجّل أول تواصل لهذا المستخدم مع البوت مهما كان مصدر الدخول (رابط سحب/مسابقة،
    أو رابط عام، أو بحث عن اسم البوت... إلخ)، ويُستدعى مرة واحدة فقط في بداية
    /start قبل معالجة أي رابط دخول.
    يعيد True فقط إذا كانت هذه أول مرة يتواصل فيها المستخدم مع البوت إطلاقًا
    (مستخدم جديد كليًا) — وFalse إن كان قد استخدم البوت من قبل بأي طريقة،
    حتى لو لم يشارك في أي سحب سابقًا. تُستخدم هذه القيمة لمنع احتساب نقطة
    لصاحب السحب عندما يشارك مستخدم "قديم" وليس مستخدمًا جديدًا حقيقيًا.
    """
    from google.api_core.exceptions import AlreadyExists
    ref = fs_db().collection("known_bot_users").document(str(user_id))
    try:
        ref.create({
            "user_id": user_id,
            "first_seen_at": datetime.now(timezone.utc).isoformat(),
        })
        return True
    except AlreadyExists:
        return False

def reward_giveaway_user(user_id: int, gw_code: str, owner_id: int, chat_id: int) -> bool:
    """يمنح النقاط مرة واحدة عالميًا بعد نجاح مشاركة السحب والكابتشا."""
    client = fs_db()
    if get_setting("points_enabled") != "1":
        return False

    from google.api_core.exceptions import AlreadyExists
    rewarded_ref = client.collection("rewarded_users").document(str(user_id))
    try:
        rewarded_ref.create({
            "user_id": user_id,
            "first_roulette_id": None,
            "first_owner_id": owner_id,
            "first_giveaway_code": gw_code,
            "rewarded_at": datetime.now(timezone.utc).isoformat(),
        })
    except AlreadyExists:
        return False

    raw_value = get_setting("points_per_user")
    amount = max(int(raw_value) if raw_value and str(raw_value).isdigit() else 1, 0)

    owner_ref = client.collection("owner_points").document(str(owner_id))
    _fs_bump_counter(owner_ref, "points", amount, extra={"owner_id": owner_id})

    channel_ref = client.collection("channel_points").document(str(chat_id))
    _fs_bump_counter(channel_ref, "points", amount, extra={
        "chat_id": chat_id,
        "owner_id": owner_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })
    return True

def award_contest_owner_points(owner_id: int) -> int:
    """يمنح صاحب المسابقة نقاطًا مقابل صوت واحد مكتمل الشروط (اشتراك + تحقق +
    عدم تلاعب). يعيد عدد النقاط الممنوحة فعليًا (0 إن كانت خاصية النقاط معطّلة).
    لا تُستدعى إلا مرة واحدة لكل تصويت مؤكد — الاستدعاء متروك لـ
    register_confirmed_contest_vote الذي يضمن ذلك."""
    if get_setting("points_enabled") != "1":
        return 0
    raw_value = get_setting("points_per_user")
    amount = max(int(raw_value) if raw_value and str(raw_value).isdigit() else 1, 0)
    if amount <= 0:
        return 0
    owner_ref = fs_db().collection("owner_points").document(str(owner_id))
    _fs_bump_counter(owner_ref, "points", amount, extra={"owner_id": owner_id})
    return amount


def reverse_contest_owner_points(owner_id: int, amount: int) -> None:
    """يخصم من صاحب المسابقة نقاطًا سبق منحها مقابل تصويت أُلغي لاحقًا (خروج
    المصوّت من القنوات الإلزامية) — لا تنزل النقاط تحت الصفر أبدًا."""
    if not amount or amount <= 0 or not owner_id:
        return
    owner_ref = fs_db().collection("owner_points").document(str(owner_id))
    _fs_bump_counter(owner_ref, "points", -amount, extra={"owner_id": owner_id})


def create_withdraw_request(user_id: int, display_name: str, username: str,
                             points_amount: int) -> str:
    """
    نظام السحب الحقيقي: ينشئ طلب سحب جديد بحالة «pending» (قيد الانتظار)
    ويخصم كامل رصيد المستخدم من نقاطه فورًا عند تقديم الطلب — وليس عند
    تأكيد المالك — حتى لا يستطيع سحب نفس النقاط مرتين أثناء انتظار المراجعة.
    لا يُطلب من المستخدم أي نص إضافي؛ التواصل يتم عبر يوزر تليجرام الخاص به
    مباشرة (username إلزامي قبل إنشاء أي طلب). يعيد معرّف الطلب (request_id).
    """
    client = fs_db()
    ref = client.collection("withdraw_requests").document()
    ref.set({
        "request_id": ref.id,
        "user_id": user_id,
        "display_name": display_name,
        "username": username,
        "points_amount": points_amount,
        "status": "pending",
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    })
    owner_ref = client.collection("owner_points").document(str(user_id))
    _fs_bump_counter(owner_ref, "points", -points_amount, extra={"owner_id": user_id})
    return ref.id


def get_withdraw_request(request_id: str):
    doc = fs_db().collection("withdraw_requests").document(request_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["request_id"] = doc.id
    return data


def get_user_withdraw_requests(user_id: int):
    """يعيد كل طلبات سحب مستخدم مرتّبة تنازليًا (الأحدث أولاً)."""
    docs = fs_db().collection("withdraw_requests").where("user_id", "==", user_id).stream()
    rows = []
    for d in docs:
        data = d.to_dict()
        data["request_id"] = d.id
        rows.append(data)
    rows.sort(key=lambda r: r.get("requested_at") or "", reverse=True)
    return rows


def get_user_latest_withdraw_request(user_id: int):
    rows = get_user_withdraw_requests(user_id)
    return rows[0] if rows else None


def has_pending_withdraw_request(user_id: int) -> bool:
    latest = get_user_latest_withdraw_request(user_id)
    return bool(latest and latest.get("status") == "pending")


def get_pending_withdraw_requests(limit: int = 15):
    """يعيد كل طلبات السحب «قيد الانتظار» الحالية مرتّبة من الأقدم للأحدث
    (تُعرض في قسم المالك — سجلات مطالبة سحب)."""
    docs = fs_db().collection("withdraw_requests").where("status", "==", "pending").stream()
    rows = []
    for d in docs:
        data = d.to_dict()
        data["request_id"] = d.id
        rows.append(data)
    rows.sort(key=lambda r: r.get("requested_at") or "")
    return rows[:limit]


def mark_withdraw_completed(request_id: str) -> bool:
    """يعلّم طلب سحب كـ«مكتمل» (استلمه المستخدم فعليًا) — يُستدعى فقط من
    قسم المالك بعد إرسال المكافأة الحقيقية للمستخدم يدويًا. يعيد True فقط
    إذا كان الطلب لا يزال «قيد الانتظار» فعليًا (يمنع التأكيد المزدوج)."""
    ref = fs_db().collection("withdraw_requests").document(request_id)
    doc = ref.get()
    if not doc.exists or doc.to_dict().get("status") != "pending":
        return False
    ref.update({
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })
    return True

def toggle_remind_win(user_id: int) -> bool:
    ref = fs_db().collection("remind_win").document(str(user_id))
    doc = ref.get()
    now = datetime.now(timezone.utc).isoformat()
    if not doc.exists:
        ref.set({"user_id": user_id, "enabled": 1, "updated_at": now})
        return True
    current = doc.to_dict().get("enabled", 1)
    new_value = 0 if current == 1 else 1
    ref.update({"enabled": new_value, "updated_at": now})
    return bool(new_value)

def get_remind_win_state(user_id: int):
    doc = fs_db().collection("remind_win").document(str(user_id)).get()
    if not doc.exists:
        return None
    return bool(doc.to_dict().get("enabled"))

def save_registered_chat(chat_id: int, owner_id: int, chat_title: str, chat_type: str):
    fs_db().collection("registered_chats").document(str(chat_id)).set({
        "chat_id": chat_id,
        "owner_id": owner_id,
        "chat_title": chat_title,
        "chat_type": chat_type,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    })

def remove_registered_chat(chat_id: int):
    fs_db().collection("registered_chats").document(str(chat_id)).delete()

def get_registered_chats(owner_id: int):
    docs = fs_db().collection("registered_chats").where("owner_id", "==", owner_id).stream()
    rows = [FSRow(d.to_dict()) for d in docs]
    rows.sort(key=lambda r: r.get("registered_at") or "", reverse=True)
    return rows

def entities_to_json(entities) -> str:
    if not entities:
        return "[]"
    out = []
    for e in entities:
        d = {"type": e.type, "offset": e.offset, "length": e.length}
        if getattr(e, "url", None):
            d["url"] = e.url
        if getattr(e, "language", None):
            d["language"] = e.language
        if getattr(e, "custom_emoji_id", None):
            d["custom_emoji_id"] = e.custom_emoji_id
        out.append(d)
    return json.dumps(out, ensure_ascii=False)


def json_to_entities(raw: str):
    try:
        data = json.loads(raw or "[]")
    except Exception:
        return []
    result = []
    for d in data:
        result.append(MessageEntity(
            type=d.get("type"),
            offset=d.get("offset", 0),
            length=d.get("length", 0),
            url=d.get("url"),
            language=d.get("language"),
            custom_emoji_id=d.get("custom_emoji_id"),
        ))
    return result


def generate_contest_code() -> str:
    """كود فريد من 8 أرقام يُستخدم في رابط المشاركة وفي بيانات الأزرار."""
    while True:
        code = str(random.randint(10_000_000, 99_999_999))
        if not get_contest(code):
            return code


def generate_participant_code(contest_code: str) -> str:
    """كود المتسابق الفريد: C + كود المسابقة + 4 أرقام عشوائية."""
    while True:
        suffix = str(random.randint(1000, 9999))
        code = f"C{contest_code}{suffix}"
        if not get_participant_by_code(code):
            return code


def create_contest(contest_code: str, owner_id: int, chat_id: int, cliche_text: str,
                    cliche_entities, target_count: int, end_type: str, time_minutes,
                    winners_count, settings: dict, votes_target=None) -> None:
    fs_db().collection("contests").document(contest_code).set({
        "contest_code": contest_code,
        "owner_id": owner_id,
        "chat_id": chat_id,
        "cliche_text": cliche_text,
        "cliche_entities": entities_to_json(cliche_entities),
        "target_count": target_count,
        "end_type": end_type,
        "time_minutes": time_minutes,
        "votes_target": votes_target,
        "winners_count": winners_count,
        "notify_win": int(bool(settings.get("contest_notify_win", False))),
        "announce_results": int(bool(settings.get("contest_announce_results", False))),
        "approve_participants": int(bool(settings.get("contest_approve_participants", True))),
        "premium_only": int(bool(settings.get("contest_premium_only", False))),
        "channel_message_id": None,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


def get_contest(contest_code: str):
    doc = fs_db().collection("contests").document(contest_code).get()
    return _fs_row_or_none(doc)


def get_contests_by_owner(owner_id: int):
    """يعيد المسابقات الجارية (غير المنتهية) الخاصة بالمالك، الأحدث أولًا."""
    docs = fs_db().collection("contests").where("owner_id", "==", owner_id).stream()
    rows = [FSRow(d.to_dict()) for d in docs if d.to_dict().get("status") in ("open", "paused")]
    rows.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    return rows


def get_chat_title_by_id(chat_id: int) -> str:
    doc = fs_db().collection("registered_chats").document(str(chat_id)).get()
    if doc.exists and doc.to_dict().get("chat_title"):
        return doc.to_dict()["chat_title"]
    return str(chat_id)


def contest_display_name(contest) -> str:
    """يستخرج اسمًا معروضًا للمسابقة من أول سطر بنص إعلانها، أو رمزها كبديل."""
    text = (contest["cliche_text"] or "").strip()
    if text:
        first_line = text.splitlines()[0].strip()
        if len(first_line) > 40:
            first_line = first_line[:40].rstrip() + "…"
        return first_line
    return f"مسابقة #{contest['contest_code']}"


async def build_contest_post_link(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id):
    """يبني رابط منشور المسابقة في القناة (عام أو خاص) إن توفّر معرف الرسالة."""
    if not message_id:
        return None
    try:
        chat = await context.bot.get_chat(chat_id)
        if chat.username:
            return f"https://t.me/{chat.username}/{message_id}"
    except Exception:
        pass
    str_id = str(chat_id)
    if str_id.startswith("-100"):
        return f"https://t.me/c/{str_id[4:]}/{message_id}"
    return None


async def build_giveaway_boost_link(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> str:
    """يبني رابط تعزيز (Boost) القناة المرتبطة بسحب مفعّل عليه خيار «تعزيز
    القناة» (Image A1/A2)، بصيغة https://t.me/boost/<username> التي يتعرّف
    عليها تطبيق تيليجرام تلقائيًا ويفتح نافذة التعزيز الأصلية عند الضغط عليها
    (Image A4). يعيد نصًا فارغًا إن تعذّر جلب يوزر القناة (مثلاً قناة خاصة بلا
    يوزر عام)، لأن رابط التعزيز يتطلب يوزر عامًا للقناة."""
    try:
        chat = await context.bot.get_chat(chat_id)
        if chat.username:
            return f"https://t.me/boost/{chat.username}"
    except Exception:
        logger.exception("تعذّر جلب يوزر القناة %s لبناء رابط التعزيز", chat_id)
    return ""


async def announce_new_post(context: ContextTypes.DEFAULT_TYPE, source_chat_id: int,
                             sent_message_id: int, kind: str, extra: dict = None) -> None:
    """بعد نشر مسابقة أو سحب بنجاح في قناة/جروب المستخدم، يُنشر إعلانًا إضافيًا في قناة
    الإعلانات العامة (ANNOUNCE_CHANNEL_CHAT_ID) يحتوي على زر أخضر يفتح المنشور الأصلي
    مباشرة، لتوسيع دائرة انتشار السحوبات والمسابقات. لا يرفع أي استثناء أبدًا حتى لا
    يؤثر فشل الإعلان على نجاح النشر الأساسي في قناة المستخدم.
    """
    try:
        chat = await context.bot.get_chat(source_chat_id)
        label = f"@{chat.username}" if chat.username else (chat.title or "قناتك")
        if chat.username:
            post_link = f"https://t.me/{chat.username}/{sent_message_id}"
        else:
            str_id = str(source_chat_id)
            post_link = f"https://t.me/c/{str_id[4:]}/{sent_message_id}" if str_id.startswith("-100") else None
    except Exception:
        label = "قناتك"
        post_link = await build_contest_post_link(context, source_chat_id, sent_message_id)

    if not post_link:
        return

    if kind == "contest":
        text = f"🏁 مسابقة جديدة في قناة - {label}"
        button_text = "المشاركة في المسابقة"
    else:
        winners_count = (extra or {}).get("winners_count") or 1
        text = f"🎉 سحب جديد في قناة: {label}\n🏆 عدد الفائزين: {winners_count}"
        button_text = "رؤية السحب"

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton(button_text, url=post_link, style="success"),
    ]])
    try:
        await context.bot.send_message(
            chat_id=ANNOUNCE_CHANNEL_CHAT_ID,
            text=text,
            reply_markup=keyboard,
        )
    except Exception:
        logger.warning("تعذر نشر الإعلان في قناة الإعلانات (%s)", ANNOUNCE_CHANNEL_CHAT_ID)


def delete_contest_completely(contest_code: str) -> None:
    """يحذف المسابقة بكل مشاركيها وأصواتها نهائيًا من قاعدة البيانات."""
    client = fs_db()
    for d in client.collection("contest_votes").where("contest_code", "==", contest_code).stream():
        d.reference.delete()
    for d in client.collection("contest_participants").where("contest_code", "==", contest_code).stream():
        d.reference.delete()
    client.collection("contests").document(contest_code).delete()


def set_contest_channel_message(contest_code: str, message_id: int):
    fs_db().collection("contests").document(contest_code).update({"channel_message_id": message_id})


def set_contest_status(contest_code: str, status: str):
    fs_db().collection("contests").document(contest_code).update({"status": status})


def count_contest_participants(contest_code: str) -> int:
    docs = fs_db().collection("contest_participants").where("contest_code", "==", contest_code).stream()
    return sum(1 for _ in docs)


def _contest_participant_doc_id(contest_code: str, user_id: int) -> str:
    return f"{contest_code}_{user_id}"


def get_contest_participant(contest_code: str, user_id: int):
    doc = fs_db().collection("contest_participants").document(_contest_participant_doc_id(contest_code, user_id)).get()
    return _fs_row_or_none(doc)


def get_participant_by_code(participant_code: str):
    docs = fs_db().collection("contest_participants").where("participant_code", "==", participant_code).limit(1).stream()
    for d in docs:
        return FSRow(d.to_dict())
    return None


def add_contest_participant(contest_code: str, user_id: int, display_name: str, participant_code: str):
    ref = fs_db().collection("contest_participants").document(_contest_participant_doc_id(contest_code, user_id))
    _fs_create_or_integrity_error(ref, {
        "contest_code": contest_code,
        "user_id": user_id,
        "display_name": display_name,
        "participant_code": participant_code,
        "channel_message_id": None,
        "joined_at": datetime.now(timezone.utc).isoformat(),
    })


def remove_contest_participant(contest_code: str, user_id: int):
    client = fs_db()
    client.collection("contest_participants").document(_contest_participant_doc_id(contest_code, user_id)).delete()
    for d in client.collection("contest_votes").where("contest_code", "==", contest_code).stream():
        vd = d.to_dict()
        if vd.get("participant_user_id") == user_id:
            if vd.get("status", "confirmed") == "confirmed" and vd.get("points_awarded"):
                reverse_contest_owner_points(vd.get("owner_id"), vd.get("points_awarded"))
            d.reference.delete()


def set_participant_channel_message(contest_code: str, user_id: int, message_id: int):
    fs_db().collection("contest_participants").document(_contest_participant_doc_id(contest_code, user_id)).update(
        {"channel_message_id": message_id}
    )


def has_voted(contest_code: str, voter_id: int) -> bool:
    """يعيد True فقط إذا كان لدى المصوّت تصويت «مؤكد» حاليًا. التصويتات
    الملغاة (بسبب مغادرة القنوات الإلزامية) لا تُحتسب هنا، ما يسمح للمصوّت
    بالتصويت من جديد إذا عاد واشترك لاحقًا."""
    doc = fs_db().collection("contest_votes").document(f"{contest_code}_{voter_id}").get()
    if not doc.exists:
        return False
    return doc.to_dict().get("status", "confirmed") == "confirmed"


def register_confirmed_contest_vote(contest_code: str, voter_id: int, participant_user_id: int,
                                     owner_id: int) -> bool:
    """يسجّل تصويتًا «مؤكدًا» بعد اجتياز كل الشروط (اشتراك + تحقق + عدم تلاعب)،
    ويمنح صاحب المسابقة نقاطه فورًا لهذا الصوت. إن كان هناك تصويت سابق أُلغي
    لنفس المصوّت في نفس المسابقة، يُستبدل بتصويت جديد مؤكد بدل رفضه. يعيد
    True إذا سُجّل التصويت فعليًا، وFalse إذا كان هناك تصويت مؤكد سابقًا بالفعل."""
    ref = fs_db().collection("contest_votes").document(f"{contest_code}_{voter_id}")
    snap = ref.get()
    if snap.exists and snap.to_dict().get("status", "confirmed") == "confirmed":
        return False
    ref.set({
        "contest_code": contest_code,
        "voter_id": voter_id,
        "participant_user_id": participant_user_id,
        "owner_id": owner_id,
        "voted_at": datetime.now(timezone.utc).isoformat(),
        "status": "confirmed",
        "points_awarded": 0,
    })
    amount = award_contest_owner_points(owner_id)
    if amount:
        ref.update({"points_awarded": amount})
    return True


def has_voted_for(contest_code: str, voter_id: int, participant_user_id: int) -> bool:
    """يتحقق من أن المستخدم صوّت تحديدًا لهذا المتسابق (وليس لأي متسابق آخر في نفس
    المسابقة) — يُستخدم للتحقق من شرط «تصويت متسابق» قبل السماح بالمشاركة في السحب.
    لا يُحتسب أي تصويت مُلغى بسبب مغادرة القنوات الإلزامية."""
    doc = fs_db().collection("contest_votes").document(f"{contest_code}_{voter_id}").get()
    if not doc.exists:
        return False
    data = doc.to_dict()
    return (
        data.get("status", "confirmed") == "confirmed"
        and data.get("participant_user_id") == participant_user_id
    )


def get_participant_votes(contest_code: str, participant_user_id: int) -> int:
    docs = fs_db().collection("contest_votes").where("contest_code", "==", contest_code).stream()
    return sum(
        1 for d in docs
        if d.to_dict().get("participant_user_id") == participant_user_id
        and d.to_dict().get("status", "confirmed") == "confirmed"
    )


def get_contest_leaderboard(contest_code: str):
    """
    يُعيد قائمة كل المتسابقين مرتّبة تنازليًا حسب عدد الأصوات (الأعلى أولًا)،
    وعند التعادل يُقدَّم من انضمّ أولًا. كل عنصر: (user_id, display_name, participant_code, votes).
    التصويتات الملغاة (بسبب مغادرة القنوات الإلزامية) لا تُحتسب ضمن العدد.
    """
    client = fs_db()
    participants = list(client.collection("contest_participants").where("contest_code", "==", contest_code).stream())
    votes = list(client.collection("contest_votes").where("contest_code", "==", contest_code).stream())
    vote_counts = {}
    for v in votes:
        vd = v.to_dict()
        if vd.get("status", "confirmed") != "confirmed":
            continue
        pid = vd.get("participant_user_id")
        vote_counts[pid] = vote_counts.get(pid, 0) + 1
    rows = []
    for p in participants:
        data = p.to_dict()
        uid = data.get("user_id")
        rows.append((
            uid, data.get("display_name") or str(uid), data.get("participant_code"),
            vote_counts.get(uid, 0), data.get("joined_at") or "",
        ))
    rows.sort(key=lambda r: (-r[3], r[4]))
    return [(r[0], r[1], r[2], r[3]) for r in rows]


def get_open_time_contests():
    """يُعيد كل المسابقات المفتوحة المعتمدة على وقت محدد (لإعادة جدولة المؤقتات بعد إعادة تشغيل البوت)."""
    docs = fs_db().collection("contests").where("status", "==", "open").stream()
    rows = []
    for d in docs:
        data = d.to_dict()
        if data.get("end_type") == "time" and data.get("time_minutes") is not None:
            rows.append(FSRow(data))
    return rows


def generate_gw_code() -> str:
    """كود فريد من 8 محارف hex يُستخدم في بيانات أزرار السحب المنشور."""
    while True:
        code = uuid.uuid4().hex[:8]
        if not get_giveaway(code):
            return code


def create_giveaway(gw_code: str, owner_id: int, chat_id: int, cliche_text: str,
                     cliche_entities, winners_count: int, settings: dict) -> None:
    autospin_mode = settings.get("gw_autospin_mode")
    autospin_target = settings.get("gw_autospin_target")
    autospin_minutes = settings.get("gw_autospin_minutes")
    autospin_ends_at = (
        (datetime.now(timezone.utc) + timedelta(minutes=autospin_minutes)).isoformat()
        if autospin_mode == "time" and autospin_minutes else None
    )
    fs_db().collection("giveaways").document(gw_code).set({
        "gw_code": gw_code,
        "owner_id": owner_id,
        "chat_id": chat_id,
        "cliche_text": cliche_text,
        "cliche_entities": entities_to_json(cliche_entities),
        "winners_count": winners_count,
        "boost_required": int(bool(settings.get("gw_boost", False))),
        "premium_only": int(bool(settings.get("gw_premium", False))),
        "antispam": int(bool(settings.get("gw_antispam", False))),
        "vote_contest_code": settings.get("gw_vote_contest_code"),
        "vote_participant_id": settings.get("gw_vote_participant_id"),
        "vote_participant_code": settings.get("gw_vote_participant_code"),
        "vote_display_name": settings.get("gw_vote_display_name"),
        "condition_channels": settings.get("gw_condition_channels") or [],
        "channel_message_id": None,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "autospin_mode": autospin_mode,
        "autospin_target": autospin_target,
        "autospin_minutes": autospin_minutes,
        "autospin_ends_at": autospin_ends_at,
    })


def get_giveaway(gw_code: str):
    doc = fs_db().collection("giveaways").document(gw_code).get()
    return _fs_row_or_none(doc)


def set_giveaway_channel_message(gw_code: str, message_id: int):
    fs_db().collection("giveaways").document(gw_code).update({"channel_message_id": message_id})


def set_giveaway_status(gw_code: str, status: str):
    fs_db().collection("giveaways").document(gw_code).update({"status": status})


def count_giveaway_participants(gw_code: str) -> int:
    docs = fs_db().collection("giveaway_participants").where("gw_code", "==", gw_code).stream()
    return sum(1 for _ in docs)


def _giveaway_participant_doc_id(gw_code: str, user_id: int) -> str:
    return f"{gw_code}_{user_id}"


def is_giveaway_participant(gw_code: str, user_id: int) -> bool:
    doc = fs_db().collection("giveaway_participants").document(_giveaway_participant_doc_id(gw_code, user_id)).get()
    return doc.exists


def add_giveaway_participant(gw_code: str, user_id: int, display_name: str, username: str = None) -> bool:
    """يضيف مشاركًا جديدًا؛ يُعيد False إن كان مسجّلاً بالفعل."""
    from google.api_core.exceptions import AlreadyExists
    ref = fs_db().collection("giveaway_participants").document(_giveaway_participant_doc_id(gw_code, user_id))
    try:
        ref.create({
            "gw_code": gw_code,
            "user_id": user_id,
            "display_name": display_name,
            "username": username,
            "joined_at": datetime.now(timezone.utc).isoformat(),
        })
        return True
    except AlreadyExists:
        return False


def remove_giveaway_participant(gw_code: str, user_id: int):
    fs_db().collection("giveaway_participants").document(_giveaway_participant_doc_id(gw_code, user_id)).delete()


def get_giveaway_participants(gw_code: str):
    docs = list(fs_db().collection("giveaway_participants").where("gw_code", "==", gw_code).stream())
    rows = [d.to_dict() for d in docs]
    rows.sort(key=lambda r: r.get("joined_at") or "")
    return [(r["user_id"], r.get("display_name") or str(r["user_id"])) for r in rows]


def get_giveaways_by_owner(owner_id: int):
    """يعيد كل سحوبات المستخدم (بجميع حالاتها)، الأقدم أولًا، لترقيمها بثبات عبر الصفحات."""
    docs = fs_db().collection("giveaways").where("owner_id", "==", owner_id).stream()
    rows = [FSRow(d.to_dict()) for d in docs]
    rows.sort(key=lambda r: r.get("created_at") or "")
    return rows


def get_open_time_giveaways():
    """يُعيد كل السحوبات المفتوحة المعتمدة على «سحب تلقائي - وقت محدد» (لإعادة
    جدولة المؤقتات بعد إعادة تشغيل البوت، ولتحديث العد التنازلي كل 10 دقائق)."""
    docs = fs_db().collection("giveaways").where("status", "==", "open").stream()
    rows = []
    for d in docs:
        data = d.to_dict()
        if data.get("autospin_mode") == "time" and data.get("autospin_ends_at"):
            rows.append(FSRow(data))
    return rows


def giveaway_autospin_end_datetime(giveaway) -> datetime:
    end_at = datetime.fromisoformat(giveaway["autospin_ends_at"])
    if end_at.tzinfo is None:
        end_at = end_at.replace(tzinfo=timezone.utc)
    return end_at


def count_giveaway_new_rewarded(gw_code: str) -> int:
    """يعيد عدد المشاركين الجدد الذين احتُسبت نقاط لصاحب السحب بسبب مشاركتهم في هذا السحب تحديدًا."""
    docs = fs_db().collection("rewarded_users").where("first_giveaway_code", "==", gw_code).stream()
    return sum(1 for _ in docs)


async def bot_chat_status_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    يلتقط لحظة إضافة/ترقية البوت كمشرف (أو إزالته) في قناة أو جروب،
    ويسجّل/يحذف القناة أو الجروب تلقائيًا لصاحب العملية.
    """
    result = update.my_chat_member
    if result is None:
        return

    chat = result.chat
    if chat.type not in ("channel", "group", "supergroup"):
        return

    if chat.username and chat.username.lower() == ANNOUNCE_CHANNEL_USERNAME.lower():
        return

    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status
    actor = result.from_user

    became_admin = new_status == "administrator" and old_status != "administrator"
    left_or_removed = new_status in ("left", "kicked", "member", "restricted") and old_status == "administrator"

    if became_admin and actor is not None:
        save_registered_chat(
            chat_id=chat.id,
            owner_id=actor.id,
            chat_title=chat.title or (f"@{chat.username}" if chat.username else str(chat.id)),
            chat_type=chat.type,
        )
    elif left_or_removed:
        remove_registered_chat(chat.id)


def build_points_message(user_id: int) -> tuple:
    """واجهة ربح مختصرة: كل المحتوى عريض والجمل الأساسية مقتبسة. يعرض أيضًا
    حالة آخر طلب سحب للمستخدم إن وُجد (قيد الانتظار / مكتمل)."""
    pts = get_points(user_id)
    content = [
        ("🎁", EMOJI["star"]),
        " ", get_setting("points_title") or "ربح من البوت",
        "\n\n",
        ([
            f"💎 رصيدك الحالي: {pts} نقطة",
            "\n",
            f"🎯 المكافأة عند: {get_setting('points_required') or '0'} نقطة",
        ], "blockquote", None),
        "\n\n",
        ([
            "📌 الشروط:\n",
            get_setting("points_conditions") or "الربح من قسم «إنشاء سحب» فقط.",
            "\n\n”",
        ], "blockquote", None),
    ]
    latest = get_user_latest_withdraw_request(user_id)
    if latest:
        status_label = "🟡 قيد الانتظار" if latest["status"] == "pending" else "🟢 مكتمل"
        content.append("\n\n")
        content.append(([
            "📋 آخر طلب سحب لك:\n",
            f"💎 عدد النقاط: {latest.get('points_amount', 0)}\n",
            f"📌 الحالة: {status_label} ”",
        ], "blockquote", None))
    return build_text_with_emojis([(content, "bold", None)])


def build_points_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """كيبورد قسم ربح: زر السحب يتغيّر حسب حالة المستخدم —
    مقفل (رمادي/عادي) إن لم يصل بعد للحد المطلوب، أخضر واحترافي عند
    الوصول إليه، أو تنبيه «قيد الانتظار» إن كان لديه طلب سابق لم يُستكمل."""
    rows = []
    required = int(get_setting("points_required") or "0")
    if required > 0:
        pts = get_points(user_id)
        if has_pending_withdraw_request(user_id):
            rows.append([InlineKeyboardButton(
                "🟡 طلب السحب قيد الانتظار", callback_data="withdraw_pending",
            )])
        elif pts >= required:
            rows.append([InlineKeyboardButton(
                f"✅ سحب {pts} نقطة", callback_data="withdraw_start", style="success",
            )])
        else:
            rows.append([InlineKeyboardButton(
                f"🔒 سحب ({pts}/{required} نقطة)", callback_data="withdraw_locked",
            )])
    rows.append([InlineKeyboardButton(
        "🔙 رجوع", callback_data="back_main_menu",
        style="danger", **emoji_kwargs("back_section_btn"),
    )])
    return InlineKeyboardMarkup(rows)


def build_points_statistics_message() -> tuple:
    """عرض أعلى خمس قنوات بحسب النقاط المسجلة فعليًا."""
    rows = get_top_channel_points(5)
    content = [
        ("📊", EMOJI["chart"]),
        " إحصائيات النقاط",
        "\n\n",
    ]
    if not rows:
        content.append((["📭 لا توجد نقاط مسجلة للقنوات حتى الآن ”"], "blockquote", None))
    else:
        content.append((["🏆 أعلى 5 قنوات بالنقاط ”"], "blockquote", None))
        content.append("\n\n")
        medals = ["🥇", "🥈", "🥉", "🏅", "🎖️"]
        for index, row in enumerate(rows):
            title = row["chat_title"] or str(row["chat_id"])
            content.append(([
                f"{medals[index]} {index + 1}. {title}\n",
                f"💎 النقاط: {row['points']}\n",
                "━━━━━━━━━━━━\n",
            ], "blockquote", None))
    content.append("\n")
    content.append((["📌 تُحتسب النقاط من المشاركات المؤكدة في سحوبات منع الرشق فقط ”"], "blockquote", None))
    return build_text_with_emojis([(content, "bold", None)])


def build_points_statistics_keyboard() -> InlineKeyboardMarkup:
    return _build_single_back_keyboard("🔙 رجوع", "back_main_menu", "danger", "back_section_btn")


def build_points_settings_message() -> tuple:
    enabled = get_setting("points_enabled") == "1"
    status = "مفعّل ✅" if enabled else "متوقف ❌"
    return build_text_with_emojis([
        ([
            ("⚙️", EMOJI["gear"]), " إعدادات النقاط",
            "\n\n",
            ([
                f"🔘 الحالة: {status}\n",
                f"💎 لكل مشارك جديد: {get_setting('points_per_user') or '1'} نقطة\n",
                f"🎯 الحد الأدنى للسحب: {get_setting('points_required') or '0'} نقطة",
            ], "blockquote", None),
            "\n\n",
            (["اختر الإعداد الذي تريد تعديله ”"], "blockquote", None),
        ], "bold", None),
    ])


def build_points_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تفعيل" if get_setting("points_enabled") != "1" else "⛔ تعطيل",
                                 callback_data="points_toggle", style="success" if get_setting("points_enabled") != "1" else "danger"),
            InlineKeyboardButton("💎 لكل مستخدم", callback_data="points_edit:points_per_user", style="primary"),
        ],
        [InlineKeyboardButton("🎯 الحد الأدنى للسحب", callback_data="points_edit:points_required", style="primary")],
        [InlineKeyboardButton("📝 نصوص قسم ربح", callback_data="points_text_settings", style="primary")],
        [InlineKeyboardButton("↩️ العودة للوضع الافتراضي", callback_data="points_restore_defaults", style="success")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_points_section", style="danger")],
    ])


def build_points_text_settings_message() -> tuple:
    return build_text_with_emojis([
        ([
            ("📝", EMOJI["doc"]), " تعديل نصوص قسم ربح",
            "\n\n",
            ([
                f"🏷️ العنوان: {get_setting('points_title') or 'ربح من البوت'}\n",
                "📌 يمكنك تعديل العنوان أو جملة الشروط من الأزرار أدناه ”",
            ], "blockquote", None),
        ], "bold", None),
    ])


def build_points_text_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏷️ تعديل العنوان", callback_data="points_edit:points_title", style="primary")],
        [InlineKeyboardButton("📌 تعديل الشروط", callback_data="points_edit:points_conditions", style="primary")],
        [InlineKeyboardButton("↩️ افتراضي", callback_data="points_restore_defaults", style="success")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="points_settings", style="danger")],
    ])


def build_owner_withdraw_section_message() -> tuple:
    """سجلات مطالبة سحب — قسم المالك: يعرض كل طلبات السحب الحالية «قيد
    الانتظار» مع يوزر ورقم كل مستخدم، ليتمكن المالك من التواصل معه مباشرة
    عبر يوزره وإرسال المكافأة يدويًا، ثم تأكيد الاستلام عبر الزر الملحق."""
    pending = get_pending_withdraw_requests()
    content = [
        "💳 سجلات طلبات السحب",
        "\n\n",
    ]
    if not pending:
        content.append((["📭 لا توجد طلبات سحب قيد الانتظار حاليًا ”"], "blockquote", None))
    else:
        for req in pending:
            name = req.get("display_name") or str(req.get("user_id"))
            username = req.get("username")
            contact = f"@{username}" if username else "-"
            content.append(([
                f"👤 {name} (ID: {req.get('user_id')})\n",
                f"🔗 يوزر: {contact}\n",
                f"💎 النقاط: {req.get('points_amount', 0)}\n",
                f"🕒 وقت الطلب: {req.get('requested_at', '')[:16]}",
            ], "blockquote", None))
            content.append("\n\n")
    return build_text_with_emojis([(content, "bold", None)])


def build_owner_withdraw_section_keyboard() -> InlineKeyboardMarkup:
    pending = get_pending_withdraw_requests()
    rows = [
        [InlineKeyboardButton(
            f"✅ تأكيد استلام: {(req.get('display_name') or str(req.get('user_id')))[:20]}",
            callback_data=f"wd_complete:{req['request_id']}", style="success",
        )]
        for req in pending
    ]
    rows.append([InlineKeyboardButton("🔙 رجوع", callback_data="owner_points_section", style="danger",
                                       **emoji_kwargs("back_section_btn"))])
    return InlineKeyboardMarkup(rows)


def build_owner_section_message() -> tuple:
    return build_text_with_emojis([
        ([
            "👑 قسم المالك",
            "\n\n",
            (["اختر القسم الذي تريد إدارته من الأزرار أدناه ”"], "blockquote", None),
        ], "bold", None),
    ])


def build_owner_section_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 قسم ربح", callback_data="owner_points_section", style="primary")],
        [InlineKeyboardButton("📢 اشتراك اجباري", callback_data="owner_sub_section", style="primary")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="back_main_menu", style="danger",
                              **emoji_kwargs("back_section_btn"))],
    ])


def build_owner_points_section_message() -> tuple:
    return build_text_with_emojis([
        ([
            "💰 قسم ربح — إدارة المالك",
            "\n\n",
            (["من هنا يمكنك التحكم بكل إعدادات قسم الربح (النقاط، المكافآت، النصوص) ”"], "blockquote", None),
        ], "bold", None),
    ])


def build_owner_points_section_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "⚙️ إعدادات", callback_data="points_settings",
            style="primary", **emoji_kwargs("gear"),
        )],
        [InlineKeyboardButton(
            "💳 سجلات طلبات السحب", callback_data="owner_withdraw_section",
            style="primary",
        )],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_section", style="danger",
                              **emoji_kwargs("back_section_btn"))],
    ])


def build_owner_sub_section_message() -> tuple:
    current = get_required_channel_username()
    next_username = get_required_channel_next_username()
    target = get_required_channel_auto_target()
    next_line = f"@{next_username} (عند {target} مشترك)" if next_username else "غير محددة (لا يوجد تغيير تلقائي)"
    return build_text_with_emojis([
        ([
            "📢 الاشتراك الإجباري — إدارة المالك",
            "\n\n",
            ([
                f"📡 القناة الحالية: @{current}\n",
                f"🔄 القناة التالية (تلقائي): {next_line}",
            ], "blockquote", None),
            "\n\n",
            (["اختر ما تريد تعديله من الأزرار أدناه ”"], "blockquote", None),
        ], "bold", None),
    ])


def build_owner_sub_section_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ تغيير القناة الحالية", callback_data="owner_sub_change_current", style="primary")],
        [InlineKeyboardButton("🔄 التغيير التلقائي", callback_data="owner_sub_auto", style="primary")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_section", style="danger",
                              **emoji_kwargs("back_section_btn"))],
    ])


def build_owner_sub_auto_message() -> tuple:
    next_username = get_required_channel_next_username()
    target = get_required_channel_auto_target()
    next_line = f"@{next_username}" if next_username else "غير محددة"
    status_line = (
        f"سيتم التحويل تلقائيًا إلى @{next_username} عند وصول القناة الحالية إلى {target} مشترك."
        if next_username else
        "لن يحدث أي تغيير تلقائي حتى تحدد القناة التالية."
    )
    return build_text_with_emojis([
        ([
            "🔄 التغيير التلقائي لقناة الاشتراك",
            "\n\n",
            ([
                f"🎯 عدد الاشتراكات المطلوب: {target}\n",
                f"📢 القناة التالية: {next_line}",
            ], "blockquote", None),
            "\n\n",
            ([status_line, " ”"], "blockquote", None),
        ], "bold", None),
    ])


def build_owner_sub_auto_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 تخصيص عدد الاشتراكات المطلوبة", callback_data="owner_sub_edit_target", style="primary")],
        [InlineKeyboardButton("📢 تحديد القناة التالية", callback_data="owner_sub_edit_next", style="primary")],
        [InlineKeyboardButton("❌ إلغاء القناة التالية", callback_data="owner_sub_clear_next", style="danger")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_sub_section", style="danger",
                              **emoji_kwargs("back_section_btn"))],
    ])


def build_main_keyboard(remind_state=None, user_id: int = None) -> InlineKeyboardMarkup:
    if remind_state is True:
        remind_emoji_key = "remind_on"
        remind_label = "ألغِ التذكير إن فزت"
    elif remind_state is False:
        remind_emoji_key = "remind_off"
        remind_label = "ذكرني إذا فزت"
    else:
        remind_emoji_key = "remind_check"
        remind_label = "ذكرني إذا فزت"

    keyboard = [
        [
            InlineKeyboardButton("انشاء سحب", callback_data="create_draw",
                                  style="primary", **emoji_kwargs("trophy_create_draw")),
            InlineKeyboardButton("روليت سريع", callback_data="quick_roulette_menu",
                                  style="primary", **emoji_kwargs("roulette")),
        ],
        [
            InlineKeyboardButton("سحوباتي", callback_data="my_draws",
                                  style="primary", **emoji_kwargs("draws_check")),
        ],
        [
            InlineKeyboardButton("📊 الإحصائيات", callback_data="points_stats",
                                 style="primary", **emoji_kwargs("chart")),
            InlineKeyboardButton("🎁 ربح", callback_data="my_stats",
                                 style="primary", **emoji_kwargs("star")),
        ],
        [
            InlineKeyboardButton("الشروط والأحكام", callback_data="terms",
                                  style="danger", **emoji_kwargs("doc")),
            InlineKeyboardButton(remind_label, callback_data="remind_win",
                                  style="success", **emoji_kwargs(remind_emoji_key)),
        ],
        [
            InlineKeyboardButton("دعم البوت", callback_data="support_bot",
                                  style="success", **emoji_kwargs("star")),
            InlineKeyboardButton("الدعم الفني", url=f"https://t.me/{TECH_SUPPORT_USERNAME}",
                                  style="success", **emoji_kwargs("tech")),
        ],
        [
            InlineKeyboardButton("انشاء مسابقة", callback_data="create_contest",
                                  style="primary", **emoji_kwargs("trophy_contest")),
        ],
    ]
    if user_id is not None and is_owner(user_id):
        keyboard.append([InlineKeyboardButton(
            "👑 قسم المالك", callback_data="owner_section",
            style="danger", **emoji_kwargs("gear"),
        )])
    return InlineKeyboardMarkup(keyboard)

def build_quick_roulette_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                "انشاء روليت",
                switch_inline_query_chosen_chat=SwitchInlineQueryChosenChat(
                    query="انشاء روليت",
                    allow_channel_chats=True,
                    allow_group_chats=True,
                    allow_bot_chats=True,
                    allow_user_chats=True,
                ),
                style="success",
                **emoji_kwargs("roulette"),
            ),
        ],
        [
            InlineKeyboardButton("الإعدادات", callback_data="qr_settings",
                                  style="primary", **emoji_kwargs("gear")),
        ],
        [
            InlineKeyboardButton("رجوع", callback_data="back_to_main",
                                  style="danger"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def build_roulette_privacy_settings_text() -> str:
    hide = get_setting("hide_participants") == "1"
    participants_status = "مخفي" if hide else "ظاهر"
    cliche = get_setting("game_cliche") or DEFAULT_GAME_CLICHE
    return (
        "⚙️ الإعدادات والخصوصية\n\n"
        f"اسماء المشاركين : {participants_status}\n"
        f"كليشة اللعبه : {cliche}\n\n"
        "يمكنك التحكم في ظهور و اخفاء اسماء المشاركين في كليشه اللعبه الرسميه\n\n"
        "🆕 يمكنك اضافه كليشه للعبه"
    )

def build_roulette_privacy_settings_keyboard() -> InlineKeyboardMarkup:
    hide = get_setting("hide_participants") == "1"
    participants_label = f"اسماء المشاركين : {'مخفي' if hide else 'ظاهر'}"
    keyboard = [
        [
            InlineKeyboardButton(participants_label, callback_data="toggle_hide_participants_internal",
                                  style="primary", **emoji_kwargs("hide_participants_btn")),
            InlineKeyboardButton("كليشة اللعبة", callback_data="edit_game_cliche",
                                  style="primary", **emoji_kwargs("cliche_btn")),
        ],
        [
            InlineKeyboardButton("الرجوع للافتراضي", callback_data="restore_defaults_roulette",
                                  style="success", **emoji_kwargs("restore_defaults_btn")),
        ],
        [
            InlineKeyboardButton("رجوع", callback_data="section_roulette",
                                  style="danger", **emoji_kwargs("back_section_btn")),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def build_cliche_prompt_text() -> str:
    cliche = get_setting("game_cliche") or DEFAULT_GAME_CLICHE
    return (
        "✍️ أرسل كليشة اللعبة\n\n"
        "اكتب نص السحب الذي تريد نشره في القناة.\n"
        "يمكنك استخدام تنسيقات تيليجرام، مثل:\n"
        "• نص عريض\n"
        "• نص مائل\n"
        "• نص مشوش\n"
        "- يمكنك وضع رابط داخل النص\n"
        "> نص مقتبس\n\n"
        "النص الحالي:\n"
        f"> • {cliche}"
    )

def build_cliche_prompt_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("رجوع", callback_data="qr_settings", style="danger", **emoji_kwargs("back_section_btn"))]
    ])

def roulette_share_keyboard(roulette_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔶 اضغط لـ المشاركة 🔶", callback_data=f"rr_join_{roulette_id}", style="primary")],
        [InlineKeyboardButton("🔷 تدوير الروليت 🔷", callback_data=f"rr_spin_{roulette_id}", style="danger")],
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscribed = await is_user_subscribed(context, update.effective_user.id)
    if not subscribed:
        text, entities = build_subscription_required_message()
        await update.message.reply_text(
            text, entities=entities, reply_markup=build_subscription_required_keyboard()
        )
        return

    is_genuinely_new = register_bot_user_and_check_new(update.effective_user.id)

    args = context.args
    if args and args[0].startswith("rr_"):
        await handle_roulette_entry(update, context, args[0][len("rr_"):])
        return
    if args and args[0].startswith("compjoin_"):
        await handle_contest_join_entry(update, context, args[0][len("compjoin_"):])
        return
    if args and args[0].startswith("compvote_"):
        await handle_contest_vote_entry(update, context, args[0][len("compvote_"):])
        return
    if args and args[0].startswith("gwcap_"):
        await handle_giveaway_captcha_entry(
            update, context, args[0][len("gwcap_"):], is_genuinely_new=is_genuinely_new,
        )
        return
    if args and args[0].startswith("gwshare_"):
        await handle_giveaway_share_entry(update, context, args[0][len("gwshare_"):])
        return
    if args and args[0] == "gw_remind":
        await handle_giveaway_remind_entry(update, context)
        return
    text, entities = build_welcome_message(update.effective_user)
    remind_state = get_remind_win_state(update.effective_user.id)
    await update.message.reply_text(
        text, entities=entities,
        reply_markup=build_main_keyboard(remind_state, update.effective_user.id),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )

async def check_sub_status_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يُستدعى عند الضغط على زر «تحقق من الاشتراك» — يعيد فحص الاشتراك في القناة."""
    query = update.callback_query
    _SUBSCRIPTION_CACHE.pop(query.from_user.id, None)
    subscribed = await is_user_subscribed(
        context, query.from_user.id, force_refresh=True
    )
    if not subscribed:
        await query.answer("⚠️ لم يتم العثور على اشتراكك، يرجى الاشتراك أولاً ثم إعادة المحاولة.", show_alert=True)
        return
    await query.answer()
    text, entities = build_welcome_message(query.from_user)
    remind_state = get_remind_win_state(query.from_user.id)
    await query.edit_message_text(
        text=text, entities=entities,
        reply_markup=build_main_keyboard(remind_state, query.from_user.id),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )

async def handle_roulette_entry(update: Update, context: ContextTypes.DEFAULT_TYPE, raw_id: str):
    user = update.effective_user
    try:
        roulette_id = int(raw_id)
    except ValueError:
        text, entities = build_welcome_message(user)
        remind_state = get_remind_win_state(user.id)
        await update.message.reply_text(
            text, entities=entities, reply_markup=build_main_keyboard(remind_state, user.id),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        return

    roulette = get_roulette(roulette_id)
    if not roulette:
        _bt, _be = bold_notice("⚠️ هذا الروليت غير موجود.")
        await update.message.reply_text(text=_bt, entities=_be)
        return

    if roulette["status"] != "open":
        _bt, _be = bold_notice("⚠️ انتهى هذا الروليت بالفعل.")
        await update.message.reply_text(text=_bt, entities=_be)
        return

    owner_id = roulette["owner_id"]
    target = roulette["target_count"]

    if is_user_counted(user.id, roulette_id):
        current = count_participants(roulette_id)
        _bt, _be = bold_notice(f"✅ أنت مسجّل بالفعل في هذا الروليت.\n👥 المشاركين: {current}/{target}")
        await update.message.reply_text(text=_bt, entities=_be)
        return

    count_user(user.id, roulette_id, user.first_name or user.username or str(user.id))

    current = count_participants(roulette_id)
    _bt, _be = bold_notice(f"✅ تم تسجيل مشاركتك بنجاح!\n👥 المشاركين: {current}/{target}")
    await update.message.reply_text(text=_bt, entities=_be)

    if roulette["inline_message_id"]:
        try:
            body_text, body_entities = build_quick_roulette_channel_message(target, current)
            await context.bot.edit_message_text(
                inline_message_id=roulette["inline_message_id"],
                text=body_text,
                entities=body_entities,
                reply_markup=roulette_share_keyboard(roulette_id),
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            )
        except Exception:
            pass

    if owner_id and owner_id != user.id:
        display_name = user.first_name or user.username or str(user.id)
        notify_text, notify_entities = build_quick_roulette_join_notify_message(display_name)
        try:
            await context.bot.send_message(
                chat_id=owner_id, text=notify_text, entities=notify_entities,
            )
        except Exception:
            pass

def join_roulette(user_id: int, roulette_id: int, display_name: str = None):
    from google.api_core.exceptions import AlreadyExists
    client = fs_db()

    roulette_doc = client.collection("roulettes").document(str(roulette_id)).get()
    if not roulette_doc.exists:
        return {"found": False}
    roulette = roulette_doc.to_dict()

    target = roulette["target_count"]
    owner_id = roulette["owner_id"]
    status = roulette["status"]

    def _current_count():
        docs = client.collection("counted_users").where("roulette_id", "==", roulette_id).stream()
        return sum(1 for _ in docs)

    counted_ref = client.collection("counted_users").document(_counted_user_doc_id(user_id, roulette_id))
    existing = counted_ref.get().exists

    if existing or status != "open":
        current = _current_count()
        return {
            "found": True, "already": existing, "current": current,
            "target": target, "owner_id": owner_id, "status": status,
        }

    try:
        counted_ref.create({
            "user_id": user_id,
            "roulette_id": roulette_id,
            "display_name": display_name,
            "counted_at": datetime.now(timezone.utc).isoformat(),
        })
    except AlreadyExists:
        current = _current_count()
        return {
            "found": True, "already": True, "current": current,
            "target": target, "owner_id": owner_id, "status": status,
        }

    current = _current_count()
    return {
        "found": True, "already": False, "current": current,
        "target": target, "owner_id": owner_id, "status": status,
    }

async def handle_contest_join_entry(update: Update, context: ContextTypes.DEFAULT_TYPE, contest_code: str):
    """يُستدعى عند فتح البوت عبر رابط ?start=compjoin_{contest_code} (زر المشاركة في المسابقة)."""
    user = update.effective_user

    contest = get_contest(contest_code)
    if not contest:
        _bt, _be = bold_notice("⚠️ هذه المسابقة غير موجودة أو انتهت.")
        await update.message.reply_text(text=_bt, entities=_be)
        return

    if contest["status"] != "open":
        _bt, _be = bold_notice("⚠️ انتهت هذه المسابقة بالفعل.")
        await update.message.reply_text(text=_bt, entities=_be)
        return

    existing = get_contest_participant(contest_code, user.id)
    if existing:
        _bt, _be = bold_notice(
            f"✅ أنت مسجّل بالفعل في هذه المسابقة بإسم: {existing['display_name']}\n"
            f"🎟 كودك: {existing['participant_code']}"
        )
        await update.message.reply_text(text=_bt, entities=_be)
        return

    current = count_contest_participants(contest_code)
    if current >= contest["target_count"]:
        _bt, _be = bold_notice("⚠️ اكتمل عدد المشاركين المسموح في هذه المسابقة.")
        await update.message.reply_text(text=_bt, entities=_be)
        return

    display_name = user.first_name or user.username or str(user.id)
    text, entities = build_contest_join_confirm_message(display_name)
    await update.message.reply_text(
        text=text,
        entities=entities,
        reply_markup=build_contest_join_confirm_keyboard(contest_code),
    )


async def handle_contest_vote_entry(update: Update, context: ContextTypes.DEFAULT_TYPE, raw_payload: str):
    """
    يُستدعى عند فتح البوت عبر رابط ?start=compvote_{contest_code}_{participant_id}
    (زر التصويت 🤍 الموجود أسفل منشور المتسابق). يعرض للمستخدم كابتشا إيموجي
    عشوائية للتحقق أنه ليس روبوتًا قبل تسجيل تصويته.
    """
    user = update.effective_user

    try:
        contest_code, participant_id_raw = raw_payload.rsplit("_", 1)
        participant_id = int(participant_id_raw)
    except (ValueError, AttributeError):
        _bt, _be = bold_notice("⚠️ رابط تصويت غير صالح.")
        await update.message.reply_text(text=_bt, entities=_be)
        return

    contest = get_contest(contest_code)
    if not contest:
        _bt, _be = bold_notice("⚠️ هذه المسابقة غير موجودة أو انتهت.")
        await update.message.reply_text(text=_bt, entities=_be)
        return
    if contest["status"] != "open":
        _bt, _be = bold_notice("⚠️ انتهت هذه المسابقة بالفعل.")
        await update.message.reply_text(text=_bt, entities=_be)
        return
    if user.id == participant_id:
        _bt, _be = bold_notice("🚫 لا يمكنك التصويت لنفسك.")
        await update.message.reply_text(text=_bt, entities=_be)
        return
    if has_voted(contest_code, user.id):
        _bt, _be = bold_notice("✅ لقد قمت بالتصويت مسبقًا في هذه المسابقة.")
        await update.message.reply_text(text=_bt, entities=_be)
        return
    participant = get_contest_participant(contest_code, participant_id)
    if not participant:
        _bt, _be = bold_notice("⚠️ هذا المتسابق لم يعد مسجّلًا في المسابقة.")
        await update.message.reply_text(text=_bt, entities=_be)
        return

    # شرط بريميوم: إن كانت المسابقة مخصّصة لمصوّتي بريميوم فقط، يُرفض أي
    # مستخدم غير مفعّل بريميوم هنا فورًا قبل أي خطوة أخرى، ويُعاد نفس الفحص
    # عند «تحقق» وعند تسجيل التصويت النهائي كطبقة حماية إضافية.
    if contest.get("premium_only") and not user.is_premium:
        text, entities = build_contest_vote_premium_blocked_message()
        await update.message.reply_text(text=text, entities=entities)
        return

    # بوابة الاشتراك الإجباري: لا تُعرض الكابتشا مباشرة إن لم يكن المستخدم
    # مشتركًا فعليًا في القناة الإلزامية؛ بل تُعرض له بوابة اشتراك + زر
    # «تحقق» صريح، ولا يُحتسب أي تصويت قبل اجتياز هذا الفحص فعليًا.
    if not await is_user_subscribed(context, user.id):
        gate_text, gate_entities = build_contest_vote_gate_message()
        await update.message.reply_text(
            text=gate_text,
            entities=gate_entities,
            reply_markup=build_contest_vote_gate_keyboard(contest_code, participant_id),
        )
        return

    text, entities, keyboard = _build_contest_vote_captcha_payload(context, contest_code, participant_id)
    await update.message.reply_text(text=text, entities=entities, reply_markup=keyboard)


def _build_contest_vote_captcha_payload(context: ContextTypes.DEFAULT_TYPE, contest_code: str,
                                         participant_id: int) -> tuple:
    """يبني رسالة/كيبورد كابتشا التصويت ويخزّن جلستها. تُستخدم عند اجتياز
    بوابة الشروط مباشرة (لا شرط اشتراك) وأيضًا بعد الضغط على زر «تحقق» في
    بوابة الاشتراك، حتى تظهر نفس الكابتشا في الحالتين."""
    correct_emoji = random.choice(CAPTCHA_EMOJIS)
    decoys_pool = [e for e in CAPTCHA_EMOJIS if e != correct_emoji]
    decoy_count = min(CAPTCHA_OPTIONS_COUNT - 1, len(decoys_pool))
    decoys = random.sample(decoys_pool, decoy_count)
    options = decoys + [correct_emoji]
    random.shuffle(options)
    correct_index = options.index(correct_emoji)

    token = secrets.token_hex(4)
    sessions = context.user_data.setdefault("vote_captchas", {})
    sessions[token] = {
        "contest_code": contest_code,
        "participant_id": participant_id,
        "correct_index": correct_index,
        "correct_emoji": correct_emoji,
        "created_at": time.time(),
    }

    text, entities = build_vote_captcha_message(correct_emoji)
    keyboard = build_vote_captcha_keyboard(token, options, correct_index)
    return text, entities, keyboard


async def contest_vote_gate_check_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج ضغط زر «تحقق ✅» في بوابة اشتراك التصويت (compcond:{contest_code}:{participant_id}).
    يُعيد التحقق الفعلي (وليس من كاش قديم) من اشتراك المستخدم، ومن شرط
    بريميوم إن وُجد، قبل السماح له بالانتقال لخطوة الكابتشا النهائية."""
    query = update.callback_query
    try:
        _, contest_code, participant_id_raw = query.data.split(":", 2)
        participant_id = int(participant_id_raw)
    except (ValueError, IndexError):
        await query.answer("⚠️ طلب غير صالح.", show_alert=True)
        return

    user = query.from_user

    contest = get_contest(contest_code)
    if not contest or contest["status"] != "open":
        await query.answer("⚠️ انتهت هذه المسابقة.", show_alert=True)
        return
    if user.id == participant_id:
        await query.answer("🚫 لا يمكنك التصويت لنفسك.", show_alert=True)
        return
    if has_voted(contest_code, user.id):
        await query.answer("✅ لقد قمت بالتصويت مسبقًا في هذه المسابقة.", show_alert=True)
        return
    if not get_contest_participant(contest_code, participant_id):
        await query.answer("⚠️ هذا المتسابق لم يعد مسجّلًا.", show_alert=True)
        return
    if contest.get("premium_only") and not user.is_premium:
        await query.answer("💎 هذه المسابقة للتصويت لمستخدمي بريميوم فقط.", show_alert=True)
        return

    if not await is_user_subscribed(context, user.id, force_refresh=True):
        await query.answer(
            "⚠️ لم يتم العثور على اشتراكك، اشترك في القناة ثم اضغط تحقق مجددًا.",
            show_alert=True,
        )
        return

    await query.answer("✅ تم التحقق من الاشتراك، أكمل التحقق أدناه.")
    text, entities, keyboard = _build_contest_vote_captcha_payload(context, contest_code, participant_id)
    try:
        await query.edit_message_text(text=text, entities=entities, reply_markup=keyboard)
    except Exception:
        await query.message.reply_text(text=text, entities=entities, reply_markup=keyboard)


def _build_giveaway_captcha_payload(context: ContextTypes.DEFAULT_TYPE, gw_code: str,
                                     is_genuinely_new: bool) -> tuple:
    """يبني رسالة/كيبورد كابتشا منع الرشق (نفس زر الإيموجي الموجود مسبقًا)
    ويخزّن جلستها. تُستخدم عند فتح البوت لأول مرة (إن كانت الشروط مكتملة
    مسبقًا) وأيضًا بعد اجتياز بوابة الشروط عبر زر «تحقق»، لتظهر نفس الكابتشا
    في الحالتين."""
    correct_emoji = random.choice(CAPTCHA_EMOJIS)
    decoys_pool = [e for e in CAPTCHA_EMOJIS if e != correct_emoji]
    decoy_count = min(CAPTCHA_OPTIONS_COUNT - 1, len(decoys_pool))
    decoys = random.sample(decoys_pool, decoy_count)
    options = decoys + [correct_emoji]
    random.shuffle(options)
    correct_index = options.index(correct_emoji)

    token = secrets.token_hex(4)
    sessions = context.user_data.setdefault("gw_captchas", {})
    sessions[token] = {
        "gw_code": gw_code,
        "correct_index": correct_index,
        "created_at": time.time(),
        "is_genuinely_new": is_genuinely_new,
    }

    text, entities = build_vote_captcha_message(correct_emoji)
    keyboard = build_vote_captcha_keyboard(token, options, correct_index, prefix="gwcap")
    return text, entities, keyboard


async def handle_giveaway_captcha_entry(
    update: Update, context: ContextTypes.DEFAULT_TYPE, gw_code: str, is_genuinely_new: bool = False,
):
    """يُستدعى عند فتح البوت عبر رابط ?start=gwcap_{gw_code} (زر «اضغط لـ
    المشاركة» على سحب مفعّل عليه «منع الرشق»).

    أولاً يتحقق من شروط السحب (الاشتراك في قناة/قنوات الشرط، التعزيز، التصويت
    للمتسابق إن وُجد). إن لم تكتمل بعد، يعرض للمستخدم بوابة الشروط (زر لكل
    قناة/شرط + زر «تحقق») بدل الكابتشا مباشرة. فقط بعد اجتياز هذه الشروط
    يظهر له زر التحقق (الكابتشا) الموجود مسبقًا."""
    user = update.effective_user

    giveaway = get_giveaway(gw_code)
    if not giveaway or giveaway["status"] != "open":
        _bt, _be = bold_notice("⚠️ هذا السحب غير متاح حالياً.")
        await update.message.reply_text(text=_bt, entities=_be)
        return
    if is_giveaway_participant(gw_code, user.id):
        _bt, _be = bold_notice("✅ أنت مسجّل بالفعل في هذا السحب.")
        await update.message.reply_text(text=_bt, entities=_be)
        return

    ok, _alert = await check_giveaway_requirements(context, user, giveaway)
    if not ok:
        boost_link, vote_link = await build_giveaway_gate_links(context, giveaway)
        gate_text, gate_entities = build_giveaway_gate_message(giveaway)
        await update.message.reply_text(
            text=gate_text,
            entities=gate_entities,
            reply_markup=build_giveaway_gate_keyboard(
                gw_code, giveaway, is_genuinely_new, boost_link=boost_link, vote_link=vote_link,
            ),
        )
        return

    text, entities, keyboard = _build_giveaway_captcha_payload(context, gw_code, is_genuinely_new)
    await update.message.reply_text(text=text, entities=entities, reply_markup=keyboard)


async def gwcond_check_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج ضغط زر «تحقق ✅» في بوابة شروط السحب (gwcond:{gw_code}:{is_genuinely_new}).
    عند اجتياز الشروط تتحوّل نفس الرسالة إلى كابتشا التحقق منع الرشق."""
    query = update.callback_query
    try:
        _, gw_code, flag_raw = query.data.split(":", 2)
        is_genuinely_new = flag_raw == "1"
    except (ValueError, IndexError):
        await query.answer("⚠️ طلب غير صالح.", show_alert=True)
        return

    giveaway = get_giveaway(gw_code)
    if not giveaway or giveaway["status"] != "open":
        await query.answer("⚠️ هذا السحب لم يعد متاحاً.", show_alert=True)
        return

    user = query.from_user
    if is_giveaway_participant(gw_code, user.id):
        await query.answer("✅ أنت مسجّل بالفعل في هذا السحب.", show_alert=True)
        return

    ok, alert_text = await check_giveaway_requirements(context, user, giveaway)
    if not ok:
        await query.answer(alert_text, show_alert=True)
        return

    await query.answer("✅ تم التحقق من الشروط، أكمل التحقق أدناه.")
    text, entities, keyboard = _build_giveaway_captcha_payload(context, gw_code, is_genuinely_new)
    try:
        await query.edit_message_text(text=text, entities=entities, reply_markup=keyboard)
    except Exception:
        await query.message.reply_text(text=text, entities=entities, reply_markup=keyboard)


async def handle_giveaway_share_entry(update: Update, context: ContextTypes.DEFAULT_TYPE, gw_code: str):
    """يُستدعى عند فتح البوت عبر رابط ?start=gwshare_{gw_code} (زر «مشاركة السحب»)."""
    giveaway = get_giveaway(gw_code)
    if not giveaway:
        _bt, _be = bold_notice("⚠️ هذا السحب غير موجود أو انتهى.")
        await update.message.reply_text(text=_bt, entities=_be)
        return
    post_link = await build_contest_post_link(context, giveaway["chat_id"], giveaway["channel_message_id"])
    if post_link:
        _bt, _be = bold_notice(f"🎁 يمكنك المشاركة في هذا السحب من هنا:\n{post_link}")
    else:
        _bt, _be = bold_notice("🎁 توجّه إلى القناة/الجروب المنشور بها السحب للمشاركة.")
    await update.message.reply_text(text=_bt, entities=_be)


async def handle_giveaway_remind_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يُستدعى عند فتح البوت عبر رابط ?start=gw_remind (زر «ذكرني اذا فزت»)."""
    enabled = toggle_remind_win(update.effective_user.id)
    _bt, _be = bold_notice(
        "🔔 تم تفعيل تذكيرك إذا فزت." if enabled else "🔕 تم إلغاء تذكيرك إذا فزت."
    )
    await update.message.reply_text(text=_bt, entities=_be)


async def finalize_giveaway_join(context: ContextTypes.DEFAULT_TYPE, gw_code: str, giveaway,
                                  user, message=None, is_genuinely_new: bool = True):
    """يسجّل مشاركة مستخدم في سحب (بعد اجتياز الكابتشا إن لزم)، يحدّث زر المشاركة،
    ويُرسل إشعارًا خاصًا لمنشئ السحب مع زر استبعاد (Image 6)."""
    display_name = user.first_name or user.username or str(user.id)
    added = add_giveaway_participant(gw_code, user.id, display_name, user.username)
    if not added:
        return
    if bool(giveaway["antispam"]) and is_genuinely_new:
        reward_giveaway_user(
            user.id, gw_code, giveaway["owner_id"], giveaway["chat_id"]
        )
    total = count_giveaway_participants(gw_code)

    new_keyboard = build_giveaway_channel_keyboard(
        gw_code, total, antispam=bool(giveaway["antispam"]), status=giveaway["status"],
    )
    try:
        if message is not None:
            await message.edit_reply_markup(reply_markup=new_keyboard)
        else:
            await context.bot.edit_message_reply_markup(
                chat_id=giveaway["chat_id"],
                message_id=giveaway["channel_message_id"],
                reply_markup=new_keyboard,
            )
    except Exception:
        pass

    notify_text, notify_entities = build_giveaway_join_notify_message(
        display_name, user.username, user.id, gw_code, total,
    )
    try:
        await context.bot.send_message(
            chat_id=giveaway["owner_id"],
            text=notify_text,
            entities=notify_entities,
            reply_markup=build_giveaway_join_notify_keyboard(gw_code, user.id),
        )
    except Exception:
        pass

    if giveaway.get("autospin_mode") == "count" and giveaway.get("autospin_target")\
            and total >= giveaway["autospin_target"]:
        await finish_giveaway_auto(context, gw_code)


async def gw_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج ضغط زر «اضغط لـ المشاركة» أسفل منشور السحب في القناة/القروب."""
    query = update.callback_query
    gw_code = query.data.split(":", 1)[1]
    giveaway = get_giveaway(gw_code)
    if not giveaway or giveaway["status"] != "open":
        await query.answer("⚠️ هذا السحب غير متاح حالياً.", show_alert=True)
        return

    user = query.from_user
    if is_giveaway_participant(gw_code, user.id):
        await query.answer("✅ أنت مسجّل بالفعل في هذا السحب.", show_alert=True)
        return

    ok, alert_text = await check_giveaway_requirements(context, user, giveaway)
    if not ok:
        await query.answer(alert_text, show_alert=True)
        return

    vote_contest_code = giveaway.get("vote_contest_code")
    vote_participant_id = giveaway.get("vote_participant_id")
    vote_required = bool(vote_contest_code and vote_participant_id)

    if giveaway["antispam"]:
        await query.answer(
            url=f"https://t.me/{BOT_USERNAME}?start=gwcap_{gw_code}",
        )
        return

    await finalize_giveaway_join(context, gw_code, giveaway, user, query.message)
    if vote_required:
        await query.answer("✅ تم اشتراكك في السحب", show_alert=True)
    else:
        await query.answer("✅ تم تسجيل مشاركتك بنجاح!")


async def gw_captcha_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج ضغط أزرار كابتشا منع الرشق قبل المشاركة في السحب (gwcap:{token}:{idx})."""
    query = update.callback_query
    data = query.data
    try:
        _, token, idx_raw = data.split(":", 2)
        chosen_index = int(idx_raw)
    except (ValueError, IndexError):
        await query.answer("⚠️ طلب غير صالح.", show_alert=True)
        return

    sessions = context.user_data.get("gw_captchas", {})
    session = sessions.get(token)
    if not session:
        await query.answer("⚠️ انتهت صلاحية هذا التحقق، أعد المحاولة من زر المشاركة.", show_alert=True)
        return
    if time.time() - session.get("created_at", 0) > CAPTCHA_SESSION_TTL_SECONDS:
        sessions.pop(token, None)
        await query.answer("⚠️ انتهت صلاحية هذا التحقق، أعد المحاولة من زر المشاركة.", show_alert=True)
        return
    if chosen_index != session["correct_index"]:
        await query.answer(build_vote_captcha_wrong_alert(), show_alert=True)
        return

    gw_code = session["gw_code"]
    giveaway = get_giveaway(gw_code)
    is_genuinely_new = session.get("is_genuinely_new", False)
    sessions.pop(token, None)
    if not giveaway or giveaway["status"] != "open":
        await query.answer("⚠️ هذا السحب لم يعد متاحاً.", show_alert=True)
        return
    if is_giveaway_participant(gw_code, query.from_user.id):
        await query.answer("✅ أنت مسجّل بالفعل في هذا السحب.", show_alert=True)
        return

    # التحقق النهائي الموحّد (بريميوم/قنوات/تعزيز/تصويت) — بهذا يتم الدخول
    # تلقائيًا في السحب فقط بعد اجتياز الكابتشا وهذه الشروط معًا دفعة واحدة.
    ok, alert_text = await check_giveaway_requirements(context, query.from_user, giveaway)
    if not ok:
        # حالة نادرة: تحقق المستخدم من الشروط عند فتح البوت ثم ألغى اشتراكه
        # قبل الضغط على الكابتشا — نعيده لبوابة الشروط بدل تنبيه فقط حتى
        # يتمكن من إصلاح الأمر والمتابعة دون طلب رابط مشاركة جديد.
        await query.answer(alert_text, show_alert=True)
        boost_link, vote_link = await build_giveaway_gate_links(context, giveaway)
        gate_text, gate_entities = build_giveaway_gate_message(giveaway)
        try:
            await query.edit_message_text(
                text=gate_text,
                entities=gate_entities,
                reply_markup=build_giveaway_gate_keyboard(
                    gw_code, giveaway, is_genuinely_new, boost_link=boost_link, vote_link=vote_link,
                ),
            )
        except Exception:
            pass
        return

    await finalize_giveaway_join(
        context, gw_code, giveaway, query.from_user, None, is_genuinely_new=is_genuinely_new,
    )
    await query.answer("✅ تم التحقق وتسجيل مشاركتك بنجاح!", show_alert=True)

    text, entities = build_vote_captcha_success_message()
    try:
        await query.edit_message_text(text=text, entities=entities)
    except Exception:
        pass


async def gw_kick_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج ضغط زر «استبعاد» في إشعار مشارك جديد (Image 6) — يحذف المشارك من السحب."""
    query = update.callback_query
    try:
        _, gw_code, uid_raw = query.data.split(":", 2)
        target_user_id = int(uid_raw)
    except (ValueError, IndexError):
        await query.answer("⚠️ طلب غير صالح.", show_alert=True)
        return

    giveaway = get_giveaway(gw_code)
    if not giveaway or giveaway["owner_id"] != query.from_user.id:
        await query.answer("⚠️ لا تملك صلاحية القيام بهذا.", show_alert=True)
        return

    remove_giveaway_participant(gw_code, target_user_id)
    total = count_giveaway_participants(gw_code)
    try:
        await context.bot.edit_message_reply_markup(
            chat_id=giveaway["chat_id"],
            message_id=giveaway["channel_message_id"],
            reply_markup=build_giveaway_channel_keyboard(
                gw_code, total, antispam=bool(giveaway["antispam"]), status=giveaway["status"],
            ),
        )
    except Exception:
        pass

    await query.answer("🚫 تم استبعاد المشارك من السحب.", show_alert=True)
    try:
        await query.message.delete()
    except Exception:
        pass


async def gw_repost_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج ضغط زر «↻ إعادة نشر» — ينشر نسخة جديدة من منشور السحب في نفس القناة/القروب."""
    query = update.callback_query
    gw_code = query.data.split(":", 1)[1]
    giveaway = get_giveaway(gw_code)
    if not giveaway or giveaway["owner_id"] != query.from_user.id:
        await query.answer("⚠️ لا تملك صلاحية القيام بهذا.", show_alert=True)
        return

    await query.answer()
    total = count_giveaway_participants(gw_code)
    cliche_entities = json_to_entities(giveaway["cliche_entities"])
    vote_contest_code = giveaway.get("vote_contest_code")
    vote_participant_id = giveaway.get("vote_participant_id")
    vote_link = (
        build_giveaway_vote_condition_link(vote_contest_code, vote_participant_id)
        if vote_contest_code and vote_participant_id else None
    )
    condition_channels = giveaway.get("condition_channels") or []
    boost_link = (
        await build_giveaway_boost_link(context, giveaway["chat_id"])
        if giveaway.get("boost_required") else ""
    )
    post_text, post_entities = build_giveaway_channel_message(
        giveaway["cliche_text"], cliche_entities, vote_link=vote_link, condition_channels=condition_channels,
        boost_link=boost_link,
    )
    post_keyboard = build_giveaway_channel_keyboard(
        gw_code, total, antispam=bool(giveaway["antispam"]), status=giveaway["status"],
    )
    old_message_id = giveaway.get("channel_message_id")
    try:
        sent = await context.bot.send_message(
            chat_id=giveaway["chat_id"],
            text=post_text,
            entities=post_entities,
            reply_markup=post_keyboard,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        set_giveaway_channel_message(gw_code, sent.message_id)
    except Exception:
        await query.message.reply_text("⚠️ تعذر إعادة نشر السحب، تأكد من أن البوت مايزال مشرفًا هناك.")
        return

    # حذف النسخة السابقة من منشور السحب حتى لا يبقى أكثر من نسخة منشورة في
    # نفس الوقت — تبقى فقط أحدث نسخة (التي أُرسلت للتو) ظاهرة في القناة/القروب.
    if old_message_id and old_message_id != sent.message_id:
        try:
            await context.bot.delete_message(chat_id=giveaway["chat_id"], message_id=old_message_id)
        except Exception:
            pass


async def gw_pause_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    يعالج ضغط زر «ايقاف وسحب» — يوقف استقبال مشاركات جديدة في السحب فقط (حالة
    "paused")، ولا يسحب الفائزين بعد. يتحوّل نفس الزر إلى «استئناف المشاركة»
    (أخضر) والزر الآخر إلى «ابدا السحب» (أحمر)، وهو الزر الذي يقوم فعليًا
    باختيار الفائزين (انظر gw_draw_callback).
    """
    query = update.callback_query
    gw_code = query.data.split(":", 1)[1]
    giveaway = get_giveaway(gw_code)
    if not giveaway or giveaway["owner_id"] != query.from_user.id:
        await query.answer("⚠️ لا تملك صلاحية القيام بهذا.", show_alert=True)
        return
    if giveaway["status"] != "open":
        await query.answer("⚠️ هذا السحب متوقف بالفعل.", show_alert=True)
        return

    await query.answer("⏸ تم إيقاف استقبال المشاركات.")
    set_giveaway_status(gw_code, "paused")
    total = count_giveaway_participants(gw_code)
    new_keyboard = build_giveaway_channel_keyboard(
        gw_code, total, antispam=bool(giveaway["antispam"]), status="paused",
    )
    try:
        await query.message.edit_reply_markup(reply_markup=new_keyboard)
    except Exception:
        pass


async def gw_resume_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    يعالج ضغط زر «استئناف المشاركة» — يعيد فتح باب المشاركة في السحب بعد إيقافه
    مؤقتًا، ويعيد الكيبورد لحالته الأصلية («ايقاف وسحب» / «ذكرني اذا فزت»).
    لا يمكن لأحد الضغط على هذا الزر سوى صاحب السحب (owner_id).
    """
    query = update.callback_query
    gw_code = query.data.split(":", 1)[1]
    giveaway = get_giveaway(gw_code)
    if not giveaway or giveaway["owner_id"] != query.from_user.id:
        await query.answer("⚠️ لا تملك صلاحية القيام بهذا.", show_alert=True)
        return
    if giveaway["status"] != "paused":
        await query.answer("⚠️ لا يمكن استئناف هذا السحب في حالته الحالية.", show_alert=True)
        return

    await query.answer("▶️ تم استئناف المشاركة.")
    set_giveaway_status(gw_code, "open")
    total = count_giveaway_participants(gw_code)
    new_keyboard = build_giveaway_channel_keyboard(
        gw_code, total, antispam=bool(giveaway["antispam"]), status="open",
    )
    try:
        await query.message.edit_reply_markup(reply_markup=new_keyboard)
    except Exception:
        pass


_GW_DRAW_STATE = {}


def build_gw_draw_result_keyboard(gw_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ اختيار فائز آخر", callback_data=f"gw_reroll:{gw_code}", style="success")],
    ])


async def notify_giveaway_winner(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int):
    """يرسل رسالة خاصة تصل للفائز فقط، بنفس تصميم/زخرفة وخط البوت العريض."""
    try:
        chat = await context.bot.get_chat(chat_id)
        channel_label = chat.title or "القناة"
    except Exception:
        channel_label = "القناة"
    try:
        text, entities = build_text_with_emojis([
            ([
                ("🎉", EMOJI["party"]),
                f" مبروك! أنت أحد الفائزين في السحب في قناة {channel_label}",
                " ",
                ("🏆", EMOJI["trophy_win"]),
            ], "bold", None),
        ])
        await context.bot.send_message(chat_id=user_id, text=text, entities=entities)
    except Exception:
        pass


async def _execute_giveaway_draw(context: ContextTypes.DEFAULT_TYPE, gw_code: str, giveaway,
                                  disable_original_keyboard: bool = True) -> list:
    """المنطق المشترك لتنفيذ سحب الفائزين فعليًا (يقفل السحب، يختار الفائزين
    عشوائيًا، وينشر منشور النتيجة). يُستخدم من:
    - gw_draw_callback (بعد ضغط «ابدا السحب» يدويًا).
    - finish_giveaway_auto (عند اكتمال السحب التلقائي — عدد أو وقت — دون أي
      ضغط يدوي لزر «ايقاف وسحب» أولًا).
    """
    set_giveaway_status(gw_code, "closed")
    participants = get_giveaway_participants(gw_code)
    winners_count = giveaway["winners_count"] or 1
    winners = random.sample(participants, min(winners_count, len(participants))) if participants else []
    remaining_pool = [p for p in participants if p not in winners]

    cliche_entities = json_to_entities(giveaway["cliche_entities"])
    end_text, end_entities = build_giveaway_ended_message(giveaway["cliche_text"], cliche_entities, winners)
    sent_message = None
    try:
        sent_message = await context.bot.send_message(
            chat_id=giveaway["chat_id"], text=end_text, entities=end_entities,
            reply_markup=build_gw_draw_result_keyboard(gw_code),
        )
    except Exception:
        pass

    if disable_original_keyboard and giveaway.get("channel_message_id"):
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=giveaway["chat_id"], message_id=giveaway["channel_message_id"], reply_markup=None,
            )
        except Exception:
            pass

    _GW_DRAW_STATE[gw_code] = {
        "winners": winners,
        "pool": remaining_pool,
        "chat_id": giveaway["chat_id"],
        "message_id": sent_message.message_id if sent_message else None,
        "cliche_text": giveaway["cliche_text"],
        "cliche_entities": giveaway["cliche_entities"],
        "owner_id": giveaway["owner_id"],
    }
    return winners


async def finish_giveaway_auto(context: ContextTypes.DEFAULT_TYPE, gw_code: str):
    """يُستدعى تلقائيًا فور اكتمال شرط «سحب تلقائي» (عدد المشاركين المطلوب أو
    انقضاء الوقت المحدد) — دون انتظار ضغط «ايقاف وسحب» يدويًا أولًا."""
    giveaway = get_giveaway(gw_code)
    if not giveaway or giveaway["status"] != "open":
        return
    winners = await _execute_giveaway_draw(context, gw_code, giveaway, disable_original_keyboard=True)
    for user_id, _name in winners:
        await notify_giveaway_winner(context, user_id, giveaway["chat_id"])


async def giveaway_autospin_time_job(context: ContextTypes.DEFAULT_TYPE):
    gw_code = context.job.data
    try:
        await finish_giveaway_auto(context, gw_code)
    except Exception:
        logger.exception("giveaway_autospin_time_job: فشل تنفيذ السحب التلقائي %s", gw_code)


def schedule_giveaway_autospin_time(job_queue, gw_code: str, delay_seconds: float):
    """يجدول تنفيذ السحب التلقائي فعليًا عند انقضاء الوقت المحدد (Image 9) —
    بنفس آلية schedule_contest_time_end تمامًا."""
    if delay_seconds is None:
        return
    if job_queue is None:
        logger.error(
            "schedule_giveaway_autospin_time: job_queue غير متاحة — لن يُنفَّذ السحب التلقائي %s! "
            "تأكد من تثبيت المكتبة عبر: pip install \"python-telegram-bot[job-queue]\"",
            gw_code,
        )
        return
    job_queue.run_once(
        giveaway_autospin_time_job,
        when=max(delay_seconds, 1),
        data=gw_code,
        name=f"gw_autospin_end_{gw_code}",
    )
    logger.info("schedule_giveaway_autospin_time: تمت جدولة السحب التلقائي %s بعد %.0f ثانية",
                gw_code, delay_seconds)


async def reschedule_pending_giveaway_timers(app):
    """يُستدعى عند إقلاع البوت لإعادة جدولة مؤقتات «سحب تلقائي - وقت محدد» المفتوحة
    (بعد أي إعادة تشغيل)، بنفس آلية reschedule_pending_contest_timers."""
    now = datetime.now(timezone.utc)
    for giveaway in get_open_time_giveaways():
        end_at = giveaway_autospin_end_datetime(giveaway)
        remaining = (end_at - now).total_seconds()
        if remaining <= 0:
            class _Ctx:
                bot = app.bot
            await finish_giveaway_auto(_Ctx(), giveaway["gw_code"])
        else:
            schedule_giveaway_autospin_time(app.job_queue, giveaway["gw_code"], remaining)


async def giveaway_autospin_countdown_tick(context: ContextTypes.DEFAULT_TYPE):
    """يعمل كل 10 دقائق (Image 9): يحدّث جملة العد التنازلي المعروضة داخل كل
    منشور سحب مفعّل عليه «سحب تلقائي - وقت محدد» ولا يزال مفتوحًا، ويُنهي فورًا
    أي سحب انقضى وقته فعليًا كخط أمان إضافي (احتياطًا لأي تعارض توقيت مع
    المؤقت الفردي run_once)."""
    for giveaway in get_open_time_giveaways():
        gw_code = giveaway["gw_code"]
        end_at = giveaway_autospin_end_datetime(giveaway)
        remaining = (end_at - datetime.now(timezone.utc)).total_seconds()
        if remaining <= 0:
            try:
                await finish_giveaway_auto(context, gw_code)
            except Exception:
                logger.exception("giveaway_autospin_countdown_tick: فشل إنهاء السحب %s", gw_code)
            continue
        if not giveaway.get("channel_message_id"):
            continue
        try:
            cliche_entities = json_to_entities(giveaway["cliche_entities"])
            vote_contest_code = giveaway.get("vote_contest_code")
            vote_participant_id = giveaway.get("vote_participant_id")
            vote_link = (
                build_giveaway_vote_condition_link(vote_contest_code, vote_participant_id)
                if vote_contest_code and vote_participant_id else None
            )
            boost_link = (
                await build_giveaway_boost_link(context, giveaway["chat_id"])
                if giveaway.get("boost_required") else ""
            )
            post_text, post_entities = build_giveaway_channel_message(
                giveaway["cliche_text"], cliche_entities, vote_link=vote_link,
                condition_channels=giveaway.get("condition_channels") or [],
                boost_link=boost_link,
                autospin={"mode": "time", "notice_text": build_giveaway_autospin_notice_text(giveaway)},
            )
            await context.bot.edit_message_text(
                chat_id=giveaway["chat_id"], message_id=giveaway["channel_message_id"],
                text=post_text, entities=post_entities,
                reply_markup=build_giveaway_channel_keyboard(
                    gw_code, count_giveaway_participants(gw_code),
                    antispam=bool(giveaway.get("antispam", False)), status=giveaway["status"],
                ),
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            )
        except Exception:
            pass


async def gw_draw_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    يعالج ضغط زر «ابدا السحب» — يقفل السحب نهائيًا ويختار عدد الفائزين المحدد
    مسبقًا (winners_count) عشوائيًا من بين المشاركين. لا يظهر هذا الزر إلا بعد
    إيقاف استقبال المشاركات (gw_pause)، ولا يمكن لأحد الضغط عليه سوى صاحب السحب.
    """
    query = update.callback_query
    gw_code = query.data.split(":", 1)[1]
    giveaway = get_giveaway(gw_code)
    if not giveaway or giveaway["owner_id"] != query.from_user.id:
        await query.answer("⚠️ لا تملك صلاحية القيام بهذا.", show_alert=True)
        return
    if giveaway["status"] != "paused":
        await query.answer("⚠️ يجب إيقاف استقبال المشاركات أولًا من زر «ايقاف وسحب».", show_alert=True)
        return

    await query.answer("🎲 جارٍ سحب الفائزين...")
    winners = await _execute_giveaway_draw(context, gw_code, giveaway, disable_original_keyboard=False)
    try:
        await query.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    for user_id, _name in winners:
        await notify_giveaway_winner(context, user_id, giveaway["chat_id"])


async def gw_reroll_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج ضغط زر «➕ اختيار فائز آخر» — يضيف فائزًا إضافيًا عشوائيًا للقائمة الحالية."""
    query = update.callback_query
    gw_code = query.data.split(":", 1)[1]
    state = _GW_DRAW_STATE.get(gw_code)
    if not state:
        await query.answer("⚠️ انتهت صلاحية هذه القائمة.", show_alert=True)
        return
    if query.from_user.id != state["owner_id"] and query.from_user.id not in ADMIN_IDS:
        await query.answer("⚠️ لا تملك صلاحية القيام بهذا.", show_alert=True)
        return
    if not state["pool"]:
        await query.answer("⚠️ لا يوجد مشاركون إضافيون لاختيارهم.", show_alert=True)
        return

    await query.answer("🎲 جارٍ اختيار فائز جديد...")
    new_winner = random.choice(state["pool"])
    state["pool"].remove(new_winner)
    state["winners"].append(new_winner)

    cliche_entities = json_to_entities(state["cliche_entities"])
    end_text, end_entities = build_giveaway_ended_message(state["cliche_text"], cliche_entities, state["winners"])
    try:
        await context.bot.edit_message_text(
            chat_id=state["chat_id"], message_id=state["message_id"],
            text=end_text, entities=end_entities,
            reply_markup=build_gw_draw_result_keyboard(gw_code),
        )
    except Exception:
        pass

    await notify_giveaway_winner(context, new_winner[0], state["chat_id"])


def contest_end_datetime(contest) -> datetime:
    """يحسب موعد انتهاء مسابقة معتمدة على وقت محدد (created_at + time_minutes)."""
    created = datetime.fromisoformat(contest["created_at"])
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    minutes = contest["time_minutes"] or 0
    return created + timedelta(minutes=minutes)


async def finish_contest_by_time(bot, contest_code: str):
    """
    يُستدعى تلقائيًا عند انقضاء الوقت المحدد للمسابقة:
    - يقفل المسابقة، يحدد الفائز/الفائزين (الأعلى أصواتًا)، وينشر منشورًا جديدًا منفصلًا
      يعرض نتيجة المسابقة (فائز واحد أو أكثر) — دون تعديل منشور المشاركة الأصلي في القناة/القروب.
    """
    contest = get_contest(contest_code)
    if not contest or contest["status"] != "open":
        return

    set_contest_status(contest_code, "ended")

    leaderboard = get_contest_leaderboard(contest_code)
    winners_count = contest["winners_count"] or 1
    winners = leaderboard[:winners_count]

    ended_text, ended_entities = build_contest_ended_message(contest["cliche_text"], None, winners)
    ended_keyboard = build_contest_ended_keyboard(contest_code)

    try:
        await bot.send_message(
            chat_id=contest["chat_id"],
            text=ended_text,
            entities=ended_entities,
            reply_markup=ended_keyboard,
        )
    except Exception as exc:
        logger.warning("finish_contest_by_time: فشل نشر منشور النتيجة الجديد للمسابقة %s: %s",
                        contest_code, exc)
        stripped = [e for e in (ended_entities or []) if getattr(e, "type", None) != MessageEntity.CUSTOM_EMOJI]
        if len(stripped) != len(ended_entities or []):
            try:
                await bot.send_message(
                    chat_id=contest["chat_id"],
                    text=ended_text,
                    entities=stripped,
                    reply_markup=ended_keyboard,
                )
            except Exception as exc2:
                logger.error("finish_contest_by_time: فشلت المحاولة الاحتياطية أيضًا: %s", exc2)

    if contest["announce_results"]:
        results_text, results_entities = build_contest_results_message(leaderboard, winners_count)
        try:
            await bot.send_message(
                chat_id=contest["chat_id"],
                text=results_text,
                entities=results_entities,
            )
        except Exception:
            pass

    if contest["notify_win"] and winners:
        for user_id, name, _, votes in winners:
            try:
                text, entities = build_text_with_emojis([
                    ([("🎉", EMOJI["party"]), f" مبروك! لقد فزت في المسابقة بإسم: {name}"], "bold", None),
                    "\n\n",
                    f"عدد أصواتك: {format_votes_label(votes)}",
                ])
                await bot.send_message(chat_id=user_id, text=text, entities=entities)
            except Exception:
                pass


async def contest_time_end_job(context: ContextTypes.DEFAULT_TYPE):
    contest_code = context.job.data
    try:
        await finish_contest_by_time(context.bot, contest_code)
    except Exception:
        logger.exception("contest_time_end_job: فشل إنهاء المسابقة %s تلقائيًا", contest_code)


def schedule_contest_time_end(job_queue, contest_code: str, delay_seconds: float):
    if delay_seconds is None:
        return
    if job_queue is None:
        logger.error(
            "schedule_contest_time_end: job_queue غير متاحة — لن تُنهى المسابقة %s تلقائيًا! "
            "تأكد من تثبيت المكتبة عبر: pip install \"python-telegram-bot[job-queue]\"",
            contest_code,
        )
        return
    job_queue.run_once(
        contest_time_end_job,
        when=max(delay_seconds, 1),
        data=contest_code,
        name=f"contest_end_{contest_code}",
    )
    logger.info("schedule_contest_time_end: تمت جدولة إنهاء المسابقة %s بعد %.0f ثانية",
                contest_code, delay_seconds)


async def reschedule_pending_contest_timers(app):
    """يُستدعى عند إقلاع البوت لإعادة جدولة مؤقتات المسابقات المفتوحة (بعد أي إعادة تشغيل)."""
    now = datetime.now(timezone.utc)
    for contest in get_open_time_contests():
        end_at = contest_end_datetime(contest)
        remaining = (end_at - now).total_seconds()
        if remaining <= 0:
            await finish_contest_by_time(app.bot, contest["contest_code"])
        else:
            schedule_contest_time_end(app.job_queue, contest["contest_code"], remaining)


async def contest_results_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج زر «عرض النتائج» أسفل منشور نهاية المسابقة — متاح لمشرفي القناة/القروب فقط."""
    query = update.callback_query
    contest_code = query.data.split(":", 1)[1]

    contest = get_contest(contest_code)
    if not contest:
        await query.answer("⚠️ هذه المسابقة لم تعد متاحة.", show_alert=True)
        return

    is_admin = False
    try:
        member = await context.bot.get_chat_member(contest["chat_id"], query.from_user.id)
        is_admin = member.status in ("administrator", "creator")
    except Exception as exc:
        logger.warning("contest_results_callback: get_chat_member failed for chat=%s user=%s: %s",
                        contest["chat_id"], query.from_user.id, exc)

    if not is_admin:
        await query.answer("❌ عرض النتائج في القناة متاح لمشرفي القناة فقط.", show_alert=True)
        return

    await query.answer()

    leaderboard = get_contest_leaderboard(contest_code)
    winners_count = contest["winners_count"] or 1

    text, entities = build_contest_results_message(leaderboard, winners_count)
    try:
        await query.message.reply_text(text=text, entities=entities)
    except Exception as exc:
        logger.warning("contest_results_callback: reply_text failed: %s", exc)


async def contest_participation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج أزرار: رفض/قبول المشاركة، وسحب الاسم من المسابقة."""
    query = update.callback_query
    try:
        await _contest_participation_callback_inner(update, context)
    except Exception:
        try:
            await query.answer("⚠️ حدث خطأ غير متوقع، حاول مرة أخرى.", show_alert=True)
        except Exception:
            pass
        raise


async def safe_edit_message_text(query, text, entities=None, reply_markup=None):
    """
    إرسال/تعديل نص مع كيانات (entities) مع شبكة أمان: إن رفض تيليجرام الرسالة (400 Bad
    Request) — غالبًا بسبب إيموجي مخصص (custom_emoji_id) غير صالح أو غير متاح لهذا البوت —
    نسجّل الخطأ الحقيقي كاملًا، ثم نعيد المحاولة بعد حذف كيانات CUSTOM_EMOJI فقط (نُبقي على
    باقي التنسيق) حتى تصل الرسالة للمستخدم دائمًا بدل أن تبقى الشاشة القديمة ظاهرة.
    """
    try:
        await query.edit_message_text(text=text, entities=entities, reply_markup=reply_markup)
        return True
    except Exception as exc:
        logger.warning("safe_edit_message_text: المحاولة الأولى فشلت: %s", exc)

    stripped = [e for e in (entities or []) if getattr(e, "type", None) != MessageEntity.CUSTOM_EMOJI]
    if len(stripped) != len(entities or []):
        try:
            await query.edit_message_text(text=text, entities=stripped, reply_markup=reply_markup)
            logger.info("safe_edit_message_text: نجحت المحاولة الثانية بعد حذف الإيموجي المخصص.")
            return True
        except Exception as exc:
            logger.warning("safe_edit_message_text: فشلت المحاولة الثانية أيضًا: %s", exc)

    try:
        await query.edit_message_text(text=text)
        logger.info("safe_edit_message_text: نجحت المحاولة الثالثة (نص عادي بلا تنسيق).")
        return True
    except Exception as exc:
        logger.error("safe_edit_message_text: فشلت كل المحاولات: %s", exc)
        return False


async def _contest_participation_callback_inner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("comp_reject_join:"):
        await query.answer()
        _bt, _be = bold_notice("❌ تم إلغاء المشاركة في المسابقة.")
        await query.edit_message_text(text=_bt, entities=_be)
        return

    if data.startswith("comp_confirm_join:"):
        contest_code = data.split(":", 1)[1]
        user = query.from_user

        contest = get_contest(contest_code)
        if not contest:
            await query.answer("⚠️ هذه المسابقة لم تعد متاحة.", show_alert=True)
            return

        existing = get_contest_participant(contest_code, user.id)
        if existing:
            await query.answer()
            text, entities = build_contest_registered_message(existing["display_name"], existing["participant_code"])
            await safe_edit_message_text(
                query, text, entities,
                reply_markup=build_contest_registered_keyboard(
                    contest_code, user.id, existing["participant_code"]
                ),
            )
            return

        if contest["status"] != "open":
            await query.answer("⚠️ هذه المسابقة لم تعد متاحة.", show_alert=True)
            return
        current = count_contest_participants(contest_code)
        if current >= contest["target_count"]:
            await query.answer("⚠️ اكتمل عدد المشاركين المسموح في هذه المسابقة.", show_alert=True)
            return

        await query.answer()

        display_name = user.first_name or user.username or str(user.id)
        participant_code = generate_participant_code(contest_code)
        try:
            add_contest_participant(contest_code, user.id, display_name, participant_code)
        except sqlite3.IntegrityError:
            existing = get_contest_participant(contest_code, user.id)
            if existing:
                display_name = existing["display_name"]
                participant_code = existing["participant_code"]
            else:
                _bt, _be = bold_notice("⚠️ حدث خطأ أثناء تسجيل مشاركتك، حاول مرة أخرى.")
                await query.message.reply_text(text=_bt, entities=_be)
                return

        text, entities = build_contest_registered_message(display_name, participant_code)
        await safe_edit_message_text(
            query, text, entities,
            reply_markup=build_contest_registered_keyboard(contest_code, user.id, participant_code),
        )

        vote_text, vote_entities = build_contest_vote_post_message(display_name)
        try:
            sent = await context.bot.send_message(
                chat_id=contest["chat_id"],
                text=vote_text,
                entities=vote_entities,
                reply_markup=build_contest_vote_keyboard(contest_code, user.id, 0, participant_code),
            )
            set_participant_channel_message(contest_code, user.id, sent.message_id)
        except Exception:
            pass
        return

    if data.startswith("comp_withdraw:"):
        _, contest_code, user_id_raw = data.split(":", 2)
        target_user_id = int(user_id_raw)
        requester = query.from_user

        if requester.id != target_user_id:
            await query.answer("🚫 لا يمكنك سحب مشاركة شخص آخر.", show_alert=True)
            return

        participant = get_contest_participant(contest_code, target_user_id)
        if not participant:
            await query.answer("⚠️ أنت غير مسجّل في هذه المسابقة.", show_alert=True)
            return

        remove_contest_participant(contest_code, target_user_id)
        await query.answer("✅ تم سحب اسمك من المسابقة.")
        _bt, _be = bold_notice("🗑 تم سحب اسمك من المسابقة بنجاح.")
        await query.edit_message_text(text=_bt, entities=_be)

        contest = get_contest(contest_code)
        if contest and participant["channel_message_id"]:
            try:
                await context.bot.delete_message(
                    chat_id=contest["chat_id"],
                    message_id=participant["channel_message_id"],
                )
            except Exception:
                pass
        return


async def cancel_contest_vote_if_unsubscribed(context: ContextTypes.DEFAULT_TYPE, vote_doc) -> bool:
    """نظام الأمان وإلغاء التصويت: يتحقق من استمرار اشتراك مصوّت واحد في القناة
    الإلزامية. إن غادرها بعد احتساب صوته يُلغي هذا النظام تلقائيًا:
    - يُسجَّل التصويت كـ«ملغى بسبب مغادرة القنوات الإلزامية» (لا يُحذف، للتوثيق) —
      وهذا يُسقطه فورًا من عدد أصوات المتسابق (get_participant_votes/leaderboard
      لا يحتسبان إلا التصويتات المؤكدة).
    - يُخصم من صاحب المسابقة أي نقاط كانت قد مُنحت مقابل هذا التصويت تحديدًا.
    - يسمح هذا للمصوّت بالتصويت من جديد إذا عاد واشترك لاحقًا (has_voted تعيد
      False لأي تصويت غير مؤكد)، مع خضوعه لنفس كابتشا منع الرشق من جديد.
    يعيد True إذا أُلغي التصويت فعليًا في هذه المرة.
    """
    data = vote_doc.to_dict()
    if data.get("status", "confirmed") != "confirmed":
        return False

    voter_id = data.get("voter_id")
    if not voter_id:
        return False

    subscribed = await is_user_subscribed(context, voter_id, force_refresh=True)
    if subscribed:
        return False

    vote_doc.reference.update({
        "status": "cancelled_unsubscribed",
        "cancelled_at": datetime.now(timezone.utc).isoformat(),
    })

    amount = data.get("points_awarded") or 0
    owner_id = data.get("owner_id")
    if amount and owner_id:
        reverse_contest_owner_points(owner_id, amount)

    contest_code = data.get("contest_code")
    participant_id = data.get("participant_user_id")
    if contest_code and participant_id:
        contest = get_contest(contest_code)
        if contest and contest.get("status") == "open":
            participant = get_contest_participant(contest_code, participant_id)
            if participant and participant.get("channel_message_id"):
                new_votes = get_participant_votes(contest_code, participant_id)
                try:
                    await context.bot.edit_message_reply_markup(
                        chat_id=contest["chat_id"],
                        message_id=participant["channel_message_id"],
                        reply_markup=build_contest_vote_keyboard(
                            contest_code, participant_id, new_votes, participant["participant_code"]
                        ),
                    )
                except Exception:
                    pass
    return True


async def contest_votes_subscription_audit(context: ContextTypes.DEFAULT_TYPE):
    """فحص دوري (نظام الأمان): يمرّ على كل التصويتات المؤكدة في المسابقات
    المفتوحة حاليًا، ويتحقق من استمرار اشتراك كل مصوّت في القناة الإلزامية.
    من غادر القناة تُلغى نقطته تلقائيًا (اكتشاف من خرج من القنوات وإلغاء
    أصواتهم تلقائيًا دون انتظار أن يفتح البوت مجددًا)."""
    client = fs_db()
    try:
        open_codes = [
            c.to_dict().get("contest_code")
            for c in client.collection("contests").where("status", "==", "open").stream()
        ]
    except Exception:
        logger.exception("contest_votes_subscription_audit: فشل جلب المسابقات المفتوحة")
        return
    if not open_codes:
        return

    checked = 0
    cancelled = 0
    for contest_code in open_codes:
        if not contest_code:
            continue
        try:
            docs = list(client.collection("contest_votes").where("contest_code", "==", contest_code).stream())
        except Exception:
            logger.exception("contest_votes_subscription_audit: فشل جلب أصوات المسابقة %s", contest_code)
            continue
        for d in docs:
            if d.to_dict().get("status", "confirmed") != "confirmed":
                continue
            checked += 1
            try:
                if await cancel_contest_vote_if_unsubscribed(context, d):
                    cancelled += 1
            except Exception:
                logger.exception("contest_votes_subscription_audit: فشل فحص التصويت %s", d.id)
            await asyncio.sleep(0.05)

    if checked:
        logger.info(
            "contest_votes_subscription_audit: تم فحص %d صوتًا، أُلغي منها %d بسبب مغادرة القناة الإلزامية",
            checked, cancelled,
        )


async def vote_captcha_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    يعالج ضغط المستخدم على أحد أزرار كابتشا التصويت (compcap:{token}:{idx}).
    إذا اختار الرمز الصحيح المطابق للهدف المعروض في الرسالة يتم تسجيل تصويته فورًا،
    وإذا اختار رمزًا خاطئًا لا يتم تسجيل أي تصويت (ويمكنه إعادة المحاولة على نفس الرسالة).
    """
    query = update.callback_query
    data = query.data

    try:
        _, token, idx_raw = data.split(":", 2)
        chosen_index = int(idx_raw)
    except (ValueError, IndexError):
        await query.answer("⚠️ طلب غير صالح.", show_alert=True)
        return

    sessions = context.user_data.get("vote_captchas", {})
    session = sessions.get(token)

    if not session:
        await query.answer("⚠️ انتهت صلاحية هذا التحقق، أعد المحاولة من زر التصويت 🤍.", show_alert=True)
        return

    if time.time() - session.get("created_at", 0) > CAPTCHA_SESSION_TTL_SECONDS:
        sessions.pop(token, None)
        await query.answer("⚠️ انتهت صلاحية هذا التحقق، أعد المحاولة من زر التصويت 🤍.", show_alert=True)
        return

    if chosen_index != session["correct_index"]:
        await query.answer(build_vote_captcha_wrong_alert(), show_alert=True)
        return

    contest_code = session["contest_code"]
    participant_id = session["participant_id"]
    voter = query.from_user

    contest = get_contest(contest_code)
    if not contest or contest["status"] != "open":
        sessions.pop(token, None)
        await query.answer("⚠️ انتهت هذه المسابقة.", show_alert=True)
        try:
            _bt, _be = bold_notice("⚠️ انتهت هذه المسابقة.")
            await query.edit_message_text(text=_bt, entities=_be)
        except Exception:
            pass
        return

    if voter.id == participant_id:
        sessions.pop(token, None)
        await query.answer("🚫 لا يمكنك التصويت لنفسك.", show_alert=True)
        return

    if has_voted(contest_code, voter.id):
        sessions.pop(token, None)
        await query.answer("✅ لقد قمت بالتصويت مسبقًا في هذه المسابقة.", show_alert=True)
        return

    participant = get_contest_participant(contest_code, participant_id)
    if not participant:
        sessions.pop(token, None)
        await query.answer("⚠️ هذا المتسابق لم يعد مسجّلًا.", show_alert=True)
        return

    # طبقة حماية أخيرة: إعادة فحص شرط بريميوم مباشرة قبل احتساب التصويت،
    # حتى لو تغيّرت حالة اشتراك المستخدم في بريميوم بين فتح الكابتشا والضغط
    # على الرمز الصحيح — فلا يُحتسب أي صوت من مستخدم غير مؤهل مهما حدث.
    if contest.get("premium_only") and not voter.is_premium:
        sessions.pop(token, None)
        await query.answer("💎 هذه المسابقة للتصويت لمستخدمي بريميوم فقط.", show_alert=True)
        return

    # نظام الأمان: لا يُحتسب أي تصويت إلا بعد التأكد من أن المصوّت لا يزال
    # مشتركًا فعليًا في القناة الإلزامية لحظة التحقق (وليس فقط لحظة فتح البوت).
    if not await is_user_subscribed(context, voter.id, force_refresh=True):
        await query.answer(
            "⚠️ يجب الاشتراك في القناة الإلزامية أولاً، اشترك ثم اضغط نفس الزر مجددًا للتحقق.",
            show_alert=True,
        )
        return

    registered = register_confirmed_contest_vote(contest_code, voter.id, participant_id, contest["owner_id"])
    if not registered:
        sessions.pop(token, None)
        await query.answer("✅ لقد قمت بالتصويت مسبقًا في هذه المسابقة.", show_alert=True)
        return
    new_votes = get_participant_votes(contest_code, participant_id)
    sessions.pop(token, None)

    await query.answer("✅ تم التحقق وتسجيل تصويتك بنجاح!", show_alert=True)

    text, entities = build_vote_captcha_success_message()
    try:
        await query.edit_message_text(text=text, entities=entities)
    except Exception:
        pass

    if participant["channel_message_id"]:
        try:
            await context.bot.edit_message_reply_markup(
                chat_id=contest["chat_id"],
                message_id=participant["channel_message_id"],
                reply_markup=build_contest_vote_keyboard(
                    contest_code, participant_id, new_votes, participant["participant_code"]
                ),
            )
        except Exception:
            pass

    # إنهاء تلقائي للمسابقات المعتمدة على «عدد أصوات محدد» عند وصول أي متسابق
    # لعدد الأصوات المستهدف — بنفس آلية إنهاء المسابقات المعتمدة على الوقت.
    if (
        contest.get("end_type") == "votes"
        and contest.get("votes_target")
        and new_votes >= contest["votes_target"]
    ):
        try:
            await finish_contest_by_time(context.bot, contest_code)
        except Exception:
            logger.exception("vote_captcha_callback: فشل إنهاء المسابقة %s تلقائيًا عند اكتمال الأصوات", contest_code)


async def rr_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    roulette_id = int(query.data.replace("rr_join_", ""))

    result = join_roulette(user.id, roulette_id, user.first_name or user.username or str(user.id))

    if not result["found"]:
        await query.answer("⚠️ هذا الروليت غير موجود.", show_alert=True)
        return

    target = result["target"]
    current = result["current"]

    if result["status"] != "open":
        await query.answer("⚠️ انتهى هذا الروليت بالفعل.", show_alert=True)
        return

    if result["already"]:
        await query.answer(
            f"✅ أنت مسجّل بالفعل.\n👥 المشاركين: {current}/{target}",
            show_alert=True,
        )
        return

    try:
        body_text, body_entities = build_quick_roulette_channel_message(target, current)
        await query.edit_message_text(
            text=body_text,
            entities=body_entities,
            reply_markup=roulette_share_keyboard(roulette_id),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
    except Exception as e:
        print(f"rr_join edit_message_text error: {e}")

    await query.answer(
        f"✅ تم تسجيل مشاركتك!\n👥 المشاركين: {current}/{target}",
        show_alert=True,
    )

    owner_id = result.get("owner_id")
    if owner_id and owner_id != user.id:
        display_name = user.first_name or user.username or str(user.id)
        notify_text, notify_entities = build_quick_roulette_join_notify_message(display_name)
        try:
            await context.bot.send_message(
                chat_id=owner_id, text=notify_text, entities=notify_entities,
            )
        except Exception:
            pass

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_id = update.inline_query.from_user.id
    results = []

    try:
        ids_map = create_roulettes_batch(owner_id, ROULETTE_COUNTS)
        for n in ROULETTE_COUNTS:
            roulette_id = ids_map[n]
            body_text, body_entities = build_quick_roulette_channel_message(n, 0)
            results.append(
                InlineQueryResultArticle(
                    id=str(roulette_id),
                    title=f"انشاء روليت لـ ({n}) مشاركين",
                    description="اضغط هنا لبدء روليت سريع بهذا العدد",
                    thumbnail_url=ROULETTE_THUMBS[n],
                    input_message_content=InputTextMessageContent(
                        body_text, entities=body_entities,
                        link_preview_options=LinkPreviewOptions(is_disabled=True),
                    ),
                    reply_markup=roulette_share_keyboard(roulette_id),
                )
            )

        await update.inline_query.answer(results, cache_time=0, is_personal=True)
    except Exception as e:
        print(f"Inline Query Error: {e}")

async def chosen_result_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chosen = update.chosen_inline_result
    if not chosen.inline_message_id:
        return
    try:
        roulette_id = int(chosen.result_id)
    except ValueError:
        return
    set_inline_message_id(roulette_id, chosen.inline_message_id)

async def rr_spin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    roulette_id = int(query.data.replace("rr_spin_", ""))
    roulette = get_roulette(roulette_id)
    if not roulette:
        await query.answer("هذا الروليت غير موجود.", show_alert=True)
        return

    if query.from_user.id != roulette["owner_id"] and query.from_user.id not in ADMIN_IDS:
        await query.answer("فقط منشئ الروليت يمكنه التدوير.", show_alert=True)
        return

    status = roulette["status"]

    if status == "closed":
        await query.answer("تم تدوير هذا الروليت من قبل.", show_alert=True)
        return

    participants = get_participants_with_names(roulette_id)
    if len(participants) < 2:
        await query.answer("يجب وجود مشاركين اثنين على الأقل!", show_alert=True)
        return

    if status == "open":
        await query.answer()
        set_roulette_status(roulette_id, "waiting_spin")
        text, entities = build_waiting_spin_message(
            roulette["target_count"], len(participants), participants
        )
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=waiting_spin_keyboard(roulette_id),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        return

    if status == "waiting_spin":
        await query.answer()
        winner_id, winner_name = random.choice(participants)
        set_roulette_status(roulette_id, "closed")

        text, entities = build_result_message(winner_id, winner_name, participants)
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=result_keyboard(roulette_id),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        return

async def rr_respin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    roulette_id = int(query.data.replace("rr_respin_", ""))
    roulette = get_roulette(roulette_id)
    if not roulette:
        await query.answer("هذا الروليت غير موجود.", show_alert=True)
        return

    if query.from_user.id != roulette["owner_id"] and query.from_user.id not in ADMIN_IDS:
        await query.answer("فقط منشئ الروليت يمكنه إعادة الاختيار.", show_alert=True)
        return

    participants = get_participants_with_names(roulette_id)
    if len(participants) < 2:
        await query.answer("يجب وجود مشاركين اثنين على الأقل!", show_alert=True)
        return

    await query.answer()
    winner_id, winner_name = random.choice(participants)

    text, entities = build_result_message(winner_id, winner_name, participants)
    await query.edit_message_text(
        text=text,
        entities=entities,
        reply_markup=result_keyboard(roulette_id),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )

async def qr_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        build_roulette_privacy_settings_text(),
        reply_markup=build_roulette_privacy_settings_keyboard(),
    )

async def roulette_privacy_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data == "toggle_hide_participants_internal":
        await query.answer()
        current = get_setting("hide_participants")
        set_setting("hide_participants", "0" if current == "1" else "1")
        await query.edit_message_text(
            build_roulette_privacy_settings_text(),
            reply_markup=build_roulette_privacy_settings_keyboard(),
        )
        return

    if data == "edit_game_cliche":
        await query.answer()
        context.user_data["awaiting_setting"] = "game_cliche"
        await query.edit_message_text(
            build_cliche_prompt_text(),
            parse_mode="Markdown",
            reply_markup=build_cliche_prompt_keyboard(),
        )
        return

    if data == "restore_defaults_roulette":
        await query.answer("تمت إعادة الإعدادات للوضع الافتراضي ✅")
        set_setting("hide_participants", DEFAULT_HIDE_PARTICIPANTS)
        set_setting("game_cliche", DEFAULT_GAME_CLICHE)
        await query.edit_message_text(
            build_roulette_privacy_settings_text(),
            reply_markup=build_roulette_privacy_settings_keyboard(),
        )
        return

    if data == "section_roulette":
        await query.answer()
        await query.edit_message_text(
            text=QUICK_ROULETTE_TEXT,
            reply_markup=build_quick_roulette_keyboard(),
        )
        return

async def handle_setting_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = context.user_data.get("awaiting_setting")
    if not field:
        return
    value = update.message.text.strip()
    if not is_owner(update.effective_user.id) and (
        field.startswith("points_") or field.startswith("required_channel_")
    ):
        context.user_data.pop("awaiting_setting", None)
        return

    if field in ("points_per_user", "points_required", "reward_value"):
        if not value.isdigit() or int(value) < 0:
            await update.message.reply_text("⚠️ أرسل رقمًا صحيحًا أكبر من أو يساوي صفر ”")
            return

    if field == "required_channel_username":
        username = _normalize_channel_username(value)
        if not username:
            await update.message.reply_text("⚠️ أرسل اسم يوزر صحيح للقناة (مثال: @channel أو رابط t.me/channel) ”")
            return
        set_setting("required_channel_username", username)
        set_setting("required_channel_url", f"https://t.me/{username}")
        _SUBSCRIPTION_CACHE.clear()
        context.user_data.pop("awaiting_setting", None)
        warning = await _check_bot_can_verify_channel(context, username)
        await update.message.reply_text(
            f"✅ تم تغيير قناة الاشتراك الإجباري إلى @{username} بنجاح."
            + (f"\n\n{warning}" if warning else ""),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="owner_sub_section", style="danger")
            ]]),
        )
        return

    if field == "required_channel_next_username":
        username = _normalize_channel_username(value)
        if not username:
            await update.message.reply_text("⚠️ أرسل اسم يوزر صحيح للقناة (مثال: @channel أو رابط t.me/channel) ”")
            return
        set_setting("required_channel_next_username", username)
        context.user_data.pop("awaiting_setting", None)
        await update.message.reply_text(
            f"✅ تم تحديد القناة التالية: @{username}\n"
            f"سيتم التحويل إليها تلقائيًا عند وصول القناة الحالية إلى {get_required_channel_auto_target()} مشترك.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="owner_sub_auto", style="danger")
            ]]),
        )
        return

    if field == "required_channel_auto_target":
        if not value.isdigit() or int(value) <= 0:
            await update.message.reply_text("⚠️ أرسل رقمًا صحيحًا أكبر من صفر ”")
            return
        set_setting("required_channel_auto_target", value)
        context.user_data.pop("awaiting_setting", None)
        await update.message.reply_text(
            f"✅ تم تحديد العدد المطلوب: {value} مشترك.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="owner_sub_auto", style="danger")
            ]]),
        )
        return

    set_setting(field, value)
    context.user_data.pop("awaiting_setting", None)

    if field == "game_cliche":
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("رجوع للإعدادات", callback_data="qr_settings", style="danger", **emoji_kwargs("back_section_btn"))]
        ])
        await update.message.reply_text(
            "✅ تم تحديث نص الترحيب في كليشة اللعبة بنجاح.",
            reply_markup=reply_markup
        )
        return
    if field.startswith("points_") or field in ("reward_type", "reward_value"):
        text, entities = build_points_settings_message()
        await update.message.reply_text(
            text="✅ تم حفظ الإعداد بنجاح ”",
            reply_markup=build_points_settings_keyboard(),
        )
        return

def build_under_development_message(emoji_key: str = None, emoji_char: str = "🚧") -> tuple:
    """رسالة موحّدة «قيد التطوير» لأي زر لم تُفعَّل وظيفته بعد — بخط عريض داخل اقتباس."""
    lead = (emoji_char, EMOJI[emoji_key]) if emoji_key else emoji_char
    return build_text_with_emojis([
        ([
            ([lead, " هذه الميزة قيد التطوير حاليًا، تابعنا قريبًا!  ”"], "bold", None),
        ], "blockquote", None),
    ])

async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "my_stats":
        text, entities = build_points_message(query.from_user.id)
        await query.edit_message_text(
            text=text, entities=entities,
            reply_markup=build_points_keyboard(query.from_user.id),
        )
        return

    if query.data == "points_stats":
        text, entities = build_points_statistics_message()
        await query.edit_message_text(
            text=text, entities=entities,
            reply_markup=build_points_statistics_keyboard(),
        )
        return

    if query.data == "owner_section":
        if not is_owner(query.from_user.id):
            await query.answer("⛔ هذا القسم خاص بمالك البوت فقط.", show_alert=True)
            return
        text, entities = build_owner_section_message()
        await query.edit_message_text(
            text=text, entities=entities,
            reply_markup=build_owner_section_keyboard(),
        )
        return

    if query.data == "owner_points_section":
        if not is_owner(query.from_user.id):
            await query.answer("⛔ هذا القسم خاص بمالك البوت فقط.", show_alert=True)
            return
        text, entities = build_owner_points_section_message()
        await query.edit_message_text(
            text=text, entities=entities,
            reply_markup=build_owner_points_section_keyboard(),
        )
        return

    if query.data == "owner_withdraw_section":
        if not is_owner(query.from_user.id):
            await query.answer("⛔ هذا القسم خاص بمالك البوت فقط.", show_alert=True)
            return
        text, entities = build_owner_withdraw_section_message()
        await query.edit_message_text(
            text=text, entities=entities,
            reply_markup=build_owner_withdraw_section_keyboard(),
        )
        return

    if query.data.startswith("wd_complete:"):
        if not is_owner(query.from_user.id):
            await query.answer("⛔ هذا الإجراء خاص بمالك البوت فقط.", show_alert=True)
            return
        request_id = query.data.split(":", 1)[1]
        req = get_withdraw_request(request_id)
        if not req:
            await query.answer("⚠️ هذا الطلب غير موجود.", show_alert=True)
        elif req.get("status") != "pending":
            await query.answer("✅ تم تأكيد هذا الطلب مسبقًا.", show_alert=True)
        else:
            mark_withdraw_completed(request_id)
            await query.answer("✅ تم تعليم الطلب كمكتمل.")
            try:
                await context.bot.send_message(
                    chat_id=req["user_id"],
                    text=(
                        "🎉 تم استلام طلب سحبك بنجاح وتحويل مكافأتك!\n\n"
                        f"💎 عدد النقاط المسحوبة: {req.get('points_amount', 0)}\n"
                        "📌 الحالة: 🟢 مكتمل"
                    ),
                )
            except Exception:
                pass
        text, entities = build_owner_withdraw_section_message()
        try:
            await query.edit_message_text(
                text=text, entities=entities,
                reply_markup=build_owner_withdraw_section_keyboard(),
            )
        except Exception:
            pass
        return

    if query.data == "withdraw_locked":
        required = int(get_setting("points_required") or "0")
        pts = get_points(query.from_user.id)
        await query.answer(
            f"🔒 تحتاج {required} نقطة على الأقل للسحب، رصيدك الحالي: {pts} نقطة.",
            show_alert=True,
        )
        return

    if query.data == "withdraw_pending":
        await query.answer(
            "🟡 لديك طلب سحب قيد الانتظار بالفعل، سيتم التواصل معك بعد مراجعته.",
            show_alert=True,
        )
        return

    if query.data == "withdraw_start":
        user = query.from_user
        required = int(get_setting("points_required") or "0")
        pts = get_points(user.id)
        if required <= 0:
            await query.answer("⚠️ ميزة السحب غير مفعّلة حاليًا.", show_alert=True)
            return
        if has_pending_withdraw_request(user.id):
            await query.answer(
                "🟡 لديك طلب سحب قيد الانتظار بالفعل، انتظر مراجعته أولاً.", show_alert=True,
            )
            return
        if pts < required:
            await query.answer(
                f"🔒 تحتاج {required} نقطة على الأقل للسحب، رصيدك الحالي: {pts} نقطة.",
                show_alert=True,
            )
            return
        # التواصل مع صاحب طلب السحب يتم عبر يوزر تليجرام مباشرة، لذا لا يمكن
        # إنشاء أي طلب لمستخدم بلا اسم مستخدم (username) — نطلب منه إضافته
        # أولاً من إعدادات تليجرام قبل السماح له بالمتابعة.
        if not user.username:
            await query.answer(
                "⚠️ يجب إضافة اسم مستخدم (Username) في إعدادات تليجرام أولاً "
                "حتى نتمكن من التواصل معك لإرسال مكافأتك، ثم اضغط على زر السحب مجددًا.",
                show_alert=True,
            )
            return

        display_name = user.first_name or user.username or str(user.id)
        request_id = create_withdraw_request(user.id, display_name, user.username, pts)

        await query.answer(
            f"✅ تم إرسال طلب سحبك بنجاح!\n💎 عدد النقاط: {pts}\n📌 الحالة: قيد الانتظار",
            show_alert=True,
        )

        text, entities = build_points_message(user.id)
        try:
            await query.edit_message_text(
                text=text, entities=entities,
                reply_markup=build_points_keyboard(user.id),
            )
        except Exception:
            pass

        for owner_id in OWNER_IDS:
            try:
                await context.bot.send_message(
                    chat_id=owner_id,
                    text=(
                        "💳 طلب سحب جديد\n\n"
                        f"👤 المستخدم: {display_name} (ID: {user.id})\n"
                        f"🔗 يوزر: @{user.username}\n"
                        f"💎 عدد النقاط: {pts}"
                    ),
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                        "✅ تأكيد الاستلام", callback_data=f"wd_complete:{request_id}", style="success",
                    )]]),
                )
            except Exception:
                pass
        return

    if query.data == "owner_sub_section":
        if not is_owner(query.from_user.id):
            await query.answer("⛔ هذا القسم خاص بمالك البوت فقط.", show_alert=True)
            return
        text, entities = build_owner_sub_section_message()
        await query.edit_message_text(
            text=text, entities=entities,
            reply_markup=build_owner_sub_section_keyboard(),
        )
        return

    if query.data == "owner_sub_change_current":
        if not is_owner(query.from_user.id):
            await query.answer("⛔ هذا القسم خاص بمالك البوت فقط.", show_alert=True)
            return
        context.user_data["awaiting_setting"] = "required_channel_username"
        await query.edit_message_text(
            "✍️ أرسل الآن يوزر القناة الجديدة للاشتراك الإجباري (مثال: @channel أو رابط t.me/channel) ”",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="owner_sub_section", style="danger")
            ]]),
        )
        return

    if query.data == "owner_sub_auto":
        if not is_owner(query.from_user.id):
            await query.answer("⛔ هذا القسم خاص بمالك البوت فقط.", show_alert=True)
            return
        text, entities = build_owner_sub_auto_message()
        await query.edit_message_text(
            text=text, entities=entities,
            reply_markup=build_owner_sub_auto_keyboard(),
        )
        return

    if query.data == "owner_sub_edit_target":
        if not is_owner(query.from_user.id):
            await query.answer("⛔ هذا القسم خاص بمالك البوت فقط.", show_alert=True)
            return
        context.user_data["awaiting_setting"] = "required_channel_auto_target"
        await query.edit_message_text(
            "✍️ أرسل الآن عدد المشتركين المطلوب للتحويل التلقائي (مثال: 1000) ”",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="owner_sub_auto", style="danger")
            ]]),
        )
        return

    if query.data == "owner_sub_edit_next":
        if not is_owner(query.from_user.id):
            await query.answer("⛔ هذا القسم خاص بمالك البوت فقط.", show_alert=True)
            return
        context.user_data["awaiting_setting"] = "required_channel_next_username"
        await query.edit_message_text(
            "✍️ أرسل الآن يوزر القناة التالية (مثال: @channel أو رابط t.me/channel) ”",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="owner_sub_auto", style="danger")
            ]]),
        )
        return

    if query.data == "owner_sub_clear_next":
        if not is_owner(query.from_user.id):
            await query.answer("⛔ هذا القسم خاص بمالك البوت فقط.", show_alert=True)
            return
        set_setting("required_channel_next_username", "")
        await query.answer("✅ تم إلغاء القناة التالية — لن يحدث تغيير تلقائي.")
        text, entities = build_owner_sub_auto_message()
        await query.edit_message_text(
            text=text, entities=entities,
            reply_markup=build_owner_sub_auto_keyboard(),
        )
        return

    if query.data == "points_settings":
        if not is_owner(query.from_user.id):
            await query.answer("⛔ هذا القسم خاص بالمشرف.", show_alert=True)
            return
        text, entities = build_points_settings_message()
        await query.edit_message_text(
            text=text, entities=entities,
            reply_markup=build_points_settings_keyboard(),
        )
        return

    if query.data == "points_text_settings":
        if not is_owner(query.from_user.id):
            await query.answer("⛔ هذا القسم خاص بالمشرف.", show_alert=True)
            return
        text, entities = build_points_text_settings_message()
        await query.edit_message_text(
            text=text, entities=entities,
            reply_markup=build_points_text_settings_keyboard(),
        )
        return

    if query.data == "points_restore_defaults":
        if not is_owner(query.from_user.id):
            await query.answer("⛔ هذا القسم خاص بالمشرف.", show_alert=True)
            return
        set_setting("points_title", DEFAULT_POINTS_TITLE)
        set_setting("points_conditions", DEFAULT_POINTS_CONDITIONS)
        await query.answer("✅ تمت إعادة نصوص قسم ربح للوضع الافتراضي.")
        text, entities = build_points_text_settings_message()
        await query.edit_message_text(
            text=text, entities=entities,
            reply_markup=build_points_text_settings_keyboard(),
        )
        return

    if query.data == "points_toggle":
        if not is_owner(query.from_user.id):
            await query.answer("⛔ هذا القسم خاص بالمشرف.", show_alert=True)
            return
        set_setting("points_enabled", "0" if get_setting("points_enabled") == "1" else "1")
        text, entities = build_points_settings_message()
        await query.edit_message_text(
            text=text, entities=entities,
            reply_markup=build_points_settings_keyboard(),
        )
        return

    if query.data.startswith("points_edit:"):
        if not is_owner(query.from_user.id):
            await query.answer("⛔ هذا القسم خاص بالمشرف.", show_alert=True)
            return
        field = query.data.split(":", 1)[1]
        labels = {
            "points_per_user": "عدد النقاط لكل مستخدم جديد",
            "points_required": "عدد النقاط المطلوبة للمكافأة",
            "reward_type": "نوع أو عملة المكافأة",
            "reward_value": "قيمة المكافأة",
            "points_title": "عنوان قسم ربح",
            "points_conditions": "شروط قسم ربح",
        }
        context.user_data["awaiting_setting"] = field
        await query.edit_message_text(
            f"✍️ أرسل الآن {labels.get(field, 'القيمة الجديدة')} ”",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="points_settings", style="danger")
            ]]),
        )
        return

    if query.data == "remind_win":
        enabled = toggle_remind_win(query.from_user.id)
        try:
            await query.edit_message_reply_markup(
                reply_markup=build_main_keyboard(enabled, query.from_user.id)
            )
        except Exception:
            pass
        return

    if query.data == "create_contest":
        text, entities = build_contest_section_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_section_keyboard(),
        )
        return

    if query.data == "terms":
        text, entities = build_terms_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_terms_keyboard(),
        )
        return

    if query.data == "support_bot":
        text, entities = build_support_bot_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_support_bot_keyboard(),
        )
        return

    if query.data == "support_pay_stars":
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title="دعم البوت ⭐",
            description=(
                f"ادفع {SUPPORT_BOT_STARS_AMOUNT} نجوم تيليجرام لدعم تطوير البوت 💖\n\n"
                "كل نجمة تساعدنا في الاستمرار وتطوير ميزات جديدة!"
            ),
            payload="support_bot_stars",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice("دعم البوت", SUPPORT_BOT_STARS_AMOUNT)],
        )
        return

    replies = {}
    if query.data in replies:
        emoji_char, emoji_key = replies[query.data]
        text, entities = build_under_development_message(emoji_key=emoji_key, emoji_char=emoji_char)
        await query.message.reply_text(text=text, entities=entities)

async def support_precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يوافق تلقائيًا على أي طلب دفع بنجوم تيليجرام (XTR) قبل تأكيد الشراء النهائي."""
    query = update.pre_checkout_query
    await query.answer(ok=True)

async def support_successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يُستدعى بعد اكتمال عملية الدفع بنجوم تيليجرام بنجاح."""
    await update.message.reply_text(
        f"✅ شكرًا لدعمك! تم استلام {SUPPORT_BOT_STARS_AMOUNT} نجوم بنجاح 💖"
    )

async def get_id_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting"] = "emoji_id"
    _bt, _be = bold_notice("أرسل الآن الإيموجي المتحرك الذي تريد معرفة رقمه 👇")
    await update.message.reply_text(text=_bt, entities=_be)

async def channel_forward_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    يلتقط رسالة مُعاد توجيهها من قناة إلى خاص البوت (الخطوة 2 في شاشة تسجيل القناة)،
    يتأكد أن البوت مشرف فيها وأن المُرسل مشرف فيها أيضًا، ثم يسجّلها له.
    هذا مسار تسجيل احتياطي ضروري لأن حدث my_chat_member لا يُعاد إرساله للقنوات
    التي كان البوت مشرفًا فيها بالفعل قبل تشغيل هذا الإصدار من الكود.
    """
    message = update.effective_message
    if message is None or message.chat.type != "private":
        return

    origin_chat = None
    forward_origin = getattr(message, "forward_origin", None)
    if forward_origin is not None and getattr(forward_origin, "type", None) == "channel":
        origin_chat = forward_origin.chat
    elif getattr(message, "forward_from_chat", None) is not None:
        origin_chat = message.forward_from_chat

    if origin_chat is None or origin_chat.type != "channel":
        return

    async def delete_forwarded_message():
        try:
            await message.delete()
        except Exception as exc:
            logger.warning("تعذر حذف رسالة القناة المُعادة: %s", exc)

    if origin_chat.username and origin_chat.username.lower() == ANNOUNCE_CHANNEL_USERNAME.lower():
        _bt, _be = bold_notice("⚠️ لا يمكن تسجيل هذه القناة.")
        await message.reply_text(text=_bt, entities=_be)
        await delete_forwarded_message()
        return

    user = update.effective_user
    try:
        bot_member = await context.bot.get_chat_member(origin_chat.id, context.bot.id)
        user_member = await context.bot.get_chat_member(origin_chat.id, user.id)
    except Exception:
        _bt, _be = bold_notice("⚠️ تعذر التحقق من القناة، أعد المحاولة.")
        await message.reply_text(text=_bt, entities=_be)
        await delete_forwarded_message()
        return

    if bot_member.status not in ("administrator", "creator"):
        _bt, _be = bold_notice("⚠️ البوت ليس مشرفًا في هذه القناة.")
        await message.reply_text(text=_bt, entities=_be)
        await delete_forwarded_message()
        return

    if user_member.status not in ("administrator", "creator"):
        _bt, _be = bold_notice("يجب أن تكون مشرفًا في هذه القناة لتسجيلها.")
        await message.reply_text(text=_bt, entities=_be)
        await delete_forwarded_message()
        return

    if context.user_data.get("awaiting") == "gw_condition_channel_private":
        pending = context.user_data.setdefault("gw_condition_channels_pending", [])
        if any(str(c.get("ref")) == str(origin_chat.id) for c in pending):
            _bt, _be = bold_notice("⚠️ هذه القناة مضافة بالفعل كشرط.")
            await message.reply_text(text=_bt, entities=_be)
            await delete_forwarded_message()
            return
        if len(pending) >= GW_CONDITION_CHANNELS_MAX:
            _bt, _be = bold_notice("❌ يمكنك إضافة قناتين كحد أقصى!")
            await message.reply_text(text=_bt, entities=_be)
            await delete_forwarded_message()
            return

        chat_title = origin_chat.title or str(origin_chat.id)
        invite_url = None
        try:
            invite_link = await context.bot.create_chat_invite_link(origin_chat.id)
            invite_url = invite_link.invite_link
        except Exception:
            try:
                invite_url = await context.bot.export_chat_invite_link(origin_chat.id)
            except Exception:
                invite_url = None

        pending.append({"ref": origin_chat.id, "title": chat_title, "url": invite_url})

        if len(pending) >= GW_CONDITION_CHANNELS_MAX:
            context.user_data["gw_condition_channels"] = pending
            context.user_data.pop("gw_condition_channels_pending", None)
            context.user_data.pop("awaiting", None)
            for key, default in GIVEAWAY_SETTINGS_DEFAULTS.items():
                context.user_data.setdefault(key, default)

            confirm_text, confirm_entities = build_giveaway_condition_linked_message(
                [c["title"] for c in pending],
            )
            await message.reply_text(text=confirm_text, entities=confirm_entities)

            settings_text, settings_entities = build_giveaway_settings_message()
            await message.reply_text(
                text=settings_text,
                entities=settings_entities,
                reply_markup=build_giveaway_settings_keyboard(context.user_data),
            )
        else:
            text, entities = build_giveaway_condition_private_message(added_count=len(pending))
            await message.reply_text(
                text=text,
                entities=entities,
                reply_markup=build_giveaway_condition_private_keyboard(added_count=len(pending)),
            )
        await delete_forwarded_message()
        return

    chat_title = origin_chat.title or (f"@{origin_chat.username}" if origin_chat.username else str(origin_chat.id))
    save_registered_chat(
        chat_id=origin_chat.id,
        owner_id=user.id,
        chat_title=chat_title,
        chat_type="channel",
    )
    _bt, _be = bold_notice(f"✅ تم تسجيل القناة «{chat_title}» بنجاح ")
    await message.reply_text(text=_bt, entities=_be)
    await delete_forwarded_message()


async def group_activation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    يلتقط كتابة «تفعيل روليت» داخل الجروب نفسه (الخطوة 2 في شاشة تسجيل الجروب)،
    يتأكد أن البوت والمُرسل مشرفان في الجروب، ثم يسجّله.
    """
    message = update.effective_message
    if message is None or message.chat.type not in ("group", "supergroup"):
        return
    if not message.text or "تفعيل روليت" not in message.text:
        return

    chat = message.chat
    user = update.effective_user
    try:
        bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
        user_member = await context.bot.get_chat_member(chat.id, user.id)
    except Exception:
        _bt, _be = bold_notice("تعذر التحقق من الصلاحيات، تأكد أن البوت مشرف في الجروب.")
        await message.reply_text(text=_bt, entities=_be)
        return

    if bot_member.status != "administrator":
        _bt, _be = bold_notice("يجب إضافة البوت كمشرف في الجروب أولاً.")
        await message.reply_text(text=_bt, entities=_be)
        return

    if user_member.status not in ("administrator", "creator"):
        _bt, _be = bold_notice("يجب أن تكون مشرفًا في هذا الجروب لتفعيله.")
        await message.reply_text(text=_bt, entities=_be)
        return

    chat_title = chat.title or str(chat.id)
    save_registered_chat(
        chat_id=chat.id,
        owner_id=user.id,
        chat_title=chat_title,
        chat_type=chat.type,
    )
    _bt, _be = bold_notice(f"✅ تم تفعيل الروليت لجروب «{chat_title}» بنجاح.")
    await message.reply_text(text=_bt, entities=_be)


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    awaiting = context.user_data.get("awaiting")
    awaiting_setting = context.user_data.get("awaiting_setting")

    if awaiting_setting:
        await handle_setting_input(update, context)
        return

    if awaiting == "contest_cliche":
        context.user_data["contest_cliche_text"] = update.message.text
        context.user_data["contest_cliche_entities"] = update.message.entities
        context.user_data["awaiting"] = "contest_count"
        text, entities = build_contest_count_message()
        await update.message.reply_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_count_keyboard(),
        )
        return

    if awaiting == "contest_count":
        raw = (update.message.text or "").strip()
        if not raw.isdigit() or int(raw) <= 0:
            _bt, _be = bold_notice("من فضلك أرسل رقمًا صحيحًا أكبر من صفر لعدد المتسابقين.")
            await update.message.reply_text(text=_bt, entities=_be)
            return
        context.user_data["contest_target_count"] = int(raw)
        context.user_data.pop("awaiting", None)
        text, entities = build_contest_end_method_message()
        await update.message.reply_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_end_method_keyboard(),
        )
        return

    if awaiting == "contest_votes_target":
        raw = (update.message.text or "").strip()
        if not raw.isdigit() or int(raw) <= 0:
            _bt, _be = bold_notice("من فضلك أرسل رقمًا صحيحًا أكبر من صفر لعدد الأصوات.")
            await update.message.reply_text(text=_bt, entities=_be)
            return
        context.user_data["contest_votes_target"] = int(raw)
        context.user_data["awaiting"] = "contest_winners_count"
        text, entities = build_contest_winners_message()
        await update.message.reply_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_winners_keyboard(),
        )
        return

    if awaiting == "contest_winners_count":
        raw = (update.message.text or "").strip()
        if not raw.isdigit() or int(raw) <= 0:
            _bt, _be = bold_notice("من فضلك أرسل رقمًا صحيحًا أكبر من صفر لعدد الفائزين.")
            await update.message.reply_text(text=_bt, entities=_be)
            return
        context.user_data["contest_winners_count"] = int(raw)
        context.user_data.pop("awaiting", None)
        for key, default in CONTEST_SETTINGS_DEFAULTS.items():
            context.user_data.setdefault(key, default)

        confirm_text, confirm_entities = build_contest_winners_confirm_message()
        await update.message.reply_text(text=confirm_text, entities=confirm_entities)

        settings_text, settings_entities = build_contest_settings_message()
        await update.message.reply_text(
            text=settings_text,
            entities=settings_entities,
            reply_markup=build_contest_settings_keyboard(context.user_data),
        )
        return

    if awaiting == "gw_cliche":
        context.user_data["gw_cliche_text"] = update.message.text
        context.user_data["gw_cliche_entities"] = update.message.entities
        context.user_data.pop("awaiting", None)
        for key, default in GIVEAWAY_SETTINGS_DEFAULTS.items():
            context.user_data.setdefault(key, default)
        text, entities = build_giveaway_settings_message()
        await update.message.reply_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_settings_keyboard(context.user_data),
        )
        return

    if awaiting == "gw_vote_code":
        raw_code = (update.message.text or "").strip()
        participant = get_participant_by_code(raw_code) if raw_code else None
        contest = get_contest(participant["contest_code"]) if participant else None
        if not participant or not contest or contest["status"] != "open":
            text, entities = build_giveaway_vote_code_error_message()
            await update.message.reply_text(
                text=text,
                entities=entities,
                reply_markup=build_giveaway_vote_code_error_keyboard(),
            )
            return

        context.user_data["gw_vote_contest_code"] = contest["contest_code"]
        context.user_data["gw_vote_participant_id"] = participant["user_id"]
        context.user_data["gw_vote_participant_code"] = raw_code
        context.user_data["gw_vote_display_name"] = participant.get("display_name") or "متسابق"
        context.user_data.pop("awaiting", None)
        for key, default in GIVEAWAY_SETTINGS_DEFAULTS.items():
            context.user_data.setdefault(key, default)

        confirm_text, confirm_entities = build_giveaway_vote_linked_message(raw_code)
        await update.message.reply_text(text=confirm_text, entities=confirm_entities)

        settings_text, settings_entities = build_giveaway_settings_message()
        await update.message.reply_text(
            text=settings_text,
            entities=settings_entities,
            reply_markup=build_giveaway_settings_keyboard(context.user_data),
        )
        return

    if awaiting == "gw_condition_channel_public":
        raw_lines = [
            line.strip() for line in (update.message.text or "").splitlines() if line.strip()
        ]
        if not raw_lines:
            text, entities = build_giveaway_condition_error_message()
            await update.message.reply_text(
                text=text, entities=entities, reply_markup=build_giveaway_condition_public_keyboard(),
            )
            return
        if len(raw_lines) > GW_CONDITION_CHANNELS_MAX:
            text, entities = build_giveaway_condition_max_error_message()
            await update.message.reply_text(
                text=text, entities=entities, reply_markup=build_giveaway_condition_public_keyboard(),
            )
            return

        resolved = []
        for raw in raw_lines:
            username = _normalize_channel_username(raw)
            if not username or " " in username:
                resolved = None
                break
            try:
                chat = await context.bot.get_chat(f"@{username}")
                bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
                if bot_member.status not in ("administrator", "creator"):
                    resolved = None
                    break
            except Exception:
                resolved = None
                break
            resolved.append({
                "ref": f"@{username}",
                "title": chat.title or f"@{username}",
                "url": f"https://t.me/{username}",
            })

        if resolved is None or not resolved:
            text, entities = build_giveaway_condition_error_message()
            await update.message.reply_text(
                text=text,
                entities=entities,
                reply_markup=build_giveaway_condition_public_keyboard(),
            )
            return

        context.user_data["gw_condition_channels"] = resolved
        context.user_data.pop("awaiting", None)
        for key, default in GIVEAWAY_SETTINGS_DEFAULTS.items():
            context.user_data.setdefault(key, default)

        confirm_text, confirm_entities = build_giveaway_condition_linked_message(
            [c["title"] for c in resolved],
        )
        await update.message.reply_text(text=confirm_text, entities=confirm_entities)

        settings_text, settings_entities = build_giveaway_settings_message()
        await update.message.reply_text(
            text=settings_text,
            entities=settings_entities,
            reply_markup=build_giveaway_settings_keyboard(context.user_data),
        )
        return

    if awaiting == "gw_autospin_count":
        raw = (update.message.text or "").strip()
        if not raw.isdigit() or int(raw) <= 0:
            _bt, _be = bold_notice("من فضلك أرسل رقمًا صحيحًا أكبر من صفر لعدد المشاركين.")
            await update.message.reply_text(text=_bt, entities=_be)
            return
        for key, default in GIVEAWAY_SETTINGS_DEFAULTS.items():
            context.user_data.setdefault(key, default)
        context.user_data["gw_autospin_mode"] = "count"
        context.user_data["gw_autospin_target"] = int(raw)
        context.user_data.pop("awaiting", None)

        text, entities = build_giveaway_settings_message()
        await update.message.reply_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_settings_keyboard(context.user_data),
        )
        return

    if awaiting == "gw_winners_count":
        raw = (update.message.text or "").strip()
        if not raw.isdigit() or int(raw) <= 0:
            _bt, _be = bold_notice("من فضلك أرسل رقمًا صحيحًا أكبر من صفر لعدد الفائزين.")
            await update.message.reply_text(text=_bt, entities=_be)
            return
        context.user_data["gw_winners_count"] = int(raw)
        context.user_data.pop("awaiting", None)
        await publish_giveaway(update, context)
        return

    if awaiting == "emoji_id":
        entities = update.message.entities or []
        found = False
        for entity in entities:
            if entity.type == "custom_emoji":
                found = True
                emoji_text = update.message.text[entity.offset: entity.offset + entity.length]
                await update.message.reply_text(
                    f"الإيموجي: {emoji_text}\nرقمه: `{entity.custom_emoji_id}`",
                    parse_mode="Markdown",
                )
        if not found:
            _bt, _be = bold_notice("لم أجد إيموجي متحرك في رسالتك.")
            await update.message.reply_text(text=_bt, entities=_be)
        context.user_data.pop("awaiting", None)
        return

async def _go_to_quick_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        text=QUICK_ROULETTE_TEXT,
        reply_markup=build_quick_roulette_keyboard(),
    )

async def show_contest_detail(query, context: ContextTypes.DEFAULT_TYPE, contest):
    """يعرض شاشة إعدادات مسابقة واحدة (تُستخدم من قائمة المسابقات الحديثة)."""
    channel_title = get_chat_title_by_id(contest["chat_id"])
    post_link = await build_contest_post_link(context, contest["chat_id"], contest["channel_message_id"])
    participants_count = count_contest_participants(contest["contest_code"])
    text, entities = build_contest_detail_message(contest, channel_title, post_link, participants_count)
    await query.edit_message_text(
        text=text,
        entities=entities,
        reply_markup=build_contest_detail_keyboard(contest),
    )


async def contest_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعرض تفاصيل مسابقة محددة عند اختيارها من قائمة «المسابقات الحديثة»."""
    query = update.callback_query
    await query.answer()
    code = query.data.split(":", 1)[1]
    contest = get_contest(code)
    if not contest or contest["owner_id"] != query.from_user.id:
        await query.answer("تعذر العثور على هذه المسابقة.", show_alert=True)
        return
    await show_contest_detail(query, context, contest)


async def contest_management_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج أزرار إدارة مسابقة محددة: الإيقاف/الاستئناف، الحذف، وغيرها."""
    query = update.callback_query
    action, _, code = query.data.partition(":")
    contest = get_contest(code)
    if not contest or contest["owner_id"] != query.from_user.id:
        await query.answer("تعذر العثور على هذه المسابقة.", show_alert=True)
        return

    if action == "comp_toggle_active":
        new_status = "paused" if contest["status"] == "open" else "open"
        set_contest_status(code, new_status)
        contest = get_contest(code)
        await query.answer("تم إيقاف المسابقة." if new_status == "paused" else "تم استئناف المسابقة.")
        await show_contest_detail(query, context, contest)
        return

    if action == "comp_delete_all":
        delete_contest_completely(code)
        await query.answer("تم حذف المسابقة بالكامل.", show_alert=True)
        text, entities = build_contest_section_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_section_keyboard(),
        )
        return

    await query.answer("🚧 هذه الميزة قيد التطوير حاليًا.", show_alert=True)


async def contest_section_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "back_main_menu":
        text, entities = build_welcome_message(query.from_user)
        remind_state = get_remind_win_state(query.from_user.id)
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_main_keyboard(remind_state, query.from_user.id),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        return

    if query.data == "section_competition":
        text, entities = build_contest_section_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_section_keyboard(),
        )
        return

    if query.data == "comp_start_create":
        context.user_data.pop("awaiting", None)
        context.user_data.pop("contest_target_chat_id", None)
        context.user_data.pop("contest_cliche_text", None)
        context.user_data.pop("contest_cliche_entities", None)
        context.user_data.pop("contest_target_count", None)
        text, entities = build_contest_target_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_target_keyboard(query.from_user.id),
        )
        return

    if query.data == "comp_recent":
        contests = get_contests_by_owner(query.from_user.id)
        if not contests:
            await query.answer("لا توجد مسابقات جارية حاليًا.", show_alert=True)
            return
        if len(contests) == 1:
            await show_contest_detail(query, context, contests[0])
            return
        text, entities = build_recent_contests_list_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_recent_contests_list_keyboard(contests),
        )
        return

    if query.data.startswith("comp_pick_chat_"):
        chat_id = int(query.data.replace("comp_pick_chat_", ""))
        context.user_data["contest_target_chat_id"] = chat_id
        context.user_data["awaiting"] = "contest_cliche"
        text, entities = build_contest_cliche_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_cliche_keyboard(),
        )
        return

    if query.data == "comp_back_to_klesha":
        context.user_data["awaiting"] = "contest_cliche"
        text, entities = build_contest_cliche_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_cliche_keyboard(),
        )
        return

    if query.data == "comp_back_to_count":
        context.user_data["awaiting"] = "contest_count"
        text, entities = build_contest_count_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_count_keyboard(),
        )
        return

    if query.data == "comp_end_votes":
        context.user_data.pop("awaiting_setting", None)
        context.user_data["contest_end_type"] = "votes"
        context.user_data["awaiting"] = "contest_votes_target"
        text, entities = build_contest_votes_target_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_votes_target_keyboard(),
        )
        return

    if query.data == "comp_end_time":
        context.user_data.pop("awaiting", None)
        context.user_data["contest_end_type"] = "time"
        text, entities = build_contest_time_menu_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_time_menu_keyboard(),
        )
        return

    if query.data == "comp_back_to_end_type":
        context.user_data.pop("awaiting", None)
        context.user_data.pop("contest_time_minutes", None)
        context.user_data.pop("contest_time_custom_minutes", None)
        context.user_data.pop("contest_votes_target", None)
        text, entities = build_contest_end_method_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_end_method_keyboard(),
        )
        return

    if query.data.startswith("comp_atime_set_"):
        minutes = int(query.data.replace("comp_atime_set_", ""))
        context.user_data["contest_time_minutes"] = minutes
        context.user_data.pop("contest_time_custom_minutes", None)
        context.user_data["awaiting"] = "contest_winners_count"
        text, entities = build_contest_winners_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_winners_keyboard(),
        )
        return

    if query.data == "comp_atime_show_custom":
        context.user_data["contest_time_custom_minutes"] = context.user_data.get("contest_time_minutes") or 0
        text, entities = build_contest_time_menu_message(
            format_duration_label(context.user_data["contest_time_custom_minutes"]),
        )
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_time_custom_keyboard(),
        )
        return

    if query.data.startswith("comp_atime_custom_delta:"):
        delta = int(query.data.split(":", 1)[1])
        current = context.user_data.get("contest_time_custom_minutes", 0)
        context.user_data["contest_time_custom_minutes"] = max(0, current + delta)
        text, entities = build_contest_time_menu_message(
            format_duration_label(context.user_data["contest_time_custom_minutes"]),
        )
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_time_custom_keyboard(),
        )
        return

    if query.data == "comp_atime_custom_reset":
        context.user_data["contest_time_custom_minutes"] = 0
        text, entities = build_contest_time_menu_message("غير محدد")
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_time_custom_keyboard(),
        )
        return

    if query.data == "comp_atime_custom_confirm":
        total = context.user_data.get("contest_time_custom_minutes", 0)
        if not total or total <= 0:
            await query.answer("⚠️ اختر وقتًا أولاً باستخدام أزرار التعديل.", show_alert=True)
            return
        context.user_data["contest_time_minutes"] = total
        context.user_data.pop("contest_time_custom_minutes", None)
        context.user_data["awaiting"] = "contest_winners_count"
        text, entities = build_contest_winners_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_winners_keyboard(),
        )
        return

    if query.data in (
        "comp_toggle_notify_win",
        "comp_toggle_announce_results",
        "comp_toggle_approve_participants",
        "comp_toggle_premium_only",
    ):
        key = query.data.replace("comp_toggle_", "contest_")
        for k, default in CONTEST_SETTINGS_DEFAULTS.items():
            context.user_data.setdefault(k, default)
        context.user_data[key] = not context.user_data.get(key, CONTEST_SETTINGS_DEFAULTS[key])
        text, entities = build_contest_settings_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_settings_keyboard(context.user_data),
        )
        return

    if query.data == "comp_back_to_winners":
        context.user_data["awaiting"] = "contest_winners_count"
        text, entities = build_contest_winners_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_contest_winners_keyboard(),
        )
        return

    if query.data == "comp_publish":
        ud = context.user_data
        chat_id = ud.get("contest_target_chat_id")
        target_count = ud.get("contest_target_count")

        if not chat_id or not target_count:
            await query.answer("⚠️ حدث خطأ، لم يتم تحديد جميع بيانات المسابقة.", show_alert=True)
            return

        cliche_text = ud.get("contest_cliche_text") or ""
        cliche_entities = ud.get("contest_cliche_entities") or []
        end_type = ud.get("contest_end_type")
        time_minutes = ud.get("contest_time_minutes")
        votes_target = ud.get("contest_votes_target")
        winners_count = ud.get("contest_winners_count")
        settings = {k: ud.get(k, d) for k, d in CONTEST_SETTINGS_DEFAULTS.items()}

        await query.answer()

        success_text, success_entities = build_publish_success_message()
        await query.edit_message_text(text=success_text, entities=success_entities)

        contest_code = generate_contest_code()
        create_contest(
            contest_code=contest_code,
            owner_id=query.from_user.id,
            chat_id=chat_id,
            cliche_text=cliche_text,
            cliche_entities=cliche_entities,
            target_count=target_count,
            end_type=end_type,
            time_minutes=time_minutes,
            winners_count=winners_count,
            settings=settings,
            votes_target=votes_target,
        )

        post_text, post_entities = build_contest_channel_message(
            cliche_text, cliche_entities, target_count, end_type, time_minutes, votes_target,
        )
        post_keyboard = build_contest_channel_keyboard(contest_code)
        try:
            sent = await context.bot.send_message(
                chat_id=chat_id,
                text=post_text,
                entities=post_entities,
                reply_markup=post_keyboard,
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            )
            set_contest_channel_message(contest_code, sent.message_id)
            asyncio.create_task(announce_new_post(context, chat_id, sent.message_id, "contest"))
        except Exception:
            await query.message.reply_text(
                "⚠️ تعذر نشر المسابقة في القناة/القروب المحدد، تأكد من أن البوت مايزال مشرفًا هناك."
            )

        if end_type == "time" and time_minutes:
            schedule_contest_time_end(context.job_queue, contest_code, time_minutes * 60)

        for key in list(ud.keys()):
            if key.startswith("contest_"):
                ud.pop(key, None)
        ud.pop("awaiting", None)
        return

    if query.data == "comp_reg_channel":
        text, entities = build_channel_registration_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_back_to_competition_keyboard(),
        )
        return

    if query.data == "comp_reg_group":
        text, entities = build_group_registration_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_back_to_competition_keyboard(),
        )
        return


async def publish_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ينشر السحب فور إرسال عدد الفائزين مباشرة (يُستدعى من text_router)."""
    ud = context.user_data
    chat_id = ud.get("gw_target_chat_id")
    if not chat_id:
        _bt, _be = bold_notice("⚠️ حدث خطأ، لم يتم تحديد قناة أو جروب السحب.")
        await update.message.reply_text(text=_bt, entities=_be)
        return

    cliche_text = ud.get("gw_cliche_text") or ""
    cliche_entities = ud.get("gw_cliche_entities") or []
    winners_count = ud.get("gw_winners_count")
    settings = {k: ud.get(k, d) for k, d in GIVEAWAY_SETTINGS_DEFAULTS.items()}

    success_text, success_entities = build_giveaway_publish_success_message()
    await update.message.reply_text(text=success_text, entities=success_entities)

    gw_code = generate_gw_code()
    create_giveaway(
        gw_code=gw_code,
        owner_id=update.effective_user.id,
        chat_id=chat_id,
        cliche_text=cliche_text,
        cliche_entities=cliche_entities,
        winners_count=winners_count,
        settings=settings,
    )

    vote_contest_code = settings.get("gw_vote_contest_code")
    vote_participant_id = settings.get("gw_vote_participant_id")
    vote_link = (
        build_giveaway_vote_condition_link(vote_contest_code, vote_participant_id)
        if vote_contest_code and vote_participant_id else None
    )
    condition_channels = settings.get("gw_condition_channels") or []
    boost_link = (
        await build_giveaway_boost_link(context, chat_id) if settings.get("gw_boost") else ""
    )

    autospin_mode = settings.get("gw_autospin_mode")
    autospin_notice = None
    if autospin_mode == "count" and settings.get("gw_autospin_target"):
        autospin_notice = {"mode": "count", "notice_text": f"يُسحب تلقائيًا عند اكتمال {settings['gw_autospin_target']} مشارك"}
    elif autospin_mode == "time" and settings.get("gw_autospin_minutes"):
        autospin_notice = {
            "mode": "time",
            "notice_text": f"يُسحب تلقائيًا بعد {format_duration_label(settings['gw_autospin_minutes'])}",
        }

    post_text, post_entities = build_giveaway_channel_message(
        cliche_text, cliche_entities, vote_link=vote_link, condition_channels=condition_channels,
        boost_link=boost_link, autospin=autospin_notice,
    )
    post_keyboard = build_giveaway_channel_keyboard(gw_code, 0, antispam=bool(settings.get("gw_antispam", False)))
    try:
        sent = await context.bot.send_message(
            chat_id=chat_id,
            text=post_text,
            entities=post_entities,
            reply_markup=post_keyboard,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        set_giveaway_channel_message(gw_code, sent.message_id)
        asyncio.create_task(announce_new_post(context, chat_id, sent.message_id, "giveaway", {"winners_count": winners_count}))
        if autospin_mode == "time" and settings.get("gw_autospin_minutes"):
            schedule_giveaway_autospin_time(
                context.job_queue, gw_code, settings["gw_autospin_minutes"] * 60,
            )
    except Exception:
        await update.message.reply_text(
            "⚠️ تعذر نشر السحب في القناة/القروب المحدد، تأكد من أن البوت مايزال مشرفًا هناك."
        )

    for key in list(ud.keys()):
        if key.startswith("gw_"):
            ud.pop(key, None)
    ud.pop("awaiting", None)


async def show_my_giveaways_list(query, context: ContextTypes.DEFAULT_TYPE, page: int = 1):
    """يعرض قائمة سحوبات المستخدم (كل الحالات)، مقسّمة إلى صفحات عند الحاجة."""
    giveaways = get_giveaways_by_owner(query.from_user.id)
    if not giveaways:
        text, entities = bold_notice("لا توجد لديك أي سحوبات حتى الآن.")
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
                "رجوع", callback_data="back_main_menu",
                style="danger", **emoji_kwargs("back_section_btn"),
            )]]),
        )
        return

    total_pages = max(1, -(-len(giveaways) // GW_LIST_PAGE_SIZE))
    page = max(1, min(page, total_pages))
    text, entities = build_my_giveaways_list_message(page, total_pages)
    await query.edit_message_text(
        text=text,
        entities=entities,
        reply_markup=build_my_giveaways_list_keyboard(giveaways, page, total_pages),
    )


async def gw_my_draws_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج زر «سحوباتي»: عرض قائمة السحوبات، التنقّل بين الصفحات، وعرض تفاصيل كل سحب."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "my_draws":
        await show_my_giveaways_list(query, context, page=1)
        return

    if data.startswith("gwmy_page:"):
        page_str = data.split(":", 1)[1]
        page = int(page_str) if page_str.isdigit() else 1
        await show_my_giveaways_list(query, context, page=page)
        return

    if data.startswith("gwmy_detail:"):
        _, gw_code, page_str = data.split(":", 2)
        giveaway = get_giveaway(gw_code)
        if not giveaway or giveaway["owner_id"] != query.from_user.id:
            await query.answer("تعذر العثور على هذا السحب.", show_alert=True)
            return
        giveaways = get_giveaways_by_owner(query.from_user.id)
        index = next((i + 1 for i, g in enumerate(giveaways) if g["gw_code"] == gw_code), 0)
        channel_title = get_chat_title_by_id(giveaway["chat_id"])
        participants_total = count_giveaway_participants(gw_code)
        new_rewarded_count = count_giveaway_new_rewarded(gw_code)
        text, entities = build_my_giveaway_detail_message(
            giveaway, index, channel_title, participants_total, new_rewarded_count,
        )
        page = int(page_str) if page_str.isdigit() else 1
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_my_giveaway_detail_keyboard(page),
        )
        return


async def gw_section_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """يعالج جميع أزرار قسم إنشاء السحب (Image 1 إلى Image 4)."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data in ("create_draw", "gw_start_create"):
        for key in list(context.user_data.keys()):
            if key.startswith("gw_"):
                context.user_data.pop(key, None)
        context.user_data.pop("awaiting", None)
        text, entities = build_giveaway_target_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_target_keyboard(query.from_user.id),
        )
        return

    if data == "gw_reg_channel":
        text, entities = build_channel_registration_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_back_to_giveaway_keyboard(),
        )
        return

    if data == "gw_reg_group":
        text, entities = build_group_registration_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_back_to_giveaway_keyboard(),
        )
        return

    if data == "gw_del_channels":
        text, entities = build_giveaway_delete_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_delete_keyboard(query.from_user.id),
        )
        return

    if data == "gw_noop":
        return

    if data.startswith("gw_delc:"):
        chat_id = int(data.split(":", 1)[1])
        remove_registered_chat(chat_id)
        await query.answer("🗑️ تم حذف القناة/الجروب.", show_alert=True)
        text, entities = build_giveaway_delete_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_delete_keyboard(query.from_user.id),
        )
        return

    if data.startswith("gw_sel:"):
        chat_id = int(data.split(":", 1)[1])
        context.user_data["gw_target_chat_id"] = chat_id
        context.user_data["awaiting"] = "gw_cliche"
        text, entities = build_giveaway_cliche_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_cliche_keyboard(),
        )
        return

    if data == "gw_back_main":
        text, entities = build_welcome_message(query.from_user)
        remind_state = get_remind_win_state(query.from_user.id)
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_main_keyboard(remind_state, query.from_user.id),
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )
        return

    if data in ("gw_toggle_boost", "gw_toggle_premium", "gw_toggle_antispam"):
        key = data.replace("gw_toggle_", "gw_")
        for k, default in GIVEAWAY_SETTINGS_DEFAULTS.items():
            context.user_data.setdefault(k, default)
        context.user_data[key] = not context.user_data.get(key, GIVEAWAY_SETTINGS_DEFAULTS[key])
        text, entities = build_giveaway_settings_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_settings_keyboard(context.user_data),
        )
        return

    if data == "gw_opt_vote":
        context.user_data["awaiting"] = "gw_vote_code"
        text, entities = build_giveaway_vote_code_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_vote_code_keyboard(),
        )
        return

    if data == "gw_opt_autospin":
        text, entities = build_giveaway_autospin_end_method_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_autospin_end_method_keyboard(),
        )
        return

    if data == "gw_atime_back":
        context.user_data.pop("awaiting", None)
        text, entities = build_giveaway_autospin_end_method_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_autospin_end_method_keyboard(),
        )
        return

    if data == "gw_atime_end_count":
        context.user_data["awaiting"] = "gw_autospin_count"
        text, entities = build_giveaway_autospin_count_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_autospin_count_keyboard(),
        )
        return

    if data == "gw_atime_end_time":
        context.user_data.pop("awaiting", None)
        text, entities = build_giveaway_autospin_time_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_autospin_time_keyboard(),
        )
        return

    if data.startswith("gw_atime_set_"):
        minutes = int(data.replace("gw_atime_set_", ""))
        for key, default in GIVEAWAY_SETTINGS_DEFAULTS.items():
            context.user_data.setdefault(key, default)
        context.user_data["gw_autospin_mode"] = "time"
        context.user_data["gw_autospin_minutes"] = minutes
        context.user_data.pop("awaiting", None)
        text, entities = build_giveaway_settings_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_settings_keyboard(context.user_data),
        )
        return

    if data == "gw_atime_show_custom":
        if context.user_data.get("gw_autospin_mode") == "time":
            context.user_data["gw_autospin_custom_minutes"] = context.user_data.get("gw_autospin_minutes") or 0
        else:
            context.user_data["gw_autospin_custom_minutes"] = 0
        text, entities = build_giveaway_autospin_time_message(
            format_duration_label(context.user_data["gw_autospin_custom_minutes"]),
        )
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_autospin_custom_keyboard(),
        )
        return

    if data.startswith("gw_atime_custom_delta:"):
        delta = int(data.split(":", 1)[1])
        current = context.user_data.get("gw_autospin_custom_minutes", 0)
        context.user_data["gw_autospin_custom_minutes"] = max(0, current + delta)
        text, entities = build_giveaway_autospin_time_message(
            format_duration_label(context.user_data["gw_autospin_custom_minutes"]),
        )
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_autospin_custom_keyboard(),
        )
        return

    if data == "gw_atime_custom_reset":
        context.user_data["gw_autospin_custom_minutes"] = 0
        text, entities = build_giveaway_autospin_time_message("غير محدد")
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_autospin_custom_keyboard(),
        )
        return

    if data == "gw_atime_custom_confirm":
        total = context.user_data.get("gw_autospin_custom_minutes", 0)
        if not total or total <= 0:
            await query.answer("⚠️ اختر وقتًا أولاً باستخدام أزرار التعديل.", show_alert=True)
            return
        for key, default in GIVEAWAY_SETTINGS_DEFAULTS.items():
            context.user_data.setdefault(key, default)
        context.user_data["gw_autospin_mode"] = "time"
        context.user_data["gw_autospin_minutes"] = total
        context.user_data.pop("gw_autospin_custom_minutes", None)
        text, entities = build_giveaway_settings_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_settings_keyboard(context.user_data),
        )
        return

    if data == "gw_opt_condition":
        context.user_data.pop("awaiting", None)
        context.user_data.pop("gw_condition_channels_pending", None)
        text, entities = build_giveaway_condition_type_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_condition_type_keyboard(),
        )
        return

    if data == "gw_cond_public":
        context.user_data["awaiting"] = "gw_condition_channel_public"
        text, entities = build_giveaway_condition_public_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_condition_public_keyboard(),
        )
        return

    if data == "gw_cond_private":
        context.user_data["awaiting"] = "gw_condition_channel_private"
        context.user_data["gw_condition_channels_pending"] = []
        text, entities = build_giveaway_condition_private_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_condition_private_keyboard(),
        )
        return

    if data == "gw_cond_private_done":
        pending = context.user_data.get("gw_condition_channels_pending") or []
        if not pending:
            await query.answer("⚠️ لم تُضِف أي قناة بعد.", show_alert=True)
            return
        context.user_data["gw_condition_channels"] = pending
        context.user_data.pop("gw_condition_channels_pending", None)
        context.user_data.pop("awaiting", None)
        for key, default in GIVEAWAY_SETTINGS_DEFAULTS.items():
            context.user_data.setdefault(key, default)
        text, entities = build_giveaway_settings_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_settings_keyboard(context.user_data),
        )
        return

    if data == "gw_opt_create":
        context.user_data["awaiting"] = "gw_winners_count"
        text, entities = build_giveaway_winners_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_winners_keyboard(),
        )
        return

    if data == "gw_back_to_options":
        context.user_data.pop("awaiting", None)
        context.user_data.pop("gw_condition_channels_pending", None)
        for key, default in GIVEAWAY_SETTINGS_DEFAULTS.items():
            context.user_data.setdefault(key, default)
        text, entities = build_giveaway_settings_message()
        await query.edit_message_text(
            text=text,
            entities=entities,
            reply_markup=build_giveaway_settings_keyboard(context.user_data),
        )
        return


async def _go_back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text, entities = build_welcome_message(query.from_user)
    remind_state = get_remind_win_state(query.from_user.id)
    await query.edit_message_text(
        text=text,
        entities=entities,
        reply_markup=build_main_keyboard(remind_state, query.from_user.id),
        link_preview_options=LinkPreviewOptions(is_disabled=True),
    )

async def _global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """يسجّل أي خطأ غير متوقع بدل أن يختفي بصمت — هذا كان السبب في تعذّر تشخيص
    مشاكل مثل «الزر لا يستجيب أحيانًا» أو «لم تُرسل رسالة عند انتهاء الوقت»."""
    logger.exception("خطأ غير متوقع أثناء معالجة تحديث: %s", update, exc_info=context.error)


def main():
    init_db()
    request = HTTPXRequest(
        connection_pool_size=20,
        connect_timeout=10.0,
        read_timeout=10.0,
        write_timeout=10.0,
        pool_timeout=10.0,
    )
    get_updates_request = HTTPXRequest(
        connection_pool_size=4,
        connect_timeout=10.0,
        read_timeout=40.0,
    )
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .request(request)
        .get_updates_request(get_updates_request)
        .concurrent_updates(True)
        .build()
    )

    if app.job_queue is None:
        logger.error(
            "JobQueue غير مفعّلة! مسابقات «وقت محدد» لن تُنهى تلقائيًا أبدًا. "
            "ثبّت المكتبة عبر: pip install \"python-telegram-bot[job-queue]\" ثم أعد التشغيل."
        )
    else:
        logger.info("JobQueue مفعّلة بنجاح.")
        app.job_queue.run_repeating(
            check_required_channel_auto_switch, interval=600, first=30,
            name="required_channel_auto_switch",
        )
        app.job_queue.run_repeating(
            giveaway_autospin_countdown_tick, interval=600, first=60,
            name="giveaway_autospin_countdown_tick",
        )
        app.job_queue.run_repeating(
            contest_votes_subscription_audit, interval=1800, first=120,
            name="contest_votes_subscription_audit",
        )

    app.add_error_handler(_global_error_handler)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("getid", get_id_prompt))

    app.add_handler(CallbackQueryHandler(_go_to_quick_roulette, pattern=r"^quick_roulette_menu$"))
    app.add_handler(CallbackQueryHandler(_go_back_to_main, pattern=r"^back_to_main$"))

    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_handler(ChosenInlineResultHandler(chosen_result_handler))

    app.add_handler(CallbackQueryHandler(rr_spin_callback, pattern=r"^rr_spin_\d+$"))
    app.add_handler(CallbackQueryHandler(rr_respin_callback, pattern=r"^rr_respin_\d+$"))
    app.add_handler(CallbackQueryHandler(rr_join_callback, pattern=r"^rr_join_\d+$"))

    app.add_handler(CallbackQueryHandler(qr_settings_callback, pattern=r"^qr_settings$"))
    app.add_handler(CallbackQueryHandler(
        roulette_privacy_settings_callback,
        pattern=r"^(toggle_hide_participants_internal|edit_game_cliche|restore_defaults_roulette|section_roulette)$",
    ))

    app.add_handler(CallbackQueryHandler(
        contest_section_callback,
        pattern=r"^(comp_start_create|comp_reg_group|comp_reg_channel|back_main_menu|section_competition"
                r"|comp_pick_chat_-?\d+|comp_back_to_klesha|comp_back_to_count|comp_end_votes|comp_end_time"
                r"|comp_back_to_end_type|comp_atime_set_\d+|comp_atime_show_custom"
                r"|comp_atime_custom_delta:-?\d+|comp_atime_custom_reset|comp_atime_custom_confirm"
                r"|comp_toggle_notify_win|comp_toggle_announce_results|comp_toggle_approve_participants"
                r"|comp_toggle_premium_only|comp_back_to_winners|comp_publish|comp_recent)$",
    ))

    app.add_handler(CallbackQueryHandler(
        contest_detail_callback,
        pattern=r"^comp_detail:",
    ))
    app.add_handler(CallbackQueryHandler(
        contest_management_callback,
        pattern=r"^(comp_toggle_active:|comp_delete_all:|comp_change_seats:|comp_edit_settings:|comp_remove_contestant:)",
    ))

    app.add_handler(CallbackQueryHandler(
        contest_participation_callback,
        pattern=r"^(comp_reject_join:|comp_confirm_join:|comp_withdraw:)",
    ))
    app.add_handler(CallbackQueryHandler(vote_captcha_callback, pattern=r"^compcap:"))
    app.add_handler(CallbackQueryHandler(contest_vote_gate_check_callback, pattern=r"^compcond:"))
    app.add_handler(CallbackQueryHandler(contest_results_callback, pattern=r"^comp_view_results:"))

    app.add_handler(CallbackQueryHandler(
        gw_section_callback,
        pattern=r"^(create_draw|gw_start_create|gw_reg_channel|gw_reg_group|gw_del_channels|gw_noop"
                r"|gw_delc:-?\d+|gw_sel:-?\d+|gw_back_main|gw_toggle_boost|gw_toggle_premium"
                r"|gw_toggle_antispam|gw_opt_condition|gw_cond_public|gw_cond_private|gw_cond_private_done"
                r"|gw_opt_vote|gw_opt_autospin|gw_opt_create"
                r"|gw_atime_back|gw_atime_end_count|gw_atime_end_time|gw_atime_set_\d+|gw_atime_show_custom"
                r"|gw_atime_custom_delta:-?\d+|gw_atime_custom_reset|gw_atime_custom_confirm"
                r"|gw_back_to_options)$",
    ))
    app.add_handler(CallbackQueryHandler(
        gw_my_draws_callback,
        pattern=r"^(my_draws|gwmy_page:\d+|gwmy_detail:)",
    ))
    app.add_handler(CallbackQueryHandler(gw_join_callback, pattern=r"^gw_join:"))
    app.add_handler(CallbackQueryHandler(gwcond_check_callback, pattern=r"^gwcond:"))
    app.add_handler(CallbackQueryHandler(gw_captcha_callback, pattern=r"^gwcap:"))
    app.add_handler(CallbackQueryHandler(gw_kick_callback, pattern=r"^gw_kick:"))
    app.add_handler(CallbackQueryHandler(gw_repost_callback, pattern=r"^gw_repost:"))
    app.add_handler(CallbackQueryHandler(gw_pause_callback, pattern=r"^gw_pause:"))
    app.add_handler(CallbackQueryHandler(gw_resume_callback, pattern=r"^gw_resume:"))
    app.add_handler(CallbackQueryHandler(gw_draw_callback, pattern=r"^gw_draw:"))
    app.add_handler(CallbackQueryHandler(gw_reroll_callback, pattern=r"^gw_reroll:"))

    app.add_handler(CallbackQueryHandler(check_sub_status_callback, pattern=r"^check_sub_status$"))
    app.add_handler(CallbackQueryHandler(main_menu_callback))
    app.add_handler(PreCheckoutQueryHandler(support_precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, support_successful_payment_callback))
    app.add_handler(MessageHandler(filters.FORWARDED & filters.ChatType.PRIVATE, channel_forward_handler))
    app.add_handler(MessageHandler(filters.Regex("تفعيل روليت") & filters.ChatType.GROUPS, group_activation_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    app.add_handler(ChatMemberHandler(bot_chat_status_update, ChatMemberHandler.MY_CHAT_MEMBER))

    async def _post_init(app_):
        await app_.bot.set_my_commands([
            BotCommand("start", "رسالة البدء"),
        ])
        await reschedule_pending_contest_timers(app_)
        await reschedule_pending_giveaway_timers(app_)
        try:
            announce_chat = await app_.bot.get_chat(f"@{ANNOUNCE_CHANNEL_USERNAME}")
            remove_registered_chat(announce_chat.id)
        except Exception:
            pass
    app.post_init = _post_init

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
