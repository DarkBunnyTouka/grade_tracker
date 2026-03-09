"""Вкладка «Выставление оценки»."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

from models import Grade
from repository import GradeRepository


class SubmitTab(ttk.Frame):
    """Вкладка выставления новой оценки студенту.

    Преподаватель выбирает студента, дисциплину, тип контроля,
    вводит значение и необязательный комментарий.
    """

    def __init__(
        self,
        parent: ttk.Notebook,
        repo: GradeRepository,
        on_change: Callable,
    ) -> None:
        """Инициализирует вкладку выставления оценки.

        Args:
            parent: Родительский виджет (ttk.Notebook).
            repo: Репозиторий данных.
            on_change: Callback, вызываемый после сохранения оценки.
        """
        super().__init__(parent)
        self.repo = repo
        self.on_change = on_change
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Создаёт элементы интерфейса вкладки."""
        form = ttk.LabelFrame(self, text="Новая оценка")
        form.pack(fill=tk.X, padx=10, pady=10)

        # преподаватель
        ttk.Label(form, text="Преподаватель:").grid(row=0, column=0, padx=8, pady=6, sticky=tk.W)
        self._teacher_var = tk.StringVar()
        self._teacher_cb = ttk.Combobox(form, textvariable=self._teacher_var, width=35, state="readonly")
        self._teacher_cb.grid(row=0, column=1, padx=8, pady=6, sticky=tk.W)

        # студент
        ttk.Label(form, text="Студент:").grid(row=1, column=0, padx=8, pady=6, sticky=tk.W)
        self._student_var = tk.StringVar()
        self._student_cb = ttk.Combobox(form, textvariable=self._student_var, width=35, state="readonly")
        self._student_cb.grid(row=1, column=1, padx=8, pady=6, sticky=tk.W)

        # дисциплина
        ttk.Label(form, text="Дисциплина:").grid(row=2, column=0, padx=8, pady=6, sticky=tk.W)
        self._disc_var = tk.StringVar()
        self._disc_cb = ttk.Combobox(form, textvariable=self._disc_var, width=35, state="readonly")
        self._disc_cb.grid(row=2, column=1, padx=8, pady=6, sticky=tk.W)

        # тип контроля
        ttk.Label(form, text="Тип контроля:").grid(row=3, column=0, padx=8, pady=6, sticky=tk.W)
        self._type_var = tk.StringVar()
        self._type_cb = ttk.Combobox(
            form,
            textvariable=self._type_var,
            values=["экзамен", "зачёт", "КР", "практика"],
            width=18,
            state="readonly",
        )
        self._type_cb.grid(row=3, column=1, padx=8, pady=6, sticky=tk.W)
        self._type_cb.current(0)

        # оценка
        ttk.Label(form, text="Оценка (2–5):").grid(row=4, column=0, padx=8, pady=6, sticky=tk.W)
        self._value_var = tk.IntVar(value=5)
        ttk.Spinbox(form, from_=2, to=5, textvariable=self._value_var, width=6).grid(
            row=4, column=1, padx=8, pady=6, sticky=tk.W
        )

        # комментарий
        ttk.Label(form, text="Комментарий:").grid(row=5, column=0, padx=8, pady=6, sticky=tk.W)
        self._comment_var = tk.StringVar()
        ttk.Entry(form, textvariable=self._comment_var, width=40).grid(
            row=5, column=1, padx=8, pady=6, sticky=tk.W
        )

        ttk.Button(form, text="Выставить оценку", command=self._submit).grid(
            row=6, column=0, columnspan=2, pady=10
        )

        self._status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self._status_var, foreground="green").pack(anchor=tk.W, padx=10, pady=4)

    def refresh(self) -> None:
        """Обновляет списки студентов, преподавателей и дисциплин."""
        self._students = self.repo.getStudents()
        self._teachers = self.repo.getTeachers()
        self._disciplines = self.repo.getDisciplines()

        self._student_cb["values"] = [s.fullName for s in self._students]
        self._teacher_cb["values"] = [t.fullName for t in self._teachers]
        self._disc_cb["values"] = [d.name for d in self._disciplines]

        if self._students:
            self._student_cb.current(0)
        if self._teachers:
            self._teacher_cb.current(0)
        if self._disciplines:
            self._disc_cb.current(0)

    def _submit(self) -> None:
        """Сохраняет новую оценку в репозиторий."""
        student_name = self._student_var.get()
        disc_name = self._disc_var.get()
        teacher_name = self._teacher_var.get()

        if not student_name or not disc_name or not teacher_name:
            messagebox.showwarning("Предупреждение", "Заполните все обязательные поля.")
            return

        student = next((s for s in self._students if s.fullName == student_name), None)
        discipline = next((d for d in self._disciplines if d.name == disc_name), None)
        teacher = next((t for t in self._teachers if t.fullName == teacher_name), None)

        if not student or not discipline or not teacher:
            messagebox.showerror("Ошибка", "Не удалось найти одну из сущностей.")
            return

        grade = Grade(
            id=self.repo.nextGradeId(),
            value=self._value_var.get(),
            assessmentType=self._type_var.get(),
            studentId=student.id,
            disciplineId=discipline.id,
            teacherId=teacher.id,
            comment=self._comment_var.get().strip(),
        )
        teacher.submitGrade(grade, self.repo)

        self._status_var.set(
            f"Оценка {grade.value} («{discipline.name}») выставлена студенту {student.fullName}."
        )
        self._comment_var.set("")
        self.on_change()
