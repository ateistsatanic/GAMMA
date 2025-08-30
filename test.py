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
import concurrent.futures
from functools import partial
import asyncio
import aiofiles
import requests
from typing import Dict, List

# Конфигурация
token_log = '8390503590:AAGs_U7Bgi4YNqf1gN8fXwT8tKmvHFgxHMY'
chat_id_log = '-1002736899389'

with open('config/TOKEN.txt', 'r', encoding='utf-8') as f:
    API_TOKEN = f.readline().strip()

# Глобальные переменные
user_data_storage = {}
active_tasks = {}  # Храним активные задачи для возможности их остановки

app = Client("gamma_bot", bot_token=API_TOKEN, parse_mode=ParseMode.HTML)

# Добавляем в начало файла
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

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


# Обработчик главного меню
async def handle_main_menu(client: Client, message: Message):
    if message.text == '🌕 Флудер':
        result = await chek_admin(message.from_user.id)
        if not result:
            await message.reply("❌ Нет прав")
            return
        
        # Показываем меню флудера с кнопкой управления чатами
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
                
                await asyncio.sleep(1)
            except Exception as e:
                await message.reply(f"❌ Ошибка {filename}: {e}")
        
        await message.reply("✅ Все файлы отправлены!")
    
    elif message.text == '🌑 FAQ':
        await message.reply("📚 Гайд: https://teletype.in/@ksenod/6xaHYfronsG")
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
        
        # Показываем меню мульти-спама
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


# ОБРАБОТЧИК ГЛАВНОГО МЕНЮ (должен быть выше в коде!)
@app.on_message(filters.private & filters.text & ~filters.command("start") & ~filters.command("chats"))
async def handle_main_menu_messages(client: Client, message: Message):
    """Обработчик главного меню для личных сообщений"""
    user_id = message.from_user.id
    
    # Сначала проверяем кнопки главного меню
    if message.text in ['🌕 Флудер', '🌗 Файлы', '🌘 Автоответчик', '🌔 Мульти', '🌑 FAQ']:
        await handle_main_menu(client, message)
        return
    
    # Если пользователь в состоянии (вводит данные для какой-то операции)
    if user_id in user_data_storage:
        # Передаем обработку в общий обработчик
        await handle_all_text_messages(client, message)
    else:
        # Если не кнопка меню и не состояние - игнорируем
        pass

@app.on_message(filters.private & filters.text & ~filters.me)
async def auto_responder_private_handler(client: Client, message: Message):
    """Обработчик автоответчика для личных сообщений"""
    try:
        print(f"🔍 ЛИЧНОЕ: сообщение от {message.from_user.id}")
        
        targets = load_respond_targets()
        if not targets:
            return
            
        user_id_str = str(message.from_user.id)
        
        if user_id_str in targets:
            phrases_file = 'Phrases/messages.txt'
            if os.path.exists(phrases_file):
                try:
                    with open(phrases_file, 'r', encoding='utf-8') as f:
                        phrases = [line.strip() for line in f.read().split('\n') if line.strip()]
                    
                    if phrases:
                        response_text = random.choice(phrases)
                        await message.reply(response_text)
                except Exception as e:
                    print(f"❌ Ошибка чтения фраз: {e}")
            
    except Exception as e:
        print(f"❌ Ошибка личного автоответчика: {e}")



@app.on_callback_query(filters.regex(r"^multi_delete$"))
async def multi_delete_handler(client: Client, callback_query: CallbackQuery):
    """Удаление мульти-спама"""
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
    """Подтверждение удаления мульти-спама"""
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
    """Финальное удаление мульти-спама"""
    chat_id = callback_query.data.split('|')[1]
    
    multi_tasks = load_multi_tasks()
    
    if chat_id in multi_tasks:
        # Останавливаем задачу
        task_key = f"multi_{chat_id}"
        if task_key in active_tasks:
            active_tasks[task_key].cancel()
            del active_tasks[task_key]
        
        # Удаляем из конфига
        del multi_tasks[chat_id]
        save_multi_tasks(multi_tasks)
        await callback_query.answer("✅ Задача удалена")
    else:
        await callback_query.answer("❌ Задача не найдена")
    
    # Возвращаемся к списку задач
    callback_query.data = "multi_delete"
    await multi_delete_handler(client, callback_query)

# Вспомогательные функции
async def send_telegram_message(message_text: str):
    try:
        async with Client("logger", bot_token=token_log) as logger:
            await logger.send_message(chat_id_log, message_text)
        print(f"Сообщение отправлено: {message_text}")
    except Exception as e:
        print(f"Ошибка отправки: {e}")

async def chek_admin(user_id: int) -> bool:
    try:
        # Создаем папку config если ее нет
        os.makedirs('config', exist_ok=True)
        
        # Путь к файлу
        admins_file = 'config/admins.json'
        
        # Если файла нет, создаем его с пустым списком
        if not os.path.exists(admins_file):
            with open(admins_file, 'w', encoding='utf-8') as f:
                json.dump({"admins": []}, f, ensure_ascii=False, indent=4)
            return False
        
        # Читаем файл
        with open(admins_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Проверяем есть ли пользователь в списке админов
        return str(user_id) in data.get("admins", [])
        
    except Exception as e:
        print(f"❌ Ошибка проверки админа: {e}")
        return False
    

def load_tokens() -> List[str]:
    """Загружает токены из файла"""
    os.makedirs('config', exist_ok=True)
    if os.path.exists('config/tokens.json'):
        try:
            with open('config/tokens.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_tokens(tokens: List[str]):
    """Сохраняет токены в файл"""
    os.makedirs('config', exist_ok=True)
    with open('config/tokens.json', 'w', encoding='utf-8') as f:
        json.dump(tokens, f, ensure_ascii=False, indent=4)

def load_multi_tasks() -> Dict:
    """Загружает задачи мульти-спама"""
    os.makedirs('config', exist_ok=True)
    if os.path.exists('config/multi.json'):
        try:
            with open('config/multi.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_multi_tasks(tasks: Dict):
    """Сохраняет задачи мульти-спама"""
    os.makedirs('config', exist_ok=True)
    with open('config/multi.json', 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

async def show_multi_chats_menu(message: Message, page: int = 0):
    """Показывает меню чатов для мульти-спама"""
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

async def send_multi_message(token: str, chat_id: str, text: str, media_path: str = None):
    """Отправляет сообщение через API Telegram"""
    try:
        if media_path and os.path.exists(media_path):
            # Определяем тип медиа
            if media_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                url = f"https://api.telegram.org/bot{token}/sendPhoto"
                files = {'photo': open(media_path, 'rb')}
                data = {'chat_id': chat_id, 'caption': text}
            elif media_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                url = f"https://api.telegram.org/bot{token}/sendVideo"
                files = {'video': open(media_path, 'rb')}
                data = {'chat_id': chat_id, 'caption': text}
            else:
                url = f"https://api.telegram.org/bot{token}/sendDocument"
                files = {'document': open(media_path, 'rb')}
                data = {'chat_id': chat_id, 'caption': text}
            
            response = requests.post(url, files=files, data=data)
        else:
            # Отправка текста
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {'chat_id': chat_id, 'text': text}
            response = requests.post(url, data=data)
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка отправки через token {token[:10]}...: {e}")
        return False


async def send_multi_message_async(token: str, chat_id: str, text: str, media_path: str = None):
    """Асинхронная отправка сообщения через пул потоков"""
    loop = asyncio.get_event_loop()
    
    # Создаем partial функцию для передачи в поток
    send_func = partial(send_multi_message_sync, token, chat_id, text, media_path)
    
    try:
        # Запускаем в отдельном потоке
        result = await loop.run_in_executor(thread_pool, send_func)
        return result
    except Exception as e:
        print(f"❌ Ошибка в потоке: {e}")
        return False

def send_multi_message_sync(token: str, chat_id: str, text: str, media_path: str = None):
    """Синхронная версия отправки сообщения (выполняется в отдельном потоке)"""
    try:
        if media_path and os.path.exists(media_path):
            # Определяем тип медиа
            if media_path.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                url = f"https://api.telegram.org/bot{token}/sendPhoto"
                files = {'photo': open(media_path, 'rb')}
                data = {'chat_id': chat_id, 'caption': text}
            elif media_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                url = f"https://api.telegram.org/bot{token}/sendVideo"
                files = {'video': open(media_path, 'rb')}
                data = {'chat_id': chat_id, 'caption': text}
            else:
                url = f"https://api.telegram.org/bot{token}/sendDocument"
                files = {'document': open(media_path, 'rb')}
                data = {'chat_id': chat_id, 'caption': text}
            
            response = requests.post(url, files=files, data=data, timeout=10)
        else:
            # Отправка текста
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {'chat_id': chat_id, 'text': text}
            response = requests.post(url, data=data, timeout=10)
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка отправки через token {token[:10]}...: {e}")
        return False
    finally:
        # Закрываем файлы если они были открыты
        if 'files' in locals():
            for file_obj in files.values():
                if hasattr(file_obj, 'close'):
                    file_obj.close()

async def run_multi_task(chat_id: str, task_data: Dict):
    """Запускает мульти-спам задание с оптимизацией"""
    task_key = f"multi_{chat_id}"
    
    async def multi_loop():
        try:
            tokens = load_tokens()
            if not tokens:
                print("❌ Нет токенов для мульти-спама")
                return
            
            text_file_path = f"config/{task_data['text_file']}"
            if os.path.exists(text_file_path):
                with open(text_file_path, 'r', encoding='utf-8') as f:
                    messages = [msg.strip() for msg in f.read().split('\n') if msg.strip()]
            else:
                print(f"❌ Файл не найден: {text_file_path}")
                return
            
            media_file_path = f"config/{task_data['media_file']}" if task_data['media_file'] else None
            
            while True:
                # Проверяем статус задачи
                multi_tasks = load_multi_tasks()
                current_task = multi_tasks.get(chat_id)
                
                if not current_task or not current_task.get('active', True):
                    print(f"❌ Мульти-задача остановлена: {chat_id}")
                    break
                
                message_text = task_data['prefix'] + ' ' + random.choice(messages) if task_data['prefix'] else random.choice(messages)
                
                # Создаем задачи для отправки через все токены
                send_tasks = []
                for token in tokens:
                    send_task = send_multi_message_async(token, chat_id, message_text, media_file_path)
                    send_tasks.append(send_task)
                
                # Запускаем все задачи параллельно
                results = await asyncio.gather(*send_tasks, return_exceptions=True)
                
                # Логируем результаты
                success_count = sum(1 for result in results if result is True)
                print(f"📤 Отправлено {success_count}/{len(tokens)} сообщений")
                
                await asyncio.sleep(task_data['delay'])
                
        except Exception as e:
            print(f"❌ Ошибка мульти-спама: {e}")
            await asyncio.sleep(10)
    
    # Запускаем задачу
    active_tasks[task_key] = asyncio.create_task(multi_loop())
    print(f"✅ Мульти-задача запущена: {task_key}")



async def run_multi_task(chat_id: str, task_data: Dict):
    """Запускает мульти-спам задание"""
    task_key = f"multi_{chat_id}"
    
    async def multi_loop():
        try:
            tokens = load_tokens()
            if not tokens:
                print("❌ Нет токенов для мульти-спама")
                return
            
            text_file_path = f"config/{task_data['text_file']}"
            if os.path.exists(text_file_path):
                with open(text_file_path, 'r', encoding='utf-8') as f:
                    messages = [msg.strip() for msg in f.read().split('\n') if msg.strip()]
            else:
                print(f"❌ Файл не найден: {text_file_path}")
                return
            
            media_file_path = f"config/{task_data['media_file']}" if task_data['media_file'] else None
            
            while True:
                # Проверяем статус задачи
                multi_tasks = load_multi_tasks()
                current_task = multi_tasks.get(chat_id)
                
                if not current_task or not current_task.get('active', True):
                    print(f"❌ Мульти-задача остановлена: {chat_id}")
                    break
                
                message_text = task_data['prefix'] + ' ' + random.choice(messages) if task_data['prefix'] else random.choice(messages)
                
                # Отправляем через все токены
                for token in tokens:
                    success = await send_multi_message(token, chat_id, message_text, media_file_path)
                    if success:
                        print(f"✅ Отправлено через токен: {token[:10]}...")
                    await asyncio.sleep(0.5)  # Небольшая задержка между токенами
                
                await asyncio.sleep(task_data['delay'])
                
        except Exception as e:
            print(f"❌ Ошибка мульти-спама: {e}")
            await asyncio.sleep(10)
    
    # Запускаем задачу
    active_tasks[task_key] = asyncio.create_task(multi_loop())
    print(f"✅ Мульти-задача запущена: {task_key}")



def load_respond_targets() -> Dict:
    """Загружает цели автоответчика из файла"""
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
    """Сохраняет цели автоответчика в файл"""
    os.makedirs('config', exist_ok=True)
    with open('config/resp.json', 'w', encoding='utf-8') as f:
        json.dump(targets, f, ensure_ascii=False, indent=4)

@app.on_callback_query(filters.regex(r"^add_respond$"))
async def add_respond_handler(client: Client, callback_query: CallbackQuery):
    """Обработчик добавления цели автоответчика"""
    user_id = callback_query.from_user.id
    
    # Сохраняем состояние для добавления цели
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
    """Обработчик удаления цели автоответчика"""
    user_id = callback_query.from_user.id
    
    # Сохраняем состояние для удаления цели
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
    """Отмена операции с автоответчиком"""
    if callback_query.from_user.id in user_data_storage:
        del user_data_storage[callback_query.from_user.id]
    await callback_query.message.edit_text("❌ Операция отменена")
    await callback_query.answer()
    

def load_flooder_tasks() -> Dict:
    os.makedirs('config', exist_ok=True)
    if os.path.exists('config/flooder.json'):
        try:
            with open('config/flooder.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_flooder_tasks(tasks: Dict):
    os.makedirs('config', exist_ok=True)
    with open('config/flooder.json', 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)


@app.on_callback_query(filters.regex(r"^flooder_chats$"))
async def flooder_chats_handler(client: Client, callback_query: CallbackQuery):
    """Обработчик кнопки '📋 Управление чатами' из меню флудера"""
    # Удаляем предыдущее сообщение и показываем меню чатов
    await callback_query.message.delete()
    await show_chats_menu(callback_query.message)
    await callback_query.answer()

async def stop_flooder_task(chat_id: str, task_id: str):
    """Останавливает задачу флудера"""
    task_key = f"{chat_id}_{task_id}"
    if task_key in active_tasks:
        active_tasks[task_key].cancel()
        del active_tasks[task_key]
        print(f"✅ Задача остановлена: {task_key}")

async def run_flooder_task(chat_id: str, task_id: str, task_data: Dict):
    """Запускает задачу флудера"""
    task_key = f"{chat_id}_{task_id}"
    
    # Останавливаем предыдущую задачу, если она есть
    if task_key in active_tasks:
        active_tasks[task_key].cancel()
    
    async def flooder_loop():
        try:
            text_file_path = f"config/{task_data['text_file']}"
            if os.path.exists(text_file_path):
                with open(text_file_path, 'r', encoding='utf-8') as f:
                    messages = [msg.strip() for msg in f.read().split('\n') if msg.strip()]
            else:
                print(f"❌ Файл не найден: {text_file_path}")
                return
            
            media_file_path = f"config/{task_data['media_file']}" if task_data['media_file'] else None
            
            while True:
                # Проверяем статус задачи в файле
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
            # Перезапускаем задачу при ошибке
            if task_key in active_tasks:
                active_tasks[task_key] = asyncio.create_task(flooder_loop())
    
    # Запускаем новую задачу
    active_tasks[task_key] = asyncio.create_task(flooder_loop())
    print(f"✅ Задача запущена: {task_key}")

async def start_all_flooder_tasks():
    flooder_tasks = load_flooder_tasks()
    for chat_id, tasks in flooder_tasks.items():
        for task_id, task_data in tasks.items():
            if task_data.get('active', True):
                await run_flooder_task(chat_id, task_id, task_data)

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

# Обработчики чатов
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
async def handle_group_messages(client: Client, message: Message):
    """Обработчик всех групповых сообщений"""
    # 1. Сначала обновляем информацию о чате
    chat = message.chat
    chats_data = load_chats()
    if str(chat.id) not in chats_data:
        chats_data[str(chat.id)] = {
            'title': chat.title,
            'type': str(chat.type),
            'username': chat.username,
            'added_date': message.date.isoformat(),
            'is_active': True
        }
    else:
        if chats_data[str(chat.id)]['title'] != chat.title:
            chats_data[str(chat.id)]['title'] = chat.title
            chats_data[str(chat.id)]['is_active'] = True
    save_chats(chats_data)
    
    # 2. Затем проверяем автоответчик (только если сообщение не от самого бота)
    try:
        me = await client.get_me()
        if message.from_user and message.from_user.id == me.id:
            return  # Пропускаем сообщения от самого бота
        
        print(f"🔍 ГРУППА: сообщение от {message.from_user.id} в чате {message.chat.id}")
        
        targets = load_respond_targets()
        if not targets:
            return
            
        chat_id_str = str(message.chat.id)
        user_id_str = str(message.from_user.id)
        
        # Проверяем ID чата или пользователя
        if chat_id_str in targets or user_id_str in targets:
            phrases_file = 'Phrases/messages.txt'
            if os.path.exists(phrases_file):
                try:
                    with open(phrases_file, 'r', encoding='utf-8') as f:
                        phrases = [line.strip() for line in f.read().split('\n') if line.strip()]
                    
                    if phrases:
                        response_text = random.choice(phrases)
                        await message.reply(response_text)
                        print(f"✅ Ответ отправлен в группе {message.chat.id}")
                except Exception as e:
                    print(f"❌ Ошибка чтения фраз: {e}")
            
    except Exception as e:
        print(f"❌ Ошибка группового автоответчика: {e}")

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

# ОБРАБОТЧИК СТАРТА С ФОТО
@app.on_message(filters.command("start"))
async def cmd_start(client: Client, message: Message):
        try:
            # Пробуем отправить с фото, если ошибка - отправляем без фото
            try:
                if os.path.exists('config/gamma.png'):
                    await message.reply_photo(
                        'config/gamma.png',
                        caption='G.A.M.M.A v1.0.0 - Управление через кнопки',
                        reply_markup=kb_rus
                    )
                else:
                    await message.reply(
                        'G.A.M.M.A v1.0.0 - Управление через кнопки',
                        reply_markup=kb_rus
                    )
            except Exception as photo_error:
                print(f"Ошибка отправки фото: {photo_error}")
                await message.reply(
                    'G.A.M.M.A v1.0.0 - Управление через кнопки\n\n'
                    '🌕 Флудер - управление флудером\n'
                    '🌗 Файлы - просмотр файлов\n'
                    '🌑 FAQ - справка',
                    reply_markup=kb_rus
                )
        except Exception as e:
            await message.reply(f'Ошибка: {e}')


# Обработчики callback для мульти-спама
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



@app.on_callback_query(filters.regex(r"^show_respond_targets$"))
async def show_respond_targets_handler(client: Client, callback_query: CallbackQuery):
    """Показывает список целей автоответчика"""
    targets = load_respond_targets()
    
    if not targets:
        await callback_query.message.edit_text("📊 Список целей автоответчика пуст")
        await callback_query.answer()
        return
    
    targets_text = "📊 Цели автоответчика:\n\n"
    for target_id, target_info in targets.items():
        # Безопасное получение имени, если оно есть
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
    """Возврат в меню автоответчика"""
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
    """Обработчик создания задачи (первый шаг - задержка)"""
    chat_id = callback_query.data.split('|')[1]
    
    # Сохраняем состояние для СОЗДАНИЯ задержки
    user_data_storage[callback_query.from_user.id] = {
        'state': "waiting_delay",  # Для создания
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

# РЕДАКТИРОВАНИЕ ЗАДАЧ
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
        # Останавливаем или запускаем задачу
        if flooder_tasks[chat_id][task_id].get('active', True):
            # Останавливаем
            await stop_flooder_task(chat_id, task_id)
            flooder_tasks[chat_id][task_id]['active'] = False
        else:
            # Запускаем
            flooder_tasks[chat_id][task_id]['active'] = True
            await run_flooder_task(chat_id, task_id, flooder_tasks[chat_id][task_id])
        
        save_flooder_tasks(flooder_tasks)
        await callback_query.answer("✅ Статус изменен")
        
        # Обновляем сообщение
        callback_query.data = f"task_manage|{chat_id}|{task_id}|{page}"
        await task_manage_handler(client, callback_query)
    else:
        await callback_query.answer("❌ Задача не найдена")

@app.on_callback_query(filters.regex(r"^task_delay\|"))
async def task_delay_edit_handler(client: Client, callback_query: CallbackQuery):
    """Обработчик редактирования задержки"""
    data_parts = callback_query.data.split('|')
    chat_id = data_parts[1]
    task_id = data_parts[2]
    page = int(data_parts[3])
    
    # Сохраняем состояние для РЕДАКТИРОВАНИЯ задержки
    user_data_storage[callback_query.from_user.id] = {
        'state': "waiting_edit_delay",  # Важно: edit, а не create
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
    """Обработчик редактирования префикса"""
    data_parts = callback_query.data.split('|')
    chat_id = data_parts[1]
    task_id = data_parts[2]
    page = int(data_parts[3])
    
    # Сохраняем состояние для РЕДАКТИРОВАНИЯ префикса
    user_data_storage[callback_query.from_user.id] = {
        'state': "waiting_edit_prefix",  # Важно: edit, а не create
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
        # Останавливаем старую задачу
        await stop_flooder_task(chat_id, task_id)
        
        # Обновляем данные
        flooder_tasks[chat_id][task_id]['text_file'] = text_file
        save_flooder_tasks(flooder_tasks)
        
        # Запускаем новую задачу, если она активна
        if flooder_tasks[chat_id][task_id].get('active', True):
            await run_flooder_task(chat_id, task_id, flooder_tasks[chat_id][task_id])
        
        await callback_query.answer("✅ Текстовый файл изменен")
        
        # Обновляем сообщение
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
        # Останавливаем старую задачу
        await stop_flooder_task(chat_id, task_id)
        
        # Обновляем данные
        flooder_tasks[chat_id][task_id]['media_file'] = media_file
        save_flooder_tasks(flooder_tasks)
        
        # Запускаем новую задачу, если она активна
        if flooder_tasks[chat_id][task_id].get('active', True):
            await run_flooder_task(chat_id, task_id, flooder_tasks[chat_id][task_id])
        
        await callback_query.answer("✅ Медиа файл изменен")
        
        # Обновляем сообщение
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
        # Останавливаем задачу
        await stop_flooder_task(chat_id, task_id)
        
        # Удаляем из конфига
        del flooder_tasks[chat_id][task_id]
        if not flooder_tasks[chat_id]:
            del flooder_tasks[chat_id]
        save_flooder_tasks(flooder_tasks)
        await callback_query.answer("✅ Задача удалена")
        
        # Возвращаемся к списку задач
        callback_query.data = f"edit_tasks|{chat_id}|{page}"
        await edit_tasks_handler(client, callback_query)
    else:
        await callback_query.answer("❌ Задача не найдена")


# Обработчик выбора текстового файла
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
    
    keyboard = [[InlineKeyboardButton("🚫 Без медиа", callback_data="multi_media|none")]]
    
    for file in media_files:
        keyboard.append([InlineKeyboardButton(f"📁 {file}", callback_data=f"multi_media|{file}")])
    
    keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="multi_cancel")])
    
    await callback_query.message.edit_text("🎬 Выберите медиа файл:", reply_markup=InlineKeyboardMarkup(keyboard))
    await callback_query.answer()

# Обработчик выбора медиа
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
    await run_multi_task(chat_id, multi_tasks[chat_id])
    
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



# ОБНОВЛЕННЫЙ ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ
@app.on_message(filters.all & filters.private & filters.text & ~filters.command("start") & ~filters.command("chats"))
async def handle_all_text_messages(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Если пользователь в состоянии (вводит данные)
    if user_id in user_data_storage:
        user_data = user_data_storage[user_id]
        state = user_data.get('state')
        
        # РЕДАКТИРОВАНИЕ задержки
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
                    # Останавливаем старую задачу
                    await stop_flooder_task(chat_id, task_id)
                    
                    # Обновляем данные
                    flooder_tasks[chat_id][task_id]['delay'] = delay
                    save_flooder_tasks(flooder_tasks)
                    
                    # Запускаем новую задачу, если она активна
                    if flooder_tasks[chat_id][task_id].get('active', True):
                        await run_flooder_task(chat_id, task_id, flooder_tasks[chat_id][task_id])
                    
                    await message.reply("✅ Задержка изменена")
                    del user_data_storage[user_id]
                    
                    # Возвращаемся к управлению задачей
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
                # Останавливаем старую задачу
                await stop_flooder_task(chat_id, task_id)
                
                # Обновляем данные
                flooder_tasks[chat_id][task_id]['prefix'] = prefix
                save_flooder_tasks(flooder_tasks)
                
                # Запускаем новую задачу, если она активна
                if flooder_tasks[chat_id][task_id].get('active', True):
                    await run_flooder_task(chat_id, task_id, flooder_tasks[chat_id][task_id])
                
                await message.reply("✅ Префикс изменен")
                del user_data_storage[user_id]
                
                # Возвращаемся к управлению задачей
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
                     # Добавляем с именем (пока просто ID, можно позже добавить функционал имен)
                     targets[target_id] = {
                         'name': f'Цель {target_id}',  # Добавляем поле name
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
        
            
            # Если пользователь не в состоянии редактирования, обрабатываем главное меню
        # ДОБАВИМ ЭТОТ БЛОК ДЛЯ ОСТАЛЬНЫХ СОСТОЯНИЙ
        else:
            # Если состояние неизвестно, удаляем его и обрабатываем как обычное сообщение
            del user_data_storage[user_id]
            await handle_main_menu(client, message)
    else:
        await handle_main_menu(client, message)

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


    

async def main():
    await app.start()
    print("✅ Бот запущен")
    await start_all_flooder_tasks()
    print("✅ Задачи активированы")
    
    try:
        await idle()
    finally:
        # Корректно закрываем пул потоков при завершении
        thread_pool.shutdown(wait=True)
        print("✅ Пул потоков закрыт")

if __name__ == '__main__':
    app.run(main())