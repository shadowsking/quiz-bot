import argparse
import os

import dotenv
import vk_api as vk
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

import quiz_parser

START = "Начать"
NEW_QUESTION = "Новый вопрос"
SURRENDER = "Сдаться"
MY_SCORE = "Мой счет"


def handle_new_question_request():
    pass


def handle_solution_attempt():
    pass


def get_keyboard():
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button(NEW_QUESTION, color=VkKeyboardColor.PRIMARY)
    keyboard.add_button(SURRENDER, color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button(MY_SCORE, color=VkKeyboardColor.SECONDARY)
    return keyboard


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
                    keyboard=keyboard.get_keyboard(),
                    random_id=get_random_id(),
                )
            elif event.text == NEW_QUESTION:
                handle_new_question_request()


if __name__ == "__main__":
    main()
