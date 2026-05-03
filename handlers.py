import sqlite3
from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject
from keyboard import *
from database import add_user, get_candidates, get_top_candidates, ADMIN_ID, get_setting, get_stats

router = Router()
LAST_BATTLE_POST = {"chat_id": None, "message_id": None}

def reset_contest():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM candidates")
    cursor.execute("DELETE FROM votes")
    conn.commit()
    conn.close()

async def is_subscribed(bot, user_id):
    channel = get_setting('channel')
    try:
        member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

@router.message(Command("start"))
async def start_handler(message: types.Message, command: CommandObject):
    user_id = message.from_user.id
    username = message.from_user.username
    add_user(user_id, username)
    
    # Ovoz berish qismi (Ref link orqali kelganda)
    args = command.args
    if args and args.startswith("vote_"):
        candidate = args.replace("vote_", "")
        
        # Obunani tekshirish
        if not await is_subscribed(message.bot, user_id):
            return await message.answer(
                f"⚠️ @{candidate}ga ovoz berish uchun avval kanalga a'zo bo'ling!", 
                reply_markup=sub_keyboard(get_setting('channel'))
            )
        
        conn = sqlite3.connect('bot_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT candidate_username FROM votes WHERE user_id = ?", (user_id,))
        already_voted = cursor.fetchone()

        if already_voted:
            conn.close()
            return await message.answer("🚫 <b>Siz allaqachon ovoz bergansiz!</b>\nFaqat bir marta ovoz berish imkoniyati mavjud.", parse_mode="HTML")

        cursor.execute("INSERT INTO votes (user_id, candidate_username) VALUES (?, ?)", (user_id, candidate))
        cursor.execute("UPDATE candidates SET votes_count = votes_count + 1 WHERE username = ?", (candidate,))
        conn.commit()
        conn.close()
        
        await message.answer(f"✅ Rahmat! @{candidate} uchun ovozingiz muvaffaqiyatli qabul qilindi.")
        return

    # Standart Start xabari
    start_txt = (
        f"👋 <b>Salom {message.from_user.first_name}!</b>\n\n"
        f"Sizni botimizda ko'rib turganimizdan xursandmiz! Bu yerda siz quyidagi imkoniyatlarga egasiz:\n\n"
        f"🎡 <b>Baraban:</b> O'z omadingizni sinab ko'ring va sovg'alar yuting!\n"
        f"✌️ <b>Enik-Benik:</b> Do'stlar bilan qiziqarli o'yinlar o'ynang!\n"
        f"🎤 <b>Ovozli Batl:</b> O'z kanalingizda professional konkurslar tashkil qiling!\n\n"
        f"🚀 <b>Pastdagi menyudan o'zingizga kerakli bo'limni tanlang:</b>"
    )
    await message.answer(start_txt, reply_markup=main_menu(user_id, ADMIN_ID), parse_mode="HTML")

@router.message(F.text == "📊 Natijalar")
async def show_results_handler(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID): return 

    results = get_top_candidates(5)
    if not results:
        return await message.answer("📊 <b>Hozircha ishtirokchilar yo'q!</b>", parse_mode="HTML")

    header = f"📊 <b>TOP 5 NATIJALAR</b>\n🏆 <b>Eng kuchli kurashchilar</b> 🥳\n\n"
    body = ""
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for i, (username, count) in enumerate(results):
        medal = medals[i] if i < 5 else "👤"
        body += f"<blockquote>{medal} @{username} — <b>{count} ta ovoz</b> </blockquote>\n\n"

    await message.answer(header + body + "🎁 <b>Konkurs davom etmoqda...</b>", parse_mode="HTML")

@router.message(F.text.contains("#konkursx"))
@router.channel_post(F.text.contains("#konkursx"))
async def start_konkurs_handler(message: types.Message):
    if message.from_user and str(message.from_user.id) != str(ADMIN_ID):
        return
            
    reset_contest()
    bot_info = await message.bot.get_me()
    
    battle_text = (
        "🏆 <b>KONKURS BOSHLANDI!</b> 🥳\n\n"
        "❕ <b>Shartlar:</b> Quyidagi kanalga obuna bo'lish va "
        "o'z yaqinlaringizdan ovoz yig'ish.\n\n"
        "<blockquote>🚫 <b>Diqqat:</b> Agar ovoz beruvchi kanaldan chiqib ketsa, uning ovozi avtomatik tarzda bekor qilinadi!</blockquote>\n\n"
        "➕ <b>Konkursga qo'shilish uchun pastdagi tugmani bosing:</b> 👇"
    )
    
    await message.answer(battle_text, reply_markup=get_battle_kb([], bot_info.username), parse_mode="HTML")
    try: await message.delete()
    except: pass

@router.callback_query(F.data == "join_contest")
async def join_callback(callback: types.CallbackQuery):
    user_username = callback.from_user.username
    if not user_username:
        return await callback.answer("❌ Xatolik: Profilingizda username bo'lishi shart!", show_alert=True)

    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO candidates (username) VALUES (?)", (user_username,))
        conn.commit()
        await callback.answer("✅ Siz muvaffaqiyatli ro'yxatga qo'shildingiz!", show_alert=True)
    except sqlite3.IntegrityError:
        await callback.answer("😊 Siz allaqachon ro'yxatdasiz.", show_alert=True)
    finally: conn.close()
