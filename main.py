import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import requests

# Установка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "7905088607:AAGTyoj1-W10hz-zgHs51ghLSWHjGHT8f90"

user_data = {}


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        'Привет! Я бот для получения прогноза погоды. Используйте /help для получения списка команд.'
    )


async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('/start - Приветствие\n'
                                    '/help - Список команд\n'
                                    '/weather - Прогноз погоды')


async def weather(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("1 день", callback_data='1')],
        [InlineKeyboardButton("3 дня", callback_data='3')],
        [InlineKeyboardButton("6 дней", callback_data='6')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите временной интервал:', reply_markup=reply_markup)


async def inline_button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    period = query.data
    user_data[query.from_user.id] = user_data.get(query.from_user.id, {})
    user_data[query.from_user.id]['interval'] = period

    await query.edit_message_text(
        text=f"Вы выбрали временной интервал: {period} дней.\nТеперь введите точки маршрута (например, 'Город1, Город2, Город3').")


async def handle_text(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    if user_id not in user_data or 'interval' not in user_data[user_id]:
        await update.message.reply_text("Пожалуйста, сначала выберите временной интервал с помощью команды /weather.")
        return

    interval = user_data[user_id]['interval']
    points = update.message.text.split(',')  # Ожидаем, что пользователь вводит точки маршрута
    points = [point.strip() for point in points]

    # Проверяем, что передано хотя бы две точки
    if len(points) >= 2:
        weather_info = await get_weather(points, interval)  # Запрос к вашему Flask-серверу
        await update.message.reply_text(weather_info)
    else:
        await update.message.reply_text("Пожалуйста, введите как минимум две точки, разделенные запятой.")


async def get_weather(points, interval):
    url = "http://127.0.0.1:5000/weather"
    params = {
        'points': ','.join(points),  # Присоединяем точки через запятую
        'interval': interval
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        weather_data = response.json()

        # Форматируем вывод для каждой точки
        result = "\n".join(
            [f"{point.strip()}:\n" + "\n".join(
                [f"Дата: {data['date']}, Температура: {data['temperature']}°C, "
                 f"Влажность: {data['humidity']}%, "
                 f"Скорость ветра: {data['wind_speed']} м/с, "
                 f"Вероятность осадков: {data['prec_prob']}%"
                 for data in weather[1]]
            ) for point, weather in zip(points, weather_data)]
        )

        return f"Прогноз погоды:\n{result}"
    else:
        return "Ошибка получения погоды с сервиса."


def main() -> None:
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("weather", weather))

    application.add_handler(
        CallbackQueryHandler(inline_button_handler))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling()


if __name__ == '__main__':
    main()