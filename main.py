import asyncio
import logging
import os
import httpx
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery
)

try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()
except ImportError:
    pass

# Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

if not BOT_TOKEN:
    print("=" * 60)
    print("XATOLIK: TELEGRAM_BOT_TOKEN topilmadi!")
    print("Iltimos backend/.env faylida tokenni o'rnating:")
    print("  TELEGRAM_BOT_TOKEN=your-bot-token-here")
    print("=" * 60)

bot = Bot(token=BOT_TOKEN if BOT_TOKEN else "123456789:AAA_DummyToken")
dp = Dispatcher()


PAYMENT_METHOD_NAMES = {
    "CASH": "💵 Naqd",
    "CARD": "💳 Karta",
    "CLICK": "📱 Click",
    "PAYME": "📱 Payme",
    "UZUM": "📱 Uzum",
    "BANK_TRANSFER": "🏦 Bank o'tkazmasi",
}


def get_main_keyboard():
    """Asosiy menyu tugmalari"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👨\u200d👩\u200d👧 Farzandimni bog'lash"),
                KeyboardButton(text="📚 Kurslar va Narxlar")
            ],
            [
                KeyboardButton(text="💳 To'lov holati"),
                KeyboardButton(text="📊 Davomat")
            ],
            [
                KeyboardButton(text="📝 Sinov darsiga yozilish"),
                KeyboardButton(text="📞 Telefon yuborish", request_contact=True)
            ],
        ],
        resize_keyboard=True
    )


def format_number(num: float) -> str:
    """Raqamni formatlash: 500000 -> 500,000"""
    return f"{num:,.0f}"


# ============================================================
# /start - Salomlashish
# ============================================================
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    welcome_text = (
        f"🏫 <b>Ta'lim Plus Education Center</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Assalomu alaykum, <b>{message.from_user.first_name}</b>! 👋\n\n"
        f"Rasmiy botimizga xush kelibsiz.\n\n"
        f"<b>Bu bot orqali siz:</b>\n"
        f"👨\u200d👩\u200d👧 Farzandingizni 6 talik ID raqami bilan bog'lab,\n"
        f"💳 <b>To'lov holati</b> va tarixini ko'rishingiz,\n"
        f"📊 <b>Davomat statistikasi</b>ni kuzatishingiz,\n"
        f"📚 <b>Kurslar</b> haqida ma'lumot olishingiz mumkin!\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⬇️ <b>Pastdagi tugmalardan birini tanlang:</b>"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode="HTML")


# ============================================================
# "Farzandimni bog'lash" tugmasi bosilganda
# ============================================================
@dp.message(F.text.contains("Farzandimni bog'lash"))
async def prompt_student_id(message: types.Message):
    await message.answer(
        "🔑 <b>Farzandingizning ID raqamini kiriting</b>\n\n"
        "O'quv markazga ro'yxatdan o'tganida berilgan\n"
        "<b>6 talik unikal ID raqamni</b> yuboring.\n\n"
        "📋 <i>Masalan:</i> <code>100101</code>\n\n"
        "💡 <i>ID raqamni bilmasangiz, markaz administratoriga murojaat qiling.</i>",
        parse_mode="HTML"
    )


# ============================================================
# 6 talik raqam kiritilganda — Farzandni bog'lash
# ============================================================
@dp.message(F.text.regexp(r'^\d{6}$'))
async def link_student_by_id(message: types.Message):
    login_id = message.text.strip()
    chat_id = str(message.chat.id)

    wait_msg = await message.answer("⏳ Tekshirilmoqda...")

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                f"{API_BASE_URL}/auth/link-telegram",
                json={"login_id": login_id, "chat_id": chat_id},
                timeout=10.0
            )
            if res.status_code == 200:
                data = res.json()
                success_text = (
                    f"✅ <b>MUVAFFAQIYATLI BOG'LANDI!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"👤 O'quvchi: <b>{data['student_name']}</b>\n"
                    f"🆔 ID: <code>{data['login_id']}</code>\n\n"
                    f"📲 Endi quyidagi xabarlar avtomatik keladi:\n"
                    f"  ✅ Darsga kelganda\n"
                    f"  ⚠️ Kechikib kelganda\n"
                    f"  ❌ Darsga kelmasa\n"
                    f"  💳 To'lov qilinganda\n"
                    f"  📋 Oylik hisob-kitob\n\n"
                    f"💡 <b>Endi menyu orqali to'lov holati va\n"
                    f"davomat statistikasini ko'rishingiz mumkin!</b>\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🎉 Rahmat! Biz bilan bo'lganingiz uchun tashakkur."
                )
                await wait_msg.edit_text(success_text, parse_mode="HTML")
            else:
                err_detail = "ID raqam topilmadi"
                try:
                    err_detail = res.json().get("detail", err_detail)
                except Exception:
                    pass
                await wait_msg.edit_text(
                    f"❌ <b>Xatolik:</b> {err_detail}\n\n"
                    f"Iltimos, ID raqamni tekshirib qayta kiriting.\n"
                    f"📋 <i>Masalan:</i> <code>100101</code>",
                    parse_mode="HTML"
                )
        except httpx.TimeoutException:
            logger.error(f"API timeout: link-telegram for login_id={login_id}")
            await wait_msg.edit_text(
                "⚠️ Server bilan bog'lanishda vaqt tugadi.\n"
                "Iltimos, bir ozdan keyin qaytadan urinib ko'ring.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"API xatolik: link-telegram - {e}")
            await wait_msg.edit_text(
                "⚠️ Server bilan bog'lanishda xatolik.\n"
                "Backend server ishlayotganini tekshiring.",
                parse_mode="HTML"
            )


# ============================================================
# "Kurslar va Narxlar" tugmasi
# ============================================================
@dp.message(F.text.contains("Kurslar va Narxlar"))
async def show_courses(message: types.Message):
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{API_BASE_URL}/courses/", timeout=5.0)
            courses = res.json()
            if not courses:
                await message.answer("📚 Hozircha faol kurslar mavjud emas.")
                return

            text = "📚 <b>MAVJUD KURSLAR</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, c in enumerate(courses, 1):
                text += f"<b>{i}. {c['title']}</b>\n"
                text += f"   💰 Oylik: <b>{c['price_monthly']:,.0f} so'm</b>\n"
                text += f"   ⏱ Davomiyligi: {c['duration_months']} oy\n"
                if c.get('description'):
                    text += f"   📝 {c['description'][:80]}\n"
                text += "\n"

            text += (
                "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "📞 Batafsil ma'lumot uchun: +998 90 123 45 67\n"
                "🌐 Sayt: talimplus.uz"
            )
            await message.answer(text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Kurslar olishda xatolik: {e}")
            await message.answer(
                "📚 Kurslar ro'yxatini yuklashda xatolik yuz berdi.\n"
                "Qaytadan urinib ko'ring.",
                parse_mode="HTML"
            )


# ============================================================
# "💳 To'lov holati" tugmasi
# ============================================================
@dp.message(F.text.contains("To'lov holati"))
async def show_payment_status(message: types.Message):
    chat_id = str(message.chat.id)
    wait_msg = await message.answer("⏳ Ma'lumotlar yuklanmoqda...")

    async with httpx.AsyncClient() as client:
        try:
            # Bog'langan o'quvchilarni olish
            res = await client.get(
                f"{API_BASE_URL}/telegram/students",
                params={"chat_id": chat_id},
                timeout=10.0
            )

            if res.status_code == 404:
                await wait_msg.edit_text(
                    "❌ <b>Hech qanday o'quvchi bog'lanmagan!</b>\n\n"
                    "Avval <b>'👨\u200d👩\u200d👧 Farzandimni bog'lash'</b> tugmasini bosib,\n"
                    "farzandingizning 6 talik ID raqamini kiriting.",
                    parse_mode="HTML"
                )
                return

            students = res.json()

            if len(students) == 1:
                # Bitta o'quvchi — to'g'ridan-to'g'ri to'lov ma'lumotini ko'rsatish
                await show_payment_details(wait_msg, chat_id, students[0]['student_id'], client)
            else:
                # Bir nechta o'quvchi — tanlash
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=f"👤 {s['full_name']} ({s['login_id']})",
                        callback_data=f"pay_{s['student_id']}"
                    )]
                    for s in students
                ])
                await wait_msg.edit_text(
                    "👨\u200d👩\u200d👧 <b>Qaysi farzandingizning to'lov holatini ko'rmoqchisiz?</b>\n\n"
                    "Pastdan birini tanlang:",
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )

        except httpx.TimeoutException:
            await wait_msg.edit_text(
                "⚠️ Server bilan bog'lanishda vaqt tugadi.\n"
                "Iltimos, qaytadan urinib ko'ring.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"To'lov holati xatolik: {e}")
            await wait_msg.edit_text(
                "⚠️ Ma'lumotlarni yuklashda xatolik yuz berdi.\n"
                "Qaytadan urinib ko'ring.",
                parse_mode="HTML"
            )


async def show_payment_details(msg, chat_id: str, student_id: int, client: httpx.AsyncClient):
    """To'lov ma'lumotlarini formatlash va ko'rsatish"""
    res = await client.get(
        f"{API_BASE_URL}/telegram/payments/{student_id}",
        params={"chat_id": chat_id},
        timeout=10.0
    )

    if res.status_code != 200:
        err = "Ma'lumot topilmadi"
        try:
            err = res.json().get("detail", err)
        except Exception:
            pass
        await msg.edit_text(f"❌ {err}", parse_mode="HTML")
        return

    data = res.json()

    # Oy nomlarini o'zbekchada formatlash
    month_names = {
        "01": "Yanvar", "02": "Fevral", "03": "Mart", "04": "Aprel",
        "05": "May", "06": "Iyun", "07": "Iyul", "08": "Avgust",
        "09": "Sentyabr", "10": "Oktyabr", "11": "Noyabr", "12": "Dekabr"
    }
    month_parts = data['current_month'].split('-')
    month_name = month_names.get(month_parts[1], month_parts[1]) if len(month_parts) == 2 else data['current_month']

    status_emoji = "✅ TO'LANGAN" if data['is_paid'] else "❌ TO'LANMAGAN"

    text = (
        f"💳 <b>TO'LOV HOLATI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 O'quvchi: <b>{data['student_name']}</b>\n"
        f"🆔 ID: <code>{data['login_id']}</code>\n\n"
        f"📅 Joriy oy: <b>{data['current_month']} ({month_name})</b>\n"
        f"💰 Oylik to'lov: <b>{format_number(data['monthly_fee'])} so'm</b>\n"
        f"✅ To'langan: <b>{format_number(data['month_amount_paid'])} so'm</b>\n"
        f"📊 Qoldiq: <b>{format_number(data['remaining'])} so'm</b>\n"
        f"📋 Holat: <b>{status_emoji}</b>\n"
    )

    if data['total_debt'] > 0:
        text += f"\n🔴 <b>Umumiy qarz: {format_number(data['total_debt'])} so'm</b>\n"
    if data['total_credit'] > 0:
        text += f"\n🟢 <b>Haqdorlik: {format_number(data['total_credit'])} so'm</b>\n"

    # Oxirgi to'lovlar
    if data['recent_payments']:
        text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        text += "📜 <b>OXIRGI TO'LOVLAR:</b>\n\n"
        for i, p in enumerate(data['recent_payments'], 1):
            pay_date = p['created_at'][:10]
            method = PAYMENT_METHOD_NAMES.get(p['payment_method'], p['payment_method'])
            text += f"{i}. {pay_date} | <b>{format_number(p['amount'])} so'm</b> | {method}\n"
    else:
        text += "\n📜 <i>Hali to'lov amalga oshirilmagan.</i>\n"

    text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━"

    await msg.edit_text(text, parse_mode="HTML")


# ============================================================
# "📊 Davomat" tugmasi
# ============================================================
@dp.message(F.text == "📊 Davomat")
async def show_attendance(message: types.Message):
    chat_id = str(message.chat.id)
    wait_msg = await message.answer("⏳ Ma'lumotlar yuklanmoqda...")

    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(
                f"{API_BASE_URL}/telegram/students",
                params={"chat_id": chat_id},
                timeout=10.0
            )

            if res.status_code == 404:
                await wait_msg.edit_text(
                    "❌ <b>Hech qanday o'quvchi bog'lanmagan!</b>\n\n"
                    "Avval <b>'👨\u200d👩\u200d👧 Farzandimni bog'lash'</b> tugmasini bosib,\n"
                    "farzandingizning 6 talik ID raqamini kiriting.",
                    parse_mode="HTML"
                )
                return

            students = res.json()

            if len(students) == 1:
                await show_attendance_details(wait_msg, chat_id, students[0]['student_id'], client)
            else:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=f"👤 {s['full_name']} ({s['login_id']})",
                        callback_data=f"att_{s['student_id']}"
                    )]
                    for s in students
                ])
                await wait_msg.edit_text(
                    "👨\u200d👩\u200d👧 <b>Qaysi farzandingizning davomatini ko'rmoqchisiz?</b>\n\n"
                    "Pastdan birini tanlang:",
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )

        except httpx.TimeoutException:
            await wait_msg.edit_text(
                "⚠️ Server bilan bog'lanishda vaqt tugadi.\n"
                "Iltimos, qaytadan urinib ko'ring.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Davomat xatolik: {e}")
            await wait_msg.edit_text(
                "⚠️ Ma'lumotlarni yuklashda xatolik yuz berdi.\n"
                "Qaytadan urinib ko'ring.",
                parse_mode="HTML"
            )


async def show_attendance_details(msg, chat_id: str, student_id: int, client: httpx.AsyncClient):
    """Davomat statistikasini formatlash va ko'rsatish"""
    res = await client.get(
        f"{API_BASE_URL}/telegram/attendance/{student_id}",
        params={"chat_id": chat_id},
        timeout=10.0
    )

    if res.status_code != 200:
        err = "Ma'lumot topilmadi"
        try:
            err = res.json().get("detail", err)
        except Exception:
            pass
        await msg.edit_text(f"❌ {err}", parse_mode="HTML")
        return

    data = res.json()

    # Oy nomlarini o'zbekchada
    month_names = {
        "01": "Yanvar", "02": "Fevral", "03": "Mart", "04": "Aprel",
        "05": "May", "06": "Iyun", "07": "Iyul", "08": "Avgust",
        "09": "Sentyabr", "10": "Oktyabr", "11": "Noyabr", "12": "Dekabr"
    }
    month_parts = data['current_month'].split('-')
    month_name = month_names.get(month_parts[1], month_parts[1]) if len(month_parts) == 2 else data['current_month']

    def pct(part, total):
        return f"{(part / total * 100):.1f}%" if total > 0 else "0%"

    text = (
        f"📊 <b>DAVOMAT STATISTIKASI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 O'quvchi: <b>{data['student_name']}</b>\n"
        f"🆔 ID: <code>{data['login_id']}</code>\n"
    )

    if data.get('group_name'):
        text += f"📚 Guruh: <b>{data['group_name']}</b>\n"
    if data.get('course_title'):
        text += f"📖 Kurs: <b>{data['course_title']}</b>\n"
    if data.get('days_of_week'):
        text += f"📅 Kunlar: <b>{data['days_of_week']}</b>\n"

    mt = data['month_total']
    text += (
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 <b>Joriy oy ({month_name} {month_parts[0]}):</b>\n\n"
    )

    if mt > 0:
        text += (
            f"  ✅ Keldi: <b>{data['month_present']}</b> ({pct(data['month_present'], mt)})\n"
            f"  ⏰ Kechikdi: <b>{data['month_late']}</b> ({pct(data['month_late'], mt)})\n"
            f"  ❌ Kelmadi: <b>{data['month_absent']}</b> ({pct(data['month_absent'], mt)})\n"
            f"  📋 Sababli: <b>{data['month_excused']}</b> ({pct(data['month_excused'], mt)})\n"
            f"  📝 Jami darslar: <b>{mt}</b>\n"
        )
    else:
        text += "  <i>Bu oyda hali dars o'tilmagan.</i>\n"

    ot = data['overall_total']
    text += (
        f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>UMUMIY STATISTIKA:</b>\n\n"
    )

    if ot > 0:
        text += (
            f"  ✅ Keldi: <b>{data['overall_present']}</b> ({pct(data['overall_present'], ot)})\n"
            f"  ⏰ Kechikdi: <b>{data['overall_late']}</b> ({pct(data['overall_late'], ot)})\n"
            f"  ❌ Kelmadi: <b>{data['overall_absent']}</b> ({pct(data['overall_absent'], ot)})\n"
            f"  📋 Sababli: <b>{data['overall_excused']}</b> ({pct(data['overall_excused'], ot)})\n"
            f"  📝 Jami darslar: <b>{ot}</b>\n"
        )
    else:
        text += "  <i>Hali davomat ma'lumotlari yo'q.</i>\n"

    text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━"

    await msg.edit_text(text, parse_mode="HTML")


# ============================================================
# Callback Query — Farzand tanlanganda (To'lov)
# ============================================================
@dp.callback_query(F.data.startswith("pay_"))
async def callback_payment(callback: CallbackQuery):
    student_id = int(callback.data.split("_")[1])
    chat_id = str(callback.message.chat.id)

    await callback.answer("⏳ Yuklanmoqda...")

    async with httpx.AsyncClient() as client:
        try:
            await show_payment_details(callback.message, chat_id, student_id, client)
        except Exception as e:
            logger.error(f"Callback payment xatolik: {e}")
            await callback.message.edit_text(
                "⚠️ Ma'lumotlarni yuklashda xatolik yuz berdi.\n"
                "Qaytadan urinib ko'ring.",
                parse_mode="HTML"
            )


# ============================================================
# Callback Query — Farzand tanlanganda (Davomat)
# ============================================================
@dp.callback_query(F.data.startswith("att_"))
async def callback_attendance(callback: CallbackQuery):
    student_id = int(callback.data.split("_")[1])
    chat_id = str(callback.message.chat.id)

    await callback.answer("⏳ Yuklanmoqda...")

    async with httpx.AsyncClient() as client:
        try:
            await show_attendance_details(callback.message, chat_id, student_id, client)
        except Exception as e:
            logger.error(f"Callback attendance xatolik: {e}")
            await callback.message.edit_text(
                "⚠️ Ma'lumotlarni yuklashda xatolik yuz berdi.\n"
                "Qaytadan urinib ko'ring.",
                parse_mode="HTML"
            )


# ============================================================
# "Sinov darsiga yozilish" tugmasi
# ============================================================
@dp.message(F.text.contains("Sinov darsiga yozilish"))
async def register_lead_start(message: types.Message):
    await message.answer(
        "📝 <b>Sinov darsiga yozilish</b>\n\n"
        "Bepul sinov darsiga yozilish uchun pastdagi\n"
        "<b>'📞 Telefon yuborish'</b> tugmasini bosing.\n\n"
        "Sizning kontaktingiz administratorga yuboriladi\n"
        "va tez orada siz bilan bog'lanishadi.",
        parse_mode="HTML"
    )


# ============================================================
# Telefon kontaktini ulashish
# ============================================================
@dp.message(F.contact)
async def handle_contact(message: types.Message):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    full_name = f"{message.contact.first_name or ''} {message.contact.last_name or ''}".strip()

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                f"{API_BASE_URL}/crm/leads",
                json={
                    "full_name": full_name,
                    "phone": phone,
                    "notes": "Telegram Bot orqali sinov darsiga yozildi",
                    "telegram_user_id": str(message.chat.id)
                },
                timeout=5.0
            )
            if res.status_code not in (200, 201):
                logger.warning(f"Lead yaratishda xatolik: status={res.status_code}")
        except Exception as e:
            logger.error(f"Lead yaratishda xatolik: {e}")

    await message.answer(
        f"✅ <b>Rahmat, {full_name}!</b>\n\n"
        f"📞 Raqamingiz: <code>{phone}</code>\n\n"
        f"Arizangiz administratorga yetkazildi.\n"
        f"Tez orada siz bilan bog'lanamiz! 🤝",
        parse_mode="HTML"
    )


# ============================================================
# Noma'lum xabarlar
# ============================================================
@dp.message()
async def handle_unknown(message: types.Message):
    if message.text and message.text.isdigit() and len(message.text) != 6:
        await message.answer(
            f"⚠️ Siz <b>{len(message.text)}</b> talik raqam kiritdingiz.\n"
            f"ID raqam aniq <b>6 ta raqamdan</b> iborat bo'lishi kerak.\n\n"
            f"📋 <i>Masalan:</i> <code>100101</code>",
            parse_mode="HTML"
        )
        return

    await message.answer(
        "🤔 Kechirasiz, bu buyruqni tushunmadim.\n\n"
        "Pastdagi <b>menyu tugmalaridan</b> birini tanlang\n"
        "yoki /start buyrug'ini yuboring.",
        parse_mode="HTML",
        reply_markup=get_main_keyboard()
    )


# ============================================================
# Botni ishga tushirish
# ============================================================
async def main():
    if not BOT_TOKEN or BOT_TOKEN == "123456789:AAA_DummyToken":
        print("=" * 60)
        print("XATOLIK: TELEGRAM_BOT_TOKEN o'rnatilmagan!")
        print()
        print("Qadamlar:")
        print("  1. @BotFather dan yangi bot yarating")
        print("  2. Token ni backend/.env faylga yozing:")
        print("     TELEGRAM_BOT_TOKEN=your-token-here")
        print("  3. Botni qayta ishga tushiring")
        print("=" * 60)
        return

    logger.info("=" * 50)
    logger.info("🤖 Ta'lim Plus Telegram Bot ishga tushmoqda...")
    logger.info(f"📡 API: {API_BASE_URL}")
    logger.info("=" * 50)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
