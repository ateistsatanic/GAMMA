from pyrogram import Client, filters, idle
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, 
    ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
)
from pyrogram.enums import ParseMode, ChatType
import os
import json
import math
import random
import time
from os import sys
import concurrent.futures
from functools import partial, lru_cache
import asyncio
import aiofiles
import aiohttp
from aiohttp import ClientSession, TCPConnector
import logging
import psutil
from typing import Dict, List
import hashlib

import sys
import io

# Исправление кодировки для Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Конфигурация
token_log = '8390503590:AAGs_U7Bgi4YNqf1gN8fXwT8tKmvHFgxHMY'
chat_id_log = '-1002736899389'

with open('config/TOKEN.txt', 'r', encoding='utf-8') as f:
    API_TOKEN = f.readline().strip()

# Глобальные переменные
user_data_storage = {}
active_tasks = {}
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=20)

app = Client("gamma_bot", bot_token=API_TOKEN, parse_mode=ParseMode.HTML)

# Клавиатуры
kb_rus = ReplyKeyboardMarkup(
    [
        [
            KeyboardButton(text='🌕 Флудер'),
            KeyboardButton(text='🌗 Файлы'),
            KeyboardButton(text='🌘 Автоответчик'),
            KeyboardButton(text='🌔 Мульти'),
            KeyboardButton(text='🌑 FAQ')
        ]
    ], resize_keyboard=True
)

# Инициализация aiohttp сессии
async def create_aiohttp_session():
    connector = TCPConnector(limit=100, limit_per_host=20, ttl_dns_cache=300)
    app.aiohttp_session = ClientSession(connector=connector, trust_env=True)
    print("✅ aiohttp сессия создана")

async def close_aiohttp_session():
    if hasattr(app, 'aiohttp_session'):
        await app.aiohttp_session.close()
        print("✅ aiohttp сессия закрыта")

# ОБРАБОТЧИК СТАРТА С ФОТО
@app.on_message(filters.command("start"))
async def cmd_start(client: Client, message: Message):
    try:
        try:
            if os.path.exists('config/gamma.png'):
                await message.reply_photo(
                    'config/gamma.png',
                    caption='G.A.M.M.A v2.0.0 - Оптимизированная версия',
                    reply_markup=kb_rus
                )
            else:
                await message.reply(
                    'G.A.M.M.A v2.0.0 - Оптимизированная версия',
                    reply_markup=kb_rus
                )
        except Exception as photo_error:
            print(f"Ошибка отправки фото: {photo_error}")
            await message.reply(
                'G.A.M.M.A v2.0.0 - Оптимизированная версия',
                reply_markup=kb_rus
            )
    except Exception as e:
        await message.reply(f'Ошибка: {e}')

# Главное меню
async def handle_main_menu(client: Client, message: Message):
    if message.text == '🌕 Флудер':
        result = await chek_admin(message.from_user.id)
        if not result:
            await message.reply("❌ Нет прав")
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 Управление чатами", callback_data="flooder_chats")]
        ])
        await message.reply(
            "🌕 Флудер - управление спамом\n\nВыберите действие:",
            reply_markup=keyboard
        )
    
    elif message.text == '🌗 Файлы':
        result = await chek_admin(message.from_user.id)
        if not result:
            await message.reply("❌ Нет прав")
            return
        
        config_dir = 'config'
        if not os.path.exists(config_dir):
            await message.reply("📁 Папка config не существует")
            return
        
        files = [f for f in os.listdir(config_dir) if os.path.isfile(os.path.join(config_dir, f))]
        if not files:
            await message.reply("📁 Папка пуста")
            return
        
        await message.reply(f"📂 Отправка {len(files)} файлов...")
        
        for filename in files:
            file_path = os.path.join(config_dir, filename)
            try:
                file_ext = os.path.splitext(filename)[1].lower()
                
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                    await message.reply_photo(file_path, caption=f"🖼️ {filename}")
                elif file_ext in ['.mp4', '.avi', '.mov']:
                    await message.reply_video(file_path, caption=f"🎥 {filename}")
                elif file_ext in ['.mp3', '.wav']:
                    await message.reply_audio(file_path, caption=f"🎵 {filename}")
                else:
                    await message.reply_document(file_path, caption=f"📄 {filename}")
                
                await asyncio.sleep(0.5)
            except Exception as e:
                await message.reply(f"❌ Ошибка {filename}: {e}")
        
        await message.reply("✅ Все файлы отправлены!")
    
    elif message.text == '🌑 FAQ':
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📖 Гайд", url="https://teletype.in/@ksenod/6xaHYfronsG")],
            [
                InlineKeyboardButton("👑 Добавить админа", callback_data="add_admin"),
                InlineKeyboardButton("🗑️ Удалить админа", callback_data="remove_admin")
            ]
        ])
        
        await message.reply(
            "📚 FAQ - Часто задаваемые вопросы\n\n"
            "Здесь вы найдете полезную информацию и руководства",
            reply_markup=keyboard
        )
    elif message.text == '🌘 Автоответчик':
         targets = load_respond_targets()
         targets_count = len(targets)
         
         keyboard = InlineKeyboardMarkup([
             [InlineKeyboardButton("📋 Добавить цель", callback_data="add_respond"),
              InlineKeyboardButton('❌ Удалить цель', callback_data='delete_respond')],
             [InlineKeyboardButton("📊 Показать цели", callback_data="show_respond_targets")]
         ])
         await message.reply(
             f"🌘 Автоответчик - управление\n\n📊 Активных целей: {targets_count}\n\nВыберите действие:",
             reply_markup=keyboard
         )
    elif message.text == '🌔 Мульти':
        result = await chek_admin(message.from_user.id)
        if not result:
            await message.reply("❌ Нет прав")
            return
        
        tokens = load_tokens()
        multi_tasks = load_multi_tasks()
        
        stats_text = f"📊 Мульти-спам:\n• Токенов: {len(tokens)}\n• Задач: {len(multi_tasks)}"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Добавить мульти спам", callback_data="multi_add")],
            [InlineKeyboardButton("🗑️ Удалить мульти спам", callback_data="multi_delete")],
            [InlineKeyboardButton("🔑 Добавить токен", callback_data="multi_add_token")],
            [InlineKeyboardButton("📋 Список токенов", callback_data="multi_list_tokens")]
        ])
        
        await message.reply(stats_text, reply_markup=keyboard)

@app.on_message(filters.group & filters.command("id"))
async def get_group_id(client: Client, message: Message):
    await message.reply(f"ID этой группы: <code>{message.chat.id}</code>")


@app.on_callback_query(filters.regex(r"^multi_textfile\|"))
async def multi_textfile_handler(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in user_data_storage:
        await callback_query.answer("❌ Сессия истекла")
        return
        
    text_file = callback_query.data.split('|', 1)[1]
    user_data = user_data_storage[callback_query.from_user.id]
    user_data['text_file'] = text_file
    user_data['state'] = "waiting_multi_media_file"
    user_data_storage[callback_query.from_user.id] = user_data
    
    # Показываем медиа файлы
    media_files = []
    if os.path.exists('config'):
        for file in os.listdir('config'):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.mov', '.mkv')):
                media_files.append(file)
    
    keyboard = [[InlineKeyboardButton("🚫 Без медиа", callback_data=f"multi_media|none")]]
    
    for file in media_files:
        keyboard.append([InlineKeyboardButton(f"📁 {file}", callback_data=f"multi_media|{file}")])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="multi_cancel")])
    
    await callback_query.message.edit_text("🎬 Выберите медиа файл:", reply_markup=InlineKeyboardMarkup(keyboard))
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^multi_media\|"))
async def multi_media_handler(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in user_data_storage:
        await callback_query.answer("❌ Сессия истекла")
        return
        
    media_data = callback_query.data.split('|', 1)[1]
    media_file = None if media_data == 'none' else media_data
    
    user_data = user_data_storage[callback_query.from_user.id]
    
    # Сохраняем задачу
    multi_tasks = load_multi_tasks()
    chat_id = user_data['chat_id']
    
    multi_tasks[chat_id] = {
        'delay': user_data['delay'],
        'prefix': user_data['prefix'],
        'text_file': user_data['text_file'],
        'media_file': media_file,
        'active': True
    }
    
    save_multi_tasks(multi_tasks)
    await run_multi_task_optimized(chat_id, multi_tasks[chat_id])
    
    del user_data_storage[callback_query.from_user.id]
    
    # Получаем название чата для красивого ответа
    chats_data = load_chats()
    chat_title = chats_data.get(chat_id, {}).get('title', f"Чат {chat_id}")
    
    await callback_query.message.edit_text(
        f"✅ Мульти-спам создан для {chat_title}!\n\n"
        f"Задержка: {user_data['delay']}сек\n"
        f"Префикс: {user_data['prefix'] or 'Нет'}\n"
        f"Файл: {user_data['text_file']}\n"
        f"Медиа: {media_file or 'Нет'}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ В меню", callback_data="multi_back_to_main")]
        ])
    )
    await callback_query.answer()

# Обработчик отмены
@app.on_callback_query(filters.regex(r"^multi_cancel$"))
async def multi_cancel_handler(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id in user_data_storage:
        del user_data_storage[callback_query.from_user.id]
    await callback_query.message.edit_text("❌ Операция отменена")
    await callback_query.answer()

# Обработчик возврата в меню
@app.on_callback_query(filters.regex(r"^multi_back_to_main$"))
async def multi_back_to_main_handler(client: Client, callback_query: CallbackQuery):
    tokens = load_tokens()
    multi_tasks = load_multi_tasks()
    
    stats_text = f"📊 Мульти-спам:\n• Токенов: {len(tokens)}\n• Задач: {len(multi_tasks)}"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить мульти спам", callback_data="multi_add")],
        [InlineKeyboardButton("🗑️ Удалить мульти спам", callback_data="multi_delete")],
        [InlineKeyboardButton("🔑 Добавить токен", callback_data="multi_add_token")],
        [InlineKeyboardButton("📋 Список токенов", callback_data="multi_list_tokens")]
    ])
    
    await callback_query.message.edit_text(stats_text, reply_markup=keyboard)
    await callback_query.answer()


@app.on_callback_query(filters.regex(r"^multi_chat_select\|"))
async def multi_chat_select_handler(client: Client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split('|')
    chat_id = data_parts[1]
    page = int(data_parts[2])
    
    chats_data = load_chats()
    chat_info = chats_data.get(chat_id)
    
    if not chat_info:
        await callback_query.answer("❌ Чат не найден")
        return
    
    # Сохраняем выбранный чат и переходим к настройкам
    user_id = callback_query.from_user.id
    user_data_storage[user_id] = {
        'state': "waiting_multi_delay",
        'chat_id': chat_id,
        'page': page
    }
    
    await callback_query.message.edit_text(
        f"⏰ Введите задержку в секундах для чата {chat_info['title']}:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="multi_cancel")]])
    )
    await callback_query.answer()

# Добавь этот обработчик для показа текстовых файлов в мульти-спаме
@app.on_callback_query(filters.regex(r"^waiting_multi_text_file$"))
async def show_multi_text_files(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in user_data_storage:
        await callback_query.answer("❌ Сессия истекла")
        return
    
    txt_files = []
    if os.path.exists('config'):
        for file in os.listdir('config'):
            if file.endswith('.txt'):
                txt_files.append(file)
    
    if not txt_files:
        await callback_query.answer("❌ Нет txt файлов")
        return
    
    keyboard = []
    for file in txt_files:
        keyboard.append([InlineKeyboardButton(f"📄 {file}", callback_data=f"multi_textfile|{file}")])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="multi_cancel")])
    
    await callback_query.message.edit_text("📁 Выберите текстовый файл:", reply_markup=InlineKeyboardMarkup(keyboard))
    await callback_query.answer()


# ОБРАБОТЧИК ГЛАВНОГО МЕНЮ
@app.on_message(filters.private & filters.text & ~filters.command("start") & ~filters.command("chats"))
async def handle_main_menu_messages(client: Client, message: Message):
    user_id = message.from_user.id
    
    if message.text in ['🌕 Флудер', '🌗 Файлы', '🌘 Автоответчик', '🌔 Мульти', '🌑 FAQ']:
        await handle_main_menu(client, message)
        return
    
    if user_id in user_data_storage:
        await handle_all_text_messages(client, message)
    else:
        pass

@app.on_message(filters.private & filters.text & ~filters.me)
async def auto_responder_private_handler(client: Client, message: Message):
    try:
        targets = load_respond_targets()
        if not targets:
            return
            
        user_id_str = str(message.from_user.id)
        
        if user_id_str in targets:
            phrases_content = await async_cached_read('Phrases/messages.txt')
            if phrases_content:
                phrases = [line.strip() for line in phrases_content.split('\n') if line.strip()]
                if phrases:
                    response_text = random.choice(phrases)
                    asyncio.create_task(message.reply(response_text))
    except Exception as e:
        print(f"❌ Ошибка личного автоответчика: {e}")

@app.on_callback_query(filters.regex(r"^multi_delete$"))
async def multi_delete_handler(client: Client, callback_query: CallbackQuery):
    multi_tasks = load_multi_tasks()
    
    if not multi_tasks:
        await callback_query.answer("❌ Нет активных задач мульти-спама")
        return
    
    keyboard = []
    for chat_id, task_data in multi_tasks.items():
        chats_data = load_chats()
        chat_title = chats_data.get(chat_id, {}).get('title', f"Чат {chat_id}")
        keyboard.append([InlineKeyboardButton(f"🗑️ {chat_title}", callback_data=f"multi_delete_confirm|{chat_id}")])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="multi_back_to_main")])
    
    await callback_query.message.edit_text(
        "🗑️ Выберите задачу для удаления:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^multi_delete_confirm\|"))
async def multi_delete_confirm_handler(client: Client, callback_query: CallbackQuery):
    chat_id = callback_query.data.split('|')[1]
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, удалить", callback_data=f"multi_delete_final|{chat_id}")],
        [InlineKeyboardButton("❌ Нет, отмена", callback_data="multi_delete")]
    ])
    
    chats_data = load_chats()
    chat_title = chats_data.get(chat_id, {}).get('title', f"Чат {chat_id}")
    
    await callback_query.message.edit_text(
        f"⚠️ Вы уверены, что хотите удалить мульти-спам для чата {chat_title}?",
        reply_markup=keyboard
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^multi_delete_final\|"))
async def multi_delete_final_handler(client: Client, callback_query: CallbackQuery):
    chat_id = callback_query.data.split('|')[1]
    
    multi_tasks = load_multi_tasks()
    
    if chat_id in multi_tasks:
        task_key = f"multi_{chat_id}"
        if task_key in active_tasks:
            active_tasks[task_key].cancel()
            del active_tasks[task_key]
        
        del multi_tasks[chat_id]
        save_multi_tasks(multi_tasks)
        await callback_query.answer("✅ Задача удалена")
    else:
        await callback_query.answer("❌ Задача не найдена")
    
    callback_query.data = "multi_delete"
    await multi_delete_handler(client, callback_query)

# Вспомогательные функции
async def send_telegram_message(message_text: str):
    try:
        async with Client("logger", bot_token=token_log) as logger:
            await logger.send_message(chat_id_log, message_text)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

async def chek_admin(user_id: int) -> bool:
    try:
        os.makedirs('config', exist_ok=True)
        admins_file = 'config/admins.json'
        
        if not os.path.exists(admins_file):
            with open(admins_file, 'w', encoding='utf-8') as f:
                json.dump({"admins": []}, f, ensure_ascii=False, indent=4)
            return False
        
        with open(admins_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return str(user_id) in data.get("admins", [])
        
    except Exception as e:
        print(f"❌ Ошибка проверки админа: {e}")
        return False

@lru_cache(maxsize=100)
def load_tokens() -> List[str]:
    os.makedirs('config', exist_ok=True)
    if os.path.exists('config/tokens.json'):
        try:
            with open('config/tokens.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_tokens(tokens: List[str]):
    os.makedirs('config', exist_ok=True)
    with open('config/tokens.json', 'w', encoding='utf-8') as f:
        json.dump(tokens, f, ensure_ascii=False, indent=4)

@lru_cache(maxsize=50)
def load_multi_tasks() -> Dict:
    os.makedirs('config', exist_ok=True)
    if os.path.exists('config/multi.json'):
        try:
            with open('config/multi.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_multi_tasks(tasks: Dict):
    os.makedirs('config', exist_ok=True)
    with open('config/multi.json', 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

async def show_multi_chats_menu(message: Message, page: int = 0):
    chats_data = load_chats()
    if not chats_data:
        await message.reply("📋 Нет чатов")
        return
    
    active_chats = {chat_id: info for chat_id, info in chats_data.items() if info.get('is_active', True)}
    if not active_chats:
        await message.reply("📋 Нет активных чатов")
        return
    
    sorted_chats = sorted(active_chats.items(), key=lambda x: x[1]['title'])
    items_per_page = 5
    total_pages = math.ceil(len(sorted_chats) / items_per_page)
    
    if page >= total_pages: page = total_pages - 1
    if page < 0: page = 0
    
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    current_chats = sorted_chats[start_idx:end_idx]
    
    keyboard = []
    for chat_id, chat_info in current_chats:
        chat_title = chat_info['title'][:30] + "..." if len(chat_info['title']) > 30 else chat_info['title']
        keyboard.append([InlineKeyboardButton(chat_title, callback_data=f"multi_chat_select|{chat_id}|{page}")])
    
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"multi_chat_page|{page-1}"))
    if page < total_pages - 1:
        pagination_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"multi_chat_page|{page+1}"))
    
    if pagination_buttons:
        keyboard.append(pagination_buttons)
    
    keyboard.append([InlineKeyboardButton("🔄 Обновить", callback_data=f"multi_chat_refresh|{page}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="multi_back_to_main")])
    
    await message.reply(
        f"📋 Выберите чат для мульти-спама (Страница {page + 1}/{total_pages}):",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def send_multi_message_optimized(token: str, chat_id: str, text: str, media_path: str = None):
    try:
        url = f"https://api.telegram.org/bot{token}/"
        
        if media_path and os.path.exists(media_path):
            async with aiofiles.open(media_path, 'rb') as f:
                file_data = await f.read()
            
            form_data = aiohttp.FormData()
            
            if media_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                url += "sendPhoto"
                form_data.add_field('photo', file_data, filename=os.path.basename(media_path))
            elif media_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                url += "sendVideo"
                form_data.add_field('video', file_data, filename=os.path.basename(media_path))
            else:
                url += "sendDocument"
                form_data.add_field('document', file_data, filename=os.path.basename(media_path))
            
            form_data.add_field('chat_id', str(chat_id))
            form_data.add_field('caption', text)
            
            async with app.aiohttp_session.post(url, data=form_data) as response:
                return response.status == 200
                
        else:
            url += "sendMessage"
            data = {'chat_id': str(chat_id), 'text': text}
            
            async with app.aiohttp_session.post(url, json=data) as response:
                return response.status == 200
                
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

async def run_multi_task_optimized(chat_id: str, task_data: Dict):
    task_key = f"multi_{chat_id}"
    
    async def optimized_loop():
        error_count = 0
        max_errors = 10
        
        while True:
            try:
                multi_tasks = load_multi_tasks()
                current_task = multi_tasks.get(chat_id)
                
                if not current_task or not current_task.get('active', True):
                    break
                
                if error_count > 0:
                    wait_time = min(300, 2 ** error_count)
                    await asyncio.sleep(wait_time)
                
                tokens = load_tokens()
                if not tokens:
                    await asyncio.sleep(60)
                    continue
                
                text_file_path = f"config/{task_data['text_file']}"
                if os.path.exists(text_file_path):
                    async with aiofiles.open(text_file_path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        messages = [msg.strip() for msg in content.split('\n') if msg.strip()]
                else:
                    await asyncio.sleep(60)
                    continue
                
                message_text = task_data['prefix'] + ' ' + random.choice(messages) if task_data['prefix'] else random.choice(messages)
                media_file_path = f"config/{task_data['media_file']}" if task_data['media_file'] else None
                
                send_tasks = []
                for token in tokens:
                    send_task = send_multi_message_optimized(token, chat_id, message_text, media_file_path)
                    send_tasks.append(send_task)
                
                results = []
                for i in range(0, len(send_tasks), 5):
                    batch = send_tasks[i:i+5]
                    batch_results = await asyncio.gather(*batch, return_exceptions=True)
                    results.extend(batch_results)
                    await asyncio.sleep(0.1)
                
                success_count = sum(1 for r in results if r is True)
                if success_count > 0:
                    error_count = max(0, error_count - 1)
                
                print(f"📤 Успешно: {success_count}/{len(tokens)}")
                
                await asyncio.sleep(task_data['delay'])
                
            except asyncio.CancelledError:
                raise
            except Exception as e:
                error_count += 1
                print(f"❌ Ошибка в задаче {chat_id}: {e}")
                if error_count >= max_errors:
                    print(f"🔴 Задача {chat_id} остановлена из-за множества ошибок")
                    break
    
    active_tasks[task_key] = asyncio.create_task(optimized_loop())
    print(f"✅ Мульти-задача запущена: {task_key}")

@lru_cache(maxsize=50)
def load_respond_targets() -> Dict:
    try:
        os.makedirs('config', exist_ok=True)
        if os.path.exists('config/resp.json'):
            with open('config/resp.json', 'r', encoding='utf-8') as f:
                data = f.read().strip()
                if not data:
                    return {}
                return json.loads(data)
        return {}
    except Exception as e:
        print(f"❌ Ошибка загрузки resp.json: {e}")
        return {}

def save_respond_targets(targets: Dict):
    os.makedirs('config', exist_ok=True)
    with open('config/resp.json', 'w', encoding='utf-8') as f:
        json.dump(targets, f, ensure_ascii=False, indent=4)

@app.on_callback_query(filters.regex(r"^add_respond$"))
async def add_respond_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    user_data_storage[user_id] = {
        'state': "waiting_add_respond_target"
    }
    
    await callback_query.message.edit_text(
        "📝 Введите ID чата или пользователя для добавления в автоответчик:\n\n"
        "Формат: <code>ID_чата</code> или <code>ID_пользователя</code>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel_respond")]])
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^delete_respond$"))
async def delete_respond_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    user_data_storage[user_id] = {
        'state': "waiting_delete_respond_target"
    }
    
    await callback_query.message.edit_text(
        "📝 Введите ID чата или пользователя для удаления из автоответчика:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel_respond")]])
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^cancel_respond$"))
async def cancel_respond_handler(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id in user_data_storage:
        del user_data_storage[callback_query.from_user.id]
    await callback_query.message.edit_text("❌ Операция отменена")
    await callback_query.answer()

@lru_cache(maxsize=50)
def load_flooder_tasks() -> Dict:
    os.makedirs('config', exist_ok=True)
    if os.path.exists('config/flooder.json'):
        try:
            with open('config/flooder.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


# ОБРАБОТЧИКИ РЕДАКТИРОВАНИЯ ЗАДАЧ
@app.on_callback_query(filters.regex(r"^edit_tasks\|"))
async def edit_tasks_handler(client: Client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split('|')
    
    if len(data_parts) < 3:
        await callback_query.answer("❌ Неверный формат данных")
        return
    
    chat_id = data_parts[1]
    page = int(data_parts[2])
    
    flooder_tasks = load_flooder_tasks()
    chat_tasks = flooder_tasks.get(chat_id, {})
    
    if not chat_tasks:
        await callback_query.answer("❌ Нет задач для редактирования")
        return
    
    keyboard = []
    for task_id, task_data in chat_tasks.items():
        status = "✅" if task_data.get('active', True) else "❌"
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {task_id} ({task_data['delay']}сек)",
                callback_data=f"task_manage|{chat_id}|{task_id}|{page}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f"chat_select|{chat_id}|{page}")])
    
    await callback_query.message.edit_text(
        "⚙️ Выберите задачу для редактирования:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^task_manage\|"))
async def task_manage_handler(client: Client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split('|')
    if len(data_parts) < 4:
        await callback_query.answer("❌ Неверный формат данных")
        return
    
    chat_id = data_parts[1]
    task_id = data_parts[2]
    page = int(data_parts[3])

    flooder_tasks = load_flooder_tasks()
    task_data = flooder_tasks.get(chat_id, {}).get(task_id)

    if not task_data:
        await callback_query.answer("❌ Задача не найдена")
        return

    status = "✅ ВКЛ" if task_data.get('active', True) else "❌ ВЫКЛ"

    keyboard = [
        [InlineKeyboardButton(f"🔄 Статус: {status}", callback_data=f"task_toggle|{chat_id}|{task_id}|{page}")],
        [InlineKeyboardButton("⏰ Изменить задержку", callback_data=f"task_delay|{chat_id}|{task_id}|{page}")],
        [InlineKeyboardButton("📝 Изменить префикс", callback_data=f"task_prefix|{chat_id}|{task_id}|{page}")],
        [InlineKeyboardButton("📄 Изменить текстовый файл", callback_data=f"task_textfile|{chat_id}|{task_id}|{page}")],
        [InlineKeyboardButton("🎬 Изменить медиа файл", callback_data=f"task_media|{chat_id}|{task_id}|{page}")],
        [InlineKeyboardButton("🗑️ Удалить задачу", callback_data=f"task_delete|{chat_id}|{task_id}|{page}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"edit_tasks|{chat_id}|{page}")]
    ]

    await callback_query.message.edit_text(
        f"⚙️ Управление задачей: {task_id}\n\n"
        f"📊 Статус: {status}\n"
        f"⏰ Задержка: {task_data['delay']} сек\n"
        f"📝 Префикс: {task_data['prefix'] or 'Нет'}\n"
        f"📄 Файл: {task_data['text_file']}\n"
        f"🎬 Медиа: {task_data['media_file'] or 'Нет'}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^task_toggle\|"))
async def task_toggle_handler(client: Client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split('|')
    chat_id = data_parts[1]
    task_id = data_parts[2]
    page = int(data_parts[3])
    
    flooder_tasks = load_flooder_tasks()
    if chat_id in flooder_tasks and task_id in flooder_tasks[chat_id]:
        if flooder_tasks[chat_id][task_id].get('active', True):
            await stop_flooder_task(chat_id, task_id)
            flooder_tasks[chat_id][task_id]['active'] = False
        else:
            flooder_tasks[chat_id][task_id]['active'] = True
            await run_flooder_task(chat_id, task_id, flooder_tasks[chat_id][task_id])
        
        save_flooder_tasks(flooder_tasks)
        await callback_query.answer("✅ Статус изменен")
        
        callback_query.data = f"task_manage|{chat_id}|{task_id}|{page}"
        await task_manage_handler(client, callback_query)
    else:
        await callback_query.answer("❌ Задача не найдена")

@app.on_callback_query(filters.regex(r"^task_delay\|"))
async def task_delay_edit_handler(client: Client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split('|')
    chat_id = data_parts[1]
    task_id = data_parts[2]
    page = int(data_parts[3])
    
    user_data_storage[callback_query.from_user.id] = {
        'state': "waiting_edit_delay",
        'chat_id': chat_id,
        'task_id': task_id,
        'page': page
    }
    
    await callback_query.message.edit_text(
        "⏰ Введите новую задержку в секундах:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data=f"task_manage|{chat_id}|{task_id}|{page}")]])
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^task_prefix\|"))
async def task_prefix_edit_handler(client: Client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split('|')
    chat_id = data_parts[1]
    task_id = data_parts[2]
    page = int(data_parts[3])
    
    user_data_storage[callback_query.from_user.id] = {
        'state': "waiting_edit_prefix",
        'chat_id': chat_id,
        'task_id': task_id,
        'page': page
    }
    
    await callback_query.message.edit_text(
        "📝 Введите новый префикс (или 'Нет'):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data=f"task_manage|{chat_id}|{task_id}|{page}")]])
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^task_textfile\|"))
async def task_textfile_handler(client: Client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split('|')
    chat_id = data_parts[1]
    task_id = data_parts[2]
    page = int(data_parts[3])
    
    txt_files = []
    if os.path.exists('config'):
        for file in os.listdir('config'):
            if file.endswith('.txt'):
                txt_files.append(file)
    
    if not txt_files:
        await callback_query.answer("❌ Нет txt файлов")
        return
    
    keyboard = []
    for file in txt_files:
        keyboard.append([InlineKeyboardButton(f"📄 {file}", callback_data=f"edit_textfile|{chat_id}|{task_id}|{page}|{file}")])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data=f"task_manage|{chat_id}|{task_id}|{page}")])
    
    await callback_query.message.edit_text(
        "📁 Выберите новый текстовый файл:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^edit_textfile\|"))
async def edit_textfile_handler(client: Client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split('|')
    chat_id = data_parts[1]
    task_id = data_parts[2]
    page = int(data_parts[3])
    text_file = data_parts[4]
    
    flooder_tasks = load_flooder_tasks()
    if chat_id in flooder_tasks and task_id in flooder_tasks[chat_id]:
        await stop_flooder_task(chat_id, task_id)
        
        flooder_tasks[chat_id][task_id]['text_file'] = text_file
        save_flooder_tasks(flooder_tasks)
        
        if flooder_tasks[chat_id][task_id].get('active', True):
            await run_flooder_task(chat_id, task_id, flooder_tasks[chat_id][task_id])
        
        await callback_query.answer("✅ Текстовый файл изменен")
        
        callback_query.data = f"task_manage|{chat_id}|{task_id}|{page}"
        await task_manage_handler(client, callback_query)
    else:
        await callback_query.answer("❌ Задача не найдена")

@app.on_callback_query(filters.regex(r"^task_media\|"))
async def task_media_handler(client: Client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split('|')
    chat_id = data_parts[1]
    task_id = data_parts[2]
    page = int(data_parts[3])
    
    media_files = []
    if os.path.exists('config'):
        for file in os.listdir('config'):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.mov', '.mkv')):
                media_files.append(file)
    
    keyboard = [[InlineKeyboardButton("🚫 Без медиа", callback_data=f"edit_media|{chat_id}|{task_id}|{page}|none")]]
    
    for file in media_files:
        keyboard.append([InlineKeyboardButton(f"📁 {file}", callback_data=f"edit_media|{chat_id}|{task_id}|{page}|{file}")])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data=f"task_manage|{chat_id}|{task_id}|{page}")])
    
    await callback_query.message.edit_text(
        "🎬 Выберите новый медиа файл:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^edit_media\|"))
async def edit_media_handler(client: Client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split('|')
    chat_id = data_parts[1]
    task_id = data_parts[2]
    page = int(data_parts[3])
    media_file = data_parts[4]
    
    if media_file == 'none':
        media_file = None
    
    flooder_tasks = load_flooder_tasks()
    if chat_id in flooder_tasks and task_id in flooder_tasks[chat_id]:
        await stop_flooder_task(chat_id, task_id)
        
        flooder_tasks[chat_id][task_id]['media_file'] = media_file
        save_flooder_tasks(flooder_tasks)
        
        if flooder_tasks[chat_id][task_id].get('active', True):
            await run_flooder_task(chat_id, task_id, flooder_tasks[chat_id][task_id])
        
        await callback_query.answer("✅ Медиа файл изменен")
        
        callback_query.data = f"task_manage|{chat_id}|{task_id}|{page}"
        await task_manage_handler(client, callback_query)
    else:
        await callback_query.answer("❌ Задача не найдена")

@app.on_callback_query(filters.regex(r"^task_delete\|"))
async def task_delete_handler(client: Client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split('|')
    chat_id = data_parts[1]
    task_id = data_parts[2]
    page = int(data_parts[3])
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete|{chat_id}|{task_id}|{page}")],
        [InlineKeyboardButton("❌ Нет, отмена", callback_data=f"task_manage|{chat_id}|{task_id}|{page}")]
    ])
    
    await callback_query.message.edit_text(
        "⚠️ Вы уверены, что хотите удалить эту задачу?",
        reply_markup=keyboard
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^confirm_delete\|"))
async def confirm_delete_handler(client: Client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split('|')
    chat_id = data_parts[1]
    task_id = data_parts[2]
    page = int(data_parts[3])
    
    flooder_tasks = load_flooder_tasks()
    if chat_id in flooder_tasks and task_id in flooder_tasks[chat_id]:
        await stop_flooder_task(chat_id, task_id)
        
        del flooder_tasks[chat_id][task_id]
        if not flooder_tasks[chat_id]:
            del flooder_tasks[chat_id]
        save_flooder_tasks(flooder_tasks)
        await callback_query.answer("✅ Задача удалена")
        
        callback_query.data = f"edit_tasks|{chat_id}|{page}"
        await edit_tasks_handler(client, callback_query)
    else:
        await callback_query.answer("❌ Задача не найдена")


def save_flooder_tasks(tasks: Dict):
    os.makedirs('config', exist_ok=True)
    with open('config/flooder.json', 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

@app.on_callback_query(filters.regex(r"^flooder_chats$"))
async def flooder_chats_handler(client: Client, callback_query: CallbackQuery):
    await callback_query.message.delete()
    await show_chats_menu(callback_query.message)
    await callback_query.answer()

async def stop_flooder_task(chat_id: str, task_id: str):
    task_key = f"{chat_id}_{task_id}"
    if task_key in active_tasks:
        active_tasks[task_key].cancel()
        del active_tasks[task_key]
        print(f"✅ Задача остановлена: {task_key}")

async def run_flooder_task(chat_id: str, task_id: str, task_data: Dict):
    task_key = f"{chat_id}_{task_id}"
    
    if task_key in active_tasks:
        active_tasks[task_key].cancel()
    
    async def flooder_loop():
        try:
            text_file_path = f"config/{task_data['text_file']}"
            if os.path.exists(text_file_path):
                async with aiofiles.open(text_file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    messages = [msg.strip() for msg in content.split('\n') if msg.strip()]
            else:
                print(f"❌ Файл не найден: {text_file_path}")
                return
            
            media_file_path = f"config/{task_data['media_file']}" if task_data['media_file'] else None
            
            while True:
                flooder_tasks = load_flooder_tasks()
                current_task = flooder_tasks.get(chat_id, {}).get(task_id)
                
                if not current_task or not current_task.get('active', True):
                    print(f"❌ Задача остановлена: {task_key}")
                    break
                
                message_text = task_data['prefix'] + ' ' + random.choice(messages) if task_data['prefix'] else random.choice(messages)
                
                try:
                    if task_data['media_file'] and media_file_path and os.path.exists(media_file_path):
                        if task_data['media_file'].lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                            await app.send_photo(chat_id, media_file_path, caption=message_text)
                        elif task_data['media_file'].lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                            await app.send_video(chat_id, media_file_path, caption=message_text)
                        else:
                            await app.send_document(chat_id, media_file_path, caption=message_text)
                    else:
                        await app.send_message(chat_id, message_text)
                    
                    await asyncio.sleep(task_data['delay'])
                    
                except Exception as e:
                    print(f"❌ Ошибка отправки: {e}")
                    await asyncio.sleep(10)
                    
        except asyncio.CancelledError:
            print(f"✅ Задача отменена: {task_key}")
            raise
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            await asyncio.sleep(5)
            if task_key in active_tasks:
                active_tasks[task_key] = asyncio.create_task(flooder_loop())
    
    active_tasks[task_key] = asyncio.create_task(flooder_loop())
    print(f"✅ Задача запущена: {task_key}")

async def start_all_flooder_tasks():
    flooder_tasks = load_flooder_tasks()
    for chat_id, tasks in flooder_tasks.items():
        for task_id, task_data in tasks.items():
            if task_data.get('active', True):
                await run_flooder_task(chat_id, task_id, task_data)

@lru_cache(maxsize=100)
def load_chats() -> Dict:
    os.makedirs('config', exist_ok=True)
    if os.path.exists('config/chats.json'):
        try:
            with open('config/chats.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_chats(chats_data: Dict):
    os.makedirs('config', exist_ok=True)
    with open('config/chats.json', 'w', encoding='utf-8') as f:
        json.dump(chats_data, f, ensure_ascii=False, indent=4)

@app.on_message(filters.group & filters.new_chat_members)
async def on_bot_added_to_group(client: Client, message: Message):
    me = await client.get_me()
    for new_member in message.new_chat_members:
        if new_member.id == me.id:
            chat = message.chat
            chats_data = load_chats()
            chats_data[str(chat.id)] = {
                'title': chat.title,
                'type': str(chat.type),
                'username': chat.username,
                'added_date': message.date.isoformat(),
                'is_active': True
            }
            save_chats(chats_data)

@app.on_message(filters.group & filters.left_chat_member)
async def on_bot_removed_from_group(client: Client, message: Message):
    me = await client.get_me()
    if message.left_chat_member and message.left_chat_member.id == me.id:
        chat = message.chat
        chats_data = load_chats()
        if str(chat.id) in chats_data:
            chats_data[str(chat.id)]['is_active'] = False
            save_chats(chats_data)

@app.on_message(filters.group)
async def optimized_group_handler(client: Client, message: Message):
    try:
        chat = message.chat
        chats_data = load_chats()
        chat_key = str(chat.id)
        
        if chat_key not in chats_data or chats_data[chat_key]['title'] != chat.title:
            chats_data[chat_key] = {
                'title': chat.title,
                'type': str(chat.type),
                'username': chat.username,
                'added_date': message.date.isoformat(),
                'is_active': True
            }
            save_chats(chats_data)
        
        targets = load_respond_targets()
        if not targets:
            return
        
        chat_id_str = chat_key
        user_id_str = str(message.from_user.id)
        
        if chat_id_str in targets or user_id_str in targets:
            phrases_content = await async_cached_read('Phrases/messages.txt')
            if phrases_content:
                phrases = [line.strip() for line in phrases_content.split('\n') if line.strip()]
                if phrases:
                    response_text = random.choice(phrases)
                    asyncio.create_task(message.reply(response_text))
                    
    except Exception as e:
        print(f"❌ Ошибка обработки: {e}")

async def show_chats_menu(message: Message, page: int = 0):
    chats_data = load_chats()
    if not chats_data:
        await message.reply("📋 Нет чатов")
        return
    
    active_chats = {chat_id: info for chat_id, info in chats_data.items() if info.get('is_active', True)}
    if not active_chats:
        await message.reply("📋 Нет активных чатов")
        return
    
    sorted_chats = sorted(active_chats.items(), key=lambda x: x[1]['title'])
    items_per_page = 5
    total_pages = math.ceil(len(sorted_chats) / items_per_page)
    
    if page >= total_pages: page = total_pages - 1
    if page < 0: page = 0
    
    start_idx = page * items_per_page
    end_idx = start_idx + items_per_page
    current_chats = sorted_chats[start_idx:end_idx]
    
    keyboard = []
    for chat_id, chat_info in current_chats:
        chat_title = chat_info['title'][:30] + "..." if len(chat_info['title']) > 30 else chat_info['title']
        keyboard.append([InlineKeyboardButton(chat_title, callback_data=f"chat_select|{chat_id}|{page}")])
    
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"chat_page|{page-1}"))
    if page < total_pages - 1:
        pagination_buttons.append(InlineKeyboardButton("Вперед ➡️", callback_data=f"chat_page|{page+1}"))
    
    if pagination_buttons:
        keyboard.append(pagination_buttons)
    
    keyboard.append([InlineKeyboardButton("🔄 Обновить", callback_data=f"chat_refresh|{page}")])
    
    await message.reply(
        f"📋 Управление чатами (Страница {page + 1}/{total_pages})\n\nВыберите чат:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@app.on_message(filters.command("chats"))
async def chats_command(client: Client, message: Message):
    await show_chats_menu(message)

@app.on_callback_query(filters.regex(r"^chat_page\|"))
async def chats_pagination_handler(client: Client, callback_query: CallbackQuery):
    page = int(callback_query.data.split('|')[1])
    await callback_query.message.delete()
    await show_chats_menu(callback_query.message, page)
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^chat_refresh\|"))
async def chats_refresh_handler(client: Client, callback_query: CallbackQuery):
    page = int(callback_query.data.split('|')[1])
    await callback_query.message.delete()
    await show_chats_menu(callback_query.message, page)
    await callback_query.answer("✅ Обновлено")

@app.on_callback_query(filters.regex(r"^chat_select\|"))
async def chat_select_handler(client: Client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split('|')
    chat_id = data_parts[1]
    page = int(data_parts[2])
    
    chats_data = load_chats()
    chat_info = chats_data.get(chat_id)
    if not chat_info:
        await callback_query.answer("❌ Чат не найден")
        return
    
    flooder_tasks = load_flooder_tasks()
    chat_tasks = flooder_tasks.get(chat_id, {})
    
    tasks_text = "📋 Активные задачи:\n"
    if chat_tasks:
        for task_id, task_data in chat_tasks.items():
            status = "✅ ВКЛ" if task_data.get('active', True) else "❌ ВЫКЛ"
            tasks_text += f"\n🔹 {task_id}: {status} ({task_data['delay']}сек)"
    else:
        tasks_text += "\n❌ Нет задач"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Создать задание", callback_data=f"create_task|{chat_id}")],
        [InlineKeyboardButton("⚙️ Редактировать", callback_data=f"edit_tasks|{chat_id}|{page}")],
        [InlineKeyboardButton("◀️ Назад", callback_data=f"back_to_chats|{page}")]
    ])
    
    await callback_query.message.edit_text(
        f"💬 Управление чатом: {chat_info['title']}\n\n{tasks_text}\n\n📍 ID: {chat_id}",
        reply_markup=keyboard
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^create_task\|"))
async def create_task_step1(client: Client, callback_query: CallbackQuery):
    chat_id = callback_query.data.split('|')[1]
    
    user_data_storage[callback_query.from_user.id] = {
        'state': "waiting_delay",
        'chat_id': chat_id
    }
    
    await callback_query.message.edit_text(
        "⏰ Введите задержку в секундах:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel_task")]])
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^cancel_task"))
async def cancel_task(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id in user_data_storage:
        del user_data_storage[callback_query.from_user.id]
    await callback_query.message.edit_text("❌ Отменено")
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^back_to_chats\|"))
async def back_to_chats_handler(client: Client, callback_query: CallbackQuery):
    page = int(callback_query.data.split('|')[1])
    await callback_query.message.delete()
    await show_chats_menu(callback_query.message, page)
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^textfile\|"))
async def create_task_step4(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in user_data_storage:
        await callback_query.answer("❌ Сессия истекла")
        return
        
    text_file = callback_query.data.split('|', 1)[1]
    user_data = user_data_storage[callback_query.from_user.id]
    user_data['text_file'] = text_file
    user_data['state'] = "waiting_media_file"
    user_data_storage[callback_query.from_user.id] = user_data
    
    media_files = []
    if os.path.exists('config'):
        for file in os.listdir('config'):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.mov', '.mkv')):
                media_files.append(file)
    
    keyboard = [
        [InlineKeyboardButton("🚫 Без медиа", callback_data="media|none")]
    ]
    
    for file in media_files:
        keyboard.append([InlineKeyboardButton(f"📁 {file}", callback_data=f"media|{file}")])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_task")])
    
    await callback_query.message.edit_text("🎬 Выберите медиа:", reply_markup=InlineKeyboardMarkup(keyboard))
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^media\|"))
async def create_task_final(client: Client, callback_query: CallbackQuery):
    if callback_query.from_user.id not in user_data_storage:
        await callback_query.answer("❌ Сессия истекла")
        return
        
    media_data = callback_query.data.split('|', 1)[1]
    media_file = None if media_data == 'none' else media_data
    
    user_data = user_data_storage[callback_query.from_user.id]
    
    task_id = f"task_{int(time.time())}"
    flooder_tasks = load_flooder_tasks()
    chat_id = user_data['chat_id']
    
    if chat_id not in flooder_tasks:
        flooder_tasks[chat_id] = {}
    
    flooder_tasks[chat_id][task_id] = {
        'delay': user_data['delay'],
        'prefix': user_data['prefix'],
        'text_file': user_data['text_file'],
        'media_file': media_file,
        'active': True
    }
    
    save_flooder_tasks(flooder_tasks)
    await run_flooder_task(chat_id, task_id, flooder_tasks[chat_id][task_id])
    
    del user_data_storage[callback_query.from_user.id]
    
    await callback_query.message.edit_text(
        f"✅ Задача создана!\n\nID: {task_id}\nЗадержка: {user_data['delay']}сек\n"
        f"Префикс: {user_data['prefix'] or 'Нет'}\nФайл: {user_data['text_file']}\n"
        f"Медиа: {media_file or 'Нет'}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data=f"chat_select|{chat_id}|0")]
        ])
    )
    await callback_query.answer()

# Остальные обработчики callback (edit_tasks, task_manage, task_toggle, task_delay_edit, task_prefix_edit, 
# task_textfile, edit_textfile, task_media, edit_media, task_delete, confirm_delete) остаются аналогичными
# но с использованием асинхронных операций и кэширования

# Оптимизированные обработчики мульти-спама
@app.on_callback_query(filters.regex(r"^multi_add_token$"))
async def multi_add_token_handler(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_data_storage[user_id] = {'state': "waiting_multi_tokens"}
    
    await callback_query.message.edit_text(
        "🔑 Пришлите токены ботов (каждый с новой строки):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="multi_cancel")]])
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^multi_list_tokens$"))
async def multi_list_tokens_handler(client: Client, callback_query: CallbackQuery):
    tokens = load_tokens()
    if not tokens:
        await callback_query.answer("❌ Нет токенов")
        return
    
    tokens_text = "🔑 Список токенов:\n\n"
    for i, token in enumerate(tokens, 1):
        tokens_text += f"{i}. {token[:10]}...{token[-10:]}\n"
    
    await callback_query.message.edit_text(
        tokens_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="multi_back_to_main")]])
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^multi_add$"))
async def multi_add_handler(client: Client, callback_query: CallbackQuery):
    await callback_query.message.delete()
    await show_multi_chats_menu(callback_query.message)
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^multi_chat_page\|"))
async def multi_chat_page_handler(client: Client, callback_query: CallbackQuery):
    page = int(callback_query.data.split('|')[1])
    await callback_query.message.delete()
    await show_multi_chats_menu(callback_query.message, page)
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^multi_chat_select\|"))
async def multi_chat_select_handler(client: Client, callback_query: CallbackQuery):
    data_parts = callback_query.data.split('|')
    chat_id = data_parts[1]
    page = int(data_parts[2])
    
    chats_data = load_chats()
    chat_info = chats_data.get(chat_id)
    
    if not chat_info:
        await callback_query.answer("❌ Чат не найден")
        return
    
    user_id = callback_query.from_user.id
    user_data_storage[user_id] = {
        'state': "waiting_multi_delay",
        'chat_id': chat_id,
        'page': page
    }
    
    await callback_query.message.edit_text(
        f"⏰ Введите задержку в секундах для чата {chat_info['title']}:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="multi_cancel")]])
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^show_respond_targets$"))
async def show_respond_targets_handler(client: Client, callback_query: CallbackQuery):
    targets = load_respond_targets()
    
    if not targets:
        await callback_query.message.edit_text("📊 Список целей автоответчика пуст")
        await callback_query.answer()
        return
    
    targets_text = "📊 Цели автоответчика:\n\n"
    for target_id, target_info in targets.items():
        name = target_info.get('name', f'Цель {target_id}')
        targets_text += f"• {name} (ID: {target_id})\n"
    
    await callback_query.message.edit_text(
        targets_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_respond_menu")]
        ])
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^back_to_respond_menu$"))
async def back_to_respond_menu_handler(client: Client, callback_query: CallbackQuery):
    targets = load_respond_targets()
    targets_count = len(targets)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Добавить цель", callback_data="add_respond"),
         InlineKeyboardButton('❌ Удалить цель', callback_data='delete_respond')],
        [InlineKeyboardButton("📊 Показать цели", callback_data="show_respond_targets")]
    ])
    
    await callback_query.message.edit_text(
        f"🌘 Автоответчик - управление\n\n📊 Активных целей: {targets_count}\n\nВыберите действие:",
        reply_markup=keyboard
    )
    await callback_query.answer()

# Кэшированное чтение файлов
@lru_cache(maxsize=100)
def cached_read_file(file_path: str):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

async def async_cached_read(file_path: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, cached_read_file, file_path)

# Мониторинг задач
async def task_monitor():
    while True:
        try:
            await asyncio.sleep(30)
            
            multi_tasks = load_multi_tasks()
            for chat_id, task_data in multi_tasks.items():
                task_key = f"multi_{chat_id}"
                if task_data.get('active', True) and task_key not in active_tasks:
                    print(f"🔄 Восстанавливаем задачу: {task_key}")
                    await run_multi_task_optimized(chat_id, task_data)
            
            flooder_tasks = load_flooder_tasks()
            for chat_id, tasks in flooder_tasks.items():
                for task_id, task_data in tasks.items():
                    task_key = f"{chat_id}_{task_id}"
                    if task_data.get('active', True) and task_key not in active_tasks:
                        print(f"🔄 Восстанавливаем задачу: {task_key}")
                        await run_flooder_task(chat_id, task_id, task_data)
                        
        except Exception as e:
            print(f"❌ Ошибка монитора: {e}")
            await asyncio.sleep(60)

# ОБНОВЛЕННЫЙ ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ
@app.on_message(filters.all & filters.private & filters.text & ~filters.command("start") & ~filters.command("chats"))
async def handle_all_text_messages(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id in user_data_storage:
        user_data = user_data_storage[user_id]
        state = user_data.get('state')
        
        if state == "waiting_edit_delay":
            try:
                delay = int(message.text)
                if delay < 1:
                    await message.reply("❌ Минимум 1 секунда")
                    return
                
                flooder_tasks = load_flooder_tasks()
                chat_id = user_data['chat_id']
                task_id = user_data['task_id']
                
                if chat_id in flooder_tasks and task_id in flooder_tasks[chat_id]:
                    await stop_flooder_task(chat_id, task_id)
                    
                    flooder_tasks[chat_id][task_id]['delay'] = delay
                    save_flooder_tasks(flooder_tasks)
                    
                    if flooder_tasks[chat_id][task_id].get('active', True):
                        await run_flooder_task(chat_id, task_id, flooder_tasks[chat_id][task_id])
                    
                    await message.reply("✅ Задержка изменена")
                    del user_data_storage[user_id]
                    
                    callback_data = f"task_manage|{chat_id}|{task_id}|{user_data['page']}"
                    callback_query = type('obj', (object,), {
                        'data': callback_data,
                        'message': message,
                        'from_user': message.from_user
                    })()
                    await task_manage_handler(client, callback_query)
                else:
                    await message.reply("❌ Задача не найдена")
                    del user_data_storage[user_id]
                    
            except ValueError:
                await message.reply("❌ Введите число")
        
        elif state == "waiting_edit_prefix":
            prefix = message.text if message.text.lower() != 'нет' else ''
            
            flooder_tasks = load_flooder_tasks()
            chat_id = user_data['chat_id']
            task_id = user_data['task_id']
            
            if chat_id in flooder_tasks and task_id in flooder_tasks[chat_id]:
                await stop_flooder_task(chat_id, task_id)
                
                flooder_tasks[chat_id][task_id]['prefix'] = prefix
                save_flooder_tasks(flooder_tasks)
                
                if flooder_tasks[chat_id][task_id].get('active', True):
                    await run_flooder_task(chat_id, task_id, flooder_tasks[chat_id][task_id])
                
                await message.reply("✅ Префикс изменен")
                del user_data_storage[user_id]
                
                callback_data = f"task_manage|{chat_id}|{task_id}|{user_data['page']}"
                callback_query = type('obj', (object,), {
                    'data': callback_data,
                    'message': message,
                    'from_user': message.from_user
                })()
                await task_manage_handler(client, callback_query)
            else:
                await message.reply("❌ Задача не найдена")
                del user_data_storage[user_id]
        
        elif state == "waiting_delay":
            try:
                delay = int(message.text)
                if delay < 1:
                    await message.reply("❌ Минимум 1 секунда")
                    return
                    
                user_data['delay'] = delay
                user_data['state'] = "waiting_prefix"
                user_data_storage[user_id] = user_data
                
                await message.reply(
                    "📝 Введите префикс (или 'Нет'):",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel_task")]])
                )
                
            except ValueError:
                await message.reply("❌ Введите число")

        elif state == "waiting_add_respond_target":
             try:
                 target_id = message.text.strip()
                 targets = load_respond_targets()
                 
                 if target_id in targets:
                     await message.reply("❌ Этот ID уже есть в списке автоответчика")
                 else:
                     targets[target_id] = {
                         'name': f'Цель {target_id}',
                         'added_date': time.time(),
                         'added_by': user_id
                     }
                     save_respond_targets(targets)
                     await message.reply(f"✅ Цель добавлена: ID {target_id}")
                 
                 del user_data_storage[user_id]
                 
             except Exception as e:
                 await message.reply(f"❌ Ошибка: {e}")
                 del user_data_storage[user_id]

        elif state == "waiting_delete_respond_target":
            try:
                target_id = message.text.strip()
                targets = load_respond_targets()
                
                if target_id in targets:
                    del targets[target_id]
                    save_respond_targets(targets)
                    await message.reply(f"✅ Цель удалена: ID {target_id}")
                else:
                    await message.reply("❌ Этот ID не найден в списке автоответчика")
                
                del user_data_storage[user_id]
                
            except Exception as e:
                 await message.reply(f"❌ Ошибка: {e}")
                 del user_data_storage[user_id]       
        
        elif state == "waiting_prefix":
            prefix = message.text if message.text.lower() != 'нет' else ''
            user_data['prefix'] = prefix
            user_data['state'] = "waiting_text_file"
            user_data_storage[user_id] = user_data
            
            txt_files = []
            if os.path.exists('config'):
                for file in os.listdir('config'):
                    if file.endswith('.txt'):
                        txt_files.append(file)
            
            if not txt_files:
                await message.reply("❌ Нет txt файлов")
                del user_data_storage[user_id]
                return
            
            keyboard = []
            for file in txt_files:
                keyboard.append([InlineKeyboardButton(f"📄 {file}", callback_data=f"textfile|{file}")])
            
            keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_task")])
            
            await message.reply("📁 Выберите файл:", reply_markup=InlineKeyboardMarkup(keyboard))
        elif state == "waiting_multi_tokens":
             tokens = load_tokens()
             new_tokens = [token.strip() for token in message.text.split('\n') if token.strip()]
             
             added_count = 0
             for token in new_tokens:
                 if token not in tokens:
                     tokens.append(token)
                     added_count += 1
             
             save_tokens(tokens)
             await message.reply(f"✅ Добавлено {added_count} новых токенов. Всего: {len(tokens)}")
             del user_data_storage[user_id]
        
        elif state == "waiting_admin_id":
            try:
                new_admin_id = message.text.strip()
                
                if not new_admin_id.isdigit():
                    await message.reply("❌ ID должен содержать только цифры")
                    return
                
                admins_file = 'config/admins.json'
                if os.path.exists(admins_file):
                    with open(admins_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    data = {"admins": []}
                
                if new_admin_id in data["admins"]:
                    await message.reply("❌ Этот пользователь уже является администратором")
                    del user_data_storage[user_id]
                    return
                
                data["admins"].append(new_admin_id)
                
                with open(admins_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                
                await message.reply(f"✅ Пользователь {new_admin_id} добавлен в администраторы")
                del user_data_storage[user_id]
                
            except Exception as e:
                await message.reply(f"❌ Ошибка при добавлении администратора: {e}")
                if user_id in user_data_storage:
                    del user_data_storage[user_id]

        elif state == "waiting_multi_delay":
            try:
                delay = int(message.text)
                if delay < 1:
                    await message.reply("❌ Минимум 1 секунда")
                    return
                    
                user_data = user_data_storage[user_id]
                user_data['delay'] = delay
                user_data['state'] = "waiting_multi_prefix"
                user_data_storage[user_id] = user_data
                
                await message.reply("📝 Введите префикс (или 'Нет'):")
                
            except ValueError:
                await message.reply("❌ Введите число")
        
        elif state == "waiting_multi_prefix":
              prefix = message.text if message.text.lower() != 'нет' else ''
              user_data = user_data_storage[user_id]
              user_data['prefix'] = prefix
              user_data['state'] = "waiting_multi_text_file"
              user_data_storage[user_id] = user_data
              
              # Показываем список txt файлов
              txt_files = []
              if os.path.exists('config'):
                  for file in os.listdir('config'):
                      if file.endswith('.txt'):
                          txt_files.append(file)
              
              if not txt_files:
                  await message.reply("❌ Нет txt файлов")
                  del user_data_storage[user_id]
                  return
              
              keyboard = []
              for file in txt_files:
                  keyboard.append([InlineKeyboardButton(f"📄 {file}", callback_data=f"multi_textfile|{file}")])
              
              keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="multi_cancel")])
              
              await message.reply("📁 Выберите текстовый файл:", reply_markup=InlineKeyboardMarkup(keyboard))
        
        else:
            del user_data_storage[user_id]
            await handle_main_menu(client, message)
    else:
        await handle_main_menu(client, message)










@app.on_callback_query(filters.regex(r"^add_admin$"))
async def add_admin_handler(client: Client, callback_query: CallbackQuery):
    """Начинает процесс добавления админа"""
    user_id = callback_query.from_user.id
    
    # Проверяем права текущего пользователя
    is_admin = await chek_admin(user_id)
    if not is_admin:
        await callback_query.answer("❌ У вас нет прав администратора")
        return
    
    # Сохраняем состояние для добавления админа
    user_data_storage[user_id] = {
        'state': "waiting_admin_id"
    }
    
    await callback_query.message.edit_text(
        "👑 Добавление администратора\n\n"
        "Введите ID пользователя, которого хотите сделать администратором:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Отмена", callback_data="cancel_add_admin")]
        ])
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^cancel_add_admin$"))
async def cancel_add_admin_handler(client: Client, callback_query: CallbackQuery):
    """Отмена добавления админа"""
    user_id = callback_query.from_user.id
    if user_id in user_data_storage:
        del user_data_storage[user_id]
    
    await callback_query.message.edit_text("❌ Добавление администратора отменено")
    await callback_query.answer()



@app.on_callback_query(filters.regex(r"^remove_admin$"))
async def remove_admin_handler(client: Client, callback_query: CallbackQuery):
    """Начинает процесс удаления админа"""
    user_id = callback_query.from_user.id
    
    # Проверяем права текущего пользователя
    is_admin = await chek_admin(user_id)
    if not is_admin:
        await callback_query.answer("❌ У вас нет прав администратора")
        return
    
    # Загружаем список админов для отображения
    admins_file = 'config/admins.json'
    if os.path.exists(admins_file):
        with open(admins_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        admins_list = data["admins"]
    else:
        admins_list = []
    
    if not admins_list:
        await callback_query.answer("❌ Нет администраторов для удаления")
        return
    
    # Создаем клавиатуру с админами для удаления
    keyboard = []
    for admin_id in admins_list:
        keyboard.append([InlineKeyboardButton(f"❌ Удалить {admin_id}", callback_data=f"remove_admin_confirm|{admin_id}")])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_remove_admin")])
    
    await callback_query.message.edit_text(
        "👑 Удаление администратора\n\n"
        "Выберите администратора для удаления:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^remove_admin_confirm\|"))
async def remove_admin_confirm_handler(client: Client, callback_query: CallbackQuery):
    """Подтверждение удаления админа"""
    admin_id_to_remove = callback_query.data.split('|')[1]
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, удалить", callback_data=f"remove_admin_final|{admin_id_to_remove}")],
        [InlineKeyboardButton("❌ Нет, отмена", callback_data="remove_admin")]
    ])
    
    await callback_query.message.edit_text(
        f"⚠️ Вы уверены, что хотите удалить администратора {admin_id_to_remove}?",
        reply_markup=keyboard
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^remove_admin_final\|"))
async def remove_admin_final_handler(client: Client, callback_query: CallbackQuery):
    """Финальное удаление админа"""
    admin_id_to_remove = callback_query.data.split('|')[1]
    
    try:
        # Загружаем текущий список админов
        admins_file = 'config/admins.json'
        if os.path.exists(admins_file):
            with open(admins_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Удаляем админа
            if admin_id_to_remove in data["admins"]:
                data["admins"].remove(admin_id_to_remove)
                
                # Сохраняем обновленный список
                with open(admins_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                
                await callback_query.answer(f"✅ Администратор {admin_id_to_remove} удален")
            else:
                await callback_query.answer("❌ Администратор не найден")
        else:
            await callback_query.answer("❌ Файл админов не найден")
    
    except Exception as e:
        await callback_query.answer(f"❌ Ошибка при удалении: {e}")
    
    # Возвращаемся к списку админов
    callback_query.data = "remove_admin"
    await remove_admin_handler(client, callback_query)


@app.on_message(filters.private & (filters.photo | filters.document | filters.video | filters.audio))
async def save_media_to_config(client: Client, message: Message):
    """Сохраняет медиафайлы в папку config"""
    result = await chek_admin(message.from_user.id)
    if not result:
        await message.reply("❌ Нет прав для сохранения файлов")
        return
    
    try:
        # Создаем папку config если нет
        os.makedirs('config', exist_ok=True)
        
        if message.photo:
            # Фото
            file_name = f"photo_{message.id}.jpg"
            file_path = f"config/{file_name}"
            await message.download(file_name=file_path)
            await message.reply(f"✅ Фото сохранено: {file_name}")
            
        elif message.document:
            # Документы
            file_name = message.document.file_name or f"document_{message.id}"
            file_path = f"config/{file_name}"
            await message.download(file_name=file_path)
            await message.reply(f"✅ Документ сохранен: {file_name}")
            
        elif message.video:
            # Видео
            file_name = message.video.file_name or f"video_{message.id}.mp4"
            file_path = f"config/{file_name}"
            await message.download(file_name=file_path)
            await message.reply(f"✅ Видео сохранено: {file_name}")
            
        elif message.audio:
            # Аудио
            file_name = message.audio.file_name or f"audio_{message.id}.mp3"
            file_path = f"config/{file_name}"
            await message.download(file_name=file_path)
            await message.reply(f"✅ Аудио сохранено: {file_name}")
            
    except Exception as e:
        await message.reply(f"❌ Ошибка сохранения: {e}")
        print(f"Ошибка сохранения файла: {e}")


async def main_optimized():
    # Инициализация aiohttp сессии
    await create_aiohttp_session()
    
    await app.start()
    print("✅ Бот запущен")
    
    asyncio.create_task(task_monitor())
    
    await start_all_flooder_tasks()
    print("✅ Задачи активированы")
    
    multi_tasks = load_multi_tasks()
    for chat_id, task_data in multi_tasks.items():
        if task_data.get('active', True):
            await run_multi_task_optimized(chat_id, task_data)
    
    print("✅ Мульти-задачи запущены")
    
    try:
        await idle()
    finally:
        # Корректное завершение
        await close_aiohttp_session()
        
        # Останавливаем все задачи
        for task in active_tasks.values():
            task.cancel()
        
        await asyncio.gather(*active_tasks.values(), return_exceptions=True)
        thread_pool.shutdown(wait=True)
        print("✅ Ресурсы освобождены")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    try:
        app.run(main_optimized())
    except KeyboardInterrupt:
        print("👋 Корректное завершение")
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        os.execv(sys.executable, [sys.executable] + sys.argv)










