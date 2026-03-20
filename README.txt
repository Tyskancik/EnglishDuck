import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

from database import init_db
from seed_data import seed_database
from services import (
    get_dashboard_stats,
    get_lessons_for_user,
    get_or_create_guest_user,
    get_questions_for_lesson,
    get_user,
    login_user,
    register_user,
    submit_lesson_result,
)

BG = "#F7F3EF"
SURFACE = "#FFFDFC"
PANEL = "#F2ECE7"
BORDER = "#E3D8CF"
TEXT = "#2D4059"
MUTED = "#7B8794"
ACCENT = "#B9DEB7"
ACCENT_DARK = "#7FB77E"
ACCENT_SOFT = "#EEF7EC"
BLUE = "#D8E8F3"
BLUE_DARK = "#8CB6D8"
BLUE_SOFT = "#EEF6FB"
PEACH = "#F5DED2"
PEACH_DARK = "#D9A48F"
PEACH_SOFT = "#FCF1EC"
YELLOW = "#F5EBC9"
YELLOW_DARK = "#CAA768"
LAVENDER = "#E6E0F5"
RED = "#D97D7D"
SUCCESS = "#7BAE75"

DIFFICULTY_COLORS = {
    "Начальный": (ACCENT_DARK, ACCENT_SOFT),
    "Средний": (BLUE_DARK, BLUE_SOFT),
    "Сложный": (PEACH_DARK, PEACH_SOFT),
}

LESSON_ICONS = {
    "Приветствия": "💬",
    "Еда и напитки": "🍎",
    "Путешествия": "✈",
    "Повседневные фразы": "🗨",
    "Работа и обучение": "💼",
    "Устойчивые выражения": "🧠",
}

DUCK_TIPS = [
    "🦆 Маленькие шаги каждый день дают сильный результат.",
    "🦆 Если ошибся — это тоже обучение. Продолжай.",
    "🦆 Сначала закрепи базу, потом переходи к сложным темам.",
    "🦆 Повторение через день помогает запоминать надолго.",
]


class EnglisDuckApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("EnglisDuck — изучение английского языка")
        self.root.geometry("1240x820")
        self.root.minsize(1080, 720)
        self.root.configure(bg=BG)

        init_db()
        seed_database()

        self.current_user = None
        self.current_lesson = None
        self.questions = []
        self.question_index = 0
        self.score = 0
        self.hearts = 3
        self.option_buttons = []
        self.current_question = None
        self.difficulty_filter = tk.StringVar(value="Все")
        self.dashboard_columns = None
        self.dashboard_lessons = []
        self.cards_container = None
        self.cards_canvas = None
        self.cards_window = None
        self.path_buttons = []
        self.animated_bars = []
        self.base_dir = Path(__file__).resolve().parent
        self.assets_dir = self.base_dir / "assets"
        self.duck_image_cache = {}

        self.main_frame = tk.Frame(self.root, bg=BG)
        self.main_frame.pack(fill="both", expand=True)

        self.style = ttk.Style()
        self.style.theme_use("default")
        self.style.configure(
            "duck.Horizontal.TProgressbar",
            thickness=14,
            troughcolor="#EEE5DB",
            background=ACCENT_DARK,
            bordercolor="#EEE5DB",
            lightcolor=ACCENT_DARK,
            darkcolor=ACCENT_DARK,
        )
        self.style.configure(
            "blue.Horizontal.TProgressbar",
            thickness=14,
            troughcolor="#EEE5DB",
            background=BLUE_DARK,
            bordercolor="#EEE5DB",
            lightcolor=BLUE_DARK,
            darkcolor=BLUE_DARK,
        )
        self.style.configure(
            "peach.Horizontal.TProgressbar",
            thickness=14,
            troughcolor="#EEE5DB",
            background=PEACH_DARK,
            bordercolor="#EEE5DB",
            lightcolor=PEACH_DARK,
            darkcolor=PEACH_DARK,
        )

        self.show_auth_screen()

    def clear_screen(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def center_window(self, window: tk.Toplevel, width: int, height: int):
        self.root.update_idletasks()
        root_w = max(self.root.winfo_width(), 1)
        root_h = max(self.root.winfo_height(), 1)
        root_x = self.root.winfo_rootx()
        root_y = self.root.winfo_rooty()
        x = root_x + (root_w - width) // 2
        y = root_y + (root_h - height) // 2
        window.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")

    def create_topbar(self, title: str, back_command=None):
        top = tk.Frame(self.main_frame, bg=BG, pady=12)
        top.pack(fill="x", padx=18)

        if back_command:
            tk.Button(
                top,
                text="← Назад",
                command=back_command,
                bg=SURFACE,
                fg=TEXT,
                activebackground=PANEL,
                activeforeground=TEXT,
                font=("Arial", 12, "bold"),
                relief="flat",
                padx=14,
                pady=8,
                cursor="hand2",
            ).pack(side="left")

        tk.Label(top, text=title, bg=BG, fg=TEXT, font=("Arial", 24, "bold")).pack(side="left", padx=16)

        if self.current_user:
            user_label = self.current_user.display_name + (" (гость)" if self.current_user.is_guest else "")
            info = f"Пользователь: {user_label}    XP: {self.current_user.xp}    Серия: {self.current_user.streak}"
            tk.Label(top, text=info, bg=BG, fg=MUTED, font=("Arial", 11)).pack(side="right")

    def get_duck_photo(self, size: int):
        if size not in self.duck_image_cache:
            image_path = self.assets_dir / "duck_real.png"
            image = Image.open(image_path).convert("RGBA")
            image = image.resize((size, size), Image.Resampling.LANCZOS)
            self.duck_image_cache[size] = ImageTk.PhotoImage(image)
        return self.duck_image_cache[size]

    def draw_duck(self, parent, size=84, bg=SURFACE):
        photo = self.get_duck_photo(size)
        label = tk.Label(parent, image=photo, bg=bg, bd=0, highlightthickness=0)
        label.image = photo
        return label

    def feature_chip(self, parent, title: str, subtitle: str, bg_color: str):
        chip = tk.Frame(parent, bg=bg_color, highlightthickness=1, highlightbackground=BORDER)
        tk.Label(chip, text=title, bg=bg_color, fg=TEXT, font=("Arial", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(chip, text=subtitle, bg=bg_color, fg=MUTED, font=("Arial", 9), justify="left", wraplength=180).pack(anchor="w", padx=14, pady=(0, 12))
        return chip

    def show_auth_screen(self):
        self.clear_screen()
        self.current_user = None

        outer = tk.Frame(self.main_frame, bg=BG)
        outer.pack(fill="both", expand=True, padx=28, pady=24)
        outer.grid_columnconfigure(0, weight=6)
        outer.grid_columnconfigure(1, weight=5)
        outer.grid_rowconfigure(0, weight=1)

        hero = tk.Frame(outer, bg=ACCENT_SOFT, highlightthickness=1, highlightbackground="#D8E6D4")
        hero.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        hero.grid_columnconfigure(0, weight=1)

        hero_inner = tk.Frame(hero, bg=ACCENT_SOFT)
        hero_inner.pack(fill="both", expand=True, padx=30, pady=24)
        self.draw_duck(hero_inner, size=172, bg=ACCENT_SOFT).pack(pady=(4, 8))
        tk.Label(hero_inner, text="EnglisDuck", bg=ACCENT_SOFT, fg=TEXT, font=("Arial", 31, "bold")).pack()
        tk.Label(
            hero_inner,
            text="Учи английский мягко и регулярно: мини-уроки, карта прогресса, серия дней и спокойный темп обучения.",
            bg=ACCENT_SOFT,
            fg=MUTED,
            font=("Arial", 12),
            justify="center",
            wraplength=470,
        ).pack(pady=(12, 20), padx=12)

        chips = tk.Frame(hero_inner, bg=ACCENT_SOFT)
        chips.pack(fill="x", pady=(4, 18))
        chips.grid_columnconfigure(0, weight=1)
        chips.grid_columnconfigure(1, weight=1)
        chip_specs = [
            ("Начальный путь", "База слов и фраз без перегруза.", "#F8FBF7"),
            ("Средний уровень", "Больше тем и полезных диалогов.", "#F5F8FC"),
            ("Сложный уровень", "Идиомы, устойчивые фразы и практика.", "#FEF7F3"),
            ("Гостевой режим", "Прогресс сохранится локально на устройстве.", "#FFF9EC"),
        ]
        for idx, (title, subtitle, chip_bg) in enumerate(chip_specs):
            chip = self.feature_chip(chips, title, subtitle, chip_bg)
            chip.grid(row=idx // 2, column=idx % 2, sticky="nsew", padx=6, pady=6)

        note = tk.Frame(hero_inner, bg="#F8FBF7", highlightthickness=1, highlightbackground="#DCEADB")
        note.pack(fill="x")
        tk.Label(
            note,
            text="EnglisDuck сохраняет локальный прогресс, показывает тропу уроков и помогает идти от простого к сложному.",
            bg="#F8FBF7",
            fg=TEXT,
            font=("Arial", 10),
            wraplength=470,
            justify="left",
        ).pack(anchor="w", padx=16, pady=14)

        card = tk.Frame(outer, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        card.grid(row=0, column=1, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        card_inner = tk.Frame(card, bg=SURFACE)
        card_inner.pack(fill="both", expand=True, padx=34, pady=34)

        head = tk.Frame(card_inner, bg=SURFACE)
        head.pack(fill="x")
        self.draw_duck(head, size=82, bg=SURFACE).pack(side="left", padx=(0, 14))
        title_wrap = tk.Frame(head, bg=SURFACE)
        title_wrap.pack(side="left", fill="x", expand=True)
        tk.Label(title_wrap, text="Добро пожаловать", bg=SURFACE, fg=TEXT, font=("Arial", 24, "bold")).pack(anchor="w")
        tk.Label(title_wrap, text="Войди, создай аккаунт или продолжи как гость.", bg=SURFACE, fg=MUTED, font=("Arial", 11)).pack(anchor="w", pady=(4, 0))

        self.auth_message = tk.Label(card_inner, text="", bg=SURFACE, fg=MUTED, font=("Arial", 10), anchor="w")
        self.auth_message.pack(fill="x", pady=(18, 8))

        tk.Label(card_inner, text="Логин", bg=SURFACE, fg=TEXT, font=("Arial", 11, "bold")).pack(anchor="w", pady=(8, 0))
        self.username_entry = tk.Entry(card_inner, font=("Arial", 13), relief="solid", bd=1)
        self.username_entry.pack(fill="x", pady=(6, 14), ipady=9)

        tk.Label(card_inner, text="Пароль", bg=SURFACE, fg=TEXT, font=("Arial", 11, "bold")).pack(anchor="w")
        self.password_entry = tk.Entry(card_inner, font=("Arial", 13), relief="solid", bd=1, show="*")
        self.password_entry.pack(fill="x", pady=(6, 22), ipady=9)

        tk.Button(card_inner, text="Войти", command=self.handle_login, bg=ACCENT, activebackground=ACCENT_DARK, fg=TEXT,
                  font=("Arial", 13, "bold"), relief="flat", pady=11, cursor="hand2").pack(fill="x")

        line = tk.Frame(card_inner, bg=SURFACE)
        line.pack(fill="x", pady=16)
        tk.Frame(line, bg="#ECE1D8", height=1).pack(side="left", fill="x", expand=True, pady=8)
        tk.Label(line, text="или", bg=SURFACE, fg=MUTED, font=("Arial", 10)).pack(side="left", padx=10)
        tk.Frame(line, bg="#ECE1D8", height=1).pack(side="left", fill="x", expand=True, pady=8)

        tk.Button(card_inner, text="Создать аккаунт", command=self.open_register_dialog, bg=BLUE, activebackground=BLUE_DARK, fg=TEXT,
                  font=("Arial", 12, "bold"), relief="flat", pady=11, cursor="hand2").pack(fill="x")
        tk.Button(card_inner, text="Продолжить как гость", command=self.start_guest_mode, bg=YELLOW, activebackground="#E7D79F", fg=TEXT,
                  font=("Arial", 12, "bold"), relief="flat", pady=11, cursor="hand2").pack(fill="x", pady=(12, 0))

        hint = tk.Frame(card_inner, bg="#FAF6F2", highlightthickness=1, highlightbackground="#EFE2D8")
        hint.pack(fill="x", pady=(22, 0))
        tk.Label(
            hint,
            text="Гость тоже может сохранять XP, серию дней и прогресс по урокам. Данные остаются на этом устройстве.",
            bg="#FAF6F2",
            fg=MUTED,
            justify="left",
            wraplength=360,
            font=("Arial", 10),
        ).pack(anchor="w", padx=14, pady=12)
    def handle_login(self):
        user = login_user(self.username_entry.get(), self.password_entry.get())
        if not user:
            self.auth_message.config(text="Неверный логин или пароль", fg=RED)
            return
        self.current_user = user
        self.show_dashboard()

    def _dialog_entry(self, parent, label, show=None):
        tk.Label(parent, text=label, bg=SURFACE, fg=TEXT, font=("Arial", 10, "bold")).pack(anchor="w", padx=34, pady=(8, 0))
        entry = tk.Entry(parent, font=("Arial", 12), relief="solid", bd=1, show=show)
        entry.pack(fill="x", padx=34, pady=(6, 0), ipady=8)
        return entry

    def open_register_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Регистрация — EnglisDuck")
        dialog.resizable(False, False)
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        dialog.grab_set()
        self.center_window(dialog, 500, 520)

        body = tk.Frame(dialog, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        body.pack(fill="both", expand=True, padx=18, pady=18)

        self.draw_duck(body, size=88, bg=SURFACE).pack(pady=(16, 8))
        tk.Label(body, text="Регистрация", bg=SURFACE, fg=TEXT, font=("Arial", 22, "bold")).pack()
        tk.Label(body, text="Создайте новый аккаунт и подтвердите действие", bg=SURFACE, fg=MUTED, font=("Arial", 11)).pack(pady=(6, 16))
        dialog_message = tk.Label(body, text="", bg=SURFACE, fg=MUTED, font=("Arial", 10), wraplength=380)
        dialog_message.pack()

        username_entry = self._dialog_entry(body, "Логин")
        password_entry = self._dialog_entry(body, "Пароль", show="*")
        confirm_entry = self._dialog_entry(body, "Подтверждение пароля", show="*")
        username_entry.focus_set()

        def do_register():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            confirm = confirm_entry.get().strip()
            if not messagebox.askyesno("Подтверждение регистрации", f"Создать аккаунт '{username}' в EnglisDuck?", parent=dialog):
                return
            ok, message = register_user(username, password, confirm)
            dialog_message.config(text=message, fg=SUCCESS if ok else RED)
            if ok:
                messagebox.showinfo("Готово", "Аккаунт создан. Теперь можно войти в приложение.", parent=dialog)
                self.username_entry.delete(0, tk.END)
                self.username_entry.insert(0, username)
                self.password_entry.delete(0, tk.END)
                dialog.destroy()

        buttons = tk.Frame(body, bg=SURFACE)
        buttons.pack(fill="x", padx=34, pady=(22, 18))
        tk.Button(buttons, text="Подтвердить", command=do_register, bg=ACCENT, activebackground=ACCENT_DARK, fg=TEXT,
                  relief="flat", font=("Arial", 11, "bold"), pady=10, cursor="hand2").pack(side="left", fill="x", expand=True)
        tk.Button(buttons, text="Отмена", command=dialog.destroy, bg=PANEL, activebackground="#E9DFD6", fg=TEXT,
                  relief="flat", font=("Arial", 11, "bold"), pady=10, padx=18, cursor="hand2").pack(side="left", padx=(10, 0))

    def start_guest_mode(self):
        answer = messagebox.askyesno("Гостевой режим", "Продолжить как гость? Прогресс будет сохранён локально на этом устройстве.")
        if not answer:
            return
        self.current_user = get_or_create_guest_user()
        self.show_dashboard()

    def stat_card(self, parent, title, value, accent, subtitle=None):
        card = tk.Frame(parent, bg="#FCFAF8", highlightthickness=1, highlightbackground="#EFE4DA")
        card.pack(fill="x", padx=18, pady=8)
        tk.Frame(card, bg=accent, width=8, height=74).pack(side="left", fill="y")
        text_wrap = tk.Frame(card, bg="#FCFAF8")
        text_wrap.pack(side="left", fill="both", expand=True, padx=12, pady=12)
        tk.Label(text_wrap, text=title, bg="#FCFAF8", fg=MUTED, font=("Arial", 10, "bold")).pack(anchor="w")
        tk.Label(text_wrap, text=value, bg="#FCFAF8", fg=TEXT, font=("Arial", 17, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(text_wrap, text=subtitle, bg="#FCFAF8", fg=MUTED, font=("Arial", 9)).pack(anchor="w", pady=(2, 0))

    def animated_progress(self, parent, title, target, style_name, color_soft):
        card = tk.Frame(parent, bg=color_soft, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", padx=18, pady=8)
        tk.Label(card, text=title, bg=color_soft, fg=TEXT, font=("Arial", 10, "bold")).pack(anchor="w", padx=14, pady=(12, 6))
        value_label = tk.Label(card, text="0%", bg=color_soft, fg=MUTED, font=("Arial", 10))
        value_label.pack(anchor="e", padx=14)
        bar = ttk.Progressbar(card, maximum=100, value=0, style=style_name)
        bar.pack(fill="x", padx=14, pady=(4, 14))
        self.animate_progressbar(bar, value_label, int(target))

    def animate_progressbar(self, bar, label, target, step=2):
        current = int(float(bar["value"]))
        if current >= target:
            label.config(text=f"{target}%")
            return
        current = min(target, current + step)
        bar["value"] = current
        label.config(text=f"{current}%")
        self.root.after(16, lambda: self.animate_progressbar(bar, label, target, step))

    def filter_button(self, parent, level: str):
        selected = self.difficulty_filter.get() == level
        bg = ACCENT if selected else PANEL
        return tk.Button(parent, text=level, command=lambda value=level: self.apply_filter(value), bg=bg, activebackground=ACCENT,
                         fg=TEXT, relief="flat", font=("Arial", 10, "bold"), padx=14, pady=8, cursor="hand2")

    def apply_filter(self, level: str):
        self.difficulty_filter.set(level)
        self.dashboard_columns = None
        self.show_dashboard()

    def show_dashboard(self):
        self.current_user = get_user(self.current_user.id)
        self.dashboard_lessons = get_lessons_for_user(self.current_user.id, self.difficulty_filter.get())
        stats = get_dashboard_stats(self.current_user.id)

        self.clear_screen()
        self.create_topbar("Главная")

        wrapper = tk.Frame(self.main_frame, bg=BG)
        wrapper.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        wrapper.grid_columnconfigure(1, weight=1)
        wrapper.grid_rowconfigure(0, weight=1)

        sidebar = tk.Frame(wrapper, bg=SURFACE, width=240, highlightthickness=1, highlightbackground=BORDER)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        content = tk.Frame(wrapper, bg=BG)
        content.grid(row=0, column=1, sticky="nsew", padx=(20, 0))
        content.grid_rowconfigure(4, weight=1)
        content.grid_columnconfigure(0, weight=1)

        self.draw_duck(sidebar, size=94, bg=SURFACE).pack(pady=(18, 6))
        tk.Label(sidebar, text="Ваш прогресс", bg=SURFACE, fg=TEXT, font=("Arial", 18, "bold")).pack(anchor="w", padx=18, pady=(4, 8))
        self.stat_card(sidebar, "XP", str(self.current_user.xp), ACCENT_DARK, "Опыт растёт за каждый урок")
        self.stat_card(sidebar, "Серия дней", str(self.current_user.streak), BLUE_DARK, "Возвращайся каждый день")
        self.stat_card(sidebar, "Пройдено уроков", f"{stats['completed_lessons']} / {stats['total_lessons']}", PEACH_DARK, "Закрывай темы по очереди")
        self.animated_progress(sidebar, "Общее выполнение", stats['completion_percent'], "duck.Horizontal.TProgressbar", ACCENT_SOFT)

        tk.Button(sidebar, text="Статистика", command=self.show_progress_screen, bg=BLUE, fg=TEXT,
                  font=("Arial", 12, "bold"), relief="flat", cursor="hand2", pady=10).pack(fill="x", padx=18, pady=(10, 8))
        tk.Button(sidebar, text="Выйти", command=self.show_auth_screen, bg=PANEL, fg=TEXT,
                  font=("Arial", 12, "bold"), relief="flat", cursor="hand2", pady=10).pack(fill="x", padx=18)

        banner = tk.Frame(content, bg=ACCENT_SOFT, highlightthickness=1, highlightbackground="#D8E7D4")
        banner.grid(row=0, column=0, sticky="ew")
        banner.grid_columnconfigure(0, weight=1)
        banner.grid_columnconfigure(1, weight=0)

        text_wrap = tk.Frame(banner, bg=ACCENT_SOFT)
        text_wrap.grid(row=0, column=0, sticky="nsew", padx=(22, 12), pady=18)
        tk.Label(text_wrap, text="EnglisDuck — учись спокойно и регулярно", bg=ACCENT_SOFT, fg=TEXT, font=("Arial", 24, "bold")).pack(anchor="w")
        tk.Label(text_wrap, text=random.choice(DUCK_TIPS), bg=ACCENT_SOFT, fg=MUTED, font=("Arial", 12), wraplength=700, justify="left").pack(anchor="w", pady=(10, 10))

        chip_row = tk.Frame(text_wrap, bg=ACCENT_SOFT)
        chip_row.pack(anchor="w", pady=(2, 0))
        dash_chips = [
            (f"Всего уроков: {stats['total_lessons']}", "#F8FBF7"),
            (f"Выполнено: {stats['completion_percent']}%", "#F5F8FC"),
            ("Уровни: начальный • средний • сложный", "#FEF7F3"),
        ]
        for text_value, chip_bg in dash_chips:
            chip = tk.Frame(chip_row, bg=chip_bg, highlightthickness=1, highlightbackground=BORDER)
            chip.pack(side="left", padx=(0, 8), pady=4)
            tk.Label(chip, text=text_value, bg=chip_bg, fg=TEXT, font=("Arial", 10, "bold")).pack(padx=12, pady=8)

        duck_wrap = tk.Frame(banner, bg=ACCENT_SOFT)
        duck_wrap.grid(row=0, column=1, padx=(4, 20), pady=14)
        self.draw_duck(duck_wrap, size=124, bg=ACCENT_SOFT).pack()

        filter_card = tk.Frame(content, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        filter_card.grid(row=1, column=0, sticky="ew", pady=(18, 12))
        tk.Label(filter_card, text="Уровень", bg=SURFACE, fg=TEXT, font=("Arial", 12, "bold")).pack(side="left", padx=(18, 12), pady=12)
        for level in ["Все", "Начальный", "Средний", "Сложный"]:
            self.filter_button(filter_card, level).pack(side="left", padx=4, pady=10)

        path_card = tk.Frame(content, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        path_card.grid(row=2, column=0, sticky="ew")
        tk.Label(path_card, text="Учебная тропа", bg=SURFACE, fg=TEXT, font=("Arial", 18, "bold")).pack(anchor="w", padx=18, pady=(16, 6))
        tk.Label(path_card, text="Выбирай тему как на карте пути: нажми на узел и начни урок.", bg=SURFACE, fg=MUTED, font=("Arial", 11)).pack(anchor="w", padx=18)
        path_canvas = tk.Canvas(path_card, bg=SURFACE, height=200, highlightthickness=0)
        path_canvas.pack(fill="x", padx=10, pady=(8, 12))
        path_canvas.bind("<Configure>", lambda e, c=path_canvas: self.draw_learning_path(c))

        tk.Label(content, text="Доступные уроки", bg=BG, fg=TEXT, font=("Arial", 22, "bold")).grid(row=3, column=0, sticky="w", pady=(14, 8))

        canvas_wrap = tk.Frame(content, bg=BG)
        canvas_wrap.grid(row=4, column=0, sticky="nsew")
        canvas_wrap.grid_rowconfigure(0, weight=1)
        canvas_wrap.grid_columnconfigure(0, weight=1)

        self.cards_canvas = tk.Canvas(canvas_wrap, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_wrap, orient="vertical", command=self.cards_canvas.yview)
        self.cards_container = tk.Frame(self.cards_canvas, bg=BG)
        self.cards_window = self.cards_canvas.create_window((0, 0), window=self.cards_container, anchor="nw")
        self.cards_canvas.configure(yscrollcommand=scrollbar.set)
        self.cards_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.cards_container.bind("<Configure>", lambda e: self.cards_canvas.configure(scrollregion=self.cards_canvas.bbox("all")))
        self.cards_canvas.bind("<Configure>", self.on_dashboard_canvas_configure)
        self._bind_mousewheel(self.cards_canvas)
        self.render_dashboard_cards(self.cards_canvas.winfo_width() or 980)
    def draw_learning_path(self, canvas: tk.Canvas):
        canvas.delete("all")
        self.path_buttons.clear()
        lessons = self.dashboard_lessons[:6]
        if not lessons:
            canvas.create_text(120, 70, text="Для этого уровня уроков пока нет.", fill=MUTED, font=("Arial", 12))
            return

        width = max(canvas.winfo_width(), 920)
        height = max(canvas.winfo_height(), 200)
        margin_x = 56
        line_y_positions = [92, 62, 120, 62, 120, 92]
        step = (width - margin_x * 2) / max(len(lessons) - 1, 1) if len(lessons) > 1 else width / 2

        points = []
        for idx, lesson in enumerate(lessons):
            x = margin_x + idx * step if len(lessons) > 1 else width / 2
            y = line_y_positions[idx % len(line_y_positions)]
            points.append((x, y, lesson))

        for i in range(len(points) - 1):
            x1, y1, _ = points[i]
            x2, y2, _ = points[i + 1]
            canvas.create_line(x1 + 24, y1, x2 - 24, y2, fill="#D7CCC3", width=4, smooth=True)

        title_map = {
            "Приветствия": "Приветствия",
            "Еда и напитки": "Еда и напитки",
            "Путешествия": "Путешествия",
            "Повседневные фразы": "Повседневные фразы",
            "Работа и обучение": "Работа и обучение",
            "Устойчивые выражения": "Устойчивые выражения",
        }

        for x, y, lesson in points:
            accent, soft = DIFFICULTY_COLORS.get(lesson.difficulty, (ACCENT_DARK, ACCENT_SOFT))
            tag = f"lesson_{lesson.id}"
            r = 20
            canvas.create_oval(x - r, y - r, x + r, y + r, fill=soft, outline=accent, width=2, tags=(tag,))
            canvas.create_text(x, y, text=LESSON_ICONS.get(lesson.title, "📘"), fill=TEXT, font=("Arial", 11, "bold"), tags=(tag,))

            label_text = title_map.get(lesson.title, lesson.title)
            approx_w = min(150, max(90, int(len(label_text) * 7.2)))
            label_y = y + 34
            canvas.create_rectangle(x - approx_w / 2, label_y - 13, x + approx_w / 2, label_y + 13,
                                    fill=accent, outline="", tags=(tag,))
            canvas.create_text(x, label_y, text=label_text, width=approx_w - 12, justify="center",
                               fill="white", font=("Arial", 9, "bold"), tags=(tag,))

            canvas.tag_bind(tag, "<Button-1>", lambda e, lid=lesson.id: self.show_lesson_screen(lid))
            canvas.tag_bind(tag, "<Enter>", lambda e, c=canvas: c.config(cursor="hand2"))
            canvas.tag_bind(tag, "<Leave>", lambda e, c=canvas: c.config(cursor=""))
    def _bind_mousewheel(self, widget: tk.Widget):
        widget.bind("<MouseWheel>", lambda e: widget.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        widget.bind("<Button-4>", lambda e: widget.yview_scroll(-1, "units"))
        widget.bind("<Button-5>", lambda e: widget.yview_scroll(1, "units"))

    def on_dashboard_canvas_configure(self, event):
        if self.cards_window is not None:
            self.cards_canvas.itemconfigure(self.cards_window, width=event.width)
        self.render_dashboard_cards(event.width)

    def render_dashboard_cards(self, width: int):
        if self.cards_container is None:
            return
        columns = 1 if width < 760 else (2 if width < 1180 else 3)
        if self.dashboard_columns == columns and self.cards_container.winfo_children():
            return
        self.dashboard_columns = columns
        for child in self.cards_container.winfo_children():
            child.destroy()

        if not self.dashboard_lessons:
            empty = tk.Frame(self.cards_container, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
            empty.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
            tk.Label(empty, text="Для выбранного уровня пока нет уроков.", bg=SURFACE, fg=MUTED, font=("Arial", 12)).pack(padx=24, pady=24)
            self.cards_container.grid_columnconfigure(0, weight=1)
            return

        for index, lesson in enumerate(self.dashboard_lessons):
            row = index // columns
            col = index % columns
            self.lesson_card(self.cards_container, lesson, row, col)

        for col in range(columns):
            self.cards_container.grid_columnconfigure(col, weight=1, uniform="lesson")

    def lesson_card(self, parent, lesson, row, col):
        accent, soft = DIFFICULTY_COLORS.get(lesson.difficulty, (ACCENT_DARK, ACCENT_SOFT))
        card = tk.Frame(parent, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)

        top = tk.Frame(card, bg=SURFACE)
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        top.grid_columnconfigure(1, weight=1)
        icon = LESSON_ICONS.get(lesson.title, "📘")
        tk.Label(top, text=icon, bg=soft, fg=accent, font=("Arial", 20, "bold"), width=3, pady=6).grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 12))
        tk.Label(top, text=lesson.title, bg=SURFACE, fg=TEXT, font=("Arial", 15, "bold"), justify="left").grid(row=0, column=1, sticky="w")
        tk.Label(top, text=lesson.difficulty, bg=soft, fg=accent, font=("Arial", 10, "bold"), padx=10, pady=4).grid(row=1, column=1, sticky="w", pady=(8, 0))

        body = tk.Frame(card, bg=SURFACE)
        body.grid(row=1, column=0, sticky="nsew", padx=16)
        body.grid_columnconfigure(0, weight=1)
        tk.Label(body, text=lesson.description, bg=SURFACE, fg=MUTED, justify="left", wraplength=280, font=("Arial", 11)).grid(row=0, column=0, sticky="nw")
        progress_text = f"Лучший результат: {lesson.best_score} / {lesson.question_count}    Попыток: {lesson.attempts}"
        tk.Label(body, text=progress_text, bg=SURFACE, fg=TEXT, font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=(18, 8))
        progress_value = int((lesson.best_score / lesson.question_count) * 100) if lesson.question_count else 0
        style_name = "duck.Horizontal.TProgressbar" if lesson.difficulty == "Начальный" else ("blue.Horizontal.TProgressbar" if lesson.difficulty == "Средний" else "peach.Horizontal.TProgressbar")
        progress = ttk.Progressbar(body, maximum=100, value=progress_value, style=style_name)
        progress.grid(row=2, column=0, sticky="ew")

        button_row = tk.Frame(card, bg=SURFACE)
        button_row.grid(row=2, column=0, sticky="ew", padx=16, pady=(14, 16))
        tk.Button(button_row, text="Начать", command=lambda lid=lesson.id: self.show_lesson_screen(lid), bg=accent,
                  activebackground=accent, fg="white", font=("Arial", 12, "bold"), relief="flat", cursor="hand2", pady=10).pack(fill="x")

    def show_progress_screen(self):
        self.current_user = get_user(self.current_user.id)
        lessons = get_lessons_for_user(self.current_user.id)
        stats = get_dashboard_stats(self.current_user.id)

        self.clear_screen()
        self.create_topbar("Статистика", back_command=self.show_dashboard)

        body = tk.Frame(self.main_frame, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        summary = tk.Frame(body, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        summary.pack(fill="x")
        header = tk.Frame(summary, bg=SURFACE)
        header.pack(fill="x", padx=18, pady=(16, 8))
        self.draw_duck(header, size=72, bg=SURFACE).pack(side="left")
        info = tk.Frame(header, bg=SURFACE)
        info.pack(side="left", padx=12)
        tk.Label(info, text="Общий прогресс", bg=SURFACE, fg=TEXT, font=("Arial", 18, "bold")).pack(anchor="w")
        tk.Label(info, text=f"Пройдено уроков: {stats['completed_lessons']} из {stats['total_lessons']} | Баллы: {stats['total_points']} | XP: {self.current_user.xp}",
                 bg=SURFACE, fg=MUTED, font=("Arial", 12)).pack(anchor="w", pady=(4, 0))
        summary_bar = ttk.Progressbar(summary, maximum=100, value=0, style="blue.Horizontal.TProgressbar")
        summary_bar.pack(fill="x", padx=20, pady=(0, 18))
        self.animate_progressbar(summary_bar, tk.Label(summary, bg=SURFACE), stats["completion_percent"])

        levels = tk.Frame(body, bg=BG)
        levels.pack(fill="x", pady=(18, 12))
        for idx, level in enumerate(["Начальный", "Средний", "Сложный"]):
            total = stats["level_totals"].get(level, 0)
            done = stats["level_completed"].get(level, 0)
            self.level_summary_card(levels, level, done, total, idx)

        chart_card = tk.Frame(body, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        chart_card.pack(fill="both", expand=True)
        tk.Label(chart_card, text="Успеваемость по урокам", bg=SURFACE, fg=TEXT, font=("Arial", 18, "bold")).pack(anchor="w", padx=20, pady=(18, 14))
        chart = tk.Canvas(chart_card, bg=SURFACE, height=320, highlightthickness=0)
        chart.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        chart.bind("<Configure>", lambda e, c=chart, l=lessons: self.draw_chart(c, l))
        self.draw_chart(chart, lessons)

    def level_summary_card(self, parent, level, done, total, column):
        accent, soft = DIFFICULTY_COLORS[level]
        card = tk.Frame(parent, bg=soft, highlightthickness=1, highlightbackground=BORDER)
        card.grid(row=0, column=column, padx=(0 if column == 0 else 10, 0), sticky="nsew")
        parent.grid_columnconfigure(column, weight=1)
        tk.Label(card, text=level, bg=soft, fg=accent, font=("Arial", 13, "bold")).pack(anchor="w", padx=18, pady=(16, 6))
        tk.Label(card, text=f"Пройдено: {done} из {total}", bg=soft, fg=TEXT, font=("Arial", 12, "bold")).pack(anchor="w", padx=18)
        pct = int((done / total) * 100) if total else 0
        lab = tk.Label(card, text="0%", bg=soft, fg=MUTED, font=("Arial", 10))
        lab.pack(anchor="e", padx=18, pady=(6, 0))
        style_name = "duck.Horizontal.TProgressbar" if level == "Начальный" else ("blue.Horizontal.TProgressbar" if level == "Средний" else "peach.Horizontal.TProgressbar")
        bar = ttk.Progressbar(card, maximum=100, value=0, style=style_name)
        bar.pack(fill="x", padx=18, pady=(4, 16))
        self.animate_progressbar(bar, lab, pct)

    def draw_chart(self, canvas: tk.Canvas, lessons):
        canvas.delete("all")
        width = max(canvas.winfo_width(), 860)
        height = max(canvas.winfo_height(), 260)
        bottom = height - 40
        left = 60
        top = 30
        available = max(1, len(lessons))
        bar_width = max(60, min(110, (width - 140) // max(available, 1) - 18))
        gap = 18

        canvas.create_line(left, top, left, bottom, fill="#C8BCB1", width=2)
        canvas.create_line(left, bottom, width - 20, bottom, fill="#C8BCB1", width=2)
        for i in range(7):
            y = bottom - i * ((bottom - top) / 6)
            canvas.create_line(left - 5, y, width - 20, y, fill="#F0E7DE")
            canvas.create_text(left - 18, y, text=str(i), fill=MUTED, font=("Arial", 10))

        for idx, lesson in enumerate(lessons):
            accent, _ = DIFFICULTY_COLORS.get(lesson.difficulty, (ACCENT_DARK, ACCENT_SOFT))
            x1 = left + 24 + idx * (bar_width + gap)
            x2 = x1 + bar_width
            bar_height = lesson.best_score * ((bottom - top - 10) / 6)
            y1 = bottom - bar_height
            canvas.create_rectangle(x1, y1, x2, bottom, fill=accent, outline="")
            canvas.create_text((x1 + x2) / 2, y1 - 10, text=str(lesson.best_score), fill=TEXT, font=("Arial", 10, "bold"))
            canvas.create_text((x1 + x2) / 2, bottom + 18, text=lesson.title, width=bar_width + 20, fill=TEXT, font=("Arial", 10))

    def show_lesson_screen(self, lesson_id: int):
        lessons = get_lessons_for_user(self.current_user.id)
        self.current_lesson = next((lesson for lesson in lessons if lesson.id == lesson_id), None)
        self.questions = get_questions_for_lesson(lesson_id)
        self.question_index = 0
        self.score = 0
        self.hearts = 3

        self.clear_screen()
        self.create_topbar(self.current_lesson.title, back_command=self.show_dashboard)

        body = tk.Frame(self.main_frame, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        top_status = tk.Frame(body, bg=BG)
        top_status.pack(fill="x", pady=(8, 12))
        self.hearts_label = tk.Label(top_status, text=f"❤ Жизни: {self.hearts}", bg=BG, fg=RED, font=("Arial", 14, "bold"))
        self.hearts_label.pack(side="left")
        self.progress_label = tk.Label(top_status, text="Вопрос 1", bg=BG, fg=TEXT, font=("Arial", 14, "bold"))
        self.progress_label.pack(side="right")
        self.lesson_progress = ttk.Progressbar(body, maximum=len(self.questions), value=1, style="duck.Horizontal.TProgressbar")
        self.lesson_progress.pack(fill="x")

        card = tk.Frame(body, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="both", expand=True, pady=(18, 0))
        accent, soft = DIFFICULTY_COLORS.get(self.current_lesson.difficulty, (ACCENT_DARK, ACCENT_SOFT))

        header = tk.Frame(card, bg=SURFACE)
        header.pack(fill="x", padx=24, pady=(20, 0))
        tk.Label(header, text=LESSON_ICONS.get(self.current_lesson.title, '📘'), bg=soft, fg=accent, font=("Arial", 22, "bold"), padx=16, pady=10).pack(side="left")
        tk.Label(header, text=f"Уровень: {self.current_lesson.difficulty}", bg=soft, fg=accent, font=("Arial", 11, "bold"), padx=12, pady=6).pack(side="left", padx=(12, 0), pady=(10, 0))

        self.prompt_label = tk.Label(card, text="", bg=SURFACE, fg=TEXT, wraplength=780, justify="center", font=("Arial", 24, "bold"))
        self.prompt_label.pack(pady=(28, 20), padx=20)
        self.feedback_label = tk.Label(card, text="", bg=SURFACE, fg=MUTED, font=("Arial", 12, "bold"))
        self.feedback_label.pack(pady=(0, 12))

        coach = tk.Label(card, text="🦆 Подсказка: читай вопрос спокойно и ищи знакомое слово или фразу.", bg=SURFACE, fg=MUTED, font=("Arial", 11))
        coach.pack(pady=(0, 8))

        options_wrap = tk.Frame(card, bg=SURFACE)
        options_wrap.pack(padx=30, pady=(0, 30), fill="both", expand=True)
        self.option_buttons = []
        for row in range(2):
            options_wrap.grid_rowconfigure(row, weight=1)
        for col in range(2):
            options_wrap.grid_columnconfigure(col, weight=1)
        for idx in range(4):
            btn = tk.Button(options_wrap, text="", bg="#FBF8F4", fg=TEXT, activebackground="#F2ECE6", font=("Arial", 14, "bold"),
                            relief="solid", bd=1, wraplength=280, cursor="hand2", padx=10, pady=18)
            btn.grid(row=idx // 2, column=idx % 2, padx=12, pady=12, sticky="nsew")
            self.option_buttons.append(btn)
        self.load_question()

    def load_question(self):
        if self.question_index >= len(self.questions) or self.hearts <= 0:
            self.finish_lesson()
            return
        self.current_question = self.questions[self.question_index]
        options = list(self.current_question.options)
        random.shuffle(options)
        self.prompt_label.config(text=self.current_question.prompt)
        self.feedback_label.config(text="Выберите правильный ответ", fg=MUTED)
        self.progress_label.config(text=f"Вопрос {self.question_index + 1} из {len(self.questions)}")
        self.hearts_label.config(text=f"❤ Жизни: {self.hearts}")
        self.lesson_progress.configure(value=self.question_index + 1)

        for button, option in zip(self.option_buttons, options):
            button.config(text=option, command=lambda value=option: self.check_answer(value), state="normal", bg="#FBF8F4", fg=TEXT, activebackground="#F2ECE6")

    def check_answer(self, selected_option: str):
        correct = self.current_question.correct_answer
        for button in self.option_buttons:
            button.config(state="disabled")
            if button.cget("text") == correct:
                button.config(bg="#E3F2DF", activebackground="#E3F2DF")
            elif button.cget("text") == selected_option and selected_option != correct:
                button.config(bg="#F8DFDF", activebackground="#F8DFDF")
        if selected_option == correct:
            self.score += 1
            self.feedback_label.config(text="Верно! Отличный шаг вперёд.", fg=SUCCESS)
        else:
            self.hearts -= 1
            self.hearts_label.config(text=f"❤ Жизни: {self.hearts}")
            self.feedback_label.config(text=f"Неправильно. Верный ответ: {correct}", fg=RED)
        self.question_index += 1
        self.root.after(1000, self.load_question)

    def finish_lesson(self):
        result = submit_lesson_result(user_id=self.current_user.id, lesson_id=self.current_lesson.id, score=self.score, total=len(self.questions))
        self.current_user = get_user(self.current_user.id)
        percent = int((result.score / result.total) * 100) if result.total else 0
        messagebox.showinfo("Урок завершён", f"Урок: {self.current_lesson.title}\n\nРезультат: {result.score} из {result.total} ({percent}%)\nПолучено XP: {result.gained_xp}\nСерия дней: {result.streak}\n\nПродолжайте обучение в EnglisDuck!")
        self.show_dashboard()


if __name__ == "__main__":
    root = tk.Tk()
    app = EnglisDuckApp(root)
    root.mainloop()
