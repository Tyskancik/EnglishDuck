from database import get_connection
from services import hash_password


LESSONS = [
    {
        "title": "Приветствия",
        "description": "Базовые слова и простые фразы для знакомства и приветствия.",
        "difficulty": "Начальный",
        "questions": [
            {"prompt": "Выберите перевод слова 'Hello'", "correct": "Привет", "options": ["Пока", "Привет", "Спасибо", "До завтра"]},
            {"prompt": "Как переводится 'Good morning'?", "correct": "Доброе утро", "options": ["Доброе утро", "Добрый вечер", "Спокойной ночи", "Добрый день"]},
            {"prompt": "Как по-английски 'Спасибо'?", "correct": "Thank you", "options": ["Sorry", "Thank you", "Please", "Welcome"]},
            {"prompt": "Выберите перевод слова 'Goodbye'", "correct": "До свидания", "options": ["Извините", "До свидания", "Привет", "Конечно"]},
            {"prompt": "Как по-английски 'Как дела?'", "correct": "How are you?", "options": ["What are you?", "How are you?", "Who are you?", "Where are you?"]},
            {"prompt": "Как переводится 'Please'?", "correct": "Пожалуйста", "options": ["Спасибо", "Хорошо", "Пожалуйста", "Скоро"]},
        ],
    },
    {
        "title": "Еда и напитки",
        "description": "Слова по теме еды, напитков и простого заказа в кафе.",
        "difficulty": "Начальный",
        "questions": [
            {"prompt": "Как переводится 'Apple'?", "correct": "Яблоко", "options": ["Груша", "Яблоко", "Апельсин", "Слива"]},
            {"prompt": "Как по-английски 'Хлеб'?", "correct": "Bread", "options": ["Bread", "Butter", "Soup", "Cake"]},
            {"prompt": "Выберите перевод слова 'Water'", "correct": "Вода", "options": ["Чай", "Вода", "Молоко", "Кофе"]},
            {"prompt": "Как переводится 'Cheese'?", "correct": "Сыр", "options": ["Сахар", "Соль", "Сыр", "Суп"]},
            {"prompt": "Как по-английски 'Чай'?", "correct": "Tea", "options": ["Tea", "Juice", "Rice", "Meal"]},
            {"prompt": "Выберите правильный перевод: 'I would like juice'", "correct": "Я бы хотел сок", "options": ["Я бы хотел сок", "Мне нужен хлеб", "Я люблю чай", "Пожалуйста, кофе"]},
        ],
    },
    {
        "title": "Путешествия",
        "description": "Полезные слова для аэропорта, гостиницы и перемещения по городу.",
        "difficulty": "Средний",
        "questions": [
            {"prompt": "Как переводится 'Airport'?", "correct": "Аэропорт", "options": ["Аэропорт", "Вокзал", "Граница", "Пляж"]},
            {"prompt": "Как по-английски 'Билет'?", "correct": "Ticket", "options": ["Passport", "Ticket", "Luggage", "Map"]},
            {"prompt": "Выберите перевод слова 'Luggage'", "correct": "Багаж", "options": ["Багаж", "Рейс", "Таможня", "Отель"]},
            {"prompt": "Как переводится 'Where is the hotel?'", "correct": "Где находится отель?", "options": ["Сколько стоит отель?", "Где находится отель?", "У меня есть багаж", "Я ищу паспорт"]},
            {"prompt": "Как по-английски 'Карта города'?", "correct": "City map", "options": ["City bus", "City hotel", "City map", "City room"]},
            {"prompt": "Как переводится 'boarding pass'?", "correct": "Посадочный талон", "options": ["Паспорт", "Билет", "Посадочный талон", "Багажная лента"]},
        ],
    },
    {
        "title": "Повседневные фразы",
        "description": "Фразы для общения каждый день, просьб и уточнений.",
        "difficulty": "Средний",
        "questions": [
            {"prompt": "Как по-английски 'Я понимаю'", "correct": "I understand", "options": ["I explain", "I understand", "I repeat", "I answer"]},
            {"prompt": "Как переводится 'I don't know'", "correct": "Я не знаю", "options": ["Я не знаю", "Я не могу", "Я не готов", "Я не дома"]},
            {"prompt": "Как переводится 'Excuse me'", "correct": "Извините", "options": ["Пожалуйста", "Извините", "Большое спасибо", "Я слушаю"]},
            {"prompt": "Как по-английски 'Мне нужна помощь'", "correct": "I need help", "options": ["I need time", "I need help", "I need food", "I need money"]},
            {"prompt": "Как переводится 'Could you repeat that?'", "correct": "Не могли бы вы это повторить?", "options": ["Где это купить?", "Не могли бы вы это повторить?", "Могу я помочь?", "Я повторю позже"]},
            {"prompt": "Как переводится 'See you later'", "correct": "Увидимся позже", "options": ["Я приду позже", "Увидимся позже", "Поговорим завтра", "Смотри сюда"]},
        ],
    },
    {
        "title": "Работа и обучение",
        "description": "Более сложная лексика для обучения, документов и деловой переписки.",
        "difficulty": "Сложный",
        "questions": [
            {"prompt": "Как переводится 'deadline'?", "correct": "Срок сдачи", "options": ["Расписание", "Срок сдачи", "Задание", "Подпись"]},
            {"prompt": "Как по-английски 'обратная связь'?", "correct": "feedback", "options": ["feature", "feedback", "forward", "forecast"]},
            {"prompt": "Выберите перевод фразы 'I have attached the document'", "correct": "Я прикрепил документ", "options": ["Я открыл документ", "Я прикрепил документ", "Я удалил документ", "Я проверил документ"]},
            {"prompt": "Как переводится 'schedule a meeting'?", "correct": "Запланировать встречу", "options": ["Пропустить встречу", "Запланировать встречу", "Отменить встречу", "Подтвердить звонок"]},
            {"prompt": "Как по-английски 'техническое задание'?", "correct": "technical specification", "options": ["technical support", "technical specification", "technical report", "technical process"]},
            {"prompt": "Как переводится 'The report needs revision'", "correct": "Отчёт требует доработки", "options": ["Отчёт уже готов", "Отчёт требует доработки", "Отчёт был отправлен", "Отчёт очень короткий"]},
        ],
    },
    {
        "title": "Устойчивые выражения",
        "description": "Идиомы и более сложные выражения для понимания контекста и речи.",
        "difficulty": "Сложный",
        "questions": [
            {"prompt": "Как переводится идиома 'break the ice'?", "correct": "Разрядить обстановку", "options": ["Сломать лёд", "Начать спор", "Разрядить обстановку", "Закрыть разговор"]},
            {"prompt": "Какой перевод ближе к 'piece of cake'?", "correct": "Очень легко", "options": ["Очень сладко", "Очень сложно", "Очень легко", "Очень быстро"]},
            {"prompt": "Как переводится 'in the long run'?", "correct": "В долгосрочной перспективе", "options": ["На длинной дороге", "В долгосрочной перспективе", "В конце дня", "На большом расстоянии"]},
            {"prompt": "Какой вариант лучше переводит 'hit the books'?", "correct": "Сесть за учёбу", "options": ["Купить книги", "Сесть за учёбу", "Потерять учебник", "Разобрать шкаф"]},
            {"prompt": "Как переводится 'under the weather'?", "correct": "Плохо себя чувствовать", "options": ["Любить дождь", "Плохо себя чувствовать", "Замёрзнуть на улице", "Спешить домой"]},
            {"prompt": "Как переводится 'once in a blue moon'?", "correct": "Очень редко", "options": ["Раз в месяц", "Очень редко", "В полнолуние", "Вовремя"]},
        ],
    },
]


def seed_database() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS count FROM lessons")
    if cur.fetchone()["count"] == 0:
        for lesson in LESSONS:
            cur.execute(
                "INSERT INTO lessons(title, description, difficulty) VALUES (?, ?, ?)",
                (lesson["title"], lesson["description"], lesson["difficulty"]),
            )
            lesson_id = cur.lastrowid
            for question in lesson["questions"]:
                options = question["options"]
                cur.execute(
                    """
                    INSERT INTO questions(
                        lesson_id, prompt, correct_answer, option1, option2, option3, option4
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        lesson_id,
                        question["prompt"],
                        question["correct"],
                        options[0],
                        options[1],
                        options[2],
                        options[3],
                    ),
                )

    cur.execute("SELECT COUNT(*) AS count FROM users WHERE username = 'demo'")
    if cur.fetchone()["count"] == 0:
        cur.execute(
            """
            INSERT INTO users(username, display_name, password_hash, xp, streak, is_guest)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            ("demo", "demo", hash_password("demo123"), 60, 2),
        )

    conn.commit()
    conn.close()
