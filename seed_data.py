from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Optional

from database import get_connection

GUEST_LOCAL_KEY = "local_guest_profile"


@dataclass
class User:
    id: int
    username: str
    display_name: str
    xp: int
    streak: int
    last_activity: Optional[str]
    is_guest: bool


@dataclass
class Lesson:
    id: int
    title: str
    description: str
    difficulty: str
    best_score: int
    attempts: int
    question_count: int


@dataclass
class Question:
    id: int
    prompt: str
    correct_answer: str
    options: List[str]


@dataclass
class LessonResult:
    score: int
    total: int
    gained_xp: int
    streak: int


LEVEL_ORDER = {"Начальный": 1, "Средний": 2, "Сложный": 3}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _row_to_user(row) -> User:
    return User(
        id=row["id"],
        username=row["username"],
        display_name=row["display_name"],
        xp=row["xp"],
        streak=row["streak"],
        last_activity=row["last_activity"],
        is_guest=bool(row["is_guest"]),
    )


def register_user(username: str, password: str, confirm_password: str) -> tuple[bool, str]:
    username = username.strip()
    password = password.strip()
    confirm_password = confirm_password.strip()

    if len(username) < 3:
        return False, "Логин должен содержать минимум 3 символа."
    if " " in username:
        return False, "Логин не должен содержать пробелы."
    if len(password) < 4:
        return False, "Пароль должен содержать минимум 4 символа."
    if password != confirm_password:
        return False, "Пароли не совпадают."

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO users(username, display_name, password_hash, is_guest)
            VALUES (?, ?, ?, 0)
            """,
            (username, username, hash_password(password)),
        )
        conn.commit()
        return True, "Регистрация успешно подтверждена. Теперь можно войти в систему."
    except Exception:
        return False, "Пользователь с таким логином уже существует."
    finally:
        conn.close()


def login_user(username: str, password: str) -> Optional[User]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, username, display_name, xp, streak, last_activity, is_guest
        FROM users
        WHERE username = ? AND password_hash = ?
        """,
        (username.strip(), hash_password(password.strip())),
    )
    row = cur.fetchone()
    conn.close()
    return _row_to_user(row) if row else None


def get_or_create_guest_user() -> User:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, username, display_name, xp, streak, last_activity, is_guest
        FROM users
        WHERE local_key = ?
        """,
        (GUEST_LOCAL_KEY,),
    )
    row = cur.fetchone()
    if row:
        conn.close()
        return _row_to_user(row)

    cur.execute(
        """
        INSERT INTO users(username, display_name, password_hash, xp, streak, is_guest, local_key)
        VALUES (?, ?, ?, 0, 0, 1, ?)
        """,
        ("guest_local", "Гость", hash_password("guest"), GUEST_LOCAL_KEY),
    )
    conn.commit()

    cur.execute(
        """
        SELECT id, username, display_name, xp, streak, last_activity, is_guest
        FROM users
        WHERE local_key = ?
        """,
        (GUEST_LOCAL_KEY,),
    )
    row = cur.fetchone()
    conn.close()
    return _row_to_user(row)


def get_user(user_id: int) -> User:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, username, display_name, xp, streak, last_activity, is_guest
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    row = cur.fetchone()
    conn.close()
    return _row_to_user(row)


def get_lessons_for_user(user_id: int, difficulty_filter: str = "Все") -> List[Lesson]:
    conn = get_connection()
    cur = conn.cursor()

    params = [user_id]
    difficulty_sql = ""
    if difficulty_filter != "Все":
        difficulty_sql = "WHERE l.difficulty = ?"
        params.append(difficulty_filter)

    cur.execute(
        f"""
        SELECT l.id,
               l.title,
               l.description,
               l.difficulty,
               COALESCE(p.best_score, 0) AS best_score,
               COALESCE(p.attempts, 0) AS attempts,
               COUNT(q.id) AS question_count
        FROM lessons l
        LEFT JOIN progress p ON p.lesson_id = l.id AND p.user_id = ?
        LEFT JOIN questions q ON q.lesson_id = l.id
        {difficulty_sql}
        GROUP BY l.id, l.title, l.description, l.difficulty, p.best_score, p.attempts
        ORDER BY CASE l.difficulty
            WHEN 'Начальный' THEN 1
            WHEN 'Средний' THEN 2
            WHEN 'Сложный' THEN 3
            ELSE 4 END, l.id
        """,
        params,
    )
    rows = cur.fetchall()
    conn.close()

    return [
        Lesson(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            difficulty=row["difficulty"],
            best_score=row["best_score"],
            attempts=row["attempts"],
            question_count=row["question_count"],
        )
        for row in rows
    ]


def get_questions_for_lesson(lesson_id: int) -> List[Question]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, prompt, correct_answer, option1, option2, option3, option4
        FROM questions
        WHERE lesson_id = ?
        ORDER BY id
        """,
        (lesson_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        Question(
            id=row["id"],
            prompt=row["prompt"],
            correct_answer=row["correct_answer"],
            options=[row["option1"], row["option2"], row["option3"], row["option4"]],
        )
        for row in rows
    ]


def submit_lesson_result(user_id: int, lesson_id: int, score: int, total: int) -> LessonResult:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT xp, streak, last_activity FROM users WHERE id = ?", (user_id,))
    user_row = cur.fetchone()
    today = date.today()

    last_activity = None
    if user_row["last_activity"]:
        try:
            last_activity = datetime.strptime(user_row["last_activity"], "%Y-%m-%d").date()
        except ValueError:
            last_activity = None

    streak = user_row["streak"]
    if last_activity is None:
        streak = 1
    elif last_activity == today:
        streak = user_row["streak"]
    elif last_activity == today - timedelta(days=1):
        streak = user_row["streak"] + 1
    else:
        streak = 1

    gained_xp = score * 10
    new_xp = user_row["xp"] + gained_xp

    cur.execute(
        "SELECT id, best_score, attempts FROM progress WHERE user_id = ? AND lesson_id = ?",
        (user_id, lesson_id),
    )
    progress_row = cur.fetchone()

    if progress_row:
        best_score = max(progress_row["best_score"], score)
        attempts = progress_row["attempts"] + 1
        cur.execute(
            """
            UPDATE progress
            SET best_score = ?, attempts = ?, last_score = ?, completed_at = ?
            WHERE id = ?
            """,
            (best_score, attempts, score, today.isoformat(), progress_row["id"]),
        )
    else:
        cur.execute(
            """
            INSERT INTO progress(user_id, lesson_id, best_score, attempts, last_score, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, lesson_id, score, 1, score, today.isoformat()),
        )

    cur.execute(
        "UPDATE users SET xp = ?, streak = ?, last_activity = ? WHERE id = ?",
        (new_xp, streak, today.isoformat(), user_id),
    )

    conn.commit()
    conn.close()
    return LessonResult(score=score, total=total, gained_xp=gained_xp, streak=streak)


def get_dashboard_stats(user_id: int) -> dict:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS total_lessons FROM lessons")
    total_lessons = cur.fetchone()["total_lessons"]

    cur.execute(
        "SELECT COUNT(*) AS completed FROM progress WHERE user_id = ? AND best_score > 0",
        (user_id,),
    )
    completed = cur.fetchone()["completed"]

    cur.execute(
        "SELECT COALESCE(SUM(best_score), 0) AS total_points FROM progress WHERE user_id = ?",
        (user_id,),
    )
    total_points = cur.fetchone()["total_points"]

    cur.execute(
        """
        SELECT l.difficulty, COUNT(*) AS amount
        FROM lessons l
        GROUP BY l.difficulty
        """
    )
    level_totals = {row["difficulty"]: row["amount"] for row in cur.fetchall()}

    cur.execute(
        """
        SELECT l.difficulty, COUNT(*) AS amount
        FROM progress p
        JOIN lessons l ON l.id = p.lesson_id
        WHERE p.user_id = ? AND p.best_score > 0
        GROUP BY l.difficulty
        """,
        (user_id,),
    )
    level_completed = {row["difficulty"]: row["amount"] for row in cur.fetchall()}

    conn.close()
    return {
        "total_lessons": total_lessons,
        "completed_lessons": completed,
        "total_points": total_points,
        "completion_percent": int((completed / total_lessons) * 100) if total_lessons else 0,
        "level_totals": level_totals,
        "level_completed": level_completed,
    }
