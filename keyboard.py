from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ASOSIY START MENYUSI
def main_menu(user_id, admin_id):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎡 Baraban o'yini", web_app={"url": "https://barabandev.netlify.app"}))
    builder.row(
        InlineKeyboardButton(text="✌️ Enik-Benik", callback_data="enik_benik"),
        InlineKeyboardButton(text="🎤 Ovozli Batl", callback_data="voice_battle")
    )
    # Admin bo'lsa boshqaruv paneli chiqadi
    if str(user_id) == str(admin_id):
        builder.row(InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="admin_panel"))
    return builder.as_markup()

# ADMIN PANEL TUGMALARI
def admin_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📢 Kanalni o'zgartirish", callback_data="change_channel"))
    builder.row(InlineKeyboardButton(text="📈 Strategiya va Statistika", callback_data="bot_strategy"))
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main"))
    return builder.as_markup()

# KONKURS POSTI TUGMALARI
def get_battle_kb(candidates_dict, bot_username):
    builder = InlineKeyboardBuilder()
    for username, votes in candidates_dict.items():
        vote_url = f"https://t.me/{bot_username}?start=vote_{username}"
        builder.row(InlineKeyboardButton(text=f"@{username} — {votes} ovoz", url=vote_url))
    
    builder.row(InlineKeyboardButton(text="🏆 KONKURSGA QO'SHILISH ➕", callback_data="join_contest"))
    builder.row(InlineKeyboardButton(text="📊 Natijalar", callback_data="results"))
    return builder.as_markup()

# MAJBURIY OBUNA TUGMASI (DINAMIK)
def sub_keyboard(channel_username):
    builder = InlineKeyboardBuilder()
    clean_username = channel_username.replace("@", "")
    builder.row(InlineKeyboardButton(text=f"➕ {channel_username}ga a'zo bo'lish", url=f"https://t.me/{clean_username}"))
    builder.row(InlineKeyboardButton(text="🔄 Obunani tekshirish", callback_data="check_sub"))
    return builder.as_markup()

def voice_battle_kb(bot_username):
    builder = InlineKeyboardBuilder()
    add_url = f"https://t.me/{bot_username}?startchannel=true&admin=post_messages+edit_messages+delete_messages+invite_users"
    builder.row(InlineKeyboardButton(text="➕ Botni kanalga admin qilish", url=add_url))
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_main"))
    return builder.as_markup()