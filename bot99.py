# telebot_creator_final.py
# Requires: pip install pyTelegramBotAPI
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time

BOT_TOKEN = "8343705527:AAGyFbDD9leXs-u34jT05xKtgKQoHmerZ9k"
OWNER_ID = 5730398152  # <--- replace with your Telegram numeric user id (owner)
CHANNEL = "@Src_hub"  # <--- replace with your channel username

bot = telebot.TeleBot(BOT_TOKEN)

# In-memory stores (you can later persist to a file)
user_sessions = {}  # per-chat temporary session state
users_db = {}       # permanent-ish per-user stats and history

# Helpers
def ensure_user_in_db(user):
    uid = user.id
    if uid not in users_db:
        users_db[uid] = {
            "id": uid,
            "username": user.username or "None",
            "name": user.full_name,
            "first_seen": int(time.time()),
            "started": False,
            "bypass_count": 0,
            "generated": [],  # list of generated results (dicts)
        }

def channel_join_keyboard():
    kb = InlineKeyboardMarkup()
    # join button opens channel URL
    kb.row(InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL.lstrip('@')}"))
    return kb

def main_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Simple Structure", callback_data="simple_struct"),
        InlineKeyboardButton("Hook Structure", callback_data="hook_struct"),
        InlineKeyboardButton("Settings", callback_data="settings"),
        InlineKeyboardButton("Bot Information", callback_data="bot_info"),
    )
    return kb

def offsets_choice_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("✨ Single Offset For Only 1 Offset", callback_data="single_offset"),
        InlineKeyboardButton("✨ Multi Offset For Multiple Offsets", callback_data="multi_offset"),
    )
    return kb

def patch_type_keyboard(mem_available=True):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🎀 Patch Lib Like This ( PATCH_LIB )", callback_data="patch_lib"),
        InlineKeyboardButton("🎀 Memory Patch like This ( MemoryPatch )", callback_data="memory_patch"),
    )
    return kb

def lib_select_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("💫 UE4 - ( libUE4.so )", callback_data="lib_UE4"),
        InlineKeyboardButton("💫 Anogs - ( libanogs.so )", callback_data="lib_Anogs"),
        InlineKeyboardButton("💫 Anort - ( libanort.so )", callback_data="lib_Anort"),
    )
    return kb

def owner_panel_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Check Users", callback_data="owner_check_users"),
        InlineKeyboardButton("Ban / Back", callback_data="owner_back"),
    )
    return kb

# ---------------- /start ----------------
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    user = message.from_user
    ensure_user_in_db(user)
    users_db[user.id]["started"] = True

    # Check channel membership
    try:
        member = bot.get_chat_member(CHANNEL, user.id)
        joined = member.status in ["member", "administrator", "creator"]
    except Exception:
        # If get_chat_member throws, treat as not joined
        joined = False

    if not joined:
        # Ask to join
        txt = f"⚠️ Aapko channel join karna padega tabhi aap bot use kar sakte ho.\n\nChannel: {CHANNEL}\n\nPress below to join, phir /start dobara karein."
        bot.send_message(chat_id, txt, reply_markup=channel_join_keyboard())
        return

    # If joined: send profile photo + welcome caption + main menu inline under same message
    fullname = user.full_name
    uname = user.username or "None"
    uid = user.id
    caption = (f"👤 Nick name : {fullname}\n"
               f"👤 Username : {uname}\n"
               f"👤 ID : {uid}\n"
               "----------------------------------------\n"
               f"Channel : {CHANNEL}")

    # try to fetch profile photo
    try:
        photos = bot.get_user_profile_photos(user.id)
        if photos.total_count > 0:
            file_id = photos.photos[0][0].file_id
            bot.send_photo(chat_id, file_id, caption=caption, reply_markup=main_menu_keyboard())
            return
    except Exception:
        pass

    # fallback: send message
    bot.send_message(chat_id, caption, reply_markup=main_menu_keyboard())

# ---------------- Callbacks ----------------
@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    user = call.from_user
    ensure_user_in_db(user)
    uid = user.id
    session = user_sessions.setdefault(chat_id, {})

    data = call.data

    # Owner-only command button handling
    if data.startswith("owner_"):
        if uid != OWNER_ID:
            bot.answer_callback_query(call.id, "Owner only.", show_alert=True)
            return
        # owner: check users
        if data == "owner_check_users":
            bot.send_message(chat_id, "Kitne users chahiye? (Number likh ke bhejein)", reply_markup=None)
            session["owner_wait_for"] = "owner_check_count"
            return
        elif data == "owner_back":
            bot.send_message(chat_id, "Owner panel closed.")
            session.pop("owner_wait_for", None)
            return

    # main menu
    if data == "simple_struct":
        session.clear()
        session["structure_type"] = "simple"
        bot.send_message(chat_id, "Choose offset type:", reply_markup=offsets_choice_keyboard())
        return

    if data == "hook_struct":
        session.clear()
        session["structure_type"] = "hook"
        bot.send_message(chat_id, "Send the offset (example: 0xc23fa50):")
        session["wait_for"] = "hook_offset"
        return

    if data == "settings":
        bot.send_message(chat_id, "⚙️ Settings: (not implemented yet)")
        return

    if data == "bot_info":
        bot.send_message(chat_id, "🤖 Bot Information:\nCreator: OWNER\nVersion: 1.0")
        return

    # Offsets choices
    if data == "single_offset":
        session["offset_mode"] = "single"
        bot.send_message(chat_id, "✨ Single Offset selected.\n\nSend the offset now (e.g. 0xc23fa50):")
        session["wait_for"] = "offset_single"
        return

    if data == "multi_offset":
        session["offset_mode"] = "multi"
        bot.send_message(chat_id, "✨ Multi Offset selected.\n\nSend multiple offsets separated by newline (example):\n0xc23fa50\n0xCA9C6F0\n0xCA6291F")
        session["wait_for"] = "offset_multi"
        return

    # patch type selection
    if data == "patch_lib":
        # select lib next but mark type
        session["selected_patch_type"] = "PATCH_LIB"
        bot.send_message(chat_id, "Choose library for Patchlib:", reply_markup=lib_select_keyboard())
        return

    if data == "memory_patch":
        # select lib next but mark type
        session["selected_patch_type"] = "memory"
        bot.send_message(chat_id, "Choose library for MemoryPatch:", reply_markup=lib_select_keyboard())
        return

    # lib selection callbacks like lib_UE4 etc
    if data.startswith("lib_"):
        lib_key = data.split("_", 1)[1]  # UE4 / Anogs / Anort
        # map to exact lib name
        lib_map = {
            "UE4": "libUE4.so",
            "Anogs": "libanogs.so",
            "Anort": "libanort.so",
        }
        lib_name = lib_map.get(lib_key, f"lib{lib_key}.so")
        session["lib_name"] = lib_name

        structure_type = session.get("structure_type", "simple")
        mode = session.get("offset_mode", "single")
        selected_patch_type = session.get("selected_patch_type", "patch")  # default patch_lib

        # Build result text depending on structure
        result_lines = []
        result_meta = {
            "Struct Type": "Simple" if structure_type == "simple" else ("Hook" if structure_type == "hook" else structure_type),
            "Structure Type": "MemoryPatch" if selected_patch_type == "memory" else "PATCH_LIB",
            "Selected Lib": lib_name
        }

        # For simple (single/multi)
        if structure_type == "simple":
            offsets = session.get("offsets", [])
            if not offsets:
                bot.send_message(chat_id, "Offsets missing. Please re-start the flow.")
                return

            if selected_patch_type == "memory":
                # MemoryPatch generation: MemoryPatch::createWithHex("libname", offset, "HEX").Modify();
                # We'll use a default HEX sample "73 6F 6E 52 65" as in examples
                hex_sample = "73 6F 6E 52 65"
                if mode == "single":
                    off = offsets[0]
                    code = f'MemoryPatch::createWithHex("{lib_name}",{off}, "{hex_sample}").Modify();'
                    result_lines.append(code)
                else:
                    for off in offsets:
                        code = f'MemoryPatch::createWithHex("{lib_name}",{off}, "{hex_sample}").Modify();'
                        result_lines.append(code)
            else:
                 selected_patch_type == "PATCH_LIB":
                # MemoryPatch generation: MemoryPatch::createWithHex("libname", offset, "HEX").Modify();
                # We'll use a default HEX sample "73 6F 6E 52 65" as in examples
                hex_sample = "73 6F 6E 52 65"
                if mode == "single":
                    off = offsets[0]
                    code = f'PATCH_LIB("{lib_name}", {off}, "{hex_sample}")
                    result_lines.append(code)
                else:
                    for off in offsets:
                        code = f'PATCH_LIB("{lib_name}",{off}, "{hex_sample}")
                        result_lines.append(code)

        elif structure_type == "hook":
            offsets = session.get("offsets", [])
            connects = session.get("connects", [])
            if not offsets or not connects:
                bot.send_message(chat_id, "Hook flow incomplete. Please provide offset and connect params first.")
                return
            # HOOK_LIB("libname", "offset", connect1, connect2);
            c1 = connects[0] if len(connects) > 0 else "connect1"
            c2 = connects[1] if len(connects) > 1 else "connect2"
            code = f'HOOK_LIB("{lib_name}", "{offsets[0]}", {c1}, {c2});'
            result_lines.append(code)

        # Save stats: mark user generated something (= bypass)
        users_db[uid]["bypass_count"] += 1
        gen_record = {
            "time": int(time.time()),
            "struct": result_meta["Struct Type"],
            "type": result_meta["Structure Type"],
            "lib": result_meta["Selected Lib"],
            "codes": result_lines,
        }
        users_db[uid]["generated"].append(gen_record)

        # Build final message
        result_text = "✅ Generated Structure\n\n"
        result_text += "```\n"  # code fence
        for line in result_lines:
            result_text += line + "\n"
        result_text += "```\n\n"
        # Quote section
        quote = (f"Struct Type : {result_meta['Struct Type']}\n"
                 f"Structure Type : {result_meta['Structure Type']}\n"
                 f"Selected Lib : {result_meta['Selected Lib']}")
        final_msg = f"{result_text}\n{quote}"
        # send as message (use Markdown for code fence)
        bot.send_message(chat_id, final_msg, parse_mode="Markdown")
        session.clear()
        return

    # owner panel access via callback (not required currently)
    if data == "owner_panel":
        if uid != OWNER_ID:
            bot.answer_callback_query(call.id, "Owner only.", show_alert=True)
            return
        # show basic stats
        total = len(users_db)
        started = sum(1 for u in users_db.values() if u.get("started"))
        total_bypass = sum(u.get("bypass_count", 0) for u in users_db.values())
        txt = (f"📊 Owner Panel\n\nTotal users seen: {total}\nStarted: {started}\nTotal bypass/generated: {total_bypass}")
        bot.send_message(chat_id, txt, reply_markup=owner_panel_keyboard())
        return

    bot.answer_callback_query(call.id, "Unhandled action.")

# ---------------- Text messages handler ----------------
@bot.message_handler(func=lambda m: True, content_types=['text'])
def handle_text_messages(message):
    chat_id = message.chat.id
    user = message.from_user
    ensure_user_in_db(user)
    session = user_sessions.setdefault(chat_id, {})

    # Owner flows
    if user.id == OWNER_ID and session.get("owner_wait_for") == "owner_check_count":
        # owner sent a number -> show up to that many users
        try:
            n = int(message.text.strip())
        except:
            bot.send_message(chat_id, "Please send a valid number.")
            return
        all_users = list(users_db.values())
        out = []
        for u in all_users[:n]:
            out.append(f"• {u['name']} @{u['username']} (id: {u['id']}) — bypass: {u.get('bypass_count',0)}")
        if not out:
            bot.send_message(chat_id, "No users to show.")
        else:
            bot.send_message(chat_id, "Users:\n" + "\n".join(out))
            bot.send_message(chat_id, "Now send a username or id to get detailed info about that user (example: @username or 123456).")
            session["owner_wait_for"] = "owner_select_user"
            session["owner_last_list_shown"] = [u['id'] for u in all_users[:n]]
        return

    if user.id == OWNER_ID and session.get("owner_wait_for") == "owner_select_user":
        text = message.text.strip()
        target = None
        if text.startswith("@"):
            uname = text.lstrip("@")
            for u in users_db.values():
                if u["username"].lower() == uname.lower():
                    target = u
                    break
        else:
            try:
                tid = int(text)
                target = users_db.get(tid)
            except:
                target = None
        if not target:
            bot.send_message(chat_id, "User not found. Send @username or numeric id from the list.")
            return
        # show details
        txt = (f"User info:\nName: {target['name']}\nUsername: @{target['username']}\nID: {target['id']}\n"
               f"Bypass count: {target.get('bypass_count',0)}\nGenerated items: {len(target.get('generated',[]))}")
        bot.send_message(chat_id, txt)
        # show generated items detail if any
        if target.get("generated"):
            s = []
            for i,g in enumerate(target["generated"][-10:], start=1):
                s.append(f"{i}. {g['time']} — {g['struct']} / {g['type']} / {g['lib']} — codes: {len(g['codes'])}")
            bot.send_message(chat_id, "Recent generated:\n" + "\n".join(s))
        session.pop("owner_wait_for", None)
        return

    # Normal flows: offsets & hook connections handling
    wait_for = session.get("wait_for")
    text = message.text.strip()

    if wait_for == "offset_single":
        # expect one offset
        session["offsets"] = [text]
        session["wait_for"] = None
        # ask for patch type
        bot.send_message(chat_id, "🤖 Choice Option :\n\nSelect Patch Type:", reply_markup=patch_type_keyboard())
        return

    if wait_for == "offset_multi":
        # split by line
        offsets = [line.strip() for line in text.splitlines() if line.strip()]
        session["offsets"] = offsets
        session["wait_for"] = None
        bot.send_message(chat_id, "🤖 Choice Option :\n\nSelect Patch Type:", reply_markup=patch_type_keyboard())
        return

    if wait_for == "hook_offset":
        session["offsets"] = [text]
        session["wait_for"] = "hook_connect"
        bot.send_message(chat_id, "Send connect params separated by comma (example: connect1,connect2):")
        return

    if wait_for == "hook_connect":
        connects = [c.strip() for c in text.split(",") if c.strip()]
        session["connects"] = connects
        session["wait_for"] = None
        # go to patch selection
        session["selected_patch_type"] = "patch"
        bot.send_message(chat_id, "🤖 Choice Option :\n\nSelect Patch Type:", reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("🎀 Patch Lib Like This ( PATCH_LIB )", callback_data="patch_lib")
        ))
        return

    # If owner sends /ownercmd via chat text
    if text.strip().lower() == "/ownercmd" and user.id == OWNER_ID:
        total = len(users_db)
        started = sum(1 for u in users_db.values() if u.get("started"))
        total_bypass = sum(u.get("bypass_count",0) for u in users_db.values())
        txt = (f"📊 Owner Panel\n\nTotal users seen: {total}\nStarted: {started}\nTotal generated: {total_bypass}")
        bot.send_message(chat_id, txt, reply_markup=owner_panel_keyboard())
        return

    # fallback: if user typed something else and we have no expectation, prompt main menu
    bot.send_message(chat_id, "Main menu:", reply_markup=main_menu_keyboard())

# ---------------- start polling ----------------
if __name__ == "__main__":
    print("Bot started...")
    bot.infinity_polling()
