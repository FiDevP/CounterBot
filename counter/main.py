# -*- coding: utf-8 -*-

from telegram import Bot
from telegram import Update

from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import ReplyKeyboardRemove
from telegram.ext import CallbackContext
from telegram.ext import CallbackQueryHandler
from telegram.ext import Updater
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.utils.request import Request
from counter.db import init_db
from counter.db import add_to_db
from counter.db import calculate_indicators
from logging import getLogger
from counter.util import logger_factory
from counter.config import TG_TOKEN

logger = getLogger(__name__)
debug_requests = logger_factory(logger=logger)

# callback_data это то, что будет присылать TG при нажатии на каждую кнопку.
# Поэтому каждый идентификатор должен быть уникальным.
CALLBACK_BUTTON1_LEFT = "callback_button1_left"
CALLBACK_BUTTON2_RIGHT = "callback_button2_right"
CALLBACK_BUTTON3_START = "callback_button3_start"


TITLES = {
    CALLBACK_BUTTON1_LEFT: "Вбить данные счетчиков",
    CALLBACK_BUTTON2_RIGHT: "Рассчитать показатели",
    CALLBACK_BUTTON3_START: "START",
}

cold_water, hot_water, el_day, el_night = 0.0, 0.0, 0.0, 0.0


def get_start_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(TITLES[CALLBACK_BUTTON3_START], callback_data=CALLBACK_BUTTON3_START),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_base_inline_keyboard():
    """
    Получить клавиатуру.
    Эта клавиатура будет видна под каждым сообщением.
    """
    keyboard = [
        [
            InlineKeyboardButton(TITLES[CALLBACK_BUTTON1_LEFT], callback_data=CALLBACK_BUTTON1_LEFT),
            InlineKeyboardButton(TITLES[CALLBACK_BUTTON2_RIGHT], callback_data=CALLBACK_BUTTON2_RIGHT),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


@debug_requests
def keyboard_callback_handler(update: Update, context: CallbackContext):
    """
    Обработчик ВСЕХ кнопок со ВСЕХ клавиатур
    """
    query = update.callback_query
    data = query.data

    # Обратите внимание: используется `effective_message`
    chat_id = update.effective_message.chat_id
    user_id = update.effective_user.id

    if data == CALLBACK_BUTTON3_START:
        query.edit_message_text(
            text="Выбери что нужно сделать",
            reply_markup=get_base_inline_keyboard(),
        )
    if data == CALLBACK_BUTTON1_LEFT:
        context.bot.send_message(
            chat_id=chat_id,
            text='Введите показания счетчиков через пробел. Дробные числа разделять точкой.\n'
            'Холодная вода Горячая вода Электричество день Электричество ночь.\n'
            'Пример: 23.34 45 344 233.4433',
            reply_markup=ReplyKeyboardRemove(),
        )
    if data == CALLBACK_BUTTON2_RIGHT:
        update.effective_message.reply_text(
            text=calculate_indicators(),
        )


@debug_requests
def text_handler(update: Update, context: CallbackContext):
    global cold_water, hot_water, el_day, el_night
    user_id = update.effective_user.id
    text = update.message.text
    try:
        count_list = text.split(' ')
        cold_water = float(count_list[0])
        hot_water = float(count_list[1])
        el_day = float(count_list[2])
        el_night = float(count_list[3])
        text = 'Показания добавлены в базу данных!'
        add_to_db(
            user_id=user_id,
            water_cold=cold_water,
            water_hot=hot_water,
            el_day=el_day,
            el_night=el_night,
        )
    except Exception:
        text = "Введите показания как указано в примере!"
    update.message.reply_text(
        text=text,
    )


@debug_requests
def do_start(update: Update, context: CallbackContext):
    update.message.reply_text(
        text="Привет! Отправь мне что-нибудь",
        reply_markup=get_start_keyboard(),
    )


def main():
    logger.info('Start Counterbot')

    req = Request(
        connect_timeout=0.5,
        read_timeout=1.0,
    )
    bot = Bot(
        request=req,
        token=TG_TOKEN,
    )
    updater = Updater(
        bot=bot,
        use_context=True,
    )

    info = bot.get_me()
    logger.info(f'Bot info: {info}')
    init_db()

    buttons_handler = CallbackQueryHandler(callback=keyboard_callback_handler)
    updater.dispatcher.add_handler(MessageHandler(filters=Filters.command, callback=do_start))
    updater.dispatcher.add_handler(MessageHandler(filters=Filters.text, callback=text_handler))
    updater.dispatcher.add_handler(buttons_handler)

    updater.start_polling()
    updater.idle()
    logger.info('Stop Countbot')


if __name__ == '__main__':
    main()
