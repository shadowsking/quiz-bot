import argparse
import os
from difflib import SequenceMatcher
from random import randint

import dotenv
import redis
import vk_api as vk
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

import quiz_parser

START = "Начать"
NEW_QUESTION = "Новый вопрос"
SURRENDER = "Сдаться"
MY_SCORE = "Мой счет"


def get_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button(NEW_QUESTION, color=VkKeyboardColor.PRIMARY)
    keyboard.add_button(SURRENDER, color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button(MY_SCORE, color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()


def get_answer(redis_client, user_id, questions) -> str | None:
    question_index = redis_client.get(user_id)
    if question_index:
        return questions[int(question_index)]["answer"]

    return None


def handle_solution_attempt(event, vk_api, redis_client, questions, **kwargs):
    answer = get_answer(redis_client, event.user_id, questions)
    matched = SequenceMatcher(a=event.text.lower(), b=answer.lower())
    if matched.ratio() < 0.7:
        return vk_api.messages.send(
            message="Неправильно… Попробуешь ещё раз?",
            random_id=get_random_id(),
            **kwargs,
        )

    vk_api.messages.send(message="Правильно", random_id=get_random_id(), **kwargs)
    return handle_new_question_request(vk_api, redis_client, questions, **kwargs)


def handle_new_question_request(
        vk_api, redis_client, questions, user_id=None, **kwargs
):
    random_question_index = randint(0, len(questions) - 1)
    redis_client.set(user_id, random_question_index)
    vk_api.messages.send(
        message=questions[random_question_index]["question"],
        random_id=get_random_id(),
        user_id=user_id,
        **kwargs,
    )


def surrender(vk_api, redis_client, questions, user_id=None, **kwargs):
    answer = get_answer(redis_client, user_id, questions)
    if not answer:
        return

    vk_api.messages.send(
        message=f"Вот тебе правильный ответ: {answer}",
        random_id=get_random_id(),
        user_id=user_id,
        **kwargs,
    )


def main() -> None:
    dotenv.load_dotenv()

    parser = argparse.ArgumentParser(description="Quiz")
    parser.add_argument(
        "-f",
        "--file",
        help="The path to the json file with the questions",
        default="questions.json",
    )
    args = parser.parse_args()

    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=os.getenv("REDIS_PORT", 6379),
        db=0,
    )
    questions = quiz_parser.get_questions_from_json(args.file)

    vk_session = vk.VkApi(token=os.environ["VK_API_KEY"])
    vk_api = vk_session.get_api()

    keyboard = get_keyboard()

    long_poll = VkLongPoll(vk_session)
    for event in long_poll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == START:
                vk_api.messages.send(
                    user_id=event.user_id,
                    message="Привет! Я бот для викторин!",
                    keyboard=keyboard,
                    random_id=get_random_id(),
                )
            elif event.text == NEW_QUESTION:
                handle_new_question_request(
                    vk_api,
                    redis_client,
                    questions,
                    user_id=event.user_id,
                    keyboard=keyboard,
                )
            elif event.text == SURRENDER:
                surrender(
                    vk_api,
                    redis_client,
                    questions,
                    user_id=event.user_id,
                    keyboard=keyboard,
                )
            else:
                handle_solution_attempt(
                    event,
                    vk_api,
                    redis_client,
                    questions,
                    user_id=event.user_id,
                    keyboard=keyboard,
                )


if __name__ == "__main__":
    main()
