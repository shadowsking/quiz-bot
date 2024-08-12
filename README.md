# quiz-bot
VK и [telegram](https://t.me/QuizQuestionsTgBot) бот для викторин


### Установка

```bash
git clone https://github.com/shadowsking/quiz-bot.git
```

Установите зависимости
```bash
pip install -r requirements.txt
```

Создайте '.env' файл и установите следующие аргументы:
- TELEGRAM_TOKEN
- VK_API_KEY


### Запуск
#### Подготовка файлов с вопросами
```bash
python quiz_parser.py
```
- -d (--dir_path): путь к исходной папке
- -f (--file): путь к конечному ".json" файлу

#### Telegram бот:
```bash
python telegram_bot.py
```

##### VK бот:
```bash
python vk_bot.py
```

- -f (--file): путь к ".json" файлу с вопросами
