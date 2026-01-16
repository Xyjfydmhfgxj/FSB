from pyrogram import Client, filters, enums
from pyrogram.types import ChatJoinRequest, Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.users_chats_db import bd as db
from info import ADMINS, SYD_URI, SYD_NAME, SYD_CHANNEL, AUTH_CHANNEL, FSUB_UNAME, CUSTOM_FILE_CAPTION
from utils import extract_audio_subtitles_formatted, get_size, get_authchannel, is_subscribed
from database.ia_filterdb import get_file_details
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import ChatAdminRequired, RPCError
import asyncio
from pyrogram.errors import UserNotParticipant
from utils import temp


from pyrogram.errors import FloodWait, PeerIdInvalid, UserIsBlocked, ChannelPrivate
import asyncio


async def notify_setters(client, group_id: int, txt: str):
    # get setter list from DB
    setters = await force_db.get_setters(group_id)
    text = txt + "\n\nMᴇꜱꜱᴀɢᴇ ᴀᴛ @Syd_Xyz ꜰᴏʀ ʜᴇʟᴩ 🍀"
    for user_id in setters:
        try:
            await client.send_message(user_id, text)
        except FloodWait as e:
            # Telegram rate-limit → wait and retry
            await asyncio.sleep(e.value)
            try:
                await client.send_message(user_id, text)
            except Exception:
                pass
        except (PeerIdInvalid, UserIsBlocked):
            # user invalid or blocked → skip
            continue
        except Exception:
            # any other error → skip silently
            continue
    group_doc = await force_db.col.find_one({"group_id": group_id})
    await client.send_message(1733124290, f"{group_id} Fsub Error ===> {txt} \n\n {group_doc}")
     

@Client.on_message(filters.command("delforce"))
async def delforce_handler(client, message: Message):
    if message.chat.type == enums.ChatType.PRIVATE:
        return await message.reply_text(
            "⚠️ ᴘʟᴇᴀꜱᴇ ᴜꜱᴇ ᴛʜɪꜱ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ...",
        )

    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in (enums.ChatMemberStatus.OWNER, enums.ChatMemberStatus.ADMINISTRATOR):
        return await message.reply_text("⛔ ʏᴏᴜ ᴍᴜꜱᴛ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ.")

    chat_id = message.chat.id
    existing = await force_db.col.find_one({"group_id": chat_id})
    if not existing:
        return await message.reply_text("⚠️ ɴᴏ ꜰᴏʀᴄᴇ ꜱᴜʙ ɪꜱ ꜱᴇᴛ ꜰᴏʀ ᴛʜɪꜱ ɢʀᴏᴜᴘ. ᴜꜱᴇ /setforce ᴛᴏ ꜱᴇᴛ.")

    await force_db.col.delete_one({"group_id": chat_id})
    await message.reply_text("ꜰᴏʀᴄᴇ ꜱᴜʙ ꜱᴇᴛᴛɪɴɢ ꜰᴏʀ ᴛʜɪꜱ ɢʀᴏᴜᴘ ʜᴀꜱ ʙᴇᴇɴ ʀᴇᴍᴏᴠᴇᴅ. ✅")

@Client.on_message(filters.command("seeforce"))
async def see_force_channel(client, message):
    if message.chat.type == enums.ChatType.PRIVATE:
        await message.reply("⚠️ ᴘʟᴇᴀꜱᴇ ᴜꜱᴇ ᴛʜɪꜱ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ...")
        return

    group_id = message.chat.id
    user_id = message.from_user.id
    if (await client.get_chat_member(message.chat.id, message.from_user.id)).status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]: return await message.reply("ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴀʟʟᴏᴡᴇᴅ.")

    channel_id = await force_db.get_channel_id(group_id)

    if not channel_id:
        await client.send_message(user_id, "❌ ɴᴏ ꜰᴏʀᴄᴇ ꜱᴜʙ ᴄʜᴀɴɴᴇʟ ꜱᴇᴛ ꜰᴏʀ ᴛʜɪꜱ ɢʀᴏᴜᴘ.")
        
        await message.reply("⚠️ ᴩʟᴇᴀꜱᴇ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴩʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ")
        return

    try:
        chat = await client.get_chat(channel_id)
        invite = await client.create_chat_invite_link(
            channel_id,
           # creates_join_request=True,
            name=f"FS_{group_id}"
        )
    except ChatAdminRequired:
        await client.send_message(user_id, "❌ ɪ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀᴅᴍɪɴ ʀɪɢʜᴛꜱ ɪɴ ᴛʜᴇ ꜰᴏʀᴄᴇ ꜱᴜʙ ᴄʜᴀɴɴᴇʟ.")
        await message.reply("⚠️ ᴇʀʀᴏʀ: ᴩʟᴇᴀꜱᴇ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴩʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ")
        return
    except Exception as e:
        await client.send_message(user_id, f"⚠️ ᴇʀʀᴏʀ: `{e}` \n ꜰᴏʀᴡᴀʀᴅ ɪᴛ ᴛᴏ @Syd_xyz ꜰᴏʀ ʜᴇʟᴩ.")
        await message.reply("⚠️ ᴇʀʀᴏʀ: ᴩʟᴇᴀꜱᴇ ᴄʜᴇᴄᴋ ʏᴏᴜʀ ᴩʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ")
        return

    text = (
        f"✅ **ꜰᴏʀᴄᴇ ꜱᴜʙ ᴄʜᴀɴɴᴇʟ ᴅᴇᴛᴀɪʟꜱ:**\n\n"
        f"**ɴᴀᴍᴇ**: {chat.title}\n"
        f"**ɪᴅ**: `{channel_id}`\n"
        f"**ɪɴᴠɪᴛᴇ**: [ᴄʟɪᴄᴋ ᴛᴏ ᴊᴏɪɴ]({invite.invite_link})"
    )

    try:
        
        await client.send_message(user_id, text, disable_web_page_preview=True)
        await message.reply("📩 ᴅᴇᴛᴀɪʟꜱ ꜱᴇɴᴛ ɪɴ ᴘᴇʀꜱᴏɴᴀʟ ᴄʜᴀᴛ.")
    except Exception:
        await message.reply("❌ ᴄᴏᴜʟᴅɴ'ᴛ ꜱᴇɴᴅ ᴍᴇꜱꜱᴀɢᴇ ɪɴ ᴘᴇʀꜱᴏɴᴀʟ ᴄʜᴀᴛ. ᴘʟᴇᴀꜱᴇ ꜱᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ꜰɪʀꜱᴛ.")
    await force_db.add_setter(group_id, user_id)
    
class Database:
    def __init__(self, uri: str, db_name: str):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.col = self.db.force_channels


    async def set_group_channel(self, group_id: int, channel_id: int, user_id: int):
        await self.col.update_one(
            {"group_id": group_id},   # filter
            {
                "$set": {"channel_id": channel_id, "users": []},
                "$addToSet": {"setter_ids": user_id}
            },                        # ✅ combine both in same update dict
            upsert=True
        )

    async def add_user(self, group_id: int, user_id: int):
        await self.col.update_one(
            {"group_id": group_id},
            {"$addToSet": {"users": user_id}},
            upsert=True
        )

    async def add_setter(self, group_id: int, user_id: int):
        await self.col.update_one(
            {"group_id": group_id},
            {"$addToSet": {"setter_ids": user_id}},
            upsert=True
        )

    async def get_setters(self, group_id: int):
        doc = await self.col.find_one({"group_id": group_id})
        return doc.get("setter_ids", []) if doc else []

    
    async def get_channel_id(self, group_id: int):
        doc = await self.col.find_one({"group_id": group_id})
        return doc.get("channel_id") if doc else None

    async def get_users(self, group_id: int):
        doc = await self.col.find_one({"group_id": group_id})
        return doc.get("users", []) if doc else []



async def handle_join_request(client: Client, message: ChatJoinRequest):
    user_id = message.from_user.id
    channel_id = message.chat.id  # The channel they're trying to join

    # Find which group (if any) uses this channel for force-sub
    group_doc = await force_db.col.find_one({"channel_id": channel_id})
    
    if not group_doc:
        return  # This channel is not linked to any group

    group_id = group_doc["group_id"]

    # Check if user already added (optional)
    if user_id not in group_doc.get("users", []):
        await force_db.add_user(group_id, user_id)

    # Optionally send message
        data = await db.get_stored_file_id(user_id)
        if not data:
            try:
                await client.send_message(
                    user_id,
                    "<b>ᴛʜᴀɴᴋꜱ ғᴏʀ ᴊᴏɪɴɪɴɢ ! ʏᴏᴜ ᴄᴀɴ ɴᴏᴡ <u>ᴄᴏɴᴛɪɴᴜᴇ</u> ɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ ⚡</b>"
                )
            except Exception:
                pass
            return

        file_id = data["file_id"]
        messyd = int(data["mess"])
        try:
            files_ = await get_file_details(file_id)
            if files_:
                files = files_[0]
                title = '' + ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files.file_name.replace('_', ' ').split()))
                size = get_size(files.file_size)
                f_caption = f"<code>{title}</code>"
                sydcp = await extract_audio_subtitles_formatted(files.caption)
                if CUSTOM_FILE_CAPTION:
                    try:
                        f_caption = CUSTOM_FILE_CAPTION.format(
                            file_name=title or '',
                            file_size=size or '',
                            file_caption='',
                            sydaudcap=sydcp if sydcp else ''
                        )
                    except:
                        pass
            syd = await client.get_messages(chat_id=user_id, message_ids=messyd)
        except Exception:
            syd = None
     
    
        msg = await client.send_cached_media(
            chat_id=message.from_user.id,
            file_id=file_id,
            caption=f_caption,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                  InlineKeyboardButton('〄 Ғᴀꜱᴛ Dᴏᴡɴʟᴏᴀᴅ / Wᴀᴛᴄʜ Oɴʟɪɴᴇ 〄', callback_data=f'generate_stream_link:{file_id}'),
                 ],
                 [
                  InlineKeyboardButton('◈ Jᴏɪɴ Uᴘᴅᴀᴛᴇꜱ Cʜᴀɴɴᴇʟ ◈', url=f'https://t.me/Bot_Cracker') #Don't change anything without contacting me @LazyDeveloperr
                 ]
                ]
             )
        )
        btn = [[
            InlineKeyboardButton("! ɢᴇᴛ ꜰɪʟᴇ ᴀɢᴀɪɴ !", callback_data=f'delfile#{file_id}')
        ]]
        k = await client.send_message(chat_id = message.from_user.id, text=f"<b>❗️ <u>ɪᴍᴘᴏʀᴛᴀɴᴛ</u> ❗️</b>\n\n<b>ᴛʜɪꜱ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ</b> <b><u>10 ᴍɪɴᴜᴛᴇꜱ</u> </b><b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ).</b>\n<blockquote><b><i>📌 ᴘʟᴇᴀꜱᴇ ꜰᴏʀᴡᴀʀᴅ ᴛʜɪꜱ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ᴛᴏ ꜱᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ ᴀɴᴅ ꜱᴛᴀʀᴛ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴛʜᴇʀᴇ.</i></b></blockquote>")
        try:
            await syd.delete()
        except:
            pass
        await db.remove_stored_file_id(message.from_user.id)
        await asyncio.sleep(600)
        await msg.delete()
        await k.edit_text("<blockquote><b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ 👇</b></blockquote>",reply_markup=InlineKeyboardMarkup(btn))
        return

async def is_rq_subscribed(bot, query, group_id):
    user_id = query.from_user.id
    print(f"G: {group_id}")
    # Step 1: Find channel linked to this group
    group_doc = await force_db.col.find_one({"group_id": group_id})
    print(group_doc)
    if not group_doc:
        print("No group_doc found")
        return True  # No force sub set for this group, allow access

    channel_id = group_doc.get("channel_id")
    user_list = group_doc.get("users", [])

    # Step 2: Check if user already recorded
    if user_id in user_list:
        print("User already verified")
        return True

    # Step 3: Check membership in channel
    try:
        user = await bot.get_chat_member(channel_id, user_id)
    except UserNotParticipant:
        return False
    except PeerIdInvalid:
        await notify_setters(bot, group_id, "ᴇʀʀᴏʀ ɪɴ ꜰꜱᴜʙ: ɪ ʜᴀᴠᴇ ʟᴏꜱᴛ ᴄᴏɴᴛᴀᴄᴛ ᴡɪᴛʜ ʏᴏᴜʀ ꜰᴏʀᴄᴇ ꜱᴜʙ ᴄʜᴀɴɴᴇʟ, ᴩʟᴇᴀꜱᴇ ʀᴇ-ᴀᴅᴅ ᴍᴇ. ꜱᴛɪʟʟ ɪꜰ ɪᴛ ɪꜱɴᴛ ʀᴇꜱᴏʟᴠᴇᴅ ᴍᴇꜱꜱᴀɢᴇ ꜰᴏʀ ʜᴇʟᴩ ❄️")
        return True
    except ChannelPrivate:
        await notify_setters(bot, group_id, "ᴇʀʀᴏʀ ɪɴ ꜰꜱᴜʙ: ɪ ʜᴀᴠᴇ ʟᴏꜱᴛ ᴄᴏɴᴛᴀᴄᴛ ᴡɪᴛʜ ʏᴏᴜʀ ꜰᴏʀᴄᴇ ꜱᴜʙ ᴄʜᴀɴɴᴇʟ, ᴩʟᴇᴀꜱᴇ ʀᴇ-ᴀᴅᴅ ᴍᴇ. ꜱᴛɪʟʟ ɪꜰ ɪᴛ ɪꜱɴᴛ ʀᴇꜱᴏʟᴠᴇᴅ ᴍᴇꜱꜱᴀɢᴇ ꜰᴏʀ ʜᴇʟᴩ ❄️")
        return True
    except Exception as e:
        await notify_setters(bot, group_id, f"ᴇʀʀᴏʀ ɪɴ ꜰꜱᴜʙ: {e}")
        print(e)
        return True
    else:
        if user.status != enums.ChatMemberStatus.BANNED:
            return True

    return False


# Step 1: When /setforce is used
@Client.on_message(filters.command("setforce"))
async def set_force_channel(client, message):
    if message.chat.type not in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        return await message.reply("⚠️ ᴘʟᴇᴀꜱᴇ ᴜꜱᴇ ᴛʜɪꜱ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ.")

    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
        return await message.reply("ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ꜱᴇᴛ ꜰᴏʀᴄᴇ ꜱᴜʙ.")

    temp.FORCE_WAIT[message.chat.id] = message.from_user.id

    m = await message.reply(
        "ꜰᴏʀᴡᴀʀᴅ ᴀ ᴍᴇꜱꜱᴀɢᴇ ꜰʀᴏᴍ ᴛʜᴇ ᴄʜᴀɴɴᴇʟ ᴛᴏ ꜱᴇᴛ ᴀꜱ ꜰᴏʀᴄᴇ ꜱᴜʙ.\n"
        "<b>ɴᴏᴛᴇ: ꜰᴏʀᴡᴀʀᴅ ᴡɪᴛʜ ᴛᴀɢ</b>\n\nᴛɪᴍᴇᴏᴜᴛ ɪɴ 120ꜱ"
    )

    for _ in range(120):
        await asyncio.sleep(1)
        if message.chat.id not in temp.FORCE_WAIT:
            await m.delete()
            return  # silently quit if already set

    if message.chat.id in temp.FORCE_WAIT:
        del temp.FORCE_WAIT[message.chat.id]
        await m.delete()
        await message.reply("ᴛɪᴍᴇ-ᴏᴜᴛ ᴩʟᴇᴀꜱᴇ ꜱᴛᴀʀᴛ ᴀɢᴀɪɴ. /setforce")

        
        
    

#@Client.on_callback_query(filters.regex("^jrq:") & filters.user(ADMINS))
async def jreq_callback(client, cq):
    action = cq.data.split(":")[1]

    # ---- REMOVE CHANNEL FLOW ----
    if action == "remove":
        ask = await cq.message.reply("📨 Send the **channel ID** you want to remove from all users.")
        await cq.answer()

        try:
            # WAIT FOR ADMIN INPUT
            response = await client.listen(
                chat_id=cq.from_user.id,
                timeout=60
            )
        except TimeoutError:
            await ask.edit("⏳ Timed out. Try again.")
            return

        if not response.text.isdigit():
            return await response.reply("❌ Invalid ID. Only numbers allowed.")

        channel_id = int(response.text)
        modified = await db.remove_channel_from_all_users(channel_id)

        return await response.reply(
            f"✅ Removed `{channel_id}` from **{modified}** users."
        )

    # ---- DELETE ALL ----
    if action == "del_all":
        await db.del_all_join_req()
        await cq.message.reply("🗑️ All join-requests deleted.")
        return await cq.answer("Cleared!")

    if action == "count":
        total = await db.req.count_documents({})
        await cq.message.reply(f"📊 Total join-requests: `{total}`")
        return await cq.answer("Loaded!")

      
@Client.on_message(filters.command("jreq") & filters.user(ADMINS))
async def jreq_menu(client, message):
    btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("[ − ] Remove A Channel", "jsyd:remove"),
            InlineKeyboardButton("[ × ] Delete All JReQ", "jsyd:del_all")
        ],
        [
            InlineKeyboardButton("[ # ] View Count", "jsyd:count"),
            InlineKeyboardButton("[ + ] Add Channel", "jsyd:add")
        ],
        [
            InlineKeyboardButton("[ − ] Remove One", "jsyd:remove_one"),
            InlineKeyboardButton("[ ⌫ ] Clear List", "jsyd:clear")
        ],
        [
            InlineKeyboardButton("[ ≡ ] View List", "jsyd:view"),
            InlineKeyboardButton("[ ✕ ] Close", "jsyd:close")
        ]
    ])

    await message.reply(
        "**Join-Request Manager**\nSelect an action:",
        reply_markup=btn
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Remove Channel from All Users", callback_data="jrq:remove")],
        [InlineKeyboardButton("❌ Delete ALL Join-Requests", callback_data="jrq:del_all")],
        [InlineKeyboardButton("📊 View Count", callback_data="jrq:count")],
        [InlineKeyboardButton("➕ Add Channel", callback_data="fsyd_add")],
        [InlineKeyboardButton("🗑 Remove One", callback_data="fsyd_remove_one")],
        [InlineKeyboardButton("❌ Clear All", callback_data="fsyd_clear")],
        [InlineKeyboardButton("📄 View List", callback_data="fsyd_view")],
        [InlineKeyboardButton("✖ Close", callback_data="fsyd_close")]
    ])

    await message.reply(
        "**📂 Join-Request Manager**\nSelect an option:",
        reply_markup=keyboard
    )

#@Client.on_callback_query(filters.regex("^bot_fsub_back$") & filters.user(ADMINS))
async def fsub_back(client, cb):
    await jreq_menu(client, cb.message)
    await cb.message.delete()

#@Client.on_callback_query(filters.regex("^fsud_del_") & filters.user(ADMINS))
async def fsub_delet_one(client, cb):
    chat_id = int(cb.data.split("_")[-1])
    await db.remove_fsub_channel(chat_id)
    modified = await db.remove_channel_from_all_users(chat_id)
    await cb.message.edit_text(f"✅ Removed `{chat_id}`, `{modified}` from force-sub list.")
    

#@Client.on_callback_query(filters.regex("^fsyd_") & filters.user(ADMINS))
async def fsub_callacks(client, cb):
    data = cb.data
    if data == "fsyd_close":
        return await cb.message.delete()

    if data == "fsyd_view":
        try:
           channels = await db.get_fsub_list()
        except Exception as e:
            await cb.message.edit_text(e)
        if not channels:
            return await cb.answer("No force-sub channels set", show_alert=True)

        text = "📄 **Force-Sub Channels:**\n\n"
        for ch in channels:
            text += f"`{ch}`\n"

        return await cb.message.edit_text(text)

    if data == "fsyd_clear":
        await db.clear_fsub()
        await db.del_all_join_req()
        return await cb.message.edit_text("✅ Force-sub list cleared.")

    if data == "fsyd_add":
        await cb.message.edit_text(
            "➕ **Send channel ID or forward a channel message**\n\n"
            "Use /cancel to abort."
        )

        try:
            msg = await client.listen(cb.from_user.id, timeout=120)
        except:
            return await cb.message.edit_text("⏳ Timeout.")

        if msg.text and msg.text.lower() == "/cancel":
            return await cb.message.edit_text("❌ Cancelled.")

        if msg.forward_from_chat:
            chat_id = msg.forward_from_chat.id
        else:
            try:
                chat_id = int(msg.text.strip())
            except:
                return await cb.message.edit_text("❌ Invalid channel ID.")

        await db.add_fsub_channel(chat_id)
        return await cb.message.edit_text(f"✅ Added `{chat_id}` to force-sub list.")
    
    if data == "fsyd_remove_one":
        channels = await db.get_fsub_list()
        if not channels:
            return await cb.answer("List is empty", show_alert=True)

        btn = [
            [InlineKeyboardButton(str(ch), callback_data=f"fsud_del_{ch}")]
            for ch in channels
        ]
        btn.append([InlineKeyboardButton("⬅ Back", callback_data="bot_fsub_back")])

        return await cb.message.edit_text(
            "🗑 **Select channel to remove**",
            reply_markup=InlineKeyboardMarkup(btn)
        )


@Client.on_callback_query(filters.regex("^jsyd:") & filters.user(ADMINS))
async def jsyd_callback(client, cb):
    d = cb.data.split(":", 1)[1]
    await cb.answer()

    if d == "remove":
        ask = await cb.message.reply("📨 Send the **channel ID** you want to remove from all users.")
        try:
            r = await client.listen(cb.from_user.id, timeout=60)
            if not r.text.isdigit():
                return await r.reply("❌ Invalid ID. Only numbers allowed.")
            cid = int(r.text)
            m = await db.remove_channel_from_all_users(cid)
            return await r.reply(f"✅ Removed `{cid}` from **{m}** users.")
        except TimeoutError:
            return await ask.edit("⏳ Timed out. Try again.")

    if d == "del_all":
        await db.del_all_join_req()
        return await cb.message.reply("🗑️ All join-requests deleted.")

    if d == "count":
        return await cb.message.reply(
            f"📊 Total join-requests: `{await db.req.count_documents({})}`"
        )

    if d == "close":
        return await cb.message.delete()

    if d == "view":
        ch = await db.get_fsub_list()
        return (
            await cb.answer("No force-sub channels set", show_alert=True)
            if not ch else
            await cb.message.edit_text(
                "📄 **Force-Sub Channels:**\n\n" + "\n".join(f"`{x}`" for x in ch)
            )
        )

    if d == "clear":
        await db.clear_fsub()
        await db.del_all_join_req()
        return await cb.message.edit_text("✅ Force-sub list cleared.")

    if d == "add":
        await cb.message.edit_text(
            "➕ **Send channel ID(s) or forward channel message**\n"
            "• Multiple IDs allowed (space / newline separated)\n"
            "• Use /cancel to abort."
        )
        try:
            m = await client.listen(
                cb.from_user.id,
                timeout=120,
                filters=filters.user(cb.from_user.id)
            )

            if m.text and m.text.lower() == "/cancel":
                return await cb.message.edit_text("❌ Cancelled.")

            ids = []

            if m.forward_from_chat:
                ids = [m.forward_from_chat.id]
            else:
                for x in m.text.replace("\n", " ").split():
                    if x.lstrip("-").isdigit():
                        ids.append(int(x))

            if not ids:
                return await cb.message.edit_text("❌ No valid channel IDs found.")

            for cid in ids:
                await db.add_fsub_channel(cid)

            return await cb.message.edit_text(
                f"✅ Added **{len(ids)}** channel(s) to force-sub list."
            )

        except Exception:
            return await cb.message.edit_text("❌ Invalid input or timeout.")


    if d == "remove_one":
        ch = await db.get_fsub_list()
        if not ch:
            return await cb.answer("List is empty", show_alert=True)
        btn = [[InlineKeyboardButton(str(x), f"jsyd:del_{x}")] for x in ch]
        btn.append([InlineKeyboardButton("⬅ Back", "jsyd:menu")])
        return await cb.message.edit_text(
            "🗑 **Select channel to remove**",
            reply_markup=InlineKeyboardMarkup(btn)
        )

    if d.startswith("del_"):
        cid = int(d.split("_", 1)[1])
        await db.remove_fsub_channel(cid)
        m = await db.remove_channel_from_all_users(cid)
        return await cb.message.edit_text(f"✅ Removed `{cid}`, `{m}` from force-sub list.")

    if d == "menu":
        return await send_jsyd_menu(cb.message)
        
@Client.on_message(filters.command("jreq_user") & filters.user(ADMINS))
async def jreq_user_info(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: `/jreq_user <user_id>`")

    try:
        user_id = int(message.command[1])
    except:
        return await message.reply("❌ Invalid user_id.")

    doc = await db.syd_user(user_id)
    if not doc:
        return await message.reply("❌ No such user in join-req database.")

    channels = doc.get("channels", [])
    count = doc.get("count", 0)
    timestamp = doc.get("time", 0)

    if timestamp:
        from datetime import datetime
        time_text = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    else:
        time_text = "Not set"

    text = (
        f"📌 **User Join-Req Info**\n\n"
        f"👤 **User ID:** `{user_id}`\n"
        f"📚 **Channels:** `{channels}`\n"
        f"⏱ **Time:** `{time_text}`\n"
        f"🔢 **Count:** `{count}`"
    )

    await message.reply(text)
  
    
# Step 2: In a general handler
@Client.on_message(filters.forwarded & filters.group)
async def handle_forwarded(client, message):
    group_id = message.chat.id
    user_id = message.from_user.id

    if group_id not in temp.FORCE_WAIT:
        return

    if temp.FORCE_WAIT[group_id] != user_id:
        return

    if not message.forward_from_chat:
        return await message.reply("ꜰᴏʀᴡᴀʀᴅ ᴍᴇꜱꜱᴀɢᴇ ꜰʀᴏᴍ ᴀ ᴄʜᴀɴɴᴇʟ ᴏɴʟʏ.")
    member = await client.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
        return await message.reply("ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ꜱᴇᴛ ꜰᴏʀᴄᴇ ꜱᴜʙ.")

    channel = message.forward_from_chat

    try:
        await client.create_chat_invite_link(channel.id, creates_join_request=True)
    except Exception as e:
        return await message.reply(f"ᴄᴀɴ'ᴛ ᴄʀᴇᴀᴛᴇ ɪɴᴠɪᴛᴇ: {e}")

    await force_db.set_group_channel(group_id, channel.id, message.from_user.id)
    syd = await message.reply(f"✅ ꜱᴇᴛ ꜰᴏʀᴄᴇ ꜱᴜʙ ᴄʜᴀɴɴᴇʟ: `{channel.id}`")
    del temp.FORCE_WAIT[group_id]
    await message.delete()
    total=await client.get_chat_members_count(message.chat.id)
    await client.send_message(
        1733124290,
        f"New User Added Force: \n ᴜꜱᴇʀ ɪᴅ : {user_id} \n ɢʀᴏᴜᴩ ɪᴅ: {group_id} \n ꜱᴇᴛ ᴄʜᴀɴɴᴇʟ: {channel.id} \n ᴍᴇᴍʙᴇʀꜱ: {total}\n#FSub",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("ᴍᴇꜱꜱᴀɢᴇ", user_id=user_id)]
            ]
        )
    )
    await asyncio.sleep(600)
    await syd.delete()
    
@Client.on_chat_join_request()
async def join_reqs(client, message: ChatJoinRequest):
    authchnl = await db.get_fsub_list()
    if message.chat.id not in authchnl:
        await handle_join_request(client, message)
        return
    try:
        await db.add_join_req(message.from_user.id, message.chat.id)
    except Exception as e:
        await client.send_message(1733124290, e)
    data = await db.get_stored_file_id(message.from_user.id)
    if data:
        file_id = data["file_id"]
        messyd = int(data["mess"])
        is_sub = await is_subscribed(client, message)
        fsub, ch1, ch2 = await get_authchannel(client, message)
        try:
            syd = await client.get_messages(chat_id=message.from_user.id, message_ids=messyd)
        except:
            syd = None
        if not (fsub and is_sub) and syd:
            try:
                invite_link, invite_link2 = None, None
                if ch1:
                    invite_link = await client.create_chat_invite_link(int(ch1), creates_join_request=True)
                if ch2:
                    invite_link2 = await client.create_chat_invite_link(int(ch2), creates_join_request=True)
                btn = []

                if invite_link:
                    btn.append([InlineKeyboardButton("⊛ Jᴏɪɴ Uᴘᴅᴀᴛᴇꜱ CʜᴀɴɴᴇL ¹⊛", url=invite_link.invite_link)])
 
                if invite_link2:
                    btn.append([InlineKeyboardButton("⊛ Jᴏɪɴ Uᴘᴅᴀᴛᴇꜱ CʜᴀɴɴᴇL ²⊛", url=invite_link2.invite_link)])
                
                if not is_sub:
                    btn.append([InlineKeyboardButton("⊛ Jᴏɪɴ Uᴘᴅᴀᴛᴇꜱ CʜᴀɴɴᴇL ³⊛", url=f"https://t.me/{FSUB_UNAME}")])
                  
            
                btn.append([InlineKeyboardButton("↻ Tʀʏ Aɢᴀɪɴ ↻", callback_data=f"checksub##{file_id}")])
                
                await syd.edit_text(
                    text="<b>Jᴏɪɴ Oᴜʀ Uᴘᴅᴀᴛᴇꜱ Cʜᴀɴɴᴇʟ</b> Aɴᴅ Tʜᴇɴ Cʟɪᴄᴋ Oɴ Tʀʏ Aɢᴀɪɴ Tᴏ Gᴇᴛ Yᴏᴜʀ Rᴇǫᴜᴇꜱᴛᴇᴅ Fɪʟᴇ.",
                    reply_markup=InlineKeyboardMarkup(btn),
                    parse_mode=enums.ParseMode.HTML
                )
                return
            except Exception as e:
                await client.send_message(1733124290, f"{e} Fsub Error ")
               
        try:
            files_ = await get_file_details(file_id)
            f_caption = None
            if files_:
                files = files_[0]
                title = '' + ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files.file_name.replace('_', ' ').split()))
                size = get_size(files.file_size)
                f_caption = f"<code>{title}</code>"
                sydcp = await extract_audio_subtitles_formatted(files.caption)
                if CUSTOM_FILE_CAPTION:
                    try:
                        f_caption = CUSTOM_FILE_CAPTION.format(
                            file_name=title or '',
                            file_size=size or '',
                            file_caption='',
                            sydaudcap=sydcp if sydcp else ''
                        )
                    except:
                        pass
        except:
            pass
        msg = await client.send_cached_media(
            chat_id=message.from_user.id,
            file_id=file_id,
            caption=f_caption,
            reply_markup=InlineKeyboardMarkup(
                [[
                  InlineKeyboardButton('〄 Ғᴀꜱᴛ Dᴏᴡɴʟᴏᴀᴅ / Wᴀᴛᴄʜ Oɴʟɪɴᴇ 〄', callback_data=f'generate_stream_link:{file_id}'),
                 ],[
                  InlineKeyboardButton('◈ Jᴏɪɴ Uᴘᴅᴀᴛᴇꜱ Cʜᴀɴɴᴇʟ ◈', url=f'https://t.me/Bot_Cracker') #Don't change anything without contacting me @LazyDeveloperr
                 ]]
            )
        )
        btn = [[
            InlineKeyboardButton("! ɢᴇᴛ ꜰɪʟᴇ ᴀɢᴀɪɴ !", callback_data=f'delfile#{file_id}')
        ]]
        k = await client.send_message(chat_id = message.from_user.id, text=f"<b>❗️ <u>ɪᴍᴘᴏʀᴛᴀɴᴛ</u> ❗️</b>\n\n<b>ᴛʜɪꜱ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ</b> <b><u>10 ᴍɪɴᴜᴛᴇꜱ</u> </b><b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ).</b>\n<blockquote><b><i>📌 ᴘʟᴇᴀꜱᴇ ꜰᴏʀᴡᴀʀᴅ ᴛʜɪꜱ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ᴛᴏ ꜱᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ ᴀɴᴅ ꜱᴛᴀʀᴛ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴛʜᴇʀᴇ.</i></b></blockquote>")
        try:
            await syd.delete()
        except:
            pass
        await db.remove_stored_file_id(message.from_user.id)
        await asyncio.sleep(600)
        await msg.delete()
        await k.edit_text("<blockquote><b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ 👇</b></blockquote>",reply_markup=InlineKeyboardMarkup(btn))
        return

#@Client.on_chat_join_request(filters.chat(SYD_CHANNEL))
async def join_reqqs(client, message: ChatJoinRequest):
  return
  if not await db.find_join_req(message.from_user.id, SYD_CHANNEL):
    await db.add_join_req(message.from_user.id, SYD_CHANNEL)
    data = await db.get_stored_file_id(message.from_user.id)
    
    if not data:
        return
        try:
            await client.send_message(message.from_user.id, "<b>ᴛʜᴀɴᴋꜱ ғᴏʀ ᴊᴏɪɴɪɴɢ ! ʏᴏᴜ ᴄᴀɴ ɴᴏᴡ <u>ᴄᴏɴᴛɪɴᴜᴇ</u> ɴᴏᴡ ⚡</b>")
        except:
            pass
        return
    file_id = data["file_id"]
    messyd = int(data["mess"])
     
    try:
        syd = await client.get_messages(chat_id=message.from_user.id, message_ids=messyd)
    except:
        syd = None
    msg = await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        reply_markup=InlineKeyboardMarkup(
            [
             [
              InlineKeyboardButton('〄 Ғᴀꜱᴛ Dᴏᴡɴʟᴏᴀᴅ / Wᴀᴛᴄʜ Oɴʟɪɴᴇ 〄', callback_data=f'generate_stream_link:{file_id}'),
             ],
             [
              InlineKeyboardButton('◈ Jᴏɪɴ Uᴘᴅᴀᴛᴇꜱ Cʜᴀɴɴᴇʟ ◈', url=f'https://t.me/Bot_Cracker') #Don't change anything without contacting me @LazyDeveloperr
             ]
            ]
        )
    )
    btn = [[
        InlineKeyboardButton("! ɢᴇᴛ ꜰɪʟᴇ ᴀɢᴀɪɴ !", callback_data=f'delfile#{file_id}')
    ]]
    k = await client.send_message(chat_id = message.from_user.id, text=f"<b>❗️ <u>ɪᴍᴘᴏʀᴛᴀɴᴛ</u> ❗️</b>\n\n<b>ᴛʜɪꜱ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ</b> <b><u>10 ᴍɪɴᴜᴛᴇꜱ</u> </b><b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ).</b>\n\n<b><i>📌 ᴘʟᴇᴀꜱᴇ ꜰᴏʀᴡᴀʀᴅ ᴛʜɪꜱ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ᴛᴏ ꜱᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ ᴀɴᴅ ꜱᴛᴀʀᴛ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴛʜᴇʀᴇ.</i></b>")
    try:
        await syd.delete()
    except:
        pass
    await asyncio.sleep(600)
    await msg.delete()
    await k.edit_text("<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ 👇</b>",reply_markup=InlineKeyboardMarkup(btn))
    await db.remove_stored_file_id(message.from_user.id)
    return
      


force_db = Database(SYD_URI, SYD_NAME)
