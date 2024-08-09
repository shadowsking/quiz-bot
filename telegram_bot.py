import argparse
import logging
import os
from difflib import SequenceMatcher
from random import randint

import dotenv
import quiz_parser
import redis
import telegram
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

(NEW_QUESTION, ATTEMPT, SURRENDER) = range(3)


def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        text="Привет! Я бот для викторин!", reply_markup=get_keyboard_markup()
    )
    return NEW_QUESTION


def stop(update: Update, context: CallbackContext) -> int:
    context.dispatcher.redis.delete(update.message.from_user.id)
    update.message.reply_text("Пока", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Help!")


def get_answer(update: Update, context: CallbackContext) -> str | None:
    question_index = context.dispatcher.redis.get(update.message.from_user.id)
    if question_index:
        return context.dispatcher.questions[int(question_index)]["answer"]

    return None


def surrender(update: Update, context: CallbackContext) -> int:
    answer = get_answer(update, context)
    if answer:
        update.message.reply_text(f"Вот тебе правильный ответ: {answer}")

    return ConversationHandler.END


def handle_new_question_request(update: Update, context: CallbackContext) -> None | int:
    questions = context.dispatcher.questions
    random_question_index = randint(0, len(questions) - 1)
    text = context.dispatcher.questions[random_question_index]["question"]
    context.dispatcher.redis.set(
        update.message.from_user.id, int(random_question_index)
    )
    update.message.reply_text(text)

    return ATTEMPT


def handle_solution_attempt(update: Update, context: CallbackContext) -> int:
    if update.message is None:
        return ATTEMPT

    matched = SequenceMatcher(
        a=update.message.text.lower(), b=get_answer(update, context).lower()
    )
    if matched.ratio() < 0.7:
        update.message.reply_text("Неправильно… Попробуешь ещё раз?")
        return ATTEMPT

    update.message.reply_text("Правильно!")
    return handle_new_question_request(update, context)


def get_keyboard_markup():
    return telegram.ReplyKeyboardMarkup([["Новый вопрос", "Сдаться"], ["Мой счёт"]])


def main() -> None:
    dotenv.load_dotenv()

    parser = argparse.ArgumentParser(description="Quiz")
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
    dispatcher.redis = redis.Redis(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=os.environ.get("REDIS_PORT", 6379),
        db=0,
    )
    dispatcher.questions = quiz_parser.get_questions_from_json(args.file)

    new_question_handler = MessageHandler(
        Filters.text & Filters.regex("^Новый вопрос$"), handle_new_question_request
    )
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), new_question_handler],
        states={
            NEW_QUESTION: [new_question_handler],
            ATTEMPT: [
                MessageHandler(Filters.text & Filters.regex("^Сдаться$"), surrender),
                MessageHandler(
                    Filters.text & ~Filters.command, handle_solution_attempt
                ),
            ],
        },
        fallbacks=[CommandHandler("stop", stop)],
    )
    dispatcher.add_handler(conversation_handler)

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    main()
