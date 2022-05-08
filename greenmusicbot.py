import os
import glob
import json
import logging
import asyncio
import youtube_dl
from pytgcalls import StreamType
from pytube import YouTube
from youtube_search import YoutubeSearch
from pytgcalls import PyTgCalls, idle
from pytgcalls.types import Update
from pyrogram.raw.base import Update
from pytgcalls.types import AudioPiped, AudioVideoPiped
from pytgcalls.types import (
    HighQualityAudio,
    HighQualityVideo,
    LowQualityVideo,
    MediumQualityVideo
)
from pytgcalls.types.stream import StreamAudioEnded, StreamVideoEnded
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant
from Farz.queues import QUEUE, add_to_queue, get_queue, clear_queue, pop_an_item
from Farz.admin_check import *

bot = Client(
    "GreenMusic",
    bot_token = os.environ["BOT_TOKEN"],
    api_id = int(os.environ["API_ID"]),
    api_hash = os.environ["API_HASH"]
)

client = Client(os.environ["SESSION_NAME"], int(os.environ["API_ID"]), os.environ["API_HASH"])

app = PyTgCalls(client)

OWNER_ID = int(os.environ["OWNER_ID"])
SUPPORT = os.environ["SUPPORT"]

LIVE_CHATS = []

START_TEXT = """━━━━━━━━━━━━━━━━━━━━━━
[💚](https://telegra.ph/file/6e420e91d0ceb5706f7bd.jpg) Salam, <b>{}</b> 
Mən Telegram qrupları üçün sürətli musiqi və video oynatma botuyam.
┏━━━━━━━━━━━━━━━━━┓
┣[Sahib](tg://user?id={})
┗━━━━━━━━━━━━━━━━━┛
Əlavə məlumatlar üçün ☘️Kömək☘️ butonuna basın.
━━━━━━━━━━━━━━━━━━━━━━
"""

START_BUTTONS = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                        "❇️ Grupa Əlavə Et ❇️", url="https://t.me/GGreenmusicbot?startgroup=true")
        ],
        [
            InlineKeyboardButton("☘️Kömək☘️", callback_data=" help_cb"),
            InlineKeyboardButton("⚙️Support⚙️", url=f"https://t.me/{SUPPORT}")
        ],
        [
            InlineKeyboardButton("🔳Repo🔳", url="https://github.com/Nihat-Farz/GreenMusicBot")
        ]
    ]
)

BUTTONS = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("▶️", callback_data="resume"),
            InlineKeyboardButton("⏸", callback_data="pause"),
            InlineKeyboardButton("⏭", callback_data="skip"),
            InlineKeyboardButton("⏹", callback_data="end"),
        ],
        [
            InlineKeyboardButton("• Bağla •", callback_data="close")
        ]
    ]
)

async def skip_current_song(chat_id):
    if chat_id in QUEUE:
        chat_queue = get_queue(chat_id)
        if len(chat_queue) == 1:
            await app.leave_group_call(chat_id)
            clear_queue(chat_id)
            return 1
        else:
            title = chat_queue[1][0]
            duration = chat_queue[1][1]
            link = chat_queue[1][2]
            playlink = chat_queue[1][3]
            type = chat_queue[1][4]
            Q = chat_queue[1][5]
            thumb = chat_queue[1][6]
            if type == "Audio":
                await app.change_stream(
                    chat_id,
                    AudioPiped(
                        playlink,
                    ),
                )
            elif type == "Video":
                if Q == "high":
                    hm = HighQualityVideo()
                elif Q == "mid":
                    hm = MediumQualityVideo()
                elif Q == "low":
                    hm = LowQualityVideo()
                else:
                    hm = MediumQualityVideo()
                await app.change_stream(
                    chat_id, AudioVideoPiped(playlink, HighQualityAudio(), hm)
                )
            pop_an_item(chat_id)
            await bot.send_photo(chat_id, photo = thumb,
                                 caption = f"🕕 <b>Müddət:</b> {duration}",
                                 reply_markup = BUTTONS)
            return [title, link, type, duration, thumb]
    else:
        return 0


async def skip_item(chat_id, lol):
    if chat_id in QUEUE:
        chat_queue = get_queue(chat_id)
        try:
            x = int(lol)
            title = chat_queue[x][0]
            chat_queue.pop(x)
            return title
        except Exception as e:
            print(e)
            return 0
    else:
        return 0


@app.on_stream_end()
async def on_end_handler(_, update: Update):
    if isinstance(update, StreamAudioEnded):
        chat_id = update.chat_id
        await skip_current_song(chat_id)


@app.on_closed_voice_chat()
async def close_handler(client: PyTgCalls, chat_id: int):
    if chat_id in QUEUE:
        clear_queue(chat_id)
        

async def yt_video(link):
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp",
        "-g",
        "-f",
        "best[height<=?720][width<=?1280]",
        f"{link}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        return 1, stdout.decode().split("\n")[0]
    else:
        return 0, stderr.decode()
    

async def yt_audio(link):
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp",
        "-g",
        "-f",
        "bestaudio",
        f"{link}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        return 1, stdout.decode().split("\n")[0]
    else:
        return 0, stderr.decode()


@bot.on_callback_query()
async def callbacks(_, cq: CallbackQuery):
    user_id = cq.from_user.id
    try:
        user = await cq.message.chat.get_member(user_id)
        admin_strings = ("creator", "administrator")
        if user.status not in admin_strings:
            is_admin = False
        else:
            is_admin = True
    except ValueError:
        is_admin = True        
    if not is_admin:
        return await cq.answer("» Bu əmrdən istifadə etməyə icazə verilmir.")   
    chat_id = cq.message.chat.id
    data = cq.data
    if data == "close":
        return await cq.message.delete()
    if not chat_id in QUEUE:
        return await cq.answer("» Heç nə səslənmir.")

    if data == "pause":
        try:
            await app.pause_stream(chat_id)
            await cq.answer("» Səsli dayandırıldı.")
        except:
            await cq.answer("» Heç nə səslənmir.")
      
    elif data == "resume":
        try:
            await app.resume_stream(chat_id)
            await cq.answer("» Musiqi davam edir")
        except:
            await cq.answer("» Heç nə səslənmir.")   

    elif data == "end":
        await app.leave_group_call(chat_id)
        clear_queue(chat_id)
        await cq.answer("» Yayım bitdi.")  

    elif data == "skip":
        op = await skip_current_song(chat_id)
        if op == 0:
            await cq.answer("» Növbə boşdur..")
        elif op == 1:
            await cq.answer("» Növbə boş, bağlı yayım.")
        else:
            await cq.answer("» Musiqi keçildi.")
            

@bot.on_message(filters.command("start") & filters.private)
async def start_private(_, message):
    msg = START_TEXT.format(message.from_user.mention, OWNER_ID)
    await message.reply_text(text = msg,
                             reply_markup = START_BUTTONS)
    

@bot.on_message(filters.command(["ping", "alive"]) & filters.group)
async def start_group(_, message):
    await message.delete()
    fuk = "<b>Green Music Aktivdir.!</b>"
    await message.reply_photo(photo="https://telegra.ph/file/6e420e91d0ceb5706f7bd.jpg", caption=fuk)


@bot.on_message(filters.command(["join", "userbotjoin", "assistant", "qatil"]) & filters.group)
@is_admin
async def join_chat(c: Client, m: Message):
    chat_id = m.chat.id
    try:
        invitelink = await c.export_chat_invite_link(chat_id)
        if invitelink.startswith("https://t.me/+"):
            invitelink = invitelink.replace(
                "https://t.me/+", "https://t.me/joinchat/"
            )
            await client.join_chat(invitelink)
            return await client.send_message(chat_id, "**» Asisstant çata uğurla qoşuldu.**")
    except UserAlreadyParticipant:
        return await client.send_message(chat_id, "**» Asisstant artıq söhbətə qoşulub.**")

    
@bot.on_message(filters.command(["play", "vplay"]) & filters.group)
async def video_play(_, message):
    await message.delete()
    user_id = message.from_user.id
    state = message.command[0].lower()
    try:
        query = message.text.split(None, 1)[1]
    except:
        return await message.reply_text(f"<b>İstifadəsi:</b> <code>/{state} [səmr]</code>")
    chat_id = message.chat.id
    if chat_id in LIVE_CHATS:
        return await message.reply_text("» Davam edən yayımı bitirmək və mahnıları yenidən oxumağa başlamaq üçün <code>/end</code> yazın.")
    
    m = await message.reply_text("**» Axtarılır,zəhmət olmasa gözləyin..**")
    if state == "play":
        damn = AudioPiped
        ded = yt_audio
        doom = "Audio"
    elif state == "vplay":
        damn = AudioVideoPiped
        ded = yt_video
        doom = "Video"
    if "low" in query:
        Q = "low"
    elif "mid" in query:
        Q = "mid"
    elif "high" in query:
        Q = "high"
    else:
        Q = "0"
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        link = f"https://youtube.com{results[0]['url_suffix']}"
        thumb = results[0]["thumbnails"][0]
        duration = results[0]["duration"]
        yt = YouTube(link)
        cap = f"» <b>Başlıq :</b> [{yt.title}]({link})\n <b>Yayım Növü :</b> `{doom}` \n🕕 <b>Müddət:</b> {duration}"
        try:
            ydl_opts = {"format": "bestvideo[height<=720]+bestaudio/best[height<=720]"}
            ydl = youtube_dl.YoutubeDL(ydl_opts)
            info_dict = ydl.extract_info(link, download=False)
            p = json.dumps(info_dict)
            a = json.loads(p)
            playlink = a['formats'][1]['manifest_url']
        except:
            ice, playlink = await ded(link)
            if ice == "0":
                return await m.edit("❗️YTDL Xəta !!!")               
    except Exception as e:
        return await m.edit(str(e))
    
    try:
        if chat_id in QUEUE:
            position = add_to_queue(chat_id, yt.title, duration, link, playlink, doom, Q, thumb)
            caps = f"» [{yt.title}]({link}) <b>Növbədəki {position}</b>\n\n🕕 <b>Müddət:</b> {duration}"
            await message.reply_photo(thumb, caption=caps)
            await m.delete()
        else:            
            await app.join_group_call(
                chat_id,
                damn(playlink),
                stream_type=StreamType().pulse_stream
            )
            add_to_queue(chat_id, yt.title, duration, link, playlink, doom, Q, thumb)
            await message.reply_photo(thumb, caption=cap, reply_markup=BUTTONS)
            await m.delete()
    except Exception as e:
        return await m.edit(str(e))
    
    
@bot.on_message(filters.command(["stream", "canli"]) & filters.group)
@is_admin
async def stream_func(_, message):
    await message.delete()
    state = message.command[0].lower()
    try:
        link = message.text.split(None, 1)[1]
    except:
        return await message.reply_text(f"<b>istifadəsi:</b> <code>/{state} [link]</code>")
    chat_id = message.chat.id
    
    if state == "stream":
        damn = AudioPiped
        emj = "🎵"
    elif state == "vstream":
        damn = AudioVideoPiped
        emj = "🎬"
    m = await message.reply_text("» Emal olunur, zəhmət olmasa gözləyin...")
    try:
        if chat_id in QUEUE:
            return await m.edit("❗️Canlı yayımdan əvvəl səsli söhbəti bitirmək üçün <code>/end</code> göndərin.")
        elif chat_id in LIVE_CHATS:
            await app.change_stream(
                chat_id,
                damn(link)
            )
            await m.edit(f"{emj} Yayım başladı: [Link]({link})", disable_web_page_preview=True)
        else:    
            await app.join_group_call(
                chat_id,
                damn(link),
                stream_type=StreamType().pulse_stream)
            await m.edit(f"{emj} Yayım başladı: [Link]({link})", disable_web_page_preview=True)
            LIVE_CHATS.append(chat_id)
    except Exception as e:
        return await m.edit(str(e))


@bot.on_message(filters.command("skip") & filters.group)
@is_admin
async def skip(_, message):
    await message.delete()
    chat_id = message.chat.id
    if len(message.command) < 2:
        op = await skip_current_song(chat_id)
        if op == 0:
            await message.reply_text("» Növbə boşdur..")
        elif op == 1:
            await message.reply_text("» Növbə boşdur,yayım bağlanır.")
    else:
        skip = message.text.split(None, 1)[1]
        out = "🗑 <b>Aşağıdakı mahnı(lar)ı növbədən sildi:</b> \n"
        if chat_id in QUEUE:
            items = [int(x) for x in skip.split(" ") if x.isdigit()]
            items.sort(reverse=True)
            for x in items:
                if x == 0:
                    pass
                else:
                    hm = await skip_item(chat_id, x)
                    if hm == 0:
                        pass
                    else:
                        out = out + "\n" + f"<b>» {x}</b> - {hm}"
            await message.reply_text(out)
            
            
@bot.on_message(filters.command(["playlist", "queue"]) & filters.group)
@is_admin
async def playlist(_, message):
    chat_id = message.chat.id
    if chat_id in QUEUE:
        chat_queue = get_queue(chat_id)
        if len(chat_queue) == 1:
            await message.delete()
            await message.reply_text(
                f"❇️ <b>Hal hazırda oynayır :</b> [{chat_queue[0][0]}]({chat_queue[0][2]}) | `{chat_queue[0][4]}`",
                disable_web_page_preview=True,
            )
        else:
            out = f"<b>📃 Növbə :</b> \n\n❇️ <b>Oynayan :</b> [{chat_queue[0][0]}]({chat_queue[0][2]}) | `{chat_queue[0][4]}` \n"
            l = len(chat_queue)
            for x in range(1, l):
                title = chat_queue[x][0]
                link = chat_queue[x][2]
                type = chat_queue[x][4]
                out = out + "\n" + f"<b>» {x}</b> - [{title}]({link}) | `{type}` \n"
            await message.reply_text(out, disable_web_page_preview=True)
    else:
        await message.reply_text("» Heç nə səslənmir.")
    

@bot.on_message(filters.command(["end", "son"]) & filters.group)
@is_admin
async def end(_, message):
    await message.delete()
    chat_id = message.chat.id
    if chat_id in LIVE_CHATS:
        await app.leave_group_call(chat_id)
        LIVE_CHATS.remove(chat_id)
        return await message.reply_text("» Yayım bitdi.")
        
    if chat_id in QUEUE:
        await app.leave_group_call(chat_id)
        clear_queue(chat_id)
        await message.reply_text("» Yayım bitdi.")
    else:
        await message.reply_text("» Heçnə səslənmir.")
        

@bot.on_message(filters.command("pause") & filters.group)
@is_admin
async def pause(_, message):
    await message.delete()
    chat_id = message.chat.id
    if chat_id in QUEUE:
        try:
            await app.pause_stream(chat_id)
            await message.reply_text("» Yayım dayandırıldı.")
        except:
            await message.reply_text("» Heçnə səslənmir")
    else:
        await message.reply_text("» Heçnə səslənmir.")
        
        
@bot.on_message(filters.command("resume") & filters.group)
@is_admin
async def resume(_, message):
    await message.delete()
    chat_id = message.chat.id
    if chat_id in QUEUE:
        try:
            await app.resume_stream(chat_id)
            await message.reply_text("» Yayım davam etdi.")
        except:
            await message.reply_text("» Heçnə səslənmir.")
    else:
        await message.reply_text("» Heçnə səslənmir.")


@bot.on_callback_query(filters.regex("help_cb"))
async def help_cmds(_, query: CallbackQuery):
    await query.answer("Əmrlər")
    await query.edit_message_text(
        f"""<b>» Əsas Əmrlər «</b>
» /play (sᴏɴɢ/ʏᴛ ʟɪɴᴋ) : Musiqi səsləndirmək üçün.
» /vplay (sᴏɴɢ/ʏᴛ ʟɪɴᴋ) : Video səsləndirmək üçün.
» /pause : Yayımı dayandırmaq üçün.
» /resume : Yayımı davam etmək üçün
» /skip : Yayımı keçmək üçün.
» /end : Yayımı sonlandırmaq üçün
» /playlist : Növbədə olan musiqilərə baxmaq üçün.
» /qatil vəya /userbotjoin - Asisstant hesabı grupa əlavə etmək üçün.
» /restart - Botu yenidən başlmaq üçün(Sahib üçün)
""")


@bot.on_message(filters.command("restart"))
async def restart(_, message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return
    await message.reply_text("» <i>Yenidən başladılır...</i>")
    os.system(f"kill -9 {os.getpid()} && python3 app.py")
            

app.start()
bot.run()
idle()
