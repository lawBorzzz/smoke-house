import os
import json
import asyncio  # Импорт для использования паузы
import calendar  # Для получения названия месяца
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import logging

logging.basicConfig(level=logging.INFO)

# Ваш токен и настройка админов
TOKEN = '7692845826:AAEWYoo1bFU22LNa79-APy_iZyio2dwc9zA'
MAIN_ADMIN_IDS = [1980610942, 394468757]  # Измените на ваш ID

# Пути к файлам
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ADMINS_FILE = os.path.join(CURRENT_DIR, 'admins.json')
USER_IDS_FILE = os.path.join(CURRENT_DIR, 'user_ids.json')

# Хранение 
user_states = {}    # Словарь для хранения состояний пользователей
reservations = {} # Словарь для хранения бронирований
confirmed_reservations = {}  # Здесь будем хранить все подтверждённые брони
admin_clarifications = {}  # Словарь для уточнения администратором
clarifying_reservation = {} # для отслеживания запросов на уточнение брони

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

# Добавляем пользователя в словарь, если его там еще нет
def add_user_id(user_id):
    user_id_str = str(user_id)  # Преобразуем user_id в строку для использования в качестве ключа
    if user_id_str not in user_ids:
        user_ids[user_id_str] = {
            "phone": "",  # Оставляем пустым, чтобы позже заполнить
            "name": "",   # Аналогично для имени
            "discount": 0  # Добавляем скидку по умолчанию — 0%
        }
    else:
        # Если пользователь существует, проверяем наличие поля discount
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
# Роли сотрудников
# Доступные имена для выбора
admin_names = ["Маша", "Аня", "Паша"]
hookah_master_names = ["Родион", "Паша", "Андрей"]

# Активные сотрудники
active_staff = {
    "admin": "Маша",  # Изначально выбранный администратор
    "hookah_master": "Родион"  # Изначально выбранный кальянщик
}

# Инициализация приложения
app = Application.builder().token(TOKEN).build()

def is_admin(user_id):
    return user_id in admins

# Функция для сброса состояния пользователя
def reset_user_state(user_id):
    if user_id in reservations:
        del reservations[user_id]

# Главное меню с запросом номера телефона и имени
async def start(update: Update, context):
    user_id = update.message.from_user.id
    
    # Добавляем пользователя, если его нет
    add_user_id(user_id)

    user_data = user_ids.get(str(user_id), {})

    # Проверяем наличие номера телефона и имени
    if 'phone' not in user_data or user_data['phone'] == "":
        await update.message.reply_text("Здравствуйте! Рады приветствовать вас в Smoke House! \nЗаполняя анкету вы даете согласие на обработку персональных данных. \nПожалуйста, введите ваш номер телефона.")
        context.user_data['awaiting_phone'] = True
        return
    if 'name' not in user_data or user_data['name'] == "":
        await update.message.reply_text("Пожалуйста, введите ваше имя.")
        context.user_data['awaiting_name'] = True
        return

    # Если данные уже есть, продолжаем как обычно
    greeting = f"Добро пожаловать в Smoke House, {user_data['name']}!"

    # Добавляем информацию о скидке, только если она больше 0
    if user_data.get('discount', 0) > 0:
        greeting += f"\nВаша текущая скидка на классический кальян - {user_data['discount']} руб."

    greeting += f"\nСегодня на смене Администратор {active_staff['admin']} и Кальянщик {active_staff['hookah_master']}."

    keyboard = [[InlineKeyboardButton("Забронировать столик", callback_data="book_table")]]
    
    if is_admin(update.message.from_user.id):
        keyboard.append([InlineKeyboardButton("Админ меню", callback_data="admin_menu")])

    await update.message.reply_text(greeting, reply_markup=InlineKeyboardMarkup(keyboard))

# Обработка кнопок меню
async def handle_main_menu(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == "book_table":
        await show_calendar(query, context)  # Запускаем процесс бронирования
    elif query.data == "admin_menu":
        if is_admin(query.from_user.id):
            await show_admin_menu(query)  # Показываем админ меню
        else:
            await query.message.reply_text("У вас нет прав для доступа в админ меню.")

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
        [InlineKeyboardButton("📋Список броней", callback_data="booking_list")],  # <-- Запятая добавлена здесь
        [InlineKeyboardButton("⬅ Назад", callback_data="go_back")]
    ])
    
    await query.message.reply_text(
        f"Вы в админ меню. Выберите действие:\nВерсия 2.2",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Обработка действий в админ меню
async def handle_admin_menu(update: Update, context):
    query = update.callback_query
    await query.answer()

    # Логируем данные для отладки
    print(f"Callback data: {query.data}")  # Смотрим, что за данные приходят

    # Показ списка админов
    if query.data == "list_admins":
        admin_list = "\n".join([str(admin_id) for admin_id in admins])
        await query.message.reply_text(f"Текущие админы:\n{admin_list}")

    # Добавление нового админа
    elif query.data == "add_admin":
        await query.message.reply_text("Введите ID пользователя, которого хотите добавить в админы:")
        context.user_data['state'] = 'awaiting_admin_id'  # Устанавливаем уникальное состояние для добавления админа

    # Удаление админа
    elif query.data == "remove_admin":
        keyboard = [[InlineKeyboardButton(f"{admin_id}", callback_data=f"delete_admin_{admin_id}")]
                    for admin_id in admins]
        keyboard.append([InlineKeyboardButton("⬅ Назад", callback_data="go_back")])
        await query.message.reply_text("Выберите админа для удаления:", reply_markup=InlineKeyboardMarkup(keyboard))

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

    await query.message.delete()

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


from datetime import datetime, timedelta

async def show_booking_list(update, context):
    query = update.callback_query
    user_id = query.from_user.id

    # Проверяем права доступа
    if not is_admin(user_id):
        await query.message.reply_text("У вас нет прав для просмотра бронирований.")
        return

    today = datetime.now().date()
    two_days_ago = today - timedelta(days=2)

    # Собираем бронирования за последние 2 дня
    booking_message = "Список подтверждённых бронирований за последние 2 дня:\n"
    for booking_id, booking in confirmed_reservations.items():
        booking_date_str = booking.get('date')  # Дата в формате 'дд-мм-гггг'

        try:
            # Преобразуем строку 'дд-мм-гггг' в объект datetime.date для сравнения
            booking_date = datetime.strptime(booking_date_str, '%d-%m-%Y').date()

            # Проверяем, что дата находится в диапазоне последних 2 дней
            if booking_date >= today:
                # Формируем сообщение с данными бронирования
                booking_message += (
                    f"- Пользователь: {booking['user']}\n"
                    f"Телефон: {booking['phone']}\n"
                    f"Скидка: {booking['discount']} руб.\n"
                    f"Дата: {booking['date']}\n"
                    f"Гости: {booking['guests']}\n"
                    f"Время: {booking['time']}\n"
                    f"Комментарий: {booking['comment']}\n\n"
                )
        except ValueError:
            # Если формат даты неправильный, пропускаем это бронирование
            continue

    if booking_message == "Список подтверждённых бронирований за последние 2 дня:\n":
        booking_message = "Нет подтверждённых бронирований за последние 2 дня."

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
    month_name_ru_translated = month_name_ru.get(month_name, month_name)  # Получаем перевод или оставляем оригинал

    keyboard = []
    today = datetime.now().date()  # Получаем текущую дату в формате date

    # Кнопки для выбора даты
    for week in range(5):
        row = []
        for day in range(7):
            day_date = (current_month + timedelta(days=(week * 7 + day))).date()  # Приводим к формату date
            if day_date.month == current_month.month:
                button_text = f"{day_date.day}"
                if day_date < today:  # Сравниваем объекты одного типа (date)
                    button_text += "❌"  # Красный крестик на прошедших датах
                row.append(InlineKeyboardButton(button_text, callback_data=f"date_{day_date}"))
        if row:
            keyboard.append(row)

    # Кнопки для переключения между месяцами
    prev_month = current_month - timedelta(days=30)
    next_month = current_month + timedelta(days=30)
    keyboard.append([
        InlineKeyboardButton("<<", callback_data=f"calendar_{prev_month.isoformat()}"),
        InlineKeyboardButton(">>", callback_data=f"calendar_{next_month.isoformat()}")
    ])

    # Удаляем предыдущее сообщение с календарем
    await query.message.delete()

    # Отправляем новое сообщение с названием месяца на русском
    await query.message.reply_text(f"Выберите дату ({month_name_ru_translated}):", reply_markup=InlineKeyboardMarkup(keyboard))

# Обработка выбора даты
async def handle_calendar(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("calendar_"):
        current_month = datetime.fromisoformat(query.data.split('_')[1])
        await show_calendar(query, current_month=current_month)
    else:
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

        # Отправляем сообщение пользователю с отформатированной датой
        await query.message.reply_text(f"Вы выбрали дату: {formatted_date}. Не забудьте!")

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

async def handle_message(update: Update, context):
    user_id = update.message.from_user.id
    message_text = update.message.text  # Получаем текст сообщения

    # Проверяем, если сообщение содержит фото
    if update.message.photo:
        file_id = update.message.photo[-1].file_id  # Получаем file_id последнего фото
        message_text = update.message.caption  # Используем подпись фото как текст сообщения, если он есть
        print(f"Фото получено, file_id: {file_id}")

        # Отправляем фото всем пользователям, кроме отправителя
        await broadcast_message(context, message_text, photo=file_id, exclude_user_id=user_id)
        return

    # Проверяем, если сообщение содержит видео
    if update.message.video:
        file_id = update.message.video.file_id  # Получаем file_id видео
        message_text = update.message.caption  # Используем подпись видео как текст сообщения, если он есть
        print(f"Видео получено, file_id: {file_id}")

        # Отправляем видео всем пользователям, кроме отправителя
        await broadcast_message(context, message_text, video=file_id, exclude_user_id=user_id)
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
    
    # Проверяем, если администратор отправляет сообщение для рассылки
    if context.user_data.get('state') == 'broadcast_message':
        message_text = update.message.text
        
        # Получаем ID администратора, который отправляет сообщение
        admin_id = update.message.from_user.id
        
        # Отправляем сообщение всем пользователям, кроме самого администратора
        await broadcast_message(context, message_text, exclude_user_id=admin_id)
        
        # Подтверждение отправки рассылки
        await update.message.reply_text("Сообщение отправлено всем пользователям.")
        
        # Сбрасываем состояние после рассылки
        context.user_data['state'] = None
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
        # Если администратор сделал бронь, он рассматривается как обычный пользователь
        if user_id in admin_clarifications:
            target_user_id = admin_clarifications[user_id]
            clarification_message = update.message.text
            await context.bot.send_message(chat_id=target_user_id, text=f"Администратор уточняет: {clarification_message}")
            del admin_clarifications[user_id]  # Удаляем процесс уточнения после завершения
            user_states[user_id] = 'IDLE'  # Сбрасываем состояние администратора

        # Проверяем, если админ, сделавший бронь, участвует в уточнении
        elif any(user_id == clarifier_id for clarifier_id in admin_clarifications.values()):
            # Находим ID администратора, кому уточняют (автор брони)
            target_user_id = next(
                key for key, clarifier_id in admin_clarifications.items() if clarifier_id == user_id
            )
            clarification_message = update.message.text
            await context.bot.send_message(chat_id=target_user_id, text=f"Пользователь уточняет: {clarification_message}")  # Меняем текст на "Пользователь"
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

    # Получаем данные пользователя (имя и телефон)
    user_data = user_ids.get(str(user_id), {})
    user_name = user_data.get('name', 'Не указано')
    user_phone = user_data.get('phone', 'Не указано')
    user_discount = user_data.get('discount', 0)

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
    user_id = int(query.data.split('_')[1])  # Приводим к int для корректной работы

    # Проверяем, существует ли запись о бронировании для пользователя
    if user_id not in reservations:
        # Если бронирования нет, просто удаляем сообщение у администратора
        await query.message.delete()
        return

    reservation = reservations[user_id]

    # Проверяем, подтверждена ли уже бронь
    if reservation.get('confirmed', False):
        await query.message.delete()
    else:
        # Подтверждаем бронь
        reservation['confirmed'] = True

        # Получаем информацию о пользователе
        user_data = user_ids.get(str(user_id), {})
        user_name = user_data.get('name', 'Не указано')
        user_phone = user_data.get('phone', 'Не указано')
        user_discount = user_data.get('discount', 0)

        # Сохраняем данные бронирования в подтверждённые брони
        confirmed_reservations[user_id] = {
            'user': user_name,
            'phone': user_phone,
            'discount': user_discount,
            'date': reservation['date'],  # Дата бронирования
            'guests': reservation['guests'],  # Количество гостей
            'time': reservation['time'],  # Время бронирования
            'comment': reservation.get('comment', 'Нет пожеланий'),  # Комментарий
        }
        print(f"Подтверждённая бронь: {confirmed_reservations[user_id]}")

        # Отправляем сообщение пользователю о подтверждении брони
        await context.bot.send_message(chat_id=user_id, text="Ваша бронь подтверждена!\nЖдём вас с нетерпением к нам в гости!")

        # Сбрасываем состояние пользователя
        reset_user_state(user_id)

        # Удаляем сообщение у администратора
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

                # Попытка найти имя администратора в базе user_ids
                user_data = user_ids.get(admin_id_to_remove)
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
            for admin_id in admins:
                # Попытка найти имя администратора в базе user_ids
                user_data = user_ids.get(admin_id)
                admin_name = user_data['name'] if user_data and 'name' in user_data else str(admin_id)
                
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
    
    # Если текст не указан
    if not message_text and not update.message.photo and not update.message.video:
        await update.message.reply_text("Введите сообщение или прикрепите фото/видео для отправки.")
        return
    
    # Получаем фото и видео (если есть)
    photo = update.message.photo[-1].file_id if update.message.photo else None
    video = update.message.video.file_id if update.message.video else None
    
    # Отправляем сообщение всем пользователям
    await broadcast_message(context, message_text, photo=photo, video=video)
    await update.message.reply_text("Сообщение отправлено всем пользователям.")

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

# Добавляем проверки в хендлеры команд
def add_handlers(app):
    # Хендлеры команд
    app.add_handler(CommandHandler("start", start))  # Команда старт
    app.add_handler(CommandHandler("add_admin", add_admin))  # Добавление админа
    app.add_handler(CommandHandler("remove_admin", remove_admin))  # Удаление админа
    app.add_handler(CommandHandler("admin_list", admin_list))  # Список админов
    app.add_handler(CommandHandler("broadcast", send_broadcast))  # Рассылка
    app.add_handler(CommandHandler("edit_discount", handle_edit_discount))  # Хендлер редактирования скидки
    app.add_handler(CommandHandler("booking_list", show_booking_list))  # Добавляем хендлер команды

    # Хендлеры для работы с callback (нажатия на кнопки)
    app.add_handler(CallbackQueryHandler(handle_main_menu, pattern=r"^(book_table|admin_menu)$"))  # Главное меню
    app.add_handler(CallbackQueryHandler(handle_calendar, pattern=r"^calendar_"))  # Выбор даты
    app.add_handler(CallbackQueryHandler(handle_calendar, pattern=r"^date_"))  # Выбор даты
    app.add_handler(CallbackQueryHandler(handle_guest_selection, pattern=r"^guests_"))  # Выбор гостей
    app.add_handler(CallbackQueryHandler(handle_time_selection, pattern=r"^time_"))  # Выбор времени
    app.add_handler(CallbackQueryHandler(skip_comment, pattern=r"^skip_comment$")) # Пропуск коментария брони
    app.add_handler(CallbackQueryHandler(confirm_reservation, pattern=r"^confirm_"))  # Подтверждение брони
    app.add_handler(CallbackQueryHandler(clarify_reservation, pattern=r"^clarify_"))  # Уточнение брони
    app.add_handler(CallbackQueryHandler(handle_shift_selection, pattern=r"^(take_shift|set_admin|set_hookah_master)$"))  # Выбор роли на смене
    app.add_handler(CallbackQueryHandler(handle_staff_choice, pattern=r"^choose_admin_|choose_hookah_master_"))  # Выбор сотрудника
    app.add_handler(CallbackQueryHandler(handle_admin_menu, pattern=r"^(list_admins|add_admin|remove_admin|broadcast_message|edit_discount|go_back)$"))  # Админ меню
    app.add_handler(CallbackQueryHandler(handle_admin_removal, pattern=r"^delete_admin_\d+$"))  # Удаление админа
    app.add_handler(CallbackQueryHandler(handle_phone_selection, pattern=r"^select_phone_"))  # Выбор телефона для редактирования скидки
    app.add_handler(CallbackQueryHandler(show_booking_list, pattern=r"^booking_list$"))
    
    # Хендлеры для обработки сообщений
    app.add_handler(MessageHandler(filters.PHOTO, handle_message))  # Обработка фото
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Обработка текста

add_handlers(app)
app.run_polling()
