"""Вкладка «Просмотр успеваемости»."""

import tkinter as tk
from tkinter import ttk, messagebox

from models import Search
from repository import GradeRepository


class ViewTab(ttk.Frame):
    """Вкладка просмотра оценок с фильтрами.

    Позволяет фильтровать оценки по студенту, дисциплине, семестру
    и типу контроля, отображая результаты в таблице.
    """

    def __init__(self, parent: ttk.Notebook, repo: GradeRepository) -> None:
        """Инициализирует вкладку просмотра.

        Args:
            parent: Родительский виджет (ttk.Notebook).
            repo: Репозиторий данных.
        """
        super().__init__(parent)
        self.repo = repo
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Создаёт элементы интерфейса вкладки."""
        # --- панель фильтров ---
        filter_frame = ttk.LabelFrame(self, text="Фильтры")
        filter_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(filter_frame, text="Студент:").grid(row=0, column=0, padx=6, pady=4, sticky=tk.W)
        self._student_var = tk.StringVar()
        self._student_cb = ttk.Combobox(filter_frame, textvariable=self._student_var, width=30, state="readonly")
        self._student_cb.grid(row=0, column=1, padx=6, pady=4)

        ttk.Label(filter_frame, text="Дисциплина:").grid(row=0, column=2, padx=6, pady=4, sticky=tk.W)
        self._disc_var = tk.StringVar()
        self._disc_cb = ttk.Combobox(filter_frame, textvariable=self._disc_var, width=30, state="readonly")
        self._disc_cb.grid(row=0, column=3, padx=6, pady=4)

        ttk.Label(filter_frame, text="Семестр:").grid(row=1, column=0, padx=6, pady=4, sticky=tk.W)
        self._sem_var = tk.StringVar()
        self._sem_cb = ttk.Combobox(filter_frame, textvariable=self._sem_var, width=12, state="readonly")
        self._sem_cb.grid(row=1, column=1, padx=6, pady=4, sticky=tk.W)

        ttk.Label(filter_frame, text="Тип контроля:").grid(row=1, column=2, padx=6, pady=4, sticky=tk.W)
        self._type_var = tk.StringVar()
        self._type_cb = ttk.Combobox(filter_frame, textvariable=self._type_var, width=18, state="readonly")
        self._type_cb.grid(row=1, column=3, padx=6, pady=4, sticky=tk.W)

        btn_frame = ttk.Frame(filter_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=6)
        ttk.Button(btn_frame, text="Найти", command=self._search).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="Сбросить", command=self._reset).pack(side=tk.LEFT, padx=4)

        # --- таблица результатов ---
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        columns = ("student", "discipline", "semester", "type", "value", "date", "teacher", "comment")
        self._tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)

        headers = {
            "student": ("Студент", 200),
            "discipline": ("Дисциплина", 190),
            "semester": ("Семестр", 65),
            "type": ("Тип контроля", 110),
            "value": ("Оценка", 60),
            "date": ("Дата", 90),
            "teacher": ("Преподаватель", 180),
            "comment": ("Комментарий", 160),
        }
        for col, (heading, width) in headers.items():
            self._tree.heading(col, text=heading)
            self._tree.column(col, width=width, anchor=tk.CENTER if col in ("semester", "value", "date") else tk.W)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # --- строка статуса ---
        self._status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self._status_var, foreground="gray").pack(anchor=tk.W, padx=10, pady=2)

    def refresh(self) -> None:
        """Обновляет списки выбора и перезагружает данные."""
        students = self.repo.getStudents()
        disciplines = self.repo.getDisciplines()

        student_names = [""] + [s.fullName for s in students]
        disc_names = [""] + [d.name for d in disciplines]
        semesters = [""] + sorted({str(d.semester) for d in disciplines})
        types = ["", "экзамен", "зачёт", "КР", "практика"]

        self._student_cb["values"] = student_names
        self._disc_cb["values"] = disc_names
        self._sem_cb["values"] = semesters
        self._type_cb["values"] = types

        self._search()

    def _search(self) -> None:
        """Выполняет поиск с текущими фильтрами и обновляет таблицу."""
        sem_text = self._sem_var.get().strip()
        criteria = Search(
            studentName=self._student_var.get().strip(),
            disciplineName=self._disc_var.get().strip(),
            semester=int(sem_text) if sem_text else None,
            assessmentType=self._type_var.get().strip(),
        )

        grades = self.repo.findGrades(criteria)
        self._populate(grades)
        self._status_var.set(f"Найдено записей: {len(grades)}")

    def _reset(self) -> None:
        """Сбрасывает фильтры и показывает все оценки."""
        self._student_var.set("")
        self._disc_var.set("")
        self._sem_var.set("")
        self._type_var.set("")
        self._search()

    def _populate(self, grades) -> None:
        """Заполняет таблицу списком оценок.

        Args:
            grades: Список объектов Grade.
        """
        for row in self._tree.get_children():
            self._tree.delete(row)

        for g in grades:
            student = self.repo.getStudentById(g.studentId)
            discipline = self.repo.getDisciplineById(g.disciplineId)
            teacher = self.repo.getTeacherById(g.teacherId)

            self._tree.insert("", tk.END, values=(
                student.fullName if student else "—",
                discipline.name if discipline else "—",
                discipline.semester if discipline else "—",
                g.assessmentType,
                g.value,
                g.date,
                teacher.fullName if teacher else "—",
                g.comment,
            ))
