import os
import json
import logging
import asyncio  # Импорт для использования паузы
import calendar  # Для получения названия месяца
from datetime import datetime, timedelta
from random import choice, choices
import threading

from dateutil.relativedelta import relativedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
from multiprocessing import context

logging.basicConfig(level=logging.INFO)

# Ваш токен и настройка админов
TOKEN = '7692845826:AAEWYoo1bFU22LNa79-APy_iZyio2dwc9zA'
MAIN_ADMIN_IDS = [1980610942, 394468757]

# Пути к файлам
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ADMINS_FILE = os.path.join(CURRENT_DIR, 'admins.json')
USER_IDS_FILE = os.path.join(CURRENT_DIR, 'user_ids.json')
RESERVATIONS_FILE = os.path.join(CURRENT_DIR, 'reservations.json')
PIZZAS_FILE = os.path.join(CURRENT_DIR, 'perchini_pizzas.json')
PASTA_FILE = os.path.join(CURRENT_DIR, 'perchini_pasta.json')
HOT_FILE = os.path.join(CURRENT_DIR, 'perchini_hot.json')
FOCACCIA_DIP_FILE = os.path.join(CURRENT_DIR, 'perchini_focaccia_dip.json')
SNACKS_FILE = os.path.join(CURRENT_DIR, 'perchini_snacks.json')
SALADS_FILE = os.path.join(CURRENT_DIR, 'perchini_salads.json')
SOUPS_FILE = os.path.join(CURRENT_DIR, 'perchini_soups.json')
GRILL_FILE = os.path.join(CURRENT_DIR, 'perchini_grill.json')
DESSERTS_FILE = os.path.join(CURRENT_DIR, 'perchini_desserts.json')


# Пути к файлам сообщений
EXCLUSIVE_MENU_FILE = os.path.join(CURRENT_DIR, 'exclusive_menu.json')
SEASONAL_MENU_FILE = os.path.join(CURRENT_DIR, 'seasonal_menu.json')
EVENTS_FILE = os.path.join(CURRENT_DIR, 'events.json')
ABOUT_US_FILE = os.path.join(CURRENT_DIR, 'about_us.json')
ARCHIVE_FILE = os.path.join(CURRENT_DIR, 'archive.json')

# Загрузка архива из файла
def load_archive():
    if os.path.exists(ARCHIVE_FILE):
        try:
            with open(ARCHIVE_FILE, 'r', encoding='utf-8') as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

# Сохранение архива
def save_archive(data):
    # Логирование, чтобы проверить, что функция получила корректные данные
    print(f"Сохранение архива: {data}")
    try:
        with open(ARCHIVE_FILE, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка при сохранении архива: {e}")

# Инициализация архива
archive = load_archive()

# Обновленная функция для загрузки эксклюзивного меню из файла
def load_exclusive_menu():
    return load_data(EXCLUSIVE_MENU_FILE, {"text": "Эксклюзивное меню:\n[Ваше сообщение здесь]", "photos": []})

# Обновленная функция для сохранения эксклюзивного меню в файл
def save_exclusive_menu(data):
    save_data(EXCLUSIVE_MENU_FILE, data)

def load_seasonal_menu():
    return load_data(SEASONAL_MENU_FILE, {"text": "Сезонное меню:\n[Ваше сообщение здесь]", "photos": []})

def save_seasonal_menu(data):
    save_data(SEASONAL_MENU_FILE, data)

def load_events():
    return load_data(EVENTS_FILE, {"text": "Наши мероприятия:\n[Ваше сообщение здесь]", "photos": []})

def save_events(data):
    save_data(EVENTS_FILE, data)

def load_contacts():
    return load_data(ABOUT_US_FILE, {"contacts": {"text": "Контакты:\n[Ваше сообщение здесь]", "photos": []}})

def save_contacts(data):
    save_data(ABOUT_US_FILE, data)

def load_our_staff():
    return load_data(ABOUT_US_FILE, {"our_staff": {"text": "Персонал:\n[Ваше сообщение здесь]", "photos": []}})

def save_our_staff(data):
    save_data(ABOUT_US_FILE, data)

def load_about_establishment():
    return load_data(ABOUT_US_FILE, {"about_establishment": {"text": "О заведении:\n[Ваше сообщение здесь]", "photos": []}})

def save_about_establishment(data):
    save_data(ABOUT_US_FILE, data)

def load_pizzas():
    return load_data(PIZZAS_FILE, {"text": "Пиццы:\n[Ваше сообщение здесь]", "photos": []})

def save_pizzas(data):
    save_data(PIZZAS_FILE, data)

def load_pasta():
    return load_data(PASTA_FILE, {"text": "Паста:\n[Ваше сообщение здесь]", "photos": []})

def save_pasta(data):
    save_data(PASTA_FILE, data)

def load_hot():
    return load_data(HOT_FILE, {"text": "Горячее:\n[Ваше сообщение здесь]", "photos": []})

def save_hot(data):
    save_data(HOT_FILE, data)

def load_focaccia_dip():
    return load_data(FOCACCIA_DIP_FILE, {"text": "Фокачча и дипы:\n[Ваше сообщение здесь]", "photos": []})

def save_focaccia_dip(data):
    save_data(FOCACCIA_DIP_FILE, data)

def load_snacks():
    return load_data(SNACKS_FILE, {"text": "Закуски:\n[Ваше сообщение здесь]", "photos": []})

def save_snacks(data):
    save_data(SNACKS_FILE, data)

def load_salads():
    return load_data(SALADS_FILE, {"text": "Салаты:\n[Ваше сообщение здесь]", "photos": []})

def save_salads(data):
    save_data(SALADS_FILE, data)

def load_soups():
    return load_data(SOUPS_FILE, {"text": "Супы:\n[Ваше сообщение здесь]", "photos": []})

def save_soups(data):
    save_data(SOUPS_FILE, data)

def load_grill():
    return load_data(GRILL_FILE, {"text": "Гриль:\n[Ваше сообщение здесь]", "photos": []})

def save_grill(data):
    save_data(GRILL_FILE, data)

def load_desserts():
    return load_data(DESSERTS_FILE, {"text": "Десерты:\n[Ваше сообщение здесь]", "photos": []})

def save_desserts(data):
    save_data(DESSERTS_FILE, data)

def load_data(file_path, default_data):
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, dict):
                    return data
        except (json.JSONDecodeError, FileNotFoundError):
            return default_data
    return default_data

def ensure_files_exist():
    files_and_defaults = [
        (EXCLUSIVE_MENU_FILE, {"text": "Эксклюзивное меню:\n[Ваше сообщение здесь]", "photos": []}),
        (SEASONAL_MENU_FILE, {"text": "Сезонное меню:\n[Ваше сообщение здесь]", "photos": []}),
        (EVENTS_FILE, {"text": "Наши мероприятия:\n[Ваше сообщение здесь]", "photos": []}),
        (ABOUT_US_FILE, {
            "contacts": {"text": "Контакты:\n[Ваше сообщение здесь]", "photos": []},
            "our_staff": {"text": "Наш персонал:\n[Ваше сообщение здесь]", "photos": []},
            "about_establishment": {"text": "О заведении:\n[Ваше сообщение здесь]", "photos": []}
        }),
        # Новые файлы для разделов "Меню Перчини"
        (PIZZAS_FILE, {"text": "Пиццы:\n[Ваше сообщение здесь]", "photos": []}),
        (PASTA_FILE, {"text": "Паста:\n[Ваше сообщение здесь]", "photos": []}),
        (HOT_FILE, {"text": "Горячее:\n[Ваше сообщение здесь]", "photos": []}),
        (FOCACCIA_DIP_FILE, {"text": "Фокачча и дипы:\n[Ваше сообщение здесь]", "photos": []}),
        (SNACKS_FILE, {"text": "Закуски:\n[Ваше сообщение здесь]", "photos": []}),
        (SALADS_FILE, {"text": "Салаты:\n[Ваше сообщение здесь]", "photos": []}),
        (SOUPS_FILE, {"text": "Супы:\n[Ваше сообщение здесь]", "photos": []}),
        (GRILL_FILE, {"text": "Гриль:\n[Ваше сообщение здесь]", "photos": []}),
        (DESSERTS_FILE, {"text": "Десерты:\n[Ваше сообщение здесь]", "photos": []}),
    ]

    for file_path, default_data in files_and_defaults:
        if not os.path.exists(file_path):
            logging.info(f"Файл {file_path} не найден. Создаем с данными по умолчанию.")
            save_data(file_path, default_data)
        else:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    if not isinstance(data, dict) or not all(key in data for key in default_data):
                        logging.warning(f"Файл {file_path} имеет некорректную структуру. Перезаписываем с данными по умолчанию.")
                        save_data(file_path, default_data)
            except (json.JSONDecodeError, FileNotFoundError):
                logging.error(f"Ошибка чтения файла {file_path}. Перезаписываем с данными по умолчанию.")
                save_data(file_path, default_data)

def save_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    # Функция для загрузки сообщения из файла
def load_message(file_path, default_message):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    return default_message

    # Функция для сохранения сообщения в файл
def save_message(file_path, message):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(message)

    # Загрузка всех сообщений при старте
def load_all_messages(app):
    # Загрузка эксклюзивного меню
    exclusive_menu_data = load_data(EXCLUSIVE_MENU_FILE, {"text": "Эксклюзивное меню:\n[Ваше сообщение здесь]", "photos": []})
    app.bot_data['exclusive_menu'] = exclusive_menu_data

    # Загрузка сезонного меню
    seasonal_menu_data = load_data(SEASONAL_MENU_FILE, {"text": "Сезонное меню:\n[Ваше сообщение здесь]", "photos": []})
    app.bot_data['seasonal_menu'] = seasonal_menu_data

    # Загрузка мероприятий
    events_data = load_data(EVENTS_FILE, {"text": "Наши мероприятия:\n[Ваше сообщение здесь]", "photos": []})
    app.bot_data['events'] = events_data

    # Загрузка данных "О нас"
    about_us_data = load_data(ABOUT_US_FILE, {
        "contacts": {"text": "Контакты:\n[Ваше сообщение здесь]", "photos": []},
        "our_staff": {"text": "Наш персонал:\n[Ваше сообщение здесь]", "photos": []},
        "about_establishment": {"text": "О заведении:\n[Ваше сообщение здесь]", "photos": []}
    })
    app.bot_data['about_us'] = about_us_data

    # Загрузка данных Меню Перчини
    app.bot_data['pizzas'] = load_data(PIZZAS_FILE, {"text": "Пиццы:\n[Ваше сообщение здесь]", "photos": []})
    app.bot_data['pasta'] = load_data(PASTA_FILE, {"text": "Паста:\n[Ваше сообщение здесь]", "photos": []})
    app.bot_data['hot'] = load_data(HOT_FILE, {"text": "Горячее:\n[Ваше сообщение здесь]", "photos": []})
    app.bot_data['focaccia_dip'] = load_data(FOCACCIA_DIP_FILE, {"text": "Фокачча и дипы:\n[Ваше сообщение здесь]", "photos": []})
    app.bot_data['snacks'] = load_data(SNACKS_FILE, {"text": "Закуски:\n[Ваше сообщение здесь]", "photos": []})
    app.bot_data['salads'] = load_data(SALADS_FILE, {"text": "Салаты:\n[Ваше сообщение здесь]", "photos": []})
    app.bot_data['soups'] = load_data(SOUPS_FILE, {"text": "Супы:\n[Ваше сообщение здесь]", "photos": []})
    app.bot_data['grill'] = load_data(GRILL_FILE, {"text": "Гриль:\n[Ваше сообщение здесь]", "photos": []})
    app.bot_data['desserts'] = load_data(DESSERTS_FILE, {"text": "Десерты:\n[Ваше сообщение здесь]", "photos": []})


# Сохранение всех сообщений
def save_all_messages(context):
    try:
        # Сохранение эксклюзивного меню
        save_data(EXCLUSIVE_MENU_FILE, context.bot_data['exclusive_menu'])

        # Сохранение сезонного меню
        save_data(SEASONAL_MENU_FILE, context.bot_data['seasonal_menu'])

        # Сохранение мероприятий
        save_data(EVENTS_FILE, context.bot_data['events'])

        # Сохранение данных "О нас"
        save_data(ABOUT_US_FILE, context.bot_data['about_us'])

        # Сохранение данных Меню Перчини
        save_data(PIZZAS_FILE, context.bot_data['pizzas'])
        save_data(PASTA_FILE, context.bot_data['pasta'])
        save_data(HOT_FILE, context.bot_data['hot'])
        save_data(FOCACCIA_DIP_FILE, context.bot_data['focaccia_dip'])
        save_data(SNACKS_FILE, context.bot_data['snacks'])
        save_data(SALADS_FILE, context.bot_data['salads'])
        save_data(SOUPS_FILE, context.bot_data['soups'])
        save_data(GRILL_FILE, context.bot_data['grill'])
        save_data(DESSERTS_FILE, context.bot_data['desserts'])
    except Exception as e:
        logging.error(f"Ошибка при сохранении всех сообщений: {e}")

def load_reservations():
    if os.path.exists(RESERVATIONS_FILE):
        try:
            with open(RESERVATIONS_FILE, 'r', encoding='utf-8') as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

def save_reservations():
    with open(RESERVATIONS_FILE, 'w', encoding='utf-8') as file:
        json.dump(confirmed_reservations, file, ensure_ascii=False, indent=4)

# Хранение 
user_states = {}    # Словарь для хранения состояний пользователей
reservations = {} # Словарь для хранения бронирований
confirmed_reservations = load_reservations()  # Здесь будем хранить все подтверждённые брони
admin_clarifications = {}  # Словарь для уточнения администратором
clarifying_reservation = {} # для отслеживания запросов на уточнение брони

# Обновленная функция для очистки старых броней и их архивирования
async def cleanup_old_reservations(context):
    current_time_utc = datetime.now(pytz.utc)  # Текущее время в UTC
    to_remove = []

    for booking_id, booking in confirmed_reservations.items():
        # Получаем время бронирования в UTC
        booking_datetime_str = f"{booking['date']} {booking['time']}"
        local_tz = pytz.timezone('Europe/Moscow')
        booking_local_time = datetime.strptime(booking_datetime_str, "%d-%m-%Y %H:%M")
        booking_utc_time = local_tz.localize(booking_local_time).astimezone(pytz.utc)

        # Проверка, если бронирование старше 2 часов после назначенного времени
        if booking_utc_time + timedelta(hours=2) < current_time_utc:
            to_remove.append(booking_id)

    # Загружаем актуальный архив перед обновлением
    global archive
    archive = load_archive()  # Обновляем переменную актуальными данными из файла

    for booking_id in to_remove:
        user_id = booking_id
        if user_id in confirmed_reservations:
            # Добавляем удаленные бронирования в архив
            archived_booking = confirmed_reservations[user_id]
            archived_booking['archived_at'] = datetime.now().strftime("%d-%m-%Y %H:%M")

            # Теперь архив будет в формате списка:
            if 'reservations' not in archive:
                archive['reservations'] = []  # Создаем список, если его еще нет
            
            archive['reservations'].append(archived_booking)

            # Отправка сообщения пользователю с просьбой оставить отзыв
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="😊 Спасибо, что посетили наше заведение! Мы надеемся, что вам понравилось! Если это так, будем рады вашему отзыву. 🌟 Оставить отзыв можно по любой удобной вам ссылке: \n\n✍️ Яндекс: https://yandex.ru/maps/-/CDhYEXLK \n📍 2gis: https://go.2gis.com/iso24 \n\nТакже, если вы захотите отблагодарить наш персонал за качественное обслуживание, вы можете оставить им приятный подарок в виде чаевых по ссылке: (ссылка) 🎁"
                )
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

            # Удаление бронирования
            del confirmed_reservations[user_id]

    # Сохранение изменений в файл с подтвержденными бронированиями
    save_reservations()

    # Сохранение архива бронирований в файл
    save_archive(archive)

    # Удаляем записи из архива старше 2 суток
    await cleanup_archive()

# Обновленная функция очистки архива
async def cleanup_archive():
    current_time_utc = datetime.now(pytz.utc)
    updated_archive = []

    for booking in archive['reservations']:
        try:
            archived_at = datetime.strptime(booking['archived_at'], "%d-%m-%Y %H:%M")
            archived_at_utc = pytz.timezone('Europe/Moscow').localize(archived_at).astimezone(pytz.utc)
            # Если бронь старше двух суток, не добавляем её в обновленный архив
            if archived_at_utc + timedelta(days=2) >= current_time_utc:
                updated_archive.append(booking)
        except Exception as e:
            print(f"Ошибка при обработке архива: {e}")

    # Обновляем архив с актуальными данными
    archive['reservations'] = updated_archive
    save_archive(archive)

def is_main_admin(user_id):
    return user_id in MAIN_ADMIN_IDS  # Проверяем, находится ли user_id в списке главных администраторов

## Загружаем список пользователей
def load_user_ids():
    if os.path.exists(USER_IDS_FILE):
        try:
            with open(USER_IDS_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, dict):
                    return data
                else:
                    return {}
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}

# Пример данных пользователя: {'phone': '1234567890', 'name': 'Иван', 'discount': 10}

# Загружаем список пользователей при старте бота
user_ids = load_user_ids()  # Должен быть словарём

## Добавляем пользователя в словарь, если его там еще нет
def add_user_id(user_id):
    user_id_str = str(user_id)  # Преобразуем user_id в строку для использования в качестве ключа
    if user_id_str not in user_ids:
        user_ids[user_id_str] = {
            "phone": "",  # Оставляем пустым, чтобы позже заполнить
            "name": "",   # Аналогично для имени
            "discount": 0,  # Добавляем скидку по умолчанию — 0%
            "has_played": False  # Новый флаг, который указывает, играл ли пользователь
        }
    else:
        # Если пользователь существует, проверяем наличие флага и других полей
        if "has_played" not in user_ids[user_id_str]:
            user_ids[user_id_str]['has_played'] = False  # Добавляем флаг, если его нет
        if "discount" not in user_ids[user_id_str]:
            user_ids[user_id_str]['discount'] = 0  # Добавляем скидку, если ее нет
    save_user_ids(user_ids)  # Сохраняем изменения

# Функция для сохранения данных пользователей
def save_user_ids(user_ids):
    with open(USER_IDS_FILE, 'w', encoding='utf-8') as file:
        json.dump(user_ids, file, ensure_ascii=False, indent=4)

# Инициализация списка админов
def load_admins():
    if os.path.exists(ADMINS_FILE):
        try:
            with open(ADMINS_FILE, 'r') as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            return [MAIN_ADMIN_IDS]
    return [MAIN_ADMIN_IDS]

def save_admins(admins):
    with open(ADMINS_FILE, 'w') as file:
        json.dump(admins, file)

admins = load_admins()

# Доступные имена для выбора
admin_names = ["Маша", "Аня", "Паша"]
hookah_master_names = ["Родион", "Паша", "Андрей"]
# Возможные призы
prizes = ["Бесплатный кальян", "Бесплатный напиток на ваш выбор", "Бесплатный чай"]
weights = [0.05, 0.25, 0.70]  # Веса, соответствующие шансам в процентах

# Активные сотрудники
active_staff = {
    "admin": "Маша",  # Изначально выбранный администратор
    "hookah_master": "Родион"  # Изначально выбранный кальянщик
}

# Проверяем и создаем файлы перед запуском бота
ensure_files_exist()

# Инициализация приложения
app = Application.builder().token(TOKEN).build()

# Загрузка сообщений при старте, передаем app
load_all_messages(app)

def is_admin(user_id):
    return user_id in admins

# Функция для сброса состояния пользователя
def reset_user_state(user_id):
    if user_id in reservations:
        del reservations[user_id]

# Функция запуска игры
async def play_game(update: Update, context):
    # Получаем данные из callback_query вместо message
    query = update.callback_query
    user_id = query.from_user.id

    # Удаляем сообщение с кнопкой
    await query.message.delete()

    # Добавляем пользователя, если его нет в базе данных
    add_user_id(user_id)

    # Выбираем случайный приз с указанными весами
    selected_prize = choices(prizes, weights=weights, k=1)[0]

    # Сохраняем приз в состоянии пользователя
    context.user_data['prize'] = selected_prize

    # Устанавливаем флаг `has_played` для пользователя
    user_ids[str(user_id)]['has_played'] = True

    # Устанавливаем разовый выигрыш для пользователя
    if 'won_prize' not in user_ids[str(user_id)]:
        user_ids[str(user_id)]['won_prize'] = selected_prize
    else:
        # Если пользователь уже имеет поле 'won_prize', оставляем его без изменений
        user_ids[str(user_id)]['won_prize'] = None  # Приз уже был учтен, теперь не нужно его дублировать

    # Сохраняем изменения в файл
    save_user_ids(user_ids)

    # Отправляем сообщение о выигрыше
    await query.message.reply_text(
        f"Поздравляем! 🎉 Вы выиграли {selected_prize}. Чтобы получить приз, пожалуйста, завершите регистрацию."
    )

    # Закрываем всплывающее окно с кнопкой
    await query.answer()

    # Отправляем уведомление всем администраторам
    mention_html = query.from_user.mention_html()  # Используем mention_html для создания ссылки на пользователя
    user_name = user_ids[str(user_id)].get('name', 'Неизвестный пользователь')
    for admin_id in admins:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"🎉 Пользователь: {mention_html}\n"
                    f"Имя: {user_name}\n"
                    f"Выиграл приз: {selected_prize}."
                ),
                parse_mode=ParseMode.HTML  # Используем HTML для корректного отображения ссылки
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение админу {admin_id}: {e}")

    # Проверяем регистрацию пользователя
    await check_registration(update, context)

# Функция для проверки регистрации пользователя
async def check_registration(update: Update, context):
    user_id = update.callback_query.from_user.id if update.callback_query else update.message.from_user.id

    user_data = user_ids.get(str(user_id), {})

    # Проверяем наличие номера телефона и имени
    if not user_data.get('phone'):
        await update.callback_query.message.reply_text("Заполняя анкету вы даете согласие на обработку персональных данных.")
        await update.callback_query.message.reply_text("Пожалуйста, введите ваш номер телефона.")
        context.user_data['awaiting_phone'] = True
        return
    if not user_data.get('name'):
        await update.callback_query.message.reply_text("Пожалуйста, введите ваше имя.")
        context.user_data['awaiting_name'] = True
        return

    # Если данные уже есть, поздравляем с успешной регистрацией
    await update.callback_query.message.reply_text(
        f"Регистрация завершена! Ваш приз: {context.user_data['prize']}. Спасибо за участие!"
    )
    del context.user_data['prize']  # Удаляем приз из состояния пользователя

# Функция для обработки команды /start
async def start(update: Update, context):
    user_id = update.message.from_user.id

    # Проверяем, есть ли пользователь в базе
    if str(user_id) not in user_ids:
        # Новый пользователь — предлагаем сыграть в игру
        await update.message.reply_text(
            "Добро пожаловать в Smoke House! У вас есть возможность сыграть в рандомайзер и выиграть один из призов:\n\nКальянный сертификат на 2000 руб. \n\nБесплатный кальян \n\nБесплатный напиток на ваш выбор \n\nБесплатный чай"
        )
        
        keyboard = [[InlineKeyboardButton("🎲 Сыграть в игру", callback_data="play_game")]]
        await update.message.reply_text(
            "Хотите сыграть?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Если пользователь есть в базе, проверяем, играл ли он в игру
    user_data = user_ids[str(user_id)]
    if not user_data.get('has_played', False):
        keyboard = [[InlineKeyboardButton("🎲 Сыграть в игру", callback_data="play_game")]]
        await update.message.reply_text(
            "Добро пожаловать обратно! Хотите сыграть в игру, чтобы выиграть один из призов? \n\nКальянный сертификат на 2000 руб. \n\nБесплатный кальян \n\nБесплатный напиток на ваш выбор \n\nБесплатный чай",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Если пользователь уже играл и зарегистрирован, отображаем основное меню
    await show_main_menu(update, context)

# Функция для обработки кнопки "Назад"
async def handle_back_menu(update: Update, context):
    query = update.callback_query
    await query.answer()

    # Удаляем текущее сообщение
    await query.message.delete()


async def handle_back_button(update: Update, context):
    query = update.callback_query
    await query.answer()

    # Удаляем текущее сообщение
    await query.message.delete()

    # Отображаем главное меню
    await show_main_menu(update, context)

# Обработка для кнопки "Назад" в подпунктах раздела "О нас"
async def handle_back_about(update: Update, context):
    query = update.callback_query
    await query.answer()

    # Удаляем текущее сообщение
    await query.message.delete()

    # Показываем подменю "О нас" после нажатия кнопки "Назад"
    keyboard = [
        [InlineKeyboardButton("📞 Контакты", callback_data="contacts")],
        [InlineKeyboardButton("👥 Наш персонал", callback_data="our_staff")],
        [InlineKeyboardButton("🏠 О заведении", callback_data="about_establishment")],
        [InlineKeyboardButton("👨‍💻 О создателе", callback_data="about_creator")],
        [InlineKeyboardButton("⬅ Назад", callback_data="back_to_main")]
    ]
    await query.message.reply_text("Информация о нас:", reply_markup=InlineKeyboardMarkup(keyboard))

# Отображение основного меню
async def show_main_menu(update: Update, context):
    # Определяем user_id в зависимости от того, был ли вызов через сообщение или callback_query
    user_id = update.message.from_user.id if update.message else update.callback_query.from_user.id
    user_data = user_ids.get(str(user_id), {})

    # Создаем приветственное сообщение
    greeting = f"Добро пожаловать в Smoke House, {user_data.get('name', 'гость')}!"

    # Добавляем информацию о скидке, только если она больше 0
    if user_data.get('discount', 0) > 0:
        greeting += f"\nВаша текущая скидка на классический кальян - {user_data['discount']} руб."

    # Добавляем информацию о смене сотрудников
    greeting += f"\nСегодня на смене Администратор {active_staff['admin']} и Кальянщик {active_staff['hookah_master']}."

    # Создаем клавиатуру для основного меню
    keyboard = [
        [InlineKeyboardButton("📋 Эксклюзивное меню", callback_data="exclusive_menu")],
        [InlineKeyboardButton("🌶️ Меню Перчини", callback_data="perchini_menu")],
        [InlineKeyboardButton("🌱 Сезонное меню", callback_data="seasonal_menu")],
        [InlineKeyboardButton("🏠 О нас", callback_data="about_us")],
        [InlineKeyboardButton("🎉 Мероприятия", callback_data="events")]
    ]

    # Если пользователь зарегистрирован, добавляем кнопку для бронирования
    if str(user_id) in user_ids:
        keyboard.insert(0, [InlineKeyboardButton("📅 Забронировать столик", callback_data="book_table")])

    # Если пользователь администратор, добавляем админ меню
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("⚙️ Админ меню", callback_data="admin_menu")])

    # Отправляем приветственное сообщение и меню
    if update.message:
        await update.message.reply_text(
            greeting,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.callback_query.message.reply_text(
            greeting,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# Обработка нажатий на кнопки
async def handle_main_menu_buttons(update: Update, context):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    is_user_admin = is_admin(user_id)  # Проверяем, является ли пользователь администратором

    if query.data == "play_game":
        # Запускаем игру и отмечаем, что пользователь играл
        await play_game(update, context)
        context.user_data['has_played'] = True

    elif query.data == "book_table":
        await show_calendar(query, context)  # Запускаем процесс бронирования

    # Обработка для эксклюзивного меню
    elif query.data == "exclusive_menu":
        await query.message.delete()
        data = load_exclusive_menu()
        text = data.get("text", "Эксклюзивное меню:\n[Ваше сообщение здесь]")
        photos = data.get("photos", [])
        
        keyboard = [[InlineKeyboardButton("⬅ Назад", callback_data="back_to_main")]]
        if is_user_admin:
            keyboard.insert(0, [InlineKeyboardButton("✏️ Редактировать", callback_data="edit_exclusive_menu")])
            keyboard.insert(1, [InlineKeyboardButton("🗑 Очистить фото", callback_data="clear_photos_exclusive_menu")])
    
        if photos:
            media_group = []
            # Создаем список объектов InputMediaPhoto для отправки группы фото
            for idx, photo in enumerate(photos):
                if idx == 0:
                    # К первой фотографии добавляем текст в качестве подписи
                    media_group.append(InputMediaPhoto(open(os.path.join(CURRENT_DIR, photo), 'rb'), caption=text))
                else:
                    media_group.append(InputMediaPhoto(open(os.path.join(CURRENT_DIR, photo), 'rb')))
            
            # Отправляем фото как медиа-группу с текстом в подписи к первой фотографии
            await context.bot.send_media_group(chat_id=query.message.chat_id, media=media_group)
        else:
            # Если фотографий нет, просто отправляем текст
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
        # Отправляем клавиатуру "назад" после отправки медиа-группы
        await query.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "perchini_menu":
        await query.message.delete()
        # Показываем подменю "Меню Перчини"
        keyboard = [
            [InlineKeyboardButton("🍕 Пиццы", callback_data="pizzas")],
            [InlineKeyboardButton("🍝 Паста", callback_data="pasta")],
            [InlineKeyboardButton("🔥 Горячее", callback_data="hot")],
            [InlineKeyboardButton("🍞 Фокачча и дипы", callback_data="focaccia_dip")],
            [InlineKeyboardButton("🍢 Закуски", callback_data="snacks")],
            [InlineKeyboardButton("🥗 Салаты", callback_data="salads")],
            [InlineKeyboardButton("🍲 Супы", callback_data="soups")],
            [InlineKeyboardButton("🍖 Гриль", callback_data="grill")],
            [InlineKeyboardButton("🍰 Десерты", callback_data="desserts")],
            [InlineKeyboardButton("⬅ Назад", callback_data="back_to_main")]
        ]
        await query.message.reply_text("Меню Перчини:", reply_markup=InlineKeyboardMarkup(keyboard))

    # Обработка для сезонного меню
    elif query.data == "seasonal_menu":
        await query.message.delete()
        data = load_data(SEASONAL_MENU_FILE, {"text": "Сезонное меню:\n[Ваше сообщение здесь]", "photos": []})
        text = data.get("text", "Сезонное меню:\n[Ваше сообщение здесь]")
        photos = data.get("photos", [])
    
        keyboard = [[InlineKeyboardButton("⬅ Назад", callback_data="back_to_main")]]
        if is_user_admin:
            keyboard.insert(0, [InlineKeyboardButton("✏️ Редактировать", callback_data="edit_seasonal_menu")])
            keyboard.insert(1, [InlineKeyboardButton("🗑 Очистить фото", callback_data="clear_photos_seasonal_menu")])
    
        if photos:
            media_group = []
            # Создаем список объектов InputMediaPhoto для отправки группы фото
            for idx, photo in enumerate(photos):
                if idx == 0:
                    # К первой фотографии добавляем текст в качестве подписи
                    media_group.append(InputMediaPhoto(open(os.path.join(CURRENT_DIR, photo), 'rb'), caption=text))
                else:
                    media_group.append(InputMediaPhoto(open(os.path.join(CURRENT_DIR, photo), 'rb')))
            
            # Отправляем фото как медиа-группу с текстом в подписи к первой фотографии
            await context.bot.send_media_group(chat_id=query.message.chat_id, media=media_group)
        else:
            # Если фотографий нет, просто отправляем текст
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
        # Отправляем клавиатуру "назад" после отправки медиа-группы
        await query.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))

    # Обработка для мероприятий
    elif query.data == "events":
        await query.message.delete()
        data = load_data(EVENTS_FILE, {"text": "Наши мероприятия:\n[Ваше сообщение здесь]", "photos": []})
        text = data.get("text", "Наши мероприятия:\n[Ваше сообщение здесь]")
        photos = data.get("photos", [])
    
        keyboard = [[InlineKeyboardButton("⬅ Назад", callback_data="back_to_main")]]
        if is_user_admin:
            keyboard.insert(0, [InlineKeyboardButton("✏️ Редактировать", callback_data="edit_events")])
            keyboard.insert(1, [InlineKeyboardButton("🗑 Очистить фото", callback_data="clear_photos_events")])
    
        if photos:
            media_group = []
            # Создаем список объектов InputMediaPhoto для отправки группы фото
            for idx, photo in enumerate(photos):
                if idx == 0:
                    # К первой фотографии добавляем текст в качестве подписи
                    media_group.append(InputMediaPhoto(open(os.path.join(CURRENT_DIR, photo), 'rb'), caption=text))
                else:
                    media_group.append(InputMediaPhoto(open(os.path.join(CURRENT_DIR, photo), 'rb')))
            
            # Отправляем фото как медиа-группу с текстом в подписи к первой фотографии
            await context.bot.send_media_group(chat_id=query.message.chat_id, media=media_group)
        else:
            # Если фотографий нет, просто отправляем текст
            await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
        # Отправляем клавиатуру "назад" после отправки медиа-группы
        await query.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == "about_us":
        await query.message.delete()
        # Показываем подменю о заведении
        keyboard = [
            [InlineKeyboardButton("📞 Контакты", callback_data="contacts")],
            [InlineKeyboardButton("👥 Наш персонал", callback_data="our_staff")],
            [InlineKeyboardButton("🏠 О заведении", callback_data="about_establishment")],
            [InlineKeyboardButton("👨‍💻 О создателе", callback_data="about_creator")],
            [InlineKeyboardButton("⬅ Назад", callback_data="back_to_main")]
        ]
        await query.message.reply_text("Информация о нас:", reply_markup=InlineKeyboardMarkup(keyboard))

        # Обработка для контактов
        # Обработка для подпунктов раздела "О нас"
    elif query.data == "contacts":
        await query.message.delete()
        data = load_data(ABOUT_US_FILE, {"contacts": {"text": "Контакты:\n[Ваше сообщение здесь]", "photos": []}})
        text = data["contacts"].get("text", "Контакты:\n[Ваше сообщение здесь]")
        photos = data["contacts"].get("photos", [])
    
        keyboard = [[InlineKeyboardButton("⬅ Назад", callback_data="back_to_about_us")]]
        if is_user_admin:
            keyboard.insert(0, [InlineKeyboardButton("✏️ Редактировать", callback_data="edit_contacts")])
            keyboard.insert(1, [InlineKeyboardButton("🗑 Очистить фото", callback_data="clear_photos_contacts")])
    
        if photos:
            media_group = []
            for idx, photo in enumerate(photos):
                if idx == 0:
                    # К первой фотографии добавляем текст в качестве подписи
                    media_group.append(InputMediaPhoto(open(os.path.join(CURRENT_DIR, photo), 'rb'), caption=text))
                else:
                    media_group.append(InputMediaPhoto(open(os.path.join(CURRENT_DIR, photo), 'rb')))
    
            await context.bot.send_media_group(chat_id=query.message.chat_id, media=media_group)
    
        # Отправляем клавиатуру "назад" после отправки медиа-группы
        await query.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == "our_staff":
        await query.message.delete()
        data = load_data(ABOUT_US_FILE, {"our_staff": {"text": "Наш персонал:\n[Ваше сообщение здесь]", "photos": []}})
        text = data["our_staff"].get("text", "Наш персонал:\n[Ваше сообщение здесь]")
        photos = data["our_staff"].get("photos", [])
    
        keyboard = [[InlineKeyboardButton("⬅ Назад", callback_data="back_to_about_us")]]
        if is_user_admin:
            keyboard.insert(0, [InlineKeyboardButton("✏️ Редактировать", callback_data="edit_our_staff")])
            keyboard.insert(1, [InlineKeyboardButton("🗑 Очистить фото", callback_data="clear_photos_our_staff")])
    
        if photos:
            media_group = []
            for idx, photo in enumerate(photos):
                if idx == 0:
                    media_group.append(InputMediaPhoto(open(os.path.join(CURRENT_DIR, photo), 'rb'), caption=text))
                else:
                    media_group.append(InputMediaPhoto(open(os.path.join(CURRENT_DIR, photo), 'rb')))
    
            await context.bot.send_media_group(chat_id=query.message.chat_id, media=media_group)
    
        await query.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == "about_establishment":
        await query.message.delete()
        data = load_data(ABOUT_US_FILE, {"about_establishment": {"text": "О заведении:\n[Ваше сообщение здесь]", "photos": []}})
        text = data["about_establishment"].get("text", "О заведении:\n[Ваше сообщение здесь]")
        photos = data["about_establishment"].get("photos", [])
    
        keyboard = [[InlineKeyboardButton("⬅ Назад", callback_data="back_to_about_us")]]
        if is_user_admin:
            keyboard.insert(0, [InlineKeyboardButton("✏️ Редактировать", callback_data="edit_about_establishment")])
            keyboard.insert(1, [InlineKeyboardButton("🗑 Очистить фото", callback_data="clear_photos_about_establishment")])
    
        if photos:
            media_group = []
            for idx, photo in enumerate(photos):
                if idx == 0:
                    media_group.append(InputMediaPhoto(open(os.path.join(CURRENT_DIR, photo), 'rb'), caption=text))
                else:
                    media_group.append(InputMediaPhoto(open(os.path.join(CURRENT_DIR, photo), 'rb')))
    
            await context.bot.send_media_group(chat_id=query.message.chat_id, media=media_group)
    
        await query.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == "about_creator":
        keyboard = [[InlineKeyboardButton("⬅ Назад", callback_data="back_to_menu")]]  # Кнопка "⬅ Назад" для возвращения к разделу "О нас"
        creator_message = (
            "Привет! 😊\n\n"
            "Меня зовут Данила, и я создал этого бота на платформе Python 🤖\n"
            "Я занимаюсь разработкой телеграм-ботов под любые задачи. Если вам нужно создать бота для вашего бизнеса или личного проекта, вы можете связаться со мной. \n\n"
            "Вот моя ссылка на Телеграм: [@devborzzz](https://t.me/devborzzz)"
        )
        await query.message.reply_text(
            creator_message,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(keyboard)  # Добавляем клавиатуру с кнопкой "Назад"
        )

    elif query.data == "admin_menu":
        if is_admin(query.from_user.id):
            await show_admin_menu(query)
        else:
            await query.message.reply_text("У вас нет прав для доступа в админ меню.")

    elif query.data == "view_archive":
        await show_archive(query)

    elif query.data == "back_to_main":
        await handle_back_button(update, context)

    # Обработка для возврата в раздел "О нас"
    elif query.data == "back_to_about_us":
        await handle_back_about(update, context)

    elif query.data == "back_to_menu":
        await handle_back_menu(update, context)

async def handle_perchini_submenu(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "pizzas":
        await show_perchini_item(query, load_pizzas(), "pizzas", context)
    elif query.data == "pasta":
        await show_perchini_item(query, load_pasta(), "pasta", context)
    elif query.data == "hot":
        await show_perchini_item(query, load_hot(), "hot", context)
    elif query.data == "focaccia_dip":
        await show_perchini_item(query, load_focaccia_dip(), "focaccia_dip", context)
    elif query.data == "snacks":
        await show_perchini_item(query, load_snacks(), "snacks", context)
    elif query.data == "salads":
        await show_perchini_item(query, load_salads(), "salads", context)
    elif query.data == "soups":
        await show_perchini_item(query, load_soups(), "soups", context)
    elif query.data == "grill":
        await show_perchini_item(query, load_grill(), "grill", context)
    elif query.data == "desserts":
        await show_perchini_item(query, load_desserts(), "desserts", context)

async def handle_edit_perchini_item(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "edit_pizzas":
        await query.message.reply_text("Введите новый текст для раздела Пиццы или отправьте новые фото.")
        context.user_data['state'] = 'edit_pizzas'
    elif query.data == "edit_pasta":
        await query.message.reply_text("Введите новый текст для раздела Паста или отправьте новые фото.")
        context.user_data['state'] = 'edit_pasta'
    elif query.data == "edit_hot":
        await query.message.reply_text("Введите новый текст для раздела Горячее или отправьте новые фото.")
        context.user_data['state'] = 'edit_hot'
    elif query.data == "edit_focaccia_dip":
        await query.message.reply_text("Введите новый текст для раздела Фокачча и дипы или отправьте новые фото.")
        context.user_data['state'] = 'edit_focaccia_dip'
    elif query.data == "edit_snacks":
        await query.message.reply_text("Введите новый текст для раздела Закуски или отправьте новые фото.")
        context.user_data['state'] = 'edit_snacks'
    elif query.data == "edit_salads":
        await query.message.reply_text("Введите новый текст для раздела Салаты или отправьте новые фото.")
        context.user_data['state'] = 'edit_salads'
    elif query.data == "edit_soups":
        await query.message.reply_text("Введите новый текст для раздела Супы или отправьте новые фото.")
        context.user_data['state'] = 'edit_soups'
    elif query.data == "edit_grill":
        await query.message.reply_text("Введите новый текст для раздела Гриль или отправьте новые фото.")
        context.user_data['state'] = 'edit_grill'
    elif query.data == "edit_desserts":
        await query.message.reply_text("Введите новый текст для раздела Десерты или отправьте новые фото.")
        context.user_data['state'] = 'edit_desserts'

async def show_perchini_item(query, data, item_type, context):
    text = data.get("text", "[Ваше сообщение здесь]")
    photos = data.get("photos", [])

    keyboard = [[InlineKeyboardButton("⬅ Назад", callback_data="perchini_menu")]]
    if is_admin(query.from_user.id):
        keyboard.insert(0, [InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_{item_type}")])
        keyboard.insert(1, [InlineKeyboardButton("🗑 Очистить фото", callback_data=f"clear_photos_{item_type}")])

    if photos:
        media_group = [InputMediaPhoto(open(os.path.join(CURRENT_DIR, photo), 'rb'), caption=text if idx == 0 else None) for idx, photo in enumerate(photos)]
        await context.bot.send_media_group(chat_id=query.message.chat_id, media=media_group)

    await query.message.reply_text("Выберите действие", reply_markup=InlineKeyboardMarkup(keyboard))


# Обработка команд редактирования для новых пунктов "О нас"
async def handle_about_us_edit(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "edit_contacts":
        await query.message.reply_text("Введите новый текст для контактов.")
        context.user_data['state'] = 'edit_contacts'
    
    elif query.data == "edit_our_staff":
        await query.message.reply_text("Введите новый текст для информации о персонале.")
        context.user_data['state'] = 'edit_our_staff'
    
    elif query.data == "edit_about_establishment":
        await query.message.reply_text("Введите новый текст для информации о заведении.")
        context.user_data['state'] = 'edit_about_establishment'

# Показ меню администратора с кнопкой "Назад"
async def show_admin_menu(query: Update):
    keyboard = []
    
    # Проверяем, является ли пользователь главным администратором
    if is_main_admin(query.from_user.id):
        # Показываем полное меню для главного администратора
        keyboard.extend([
            [InlineKeyboardButton("👨‍👩‍👧‍👦Список админов", callback_data="list_admins")],
            [InlineKeyboardButton("🙋‍♀️Добавить админа", callback_data="add_admin")],
            [InlineKeyboardButton("🙅‍♀️Удалить админа", callback_data="remove_admin")],
        ])
    
    # Общие функции, доступные для всех администраторов
    keyboard.extend([
        [InlineKeyboardButton("🫡Встать на смену", callback_data="take_shift")],
        [InlineKeyboardButton("📨 Рассылка", callback_data="broadcast_message")],
        [InlineKeyboardButton("🧾Редактировать скидку", callback_data="edit_discount")],
        [InlineKeyboardButton("📋Список броней", callback_data="booking_list")],
        [InlineKeyboardButton("📦 Архив", callback_data="view_archive")],
        [InlineKeyboardButton("⬅ Назад", callback_data="back_to_main")]
    ])
    
    await query.message.reply_text(
        f"Вы в админ меню. Выберите действие:\nВерсия 1.3",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Обновленная функция для показа архива
async def show_archive(query):
    archive_data = load_archive()  # Загрузим актуальные данные архива
    if 'reservations' in archive_data and archive_data['reservations']:
        text = "Архив бронирований:\n\n"
        for booking in archive_data['reservations']:
            text += (
                f"Пользователь: {booking['user']}\n"
                f"Телефон: {booking['phone']}\n"
                f"Скидка: {booking['discount']}%\n"
                f"Дата: {booking['date']}\n"
                f"Гости: {booking['guests']}\n"
                f"Время: {booking['time']}\n"
                f"Комментарий: {booking['comment']}\n"
                f"Архивировано: {booking['archived_at']}\n"
                f"--------------------------\n"
            )
    else:
        text = "Архив пуст."

    await query.message.reply_text(text)

# Обработка действий в админ меню
async def handle_admin_menu(update: Update, context):
    query = update.callback_query
    await query.answer()

    # Логируем данные для отладки
    print(f"Callback data: {query.data}")  # Смотрим, что за данные приходят

    if query.data == "edit_exclusive_menu":
        await query.message.reply_text("Введите новый текст для эксклюзивного меню или отправьте новые фото.")
        context.user_data['state'] = 'edit_exclusive_menu'

    elif query.data == "edit_seasonal_menu":
        await query.message.reply_text("Введите новый текст для сезонного меню или отправьте новое фото.")
        context.user_data['state'] = 'edit_seasonal_menu'

    elif query.data == "edit_events":
        await query.message.reply_text("Введите новый текст для мероприятий или отправьте новое фото.")
        context.user_data['state'] = 'edit_events'

        # Добавлено редактирование для "Контакты"
    elif query.data == "edit_contacts":
        await query.message.reply_text("Введите новый текст для контактов или отправьте новые фото.")
        context.user_data['state'] = 'edit_contacts'
    
    # Добавлено редактирование для "Наш персонал"
    elif query.data == "edit_our_staff":
        await query.message.reply_text("Введите новый текст для информации о персонале или отправьте новые фото.")
        context.user_data['state'] = 'edit_our_staff'
    
    # Добавлено редактирование для "О заведении"
    elif query.data == "edit_about_establishment":
        await query.message.reply_text("Введите новый текст для информации о заведении или отправьте новые фото.")
        context.user_data['state'] = 'edit_about_establishment'

        # Обработка очистки фотографий для эксклюзивного меню
    elif query.data == "clear_photos_exclusive_menu":
        data = load_exclusive_menu()
        data["photos"] = []  # Очищаем список фото
        save_exclusive_menu(data)  # Сохраняем обновленный файл
        await query.message.reply_text("Все фотографии эксклюзивного меню успешно удалены.")
        await query.answer()
    
    # Обработка очистки фотографий для сезонного меню
    elif query.data == "clear_photos_seasonal_menu":
        data = load_data(SEASONAL_MENU_FILE, {"text": "Сезонное меню:\n[Ваше сообщение здесь]", "photos": []})
        data["photos"] = []  # Очищаем список фото
        save_data(SEASONAL_MENU_FILE, data)  # Сохраняем обновленный файл
        await query.message.reply_text("Все фотографии сезонного меню успешно удалены.")
        await query.answer()
    
    # Обработка очистки фотографий для мероприятий
    elif query.data == "clear_photos_events":
        data = load_data(EVENTS_FILE, {"text": "Наши мероприятия:\n[Ваше сообщение здесь]", "photos": []})
        data["photos"] = []  # Очищаем список фото
        save_data(EVENTS_FILE, data)  # Сохраняем обновленный файл
        await query.message.reply_text("Все фотографии мероприятий успешно удалены.")
        await query.answer()
    
    # Обработка для удаления фотографий для "Контакты"
    elif query.data == "clear_photos_contacts":
        data = load_data(ABOUT_US_FILE, {"contacts": {"text": "Контакты:\n[Ваше сообщение здесь]", "photos": []}})
        data["contacts"]["photos"] = []  # Очищаем список фото
        save_data(ABOUT_US_FILE, data)  # Сохраняем обновленный файл
        await query.message.reply_text("Все фотографии раздела 'Контакты' успешно удалены.")
        await query.answer()

        # Обработка для удаления фотографий для "пиццы"
    elif query.data == "clear_photos_pizzas":
        data = load_data(PIZZAS_FILE, {"text": "Пицца:\n[Ваше сообщение здесь]", "photos": []})
        data["photos"] = []  # Очищаем список фото
        save_data(PIZZAS_FILE, data)  # Сохраняем обновленный файл
        await query.message.reply_text("Все фотографии раздела 'пицца' успешно удалены.")
        await query.answer()
    
    # Обработка для удаления фотографий для "паста"
    elif query.data == "clear_photos_pasta":
        data = load_data(PASTA_FILE, {"text": "Паста:\n[Ваше сообщение здесь]", "photos": []})
        data["photos"] = []  # Очищаем список фото
        save_data(PASTA_FILE, data)  # Сохраняем обновленный файл
        await query.message.reply_text("Все фотографии раздела 'паста' успешно удалены.")
        await query.answer()
    
    # Обработка для удаления фотографий для "горячее"
    elif query.data == "clear_photos_hot":
        data = load_data(HOT_FILE, {"text": "Горячее:\n[Ваше сообщение здесь]", "photos": []})
        data["photos"] = []  # Очищаем список фото
        save_data(HOT_FILE, data)  # Сохраняем обновленный файл
        await query.message.reply_text("Все фотографии раздела 'горячее' успешно удалены.")
        await query.answer()
    
    # Обработка для удаления фотографий для "фокачча и дипы"
    elif query.data == "clear_photos_focaccia_dip":
        data = load_data(FOCACCIA_DIP_FILE, {"text": "Фокачча и дипы:\n[Ваше сообщение здесь]", "photos": []})
        data["photos"] = []  # Очищаем список фото
        save_data(FOCACCIA_DIP_FILE, data)  # Сохраняем обновленный файл
        await query.message.reply_text("Все фотографии раздела 'фокачча и дипы' успешно удалены.")
        await query.answer()
    
    # Обработка для удаления фотографий для "закуски"
    elif query.data == "clear_photos_snacks":
        data = load_data(SNACKS_FILE, {"text": "Закуски:\n[Ваше сообщение здесь]", "photos": []})
        data["photos"] = []  # Очищаем список фото
        save_data(SNACKS_FILE, data)  # Сохраняем обновленный файл
        await query.message.reply_text("Все фотографии раздела 'закуски' успешно удалены.")
        await query.answer()
    
    # Обработка для удаления фотографий для "салаты"
    elif query.data == "clear_photos_salads":
        data = load_data(SALADS_FILE, {"text": "Салаты:\n[Ваше сообщение здесь]", "photos": []})
        data["photos"] = []  # Очищаем список фото
        save_data(SALADS_FILE, data)  # Сохраняем обновленный файл
        await query.message.reply_text("Все фотографии раздела 'салаты' успешно удалены.")
        await query.answer()
    
    # Обработка для удаления фотографий для "супы"
    elif query.data == "clear_photos_soups":
        data = load_data(SOUPS_FILE, {"text": "Супы:\n[Ваше сообщение здесь]", "photos": []})
        data["photos"] = []  # Очищаем список фото
        save_data(SOUPS_FILE, data)  # Сохраняем обновленный файл
        await query.message.reply_text("Все фотографии раздела 'супы' успешно удалены.")
        await query.answer()
    
    # Обработка для удаления фотографий для "гриль"
    elif query.data == "clear_photos_grill":
        data = load_data(GRILL_FILE, {"text": "Гриль:\n[Ваше сообщение здесь]", "photos": []})
        data["photos"] = []  # Очищаем список фото
        save_data(GRILL_FILE, data)  # Сохраняем обновленный файл
        await query.message.reply_text("Все фотографии раздела 'гриль' успешно удалены.")
        await query.answer()
    
    # Обработка для удаления фотографий для "десерты"
    elif query.data == "clear_photos_desserts":
        data = load_data(DESSERTS_FILE, {"text": "Десерты:\n[Ваше сообщение здесь]", "photos": []})
        data["photos"] = []  # Очищаем список фото
        save_data(DESSERTS_FILE, data)  # Сохраняем обновленный файл
        await query.message.reply_text("Все фотографии раздела 'десерты' успешно удалены.")
        await query.answer()

    # Обработка очистки фотографий для "Наш персонал"
    elif query.data == "clear_photos_our_staff":
        data = load_data(ABOUT_US_FILE, {
            "contacts": {"text": "Контакты:\n[Ваше сообщение здесь]", "photos": []},
            "our_staff": {"text": "Наш персонал:\n[Ваше сообщение здесь]", "photos": []},
            "about_establishment": {"text": "О заведении:\n[Ваше сообщение здесь]", "photos": []}
        })
   
        if 'our_staff' in data and 'photos' in data['our_staff']:
            data['our_staff']['photos'] = []  # Очищаем список фото
            save_data(ABOUT_US_FILE, data)  # Сохраняем обновленный файл
            await query.message.reply_text("Все фотографии нашего персонала успешно удалены.")
        else:
            await query.message.reply_text("Ошибка: Не удалось найти данные для удаления фотографий о персонале.")
        
        await query.answer()
   
    # Обработка очистки фотографий для "О заведении"
    elif query.data == "clear_photos_about_establishment":
        data = load_data(ABOUT_US_FILE, {
            "contacts": {"text": "Контакты:\n[Ваше сообщение здесь]", "photos": []},
            "our_staff": {"text": "Наш персонал:\n[Ваше сообщение здесь]", "photos": []},
            "about_establishment": {"text": "О заведении:\n[Ваше сообщение здесь]", "photos": []}
        })
   
        if 'about_establishment' in data and 'photos' in data['about_establishment']:
            data['about_establishment']['photos'] = []  # Очищаем список фото
            save_data(ABOUT_US_FILE, data)  # Сохраняем обновленный файл
            await query.message.reply_text("Все фотографии раздела 'О заведении' успешно удалены.")
        else:
            await query.message.reply_text("Ошибка: Не удалось найти данные для удаления фотографий о заведении.")
        
        await query.answer()
    

    # Показ списка админов
    if query.data == "list_admins":
        admin_list = []
        for admin_id in admins:
            user_data = user_ids.get(str(admin_id))  # Получаем данные по admin_id
            print(f"Проверка admin_id: {admin_id}, user_data: {user_data}")  # Логируем admin_id и user_data
            
            if user_data and 'name' in user_data:
                admin_name = user_data['name']
                print(f"Найдено имя для {admin_id}: {admin_name}")  # Логируем найденное имя
            else:
                admin_name = str(admin_id)
                print(f"Имя не найдено для {admin_id}, выводим ID")  # Логируем, если имя не найдено
            
            admin_list.append(admin_name)

        print(f"Текущие админы: {admin_list}")  # Логируем список администраторов
        await query.message.reply_text(f"Текущие админы:\n" + "\n".join(admin_list))

    # Добавление нового админа
    elif query.data == "add_admin":
        await query.message.reply_text("Введите ID пользователя, которого хотите добавить в админы:")
        context.user_data['state'] = 'awaiting_admin_id'  # Устанавливаем уникальное состояние для добавления админа

    # Удаление админа
    elif query.data == "remove_admin":
        keyboard = [
            [InlineKeyboardButton(f"{user_ids[str(admin_id)]['name']}", callback_data=f"delete_admin_{admin_id}")]
            for admin_id in admins if str(admin_id) in user_ids  # Убедитесь, что user_ids содержит данные
        ]
        keyboard.append([InlineKeyboardButton("⬅ Назад", callback_data="go_back")])
        
        if keyboard:  # Проверяем, есть ли администраторы для удаления
            await query.message.reply_text("Выберите админа для удаления:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.message.reply_text("Список администраторов пуст.")

    # Установка сменщика
    elif query.data == "set_shift_admin":
        keyboard = [[InlineKeyboardButton(f"{admin_id}", callback_data=f"set_shift_{admin_id}")]
                    for admin_id in admins]
        keyboard.append([InlineKeyboardButton("⬅ Назад", callback_data="go_back")])
        await query.message.reply_text("Выберите админа для установки сменщиком:", reply_markup=InlineKeyboardMarkup(keyboard))

    # Рассылка сообщения
    if query.data == "broadcast_message":
        await query.message.reply_text("Введите сообщение для рассылки:")
        context.user_data['state'] = 'broadcast_message'  # Устанавливаем состояние для рассылки

    # Редактирование скидки
    elif query.data == "edit_discount":
        print("Пользователь нажал на кнопку редактирования скидки")  # Логируем
        await show_edit_discount_menu(query, context)  # Вызываем нужную функцию

    # Обработка нажатия на "Назад"
    elif query.data == "go_back":
        await show_admin_menu(query)

# Обработка удаления админа
async def handle_admin_removal(update: Update, context):
    query = update.callback_query
    await query.answer()
    admin_id = int(query.data.split('_')[2])  # Получаем ID админа из callback_data

    if admin_id in admins:
        admins.remove(admin_id)
        save_admins(admins)  # Сохраняем обновленный список админов
        await query.message.reply_text(f"Админ {admin_id} успешно удален.")
    else:
        await query.message.reply_text("Админ не найден.")

async def handle_shift_selection(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "take_shift":
        keyboard = [
            [InlineKeyboardButton("Администратор", callback_data="set_admin")],
            [InlineKeyboardButton("Кальянщик", callback_data="set_hookah_master")],
            [InlineKeyboardButton("⬅ Назад", callback_data="go_back")]
        ]
        await query.message.reply_text("Выберите роль:", reply_markup=InlineKeyboardMarkup(keyboard))

    # Если выбирают роль Администратора
    elif query.data == "set_admin":
        keyboard = [[InlineKeyboardButton(name, callback_data=f"choose_admin_{name}")]
                    for name in admin_names]
        keyboard.append([InlineKeyboardButton("⬅ Назад", callback_data="go_back")])
        await query.message.reply_text("Выберите администратора:", reply_markup=InlineKeyboardMarkup(keyboard))

    # Если выбирают роль Кальянщика
    elif query.data == "set_hookah_master":
        keyboard = [[InlineKeyboardButton(name, callback_data=f"choose_hookah_master_{name}")]
                    for name in hookah_master_names]
        keyboard.append([InlineKeyboardButton("⬅ Назад", callback_data="go_back")])
        await query.message.reply_text("Выберите кальянщика:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_edit_discount(update: Update, context):
    if is_admin(update.message.from_user.id):  # Проверка, что пользователь администратор
        await update.message.reply_text("Введите номер телефона пользователя для редактирования скидки:")
        context.user_data['awaiting_phone_for_discount'] = True
    else:
        await update.message.reply_text("У вас нет прав для редактирования скидок.")

async def show_booking_list(update, context):
    query = update.callback_query
    user_id = query.from_user.id

    # Проверяем права доступа
    if not is_admin(user_id):
        await query.message.reply_text("У вас нет прав для просмотра бронирований.")
        return

    # Ответ на callback_query, чтобы Telegram знал, что запрос был обработан
    await query.answer()

    today = datetime.now().date()
    two_days_later = today + timedelta(days=2)

    logging.info(f"Сегодняшняя дата: {today}, Через два дня: {two_days_later}")
    logging.info(f"Загруженные бронирования: {confirmed_reservations}")

    # Собираем бронирования на сегодня и следующие 2 дня
    booking_message = "Список подтверждённых бронирований на сегодня и следующие 2 дня:\n"
    for booking_id, booking in confirmed_reservations.items():
        booking_date_str = booking.get('date')  # Дата в формате 'дд-мм-гггг'

        try:
            # Преобразуем строку 'дд-мм-гггг' в объект datetime.date для сравнения
            booking_date = datetime.strptime(booking_date_str, '%d-%m-%Y').date()

            # Логируем дату бронирования для отладки
            logging.info(f"Дата бронирования ID {booking_id}: {booking_date}")

            # Проверяем, что дата находится в диапазоне от сегодня до двух дней вперед
            if today <= booking_date <= two_days_later:
                # Формируем сообщение с данными бронирования
                booking_message += (
                    f"Пользователь: {booking['user']}\n"
                    f"Телефон: {booking['phone']}\n"
                    f"Скидка: {booking['discount']} руб.\n"
                    f"Дата: {booking['date']}\n"
                    f"Гости: {booking['guests']}\n"
                    f"Время: {booking['time']}\n"
                    f"Комментарий: {booking['comment']}\n\n"
                )
            else:
                logging.info(f"Бронирование ID {booking_id} не входит в диапазон.")
        except ValueError as e:
            # Если формат даты неправильный, пропускаем это бронирование и логируем ошибку
            logging.error(f"Ошибка при обработке бронирования ID {booking_id}: {e}")
            continue

    if booking_message == "Список подтверждённых бронирований на сегодня и следующие 2 дня:\n":
        booking_message = "Нет подтверждённых бронирований на сегодня и следующие 2 дня."

    await query.message.reply_text(booking_message)

# Редактирование скидки
async def show_edit_discount_menu(update: Update, context):
    if user_ids:
        # Логируем список пользователей для проверки
        print(f"Текущие пользователи: {user_ids}")

        # Формируем список имен, номеров телефонов (последние 4 цифры) и скидок
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{user_data.get('name', 'Неизвестно')} {user_data['phone']} - {user_data.get('discount', 0)} руб.",
                    callback_data=f"select_phone_{user_data['phone']}"
                )
            ]
            for user_data in user_ids.values() 
            if 'phone' in user_data and user_data['phone'] and len(user_data['phone']) >= 4
        ]
        
        if keyboard:  # Если есть номера для выбора
            await update.message.reply_text(
                "Выберите номер телефона для изменения скидки:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text("В базе данных нет пользователей с номерами телефонов.")
    else:
        await update.message.reply_text("В базе данных нет пользователей.")

# Обработка выбора администратора или кальянщика
async def handle_staff_choice(update: Update, context):
    query = update.callback_query
    await query.answer()

    # Выбор Администратора
    if query.data.startswith("choose_admin_"):
        chosen_name = query.data.split('choose_admin_')[1]  # Получаем имя администратора
        active_staff["admin"] = chosen_name  # Обновляем администратора
        await query.message.reply_text(f"Теперь на смене Администратор: {chosen_name}.")

    # Выбор Кальянщика
    elif query.data.startswith("choose_hookah_master_"):
        chosen_name = query.data.split('choose_hookah_master_')[1]  # Получаем имя кальянщика
        active_staff["hookah_master"] = chosen_name  # Обновляем кальянщика
        await query.message.reply_text(f"Теперь на смене Кальянщик: {chosen_name}.")

    await query.message.delete()

# Обработка выбора пользователя для изменения скидки
async def handle_phone_selection(update: Update, context):
    query = update.callback_query
    await query.answer()

    # Извлекаем номер телефона из callback_data
    selected_phone = query.data.split('_')[2]
    context.user_data['phone_for_discount'] = selected_phone

    await query.message.reply_text(f"Вы выбрали номер телефона: {selected_phone}. Введите скидку в рублях для этого пользователя:")
    context.user_data['awaiting_discount'] = True  # Устанавливаем состояние для ожидания ввода скидки
    await query.message.delete()  # Удаляем старое сообщение

# Календарь для выбора даты
async def show_calendar(query, selected_date=None, current_month=None):
    if current_month is None:
        current_month = datetime.now().replace(day=1)

    # Получаем название месяца на английском и переводим его
    month_name = calendar.month_name[current_month.month]
    month_name_ru = {
        'January': 'Январь',
        'February': 'Февраль',
        'March': 'Март',
        'April': 'Апрель',
        'May': 'Май',
        'June': 'Июнь',
        'July': 'Июль',
        'August': 'Август',
        'September': 'Сентябрь',
        'October': 'Октябрь',
        'November': 'Ноябрь',
        'December': 'Декабрь'
    }
    # Преобразуем название месяца
    month_name_ru_translated = month_name_ru.get(month_name, month_name)

    # Создаем календарь для текущего месяца
    cal = calendar.Calendar(firstweekday=calendar.MONDAY)
    month_days = list(cal.itermonthdays(current_month.year, current_month.month))

    keyboard = []
    today = datetime.now().date()  # Получаем текущую дату

    # Кнопки для выбора даты
    week_row = []
    for idx, day in enumerate(month_days):
        if day == 0:
            # Пустые дни (не относящиеся к текущему месяцу)
            week_row.append(InlineKeyboardButton(" ", callback_data="ignore"))
        else:
            day_date = datetime(current_month.year, current_month.month, day).date()
            button_text = f"{day_date.day}"
            if day_date < today:  # Сравниваем объекты одного типа (date)
                button_text += "❌"  # Красный крестик на прошедших датах
            week_row.append(InlineKeyboardButton(button_text, callback_data=f"date_{day_date}"))

        # Добавляем неделю в клавиатуру
        if (idx + 1) % 7 == 0:
            keyboard.append(week_row)
            week_row = []

    # Добавляем последнюю неделю, если она не пуста
    if week_row:
        keyboard.append(week_row)

    # Кнопки для переключения между месяцами
    prev_month = (current_month - timedelta(days=1)).replace(day=1)
    next_month = (current_month + timedelta(days=31)).replace(day=1)
    keyboard.append([
        InlineKeyboardButton("<<", callback_data=f"calendar_{prev_month.isoformat()}"),
        InlineKeyboardButton(">>", callback_data=f"calendar_{next_month.isoformat()}")
    ])

    # Удаляем предыдущее сообщение с календарем
    await query.message.delete()

    # Отправляем новое сообщение с названием месяца на русском
    await query.message.reply_text(f"Выберите дату {month_name_ru_translated}:", reply_markup=InlineKeyboardMarkup(keyboard))

# Обработка выбора даты
async def handle_calendar(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("calendar_"):
        current_month = datetime.fromisoformat(query.data.split('_')[1])
        await show_calendar(query, current_month=current_month)
    elif query.data.startswith("date_"):
        selected_date_str = query.data.split('_')[1]
        user_id = query.from_user.id

        # Преобразуем строку с датой в объект datetime
        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()

        # Инициализируем запись бронирования
        if user_id not in reservations:
            reservations[user_id] = {}

        # Удаляем предыдущее сообщение
        await query.message.delete()

        # Сохраняем дату в формате "дд-мм-гггг"
        formatted_date = selected_date.strftime("%d-%m-%Y")
        reservations[user_id]['date'] = formatted_date

        # Переходим к выбору гостей
        keyboard = [[InlineKeyboardButton(f"{i}", callback_data=f"guests_{i}") for i in range(1, 11)]]
        await query.message.reply_text("Выберите количество гостей:", reply_markup=InlineKeyboardMarkup(keyboard))

        # Устанавливаем состояние пользователя как 'IN_BOOKING' (в процессе бронирования)
        user_states[user_id] = 'IN_BOOKING'

# Обработка выбора количества гостей
async def handle_guest_selection(update: Update, context):
    query = update.callback_query
    await query.answer()
    guests = query.data.split('_')[1]
    user_id = query.from_user.id
    await query.message.delete()

    if user_id not in reservations:
        reservations[user_id] = {}

    reservations[user_id]['guests'] = guests

    # Переход к выбору времени
    keyboard = []
    start_hour = 14  # Начинаем с 14:00
    end_hour = 26  # 02:00 следующего дня (24 + 2)

    for hour in range(start_hour, end_hour):
        row = []
        row.append(InlineKeyboardButton(f"{hour % 24}:00", callback_data=f"time_{hour % 24}:00"))
        row.append(InlineKeyboardButton(f"{hour % 24}:30", callback_data=f"time_{hour % 24}:30"))
        keyboard.append(row)

    await query.message.reply_text("Выберите время:", reply_markup=InlineKeyboardMarkup(keyboard))

## Обработка выбора времени
async def handle_time_selection(update: Update, context):
    query = update.callback_query
    await query.answer()
    time = query.data.split('_')[1]
    user_id = query.from_user.id

    if user_id not in reservations:
        reservations[user_id] = {}

    reservations[user_id]['time'] = time

    await query.message.delete()
    
    # Спрашиваем пожелания
    keyboard = [
        [InlineKeyboardButton("Пропустить", callback_data=f"skip_comment")]
    ]
    await query.message.reply_text("Есть ли какие-то пожелания? Напишите ваш комментарий.", reply_markup=InlineKeyboardMarkup(keyboard))

    # Ожидаем комментарий или пожелание от пользователя

async def skip_comment(update: Update, context):
    query = update.callback_query
    user_id = query.from_user.id  # Меняем на query.from_user.id
    
    if user_id not in reservations:
        reservations[user_id] = {}

    # Добавляем комментарий "Нет пожеланий"
    reservations[user_id]['comment'] = "Нет пожеланий"
    
    await query.message.delete()
    await query.message.reply_text("Пожалуйста, подождите подтверждения от администратора.")
    
    # Отправляем бронирование админу
    await send_reservation_to_admin(update, context, reservations[user_id])
    user_states[user_id] = 'IDLE'

def is_admin(user_id):
    # Проверяем, находится ли user_id в списке администраторов
    return user_id in admins

# Обработка текста администратора для обновления сообщений
async def handle_message(update: Update, context):
    user_id = update.message.from_user.id
    message_text = update.message.text
    photo = update.message.photo

    # Проверяем, если администратор редактирует "Контакты"
    if context.user_data.get('state') == 'edit_contacts':
        data = load_data(ABOUT_US_FILE, {"contacts": {"text": "", "photos": []}})
    
        if message_text:
            data["contacts"]["text"] = message_text
    
        if photo:
            if "photos" not in data["contacts"]:
                data["contacts"]["photos"] = []
            if len(data["contacts"]["photos"]) < 10:
                file_id = photo[-1].file_id
                new_photo_path = f"contacts_{file_id}.jpg"
                new_photo_file = await context.bot.get_file(file_id)
                await new_photo_file.download_to_drive(os.path.join(CURRENT_DIR, new_photo_path))
                data["contacts"]["photos"].append(new_photo_path)
            else:
                await update.message.reply_text("Достигнут лимит в 10 фотографий для контактов. Удалите одну, чтобы добавить новую.")
    
        save_data(ABOUT_US_FILE, data)
        await update.message.reply_text("Контакты успешно обновлены.")
        context.user_data['state'] = None
        return

    # Редактирование информации о персонале
    elif context.user_data.get('state') == 'edit_our_staff':
        data = load_data(ABOUT_US_FILE, {"our_staff": {"text": "", "photos": []}})
    
        if message_text:
            data["our_staff"]["text"] = message_text
    
        if photo:
            if "photos" not in data["our_staff"]:
                data["our_staff"]["photos"] = []
            if len(data["our_staff"]["photos"]) < 10:
                file_id = photo[-1].file_id
                new_photo_path = f"our_staff_{file_id}.jpg"
                new_photo_file = await context.bot.get_file(file_id)
                await new_photo_file.download_to_drive(os.path.join(CURRENT_DIR, new_photo_path))
                data["our_staff"]["photos"].append(new_photo_path)
            else:
                await update.message.reply_text("Достигнут лимит в 10 фотографий для информации о персонале. Удалите одну, чтобы добавить новую.")
    
        save_data(ABOUT_US_FILE, data)
        await update.message.reply_text("Информация о персонале успешно обновлена.")
        context.user_data['state'] = None
        return

    # Редактирование информации о заведении
    elif context.user_data.get('state') == 'edit_about_establishment':
        data = load_data(ABOUT_US_FILE, {"about_establishment": {"text": "", "photos": []}})

        if message_text:
            data["about_establishment"]["text"] = message_text

        if photo:
            if "photos" not in data["about_establishment"]:
                data["about_establishment"]["photos"] = []
            if len(data["about_establishment"]["photos"]) < 10:
                file_id = photo[-1].file_id
                new_photo_path = f"about_establishment_{file_id}.jpg"
                new_photo_file = await context.bot.get_file(file_id)
                await new_photo_file.download_to_drive(os.path.join(CURRENT_DIR, new_photo_path))
                data["about_establishment"]["photos"].append(new_photo_path)
            else:
                await update.message.reply_text("Достигнут лимит в 10 фотографий для информации о заведении. Удалите одну, чтобы добавить новую.")

        save_data(ABOUT_US_FILE, data)
        await update.message.reply_text("Информация о заведении успешно обновлена.")
        context.user_data['state'] = None
        return
    
        # Обработка редактирования разделов Меню Перчини
    elif context.user_data.get('state') == 'edit_pizzas':
        data = load_pizzas()
        if message_text:
            data["text"] = message_text
        if photo:
            if "photos" not in data:
                data["photos"] = []
            if len(data["photos"]) < 10:
                file_id = photo[-1].file_id
                new_photo_path = f"pizzas_{file_id}.jpg"
                new_photo_file = await context.bot.get_file(file_id)
                await new_photo_file.download_to_drive(os.path.join(CURRENT_DIR, new_photo_path))
                data["photos"].append(new_photo_path)
        save_pizzas(data)
        await update.message.reply_text("Раздел Пиццы успешно обновлён.")
        context.user_data['state'] = None
        return
    
    elif context.user_data.get('state') == 'edit_pasta':
        data = load_pasta()
        if message_text:
            data["text"] = message_text
        if photo:
            if "photos" not in data:
                data["photos"] = []
            if len(data["photos"]) < 10:
                file_id = photo[-1].file_id
                new_photo_path = f"pasta_{file_id}.jpg"
                new_photo_file = await context.bot.get_file(file_id)
                await new_photo_file.download_to_drive(os.path.join(CURRENT_DIR, new_photo_path))
                data["photos"].append(new_photo_path)
        save_pasta(data)
        await update.message.reply_text("Раздел Паста успешно обновлён.")
        context.user_data['state'] = None
        return
    
    elif context.user_data.get('state') == 'edit_hot':
        data = load_hot()
        if message_text:
            data["text"] = message_text
        if photo:
            if "photos" not in data:
                data["photos"] = []
            if len(data["photos"]) < 10:
                file_id = photo[-1].file_id
                new_photo_path = f"hot_{file_id}.jpg"
                new_photo_file = await context.bot.get_file(file_id)
                await new_photo_file.download_to_drive(os.path.join(CURRENT_DIR, new_photo_path))
                data["photos"].append(new_photo_path)
        save_hot(data)
        await update.message.reply_text("Раздел Горячее успешно обновлён.")
        context.user_data['state'] = None
        return
    
    elif context.user_data.get('state') == 'edit_focaccia_dip':
        data = load_focaccia_dip()
        if message_text:
            data["text"] = message_text
        if photo:
            if "photos" not in data:
                data["photos"] = []
            if len(data["photos"]) < 10:
                file_id = photo[-1].file_id
                new_photo_path = f"focaccia_dip_{file_id}.jpg"
                new_photo_file = await context.bot.get_file(file_id)
                await new_photo_file.download_to_drive(os.path.join(CURRENT_DIR, new_photo_path))
                data["photos"].append(new_photo_path)
        save_focaccia_dip(data)
        await update.message.reply_text("Раздел Фокачча и дипы успешно обновлён.")
        context.user_data['state'] = None
        return
    
    elif context.user_data.get('state') == 'edit_snacks':
        data = load_snacks()
        if message_text:
            data["text"] = message_text
        if photo:
            if "photos" not in data:
                data["photos"] = []
            if len(data["photos"]) < 10:
                file_id = photo[-1].file_id
                new_photo_path = f"snacks_{file_id}.jpg"
                new_photo_file = await context.bot.get_file(file_id)
                await new_photo_file.download_to_drive(os.path.join(CURRENT_DIR, new_photo_path))
                data["photos"].append(new_photo_path)
        save_snacks(data)
        await update.message.reply_text("Раздел Закуски успешно обновлён.")
        context.user_data['state'] = None
        return
    
    elif context.user_data.get('state') == 'edit_salads':
        data = load_salads()
        if message_text:
            data["text"] = message_text
        if photo:
            if "photos" not in data:
                data["photos"] = []
            if len(data["photos"]) < 10:
                file_id = photo[-1].file_id
                new_photo_path = f"salads_{file_id}.jpg"
                new_photo_file = await context.bot.get_file(file_id)
                await new_photo_file.download_to_drive(os.path.join(CURRENT_DIR, new_photo_path))
                data["photos"].append(new_photo_path)
        save_salads(data)
        await update.message.reply_text("Раздел Салаты успешно обновлён.")
        context.user_data['state'] = None
        return
    
    elif context.user_data.get('state') == 'edit_soups':
        data = load_soups()
        if message_text:
            data["text"] = message_text
        if photo:
            if "photos" not in data:
                data["photos"] = []
            if len(data["photos"]) < 10:
                file_id = photo[-1].file_id
                new_photo_path = f"soups_{file_id}.jpg"
                new_photo_file = await context.bot.get_file(file_id)
                await new_photo_file.download_to_drive(os.path.join(CURRENT_DIR, new_photo_path))
                data["photos"].append(new_photo_path)
        save_soups(data)
        await update.message.reply_text("Раздел Супы успешно обновлён.")
        context.user_data['state'] = None
        return
    
    elif context.user_data.get('state') == 'edit_grill':
        data = load_grill()
        if message_text:
            data["text"] = message_text
        if photo:
            if "photos" not in data:
                data["photos"] = []
            if len(data["photos"]) < 10:
                file_id = photo[-1].file_id
                new_photo_path = f"grill_{file_id}.jpg"
                new_photo_file = await context.bot.get_file(file_id)
                await new_photo_file.download_to_drive(os.path.join(CURRENT_DIR, new_photo_path))
                data["photos"].append(new_photo_path)
        save_grill(data)
        await update.message.reply_text("Раздел Гриль успешно обновлён.")
        context.user_data['state'] = None
        return
    
    elif context.user_data.get('state') == 'edit_desserts':
        data = load_desserts()
        if message_text:
            data["text"] = message_text
        if photo:
            if "photos" not in data:
                data["photos"] = []
            if len(data["photos"]) < 10:
                file_id = photo[-1].file_id
                new_photo_path = f"desserts_{file_id}.jpg"
                new_photo_file = await context.bot.get_file(file_id)
                await new_photo_file.download_to_drive(os.path.join(CURRENT_DIR, new_photo_path))
                data["photos"].append(new_photo_path)
        save_desserts(data)
        await update.message.reply_text("Раздел Десерты успешно обновлён.")
        context.user_data['state'] = None
        return


    # Обработка редактирования эксклюзивного меню
    elif context.user_data.get('state') == 'edit_exclusive_menu':
        data = load_exclusive_menu()

        if message_text:
            data["text"] = message_text

        if photo:
            if "photos" not in data:
                data["photos"] = []
            if len(data["photos"]) < 10:
                file_id = photo[-1].file_id
                new_photo_path = f"exclusive_menu_{file_id}.jpg"
                new_photo_file = await context.bot.get_file(file_id)
                await new_photo_file.download_to_drive(os.path.join(CURRENT_DIR, new_photo_path))
                data["photos"].append(new_photo_path)
            else:
                await update.message.reply_text("Достигнут лимит в 10 фотографий для эксклюзивного меню. Удалите одну, чтобы добавить новую.")

        save_exclusive_menu(data)
        await update.message.reply_text("Эксклюзивное меню успешно обновлено.")
        context.user_data['state'] = None
        return

    # Редактирование сезонного меню
    elif context.user_data.get('state') == 'edit_seasonal_menu':
        data = load_data(SEASONAL_MENU_FILE, {"text": "", "photos": []})

        if message_text:
            data["text"] = message_text

        if photo:
            if "photos" not in data:
                data["photos"] = []
            if len(data["photos"]) < 10:
                file_id = photo[-1].file_id
                new_photo_path = f"seasonal_menu_{file_id}.jpg"
                new_photo_file = await context.bot.get_file(file_id)
                await new_photo_file.download_to_drive(os.path.join(CURRENT_DIR, new_photo_path))
                data["photos"].append(new_photo_path)
            else:
                await update.message.reply_text("Достигнут лимит в 10 фотографий для сезонного меню. Удалите одну, чтобы добавить новую.")

        save_data(SEASONAL_MENU_FILE, data)
        await update.message.reply_text("Сезонное меню успешно обновлено.")
        context.user_data['state'] = None
        return

    # Редактирование информации о мероприятиях
    elif context.user_data.get('state') == 'edit_events':
        data = load_data(EVENTS_FILE, {"text": "", "photos": []})

        if message_text:
            data["text"] = message_text

        if photo:
            if "photos" not in data:
                data["photos"] = []
            if len(data["photos"]) < 10:
                file_id = photo[-1].file_id
                new_photo_path = f"events_{file_id}.jpg"
                new_photo_file = await context.bot.get_file(file_id)
                await new_photo_file.download_to_drive(os.path.join(CURRENT_DIR, new_photo_path))
                data["photos"].append(new_photo_path)
            else:
                await update.message.reply_text("Достигнут лимит в 10 фотографий для мероприятий. Удалите одну, чтобы добавить новую.")

        save_data(EVENTS_FILE, data)
        await update.message.reply_text("Мероприятия успешно обновлены.")
        context.user_data['state'] = None
        return

    # Проверяем, если сообщение содержит фото или видео для рассылки

    if update.message.photo or update.message.video:
        # Логика рассылки, если состояние администратора - "broadcast_message"
        if context.user_data.get('state') == 'broadcast_message':
            file_id = update.message.photo[-1].file_id if update.message.photo else update.message.video.file_id
            message_text = update.message.caption if update.message.caption else ""

            if update.message.photo:
                await broadcast_message(context, message_text, photo=file_id, exclude_user_id=user_id)
            elif update.message.video:
                await broadcast_message(context, message_text, video=file_id, exclude_user_id=user_id)

            # Подтверждение отправки рассылки
            await update.message.reply_text("Сообщение отправлено всем пользователям.")
            context.user_data['state'] = None  # Сбрасываем состояние
        return

    # Проверяем, если администратор вводит новый процент скидки
    if context.user_data.get('awaiting_discount'):
        try:
            discount = int(message_text)
            phone = context.user_data.get('phone_for_discount')

            # Находим пользователя по номеру телефона и сохраняем скидку
            for user_id, user_data in user_ids.items():
                if user_data.get('phone') == phone:
                    user_data['discount'] = discount
                    save_user_ids(user_ids)
                    # Уведомляем администратора о смене скидки
                    await update.message.reply_text(f"Скидка для пользователя {phone} успешно изменена на - {discount} руб.")

                    # Отправляем сообщение самому пользователю о новой скидке
                    await context.bot.send_message(chat_id=user_id, text=f"Ваша новая скидка на классический кальян - {discount} руб.!")

                    break

            context.user_data['awaiting_discount'] = False  # Сбрасываем состояние
        except ValueError:
            await update.message.reply_text("Введите корректное число для скидки.")
        return
    
    # Шаг 1: Обрабатываем ввод номера телефона
    if context.user_data.get('awaiting_phone'):
        if message_text.isdigit() and len(message_text) >= 10:  # Проверяем, что это номер телефона
            if str(user_id) not in user_ids:  # Используем строковый ключ
                user_ids[str(user_id)] = {}  # Инициализируем пустой словарь для пользователя
            user_ids[str(user_id)]['phone'] = message_text

            # Сохраняем номер телефона
            save_user_ids(user_ids)

            # Запрашиваем имя после получения телефона
            await update.message.reply_text("Спасибо! Теперь введите ваше имя.")
            context.user_data['awaiting_phone'] = False
            context.user_data['awaiting_name'] = True
        else:
            await update.message.reply_text("Пожалуйста, введите корректный номер телефона (не менее 10 цифр).")
        return

    # Шаг 2: Обрабатываем ввод имени
    if context.user_data.get('awaiting_name'):
        if len(message_text) > 0:  # Проверяем, что имя не пустое
            user_ids[str(user_id)]['name'] = message_text

            # Сохраняем имя
            save_user_ids(user_ids)

            await update.message.reply_text(f"Спасибо! Ваши данные сохранены.\nНомер телефона: {user_ids[str(user_id)]['phone']}\nИмя: {message_text}")

            context.user_data['awaiting_name'] = False  # Сбрасываем ожидание
            # Продолжаем обычную логику после сохранения данных
            await start(update, context)
        else:
            await update.message.reply_text("Пожалуйста, введите ваше имя.")
        return
    
    
    # Проверяем, если администратор отправляет текст для рассылки
    if context.user_data.get('state') == 'broadcast_message':
        # Получаем ID администратора, который отправляет сообщение
        admin_id = update.message.from_user.id

        # Отправляем сообщение всем пользователям, кроме самого администратора
        await broadcast_message(context, message_text, exclude_user_id=admin_id)

        # Подтверждение отправки рассылки
        await update.message.reply_text("Сообщение отправлено всем пользователям.")
        context.user_data['state'] = None  # Сбрасываем состояние после рассылки
        return
    
    # Проверяем, если администратор вводит новый ID для добавления
    if context.user_data.get('state') == 'awaiting_admin_id':  # Уникальное состояние для добавления админа
        try:
            new_admin_id = int(message_text)
            if new_admin_id not in admins:
                admins.append(new_admin_id)
                save_admins(admins)  # Сохраняем обновленный список админов
                await update.message.reply_text(f"Пользователь {new_admin_id} добавлен в админы.")
            else:
                await update.message.reply_text(f"Пользователь {new_admin_id} уже является админом.")
        except ValueError:
            await update.message.reply_text("Введите корректный ID пользователя.")
        
        context.user_data['state'] = None  # Сбрасываем состояние после добавления
        return

# Если это администратор
    if user_states.get(user_id) == 'IN_BOOKING':
        reservation = reservations.get(user_id, {})
        reservations[user_id]['comment'] = update.message.text
        await update.message.reply_text("Пожалуйста, подождите подтверждения от администратора.")
        await send_reservation_to_admin(update, context, reservations[user_id])
        user_states[user_id] = 'IDLE'

    elif is_admin(user_id):
        # Проверка, участвует ли администратор в процессе уточнения (или делает свою бронь)
        if user_id in admin_clarifications:
            # Это означает, что администратор уточняет бронь другого пользователя (не свою)
            target_user_id = admin_clarifications[user_id]
            clarification_message = update.message.text
            await context.bot.send_message(chat_id=target_user_id, text=f"Администратор уточняет: {clarification_message}")
            del admin_clarifications[user_id]  # Удаляем процесс уточнения после завершения
            user_states[user_id] = 'IDLE'  # Сбрасываем состояние администратора

        elif user_states.get(user_id) == 'WAITING_FOR_CLARIFICATION':
            # Если администратор участвует в уточнении своей собственной брони
            reservations[user_id]['clarification'] = update.message.text
            await update.message.reply_text(f"Ваше сообщение передано другим администраторам, ожидайте.")
            
            # Отправляем уточнение всем остальным администраторам, кроме того, кто инициировал бронирование
            clarification_message = (
                f"Администратор {update.message.from_user.mention_html()} уточняет свою бронь:\n"
                f"{reservations[user_id]['clarification']}"
            )

            # Проходим по всем администраторам и отправляем уточнение всем, кроме текущего
            for admin_id in admins:
                if admin_id != user_id:  # Исключаем администратора, который инициировал бронирование
                    try:
                        await context.bot.send_message(
                            chat_id=admin_id,
                            text=clarification_message,
                            parse_mode=ParseMode.HTML
                        )
                    except Exception as e:
                        print(f"Не удалось отправить уточнение админу {admin_id}: {e}")

            user_states[user_id] = 'IDLE'  # Сбрасываем состояние администратора после уточнения

        elif any(user_id == clarifier_id for clarifier_id in admin_clarifications.values()):
            # Находим ID администратора, для которого идет уточнение (автор брони)
            target_user_id = next(
                key for key, clarifier_id in admin_clarifications.items() if clarifier_id == user_id
            )
            clarification_message = update.message.text
            await context.bot.send_message(chat_id=target_user_id, text=f"Пользователь уточняет: {clarification_message}")
            del admin_clarifications[target_user_id]  # Удаляем процесс уточнения после завершения
            user_states[user_id] = 'IDLE'  # Сбрасываем состояние администратора

        else:
            await update.message.reply_text("Вы не начали процесс уточнения бронирования.")
        return

# Если это обычный пользователь
    else:
        if user_states.get(user_id) == 'IN_BOOKING':
            reservation = reservations.get(user_id, {})
            reservations[user_id]['comment'] = update.message.text
            await update.message.reply_text("Пожалуйста, подождите подтверждения от администратора.")
            await send_reservation_to_admin(update, context, reservations[user_id])
            user_states[user_id] = 'IDLE'  # Сбрасываем состояние пользователя после брони
        elif user_states.get(user_id) == 'WAITING_FOR_CLARIFICATION':
            reservations[user_id]['clarification'] = update.message.text
            await update.message.reply_text(f"Ваше сообщение передано администратору, ожидайте.")
            await send_clarification_to_admin(update, context, reservations[user_id])
            user_states[user_id] = 'IDLE'  # Сбрасываем состояние пользователя после уточнения
        else:
            await update.message.reply_text("Вы не начинали бронирование.")
        return

# Обработка уточнения бронирования от администратора
async def clarify_reservation(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split('_')[1])

    admin_clarifications[query.from_user.id] = user_id  # Запоминаем ID пользователя для уточнения

    # Изменяем состояние пользователя на уточнение
    user_states[user_id] = 'WAITING_FOR_CLARIFICATION'

    await query.message.reply_text("Напишите сообщение для уточнения брони пользователя.")

# Отправляем запрос админу
async def send_reservation_to_admin(update: Update, context, reservation):
    if update.message:
        user_id = update.message.from_user.id
        mention_html = update.message.from_user.mention_html()
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
        mention_html = update.callback_query.from_user.mention_html()
    else:
        return  # Если ни то, ни другое, просто выходим

    add_user_id(user_id)

    # Получаем данные пользователя (имя, телефон и выигрыш)
    user_data = user_ids.get(str(user_id), {})
    user_name = user_data.get('name', 'Не указано')
    user_phone = user_data.get('phone', 'Не указано')
    user_discount = user_data.get('discount', 0)
    user_prize = user_data.get('won_prize', None)

    # Основное сообщение с бронированием
    message = (
        f"Пользователь: {mention_html}\n"
        f"Данные: {user_name} {user_phone}\n"
        f"Скидка: {user_discount} руб.\n"
        f"Дата: {reservation['date']}\n"
        f"Гости: {reservation['guests']}\n"
        f"Время: {reservation['time']}\n"
        f"Комментарий: {reservation.get('comment', 'Нет пожеланий')}"
    )

    # Если пользователь выиграл приз, добавляем эту информацию в сообщение для админа
    if user_prize:
        message += f"\n🎁 Выиграл приз: {user_prize}"
        # После первого уведомления об этом выигрыше, очищаем поле, чтобы больше не повторялось
        user_ids[str(user_id)]['won_prize'] = None
        save_user_ids(user_ids)  # Сохраняем изменения в файл

    # Определяем клавиатуру
    keyboard = [
        [InlineKeyboardButton("Подтвердить бронь", callback_data=f"confirm_{user_id}"),
         InlineKeyboardButton("Уточнить бронь", callback_data=f"clarify_{user_id}")]
    ]

    # Отправляем сообщение другим администраторам (кроме того, кто сделал бронь)
    for admin_id in admins:
        if admin_id != user_id:  # Исключаем администратора, который делает бронирование
            await context.bot.send_message(
                chat_id=admin_id,
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )

    # Изменяем состояние пользователя на "Ожидание"
    user_states[user_id] = 'IDLE'

    # Если администратор сделал бронь, ставим его в статус обычного пользователя для этой брони
    if is_admin(user_id):
        user_states[user_id] = 'USER_IN_BOOKING'  # Устанавливаем статус как обычного пользователя

# Отправляем уточнение админу
async def send_clarification_to_admin(update: Update, context, reservation):
    user_id = update.message.from_user.id

    # Сообщение с уточнением
    clarification_message = (
        f"Пользователь: {update.message.from_user.mention_html()}\n"
        f"Уточнение: {reservation.get('clarification', 'Нет уточнений')}"
    )

    # Кнопки для администратора
    keyboard = [
        [InlineKeyboardButton("Подтвердить бронь", callback_data=f"confirm_{user_id}"),
         InlineKeyboardButton("Уточнить бронь", callback_data=f"clarify_{user_id}")]
    ]

    # Отправляем новое сообщение всем администраторам с уточнением
    for admin_id in admins:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=clarification_message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Не удалось отправить сообщение админу {admin_id}: {e}")

    # Изменяем состояние пользователя на "Ожидание"
    user_states[user_id] = 'IDLE'

# Подтверждение брони и сброс
async def confirm_reservation(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = int(query.data.split('_')[1])

    if user_id not in reservations:
        await query.message.delete()
        return

    reservation = reservations[user_id]

    if reservation.get('confirmed', False):
        await query.message.delete()
    else:
        reservation['confirmed'] = True

        user_data = user_ids.get(str(user_id), {})
        user_name = user_data.get('name', 'Не указано')
        user_phone = user_data.get('phone', 'Не указано')
        user_discount = user_data.get('discount', 0)

        confirmed_reservations[user_id] = {
            'user': user_name,
            'phone': user_phone,
            'discount': user_discount,
            'date': reservation['date'],
            'guests': reservation['guests'],
            'time': reservation['time'],
            'comment': reservation.get('comment', 'Нет пожеланий'),
        }

        # Сохранение в файл
        save_reservations()

        # Формируем сообщение с информацией о подтвержденной брони
        confirmation_message = (
            f"Ваша бронь подтверждена!\n"
            f"Ждём вас {reservation['date']} в {reservation['time']} с нетерпением к нам в гости!"
        )

        await context.bot.send_message(chat_id=user_id, text=confirmation_message)
        reset_user_state(user_id)
        await query.message.delete()

# Сброс состояния пользователя
def reset_user_state(user_id):
    global reservations  # Указываем, что работаем с глобальной переменной

    if user_id in reservations:
        del reservations[user_id]
        user_states[user_id] = 'IDLE'  # Сбрасываем состояние в IDLE
        print(f"Состояние пользователя {user_id} успешно сброшено.")  # Для отладки
    else:
        print(f"Пользователь {user_id} не имеет активной брони.")  # Для отладки

# Удаление администратора
async def remove_admin(update: Update, context):
    if is_main_admin(update.message.from_user.id):
        if context.args:
            admin_id_to_remove = int(context.args[0])
            if admin_id_to_remove in admins:
                admins.remove(admin_id_to_remove)
                save_admins(admins)

                # Получаем данные пользователя по ID администратора
                user_data = user_ids.get(str(admin_id_to_remove))

                # Если нашли данные, используем имя, иначе показываем ID
                admin_name = user_data['name'] if user_data and 'name' in user_data else str(admin_id_to_remove)

                await update.message.reply_text(f"Администратор {admin_name} удалён.")
            else:
                await update.message.reply_text("Этот пользователь не является администратором.")
        else:
            await update.message.reply_text("Пожалуйста, укажите ID администратора для удаления.")
    else:
        await update.message.reply_text("У вас нет прав для удаления администратора.")

# Список администраторов
async def admin_list(update: Update, context):
    if is_main_admin(update.message.from_user.id):
        if admins:
            admin_list = []
            print("Проверка: user_ids содержимое:", user_ids)  # Выводим содержимое user_ids для проверки

            for admin_id in admins:
                user_data = user_ids.get(str(admin_id))
                if user_data and 'name' in user_data:
                    admin_name = user_data['name']
                    print(f"Найдено имя для {admin_id}: {admin_name}")  # Логируем найденное имя
                else:
                    admin_name = str(admin_id)  # Если имя не найдено, используем ID
                    print(f"Имя не найдено для {admin_id}, выводим ID")  # Логируем, если имя не найдено

                admin_list.append(admin_name)
            
            await update.message.reply_text("Список администраторов:\n" + "\n".join(admin_list))
        else:
            await update.message.reply_text("Список администраторов пуст.")
    else:
        await update.message.reply_text("У вас нет прав для просмотра списка администраторов.")

# Команды, доступные только главному администратору
async def add_admin(update: Update, context):
    if is_main_admin(update.message.from_user.id):
        if context.args:
            new_admin_id = int(context.args[0])
            if new_admin_id not in admins:
                admins.append(new_admin_id)
                save_admins(admins)
                await update.message.reply_text(f"Администратор {new_admin_id} добавлен.")
            else:
                await update.message.reply_text("Этот пользователь уже администратор.")
        else:
            await update.message.reply_text("Пожалуйста, укажите ID пользователя для добавления в администраторы.")
    else:
        await update.message.reply_text("У вас нет прав для добавления администратора.")

# Функция для отправки фото по file_id
async def broadcast_message(context, message_text, photo=None, video=None, exclude_user_id=None):
    # Проходим по всем пользователям
    for user_id in user_ids:
        # Если пользователь не является отправителем, продолжаем рассылку
        if str(user_id) != str(exclude_user_id):
            try:
                # Если передано фото, отправляем фото
                if photo:
                    await context.bot.send_photo(chat_id=user_id, photo=photo, caption=message_text)
                # Если передано видео, отправляем видео
                elif video:
                    await context.bot.send_video(chat_id=user_id, video=video, caption=message_text)
                # В противном случае отправляем текст
                else:
                    await context.bot.send_message(chat_id=user_id, text=message_text)
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

# Получение файла и отправка по его file_id
async def send_broadcast(update: Update, context):
    # Только для администраторов
    if not is_admin(update.message.from_user.id):
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return
    
    # Получаем текст сообщения от администратора
    message_text = " ".join(context.args)
    
    # Если текст не указан и нет фото/видео
    if not message_text and not update.message.photo and not update.message.video:
        await update.message.reply_text("Введите сообщение или прикрепите фото/видео для отправки.")
        return
    
    # Получаем фото и видео (если есть)
    photo = update.message.photo[-1].file_id if update.message.photo else None
    video = update.message.video.file_id if update.message.video else None
    
    # Отправляем сообщение всем пользователям
    await broadcast_message(context, message_text, photo=photo, video=video)
    
    # Подтверждение отправки рассылки
    await update.message.reply_text("Сообщение отправлено всем пользователям.")

    # Сбрасываем состояние администратора, если он был в состоянии рассылки
    if context.user_data.get('state') == 'broadcast_message':
        context.user_data['state'] = None

# Сохранение списка админов в файл
def save_admins(admins):
    with open(ADMINS_FILE, 'w') as file:
        json.dump(admins, file)

# Загрузка списка админов из файла
def load_admins():
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, 'r') as file:
            return json.load(file)
    return []

# Обновленный список хендлеров для редактирования
def add_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_admin", add_admin))
    app.add_handler(CommandHandler("remove_admin", remove_admin))
    app.add_handler(CommandHandler("admin_list", admin_list))
    app.add_handler(CommandHandler("broadcast", send_broadcast))
    app.add_handler(CommandHandler("edit_discount", handle_edit_discount))
    app.add_handler(CommandHandler("booking_list", show_booking_list))

    app.add_handler(CallbackQueryHandler(handle_main_menu_buttons, pattern=r"^(play_game|book_table|perchini_menu|exclusive_menu|seasonal_menu|about_us|events|contacts|our_staff|about_establishment|about_creator|admin_menu|view_archive|back_to_main|back_to_menu|back_to_about_us)$"))
    app.add_handler(CallbackQueryHandler(handle_calendar, pattern=r"^calendar_"))
    app.add_handler(CallbackQueryHandler(handle_calendar, pattern=r"^date_"))
    app.add_handler(CallbackQueryHandler(handle_guest_selection, pattern=r"^guests_"))
    app.add_handler(CallbackQueryHandler(handle_time_selection, pattern=r"^time_"))
    app.add_handler(CallbackQueryHandler(skip_comment, pattern=r"^skip_comment$"))
    app.add_handler(CallbackQueryHandler(confirm_reservation, pattern=r"^confirm_"))
    app.add_handler(CallbackQueryHandler(clarify_reservation, pattern=r"^clarify_"))
    app.add_handler(CallbackQueryHandler(handle_shift_selection, pattern=r"^(take_shift|set_admin|set_hookah_master)$"))
    app.add_handler(CallbackQueryHandler(handle_staff_choice, pattern=r"^choose_admin_|choose_hookah_master_"))
    app.add_handler(CallbackQueryHandler(handle_admin_menu, pattern=r"^(clear_photos_exclusive_menu|clear_photos_seasonal_menu|clear_photos_events|clear_photos_contacts|clear_photos_our_staff|clear_photos_about_establishment|clear_photos_perchini_menu|list_admins|add_admin|remove_admin|broadcast_message|edit_discount|edit_exclusive_menu|edit_seasonal_menu|edit_events|edit_perchini_menu|go_back)$"))
    app.add_handler(CallbackQueryHandler(handle_admin_removal, pattern=r"^delete_admin_\d+$"))
    app.add_handler(CallbackQueryHandler(handle_phone_selection, pattern=r"^select_phone_"))
    app.add_handler(CallbackQueryHandler(show_booking_list, pattern=r"^booking_list$"))
    app.add_handler(CallbackQueryHandler(handle_about_us_edit, pattern=r"^(edit_contacts|edit_our_staff|edit_about_establishment)$"))
    app.add_handler(CallbackQueryHandler(handle_back_about, pattern=r"^back_to_about_us$"))
    app.add_handler(CallbackQueryHandler(handle_back_button, pattern=r"^back_to_menu$"))
    app.add_handler(CallbackQueryHandler(handle_perchini_submenu, pattern=r"^(pizzas|pasta|hot|focaccia_dip|snacks|salads|soups|grill|desserts)$"))
    app.add_handler(CallbackQueryHandler(handle_edit_perchini_item, pattern=r"^(edit_pizzas|edit_pasta|edit_hot|edit_focaccia_dip|edit_snacks|edit_salads|edit_soups|edit_grill|edit_desserts)$"))
    # Хендлеры для очистки фотографий меню Перчини
    app.add_handler(CallbackQueryHandler(handle_admin_menu, pattern=r"^clear_photos_pizzas$"))
    app.add_handler(CallbackQueryHandler(handle_admin_menu, pattern=r"^clear_photos_pasta$"))
    app.add_handler(CallbackQueryHandler(handle_admin_menu, pattern=r"^clear_photos_hot$"))
    app.add_handler(CallbackQueryHandler(handle_admin_menu, pattern=r"^clear_photos_focaccia_dip$"))
    app.add_handler(CallbackQueryHandler(handle_admin_menu, pattern=r"^clear_photos_snacks$"))
    app.add_handler(CallbackQueryHandler(handle_admin_menu, pattern=r"^clear_photos_salads$"))
    app.add_handler(CallbackQueryHandler(handle_admin_menu, pattern=r"^clear_photos_soups$"))
    app.add_handler(CallbackQueryHandler(handle_admin_menu, pattern=r"^clear_photos_grill$"))
    app.add_handler(CallbackQueryHandler(handle_admin_menu, pattern=r"^clear_photos_desserts$"))

    # Хендлер для выбора редактируемого сообщения
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))  # Обработка фото
    app.add_handler(MessageHandler(filters.VIDEO, handle_message))  # Обработка видео
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Обработка текста

# Добавляем обработчики
add_handlers(app)
# Добавляем задачу в планировщик только один раз
existing_jobs = app.job_queue.get_jobs_by_name('cleanup_old_reservations')

if not existing_jobs:
    app.job_queue.run_repeating(cleanup_old_reservations, interval=timedelta(hours=1), first=timedelta(seconds=10), name='cleanup_old_reservations')

app.run_polling()
