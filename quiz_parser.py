import argparse
import json
import os
import re
from pathlib import Path
from tqdm import tqdm


def get_questions_from_path(path, start_id=None):
    with open(path, "r", encoding="KOI8-R") as f:
        quiz = f.read()

    quiz_questions = []
    start_id = start_id or 1
    compiled = re.compile("(Вопрос|Ответ).?(?P<number>\d*):\n(?P<text>[\s\S]*)")
    for text in re.split("\n{2,}", quiz):
        matched = compiled.match(text)
        if not matched:
            continue

        question = matched.groupdict()
        if quiz_questions and not question["number"]:
            quiz_questions[-1]["answer"] = question["text"]
            continue

        quiz_questions.append(
            {
                "number": start_id + len(quiz_questions),
                "question": question["text"],
            }
        )

    return quiz_questions


def get_questions_from_dir(dir_path):
    questions = []
    for filename in tqdm(os.listdir(dir_path)):
        quiz_questions = get_questions_from_path(
            dir_path / Path(filename), len(questions) + 1
        )
        questions.extend(quiz_questions)

    return questions


def save_to_json(path, questions):
    with open(path, "w", encoding="utf8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=4)


def get_questions_from_json(path):
    with open(path, "r", encoding="utf8") as f:
        return json.load(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create new intents from json file")
    parser.add_argument(
        "-d",
        "--dir_path",
        type=str,
        help="The path to the folder with questions",
        default="quiz-questions",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=str,
        help="The path to the json file with the questions",
        default="questions.json",
    )
    args = parser.parse_args()

    questions = get_questions_from_dir(args.dir_path)
    save_to_json(args.file, questions)
