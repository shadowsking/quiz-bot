import argparse
import logging
import os
from random import randint

import dotenv
import quiz_parser
import redis
import telegram
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        text="Привет! Я бот для викторин!", reply_markup=get_keyboard_markup()
    )


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Help!")


def reply_text(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    if update.message.text == "Новый вопрос":
        questions = context.dispatcher.questions
        random_question_index = randint(0, len(questions) - 1)
        text = context.dispatcher.questions[random_question_index]["question"]
        context.dispatcher.redis.set(
            update.message.from_user.id, int(random_question_index)
        )
        update.message.reply_text(text)
        return

    question_index = context.dispatcher.redis.get(update.message.from_user.id)
    if not question_index:
        return

    answer = context.dispatcher.questions[int(question_index)]["answer"]
    if update.message.text == "Сдаться":
        text = f"Вот тебе правильный ответ: {answer}"
    elif text == answer:  # todo fix
        text = "Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»"
    else:
        text = "Неправильно… Попробуешь ещё раз?"

    update.message.reply_text(text)


def get_keyboard_markup():
    return telegram.ReplyKeyboardMarkup([["Новый вопрос", "Сдаться"], ["Мой счёт"]])


def main() -> None:
    dotenv.load_dotenv()

    parser = argparse.ArgumentParser(description="Create new intents from json file")
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        help="The path to the json file with the questions",
        default="questions.json",
    )
    args = parser.parse_args()

    updater = Updater(os.getenv("TELEGRAM_TOKEN"))

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, reply_text))
    dispatcher.redis = redis.Redis(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=os.environ.get("REDIS_PORT", 6379),
        db=0,
    )
    dispatcher.questions = quiz_parser.get_questions_from_json(args.file)

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()
