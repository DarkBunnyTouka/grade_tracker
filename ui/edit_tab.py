"""Вкладка «Редактирование оценки»."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

from repository import GradeRepository


class EditTab(ttk.Frame):
    """Вкладка редактирования существующей оценки.

    Преподаватель находит оценку по ID и изменяет её значение и комментарий.
    Проверяется, что оценка существует.
    """

    def __init__(
        self,
        parent: ttk.Notebook,
        repo: GradeRepository,
        on_change: Callable,
    ) -> None:
        """Инициализирует вкладку редактирования оценки.

        Args:
            parent: Родительский виджет (ttk.Notebook).
            repo: Репозиторий данных.
            on_change: Callback, вызываемый после успешного сохранения.
        """
        super().__init__(parent)
        self.repo = repo
        self.on_change = on_change
        self._current_grade = None
        self._build_ui()

    def _build_ui(self) -> None:
        """Создаёт элементы интерфейса вкладки."""
        # --- поиск оценки по ID ---
        find_frame = ttk.LabelFrame(self, text="Поиск оценки")
        find_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(find_frame, text="ID оценки:").grid(row=0, column=0, padx=8, pady=6, sticky=tk.W)
        self._id_var = tk.StringVar()
        ttk.Entry(find_frame, textvariable=self._id_var, width=10).grid(
            row=0, column=1, padx=8, pady=6, sticky=tk.W
        )
        ttk.Button(find_frame, text="Найти", command=self._find).grid(
            row=0, column=2, padx=8, pady=6
        )

        # --- информация о найденной оценке ---
        self._info_frame = ttk.LabelFrame(self, text="Найденная оценка")
        self._info_frame.pack(fill=tk.X, padx=10, pady=4)

        self._info_var = tk.StringVar(value="Введите ID оценки и нажмите «Найти».")
        ttk.Label(self._info_frame, textvariable=self._info_var, foreground="gray").pack(
            anchor=tk.W, padx=8, pady=6
        )

        # --- форма редактирования ---
        edit_frame = ttk.LabelFrame(self, text="Изменить данные")
        edit_frame.pack(fill=tk.X, padx=10, pady=4)

        ttk.Label(edit_frame, text="Новая оценка (2–5):").grid(row=0, column=0, padx=8, pady=6, sticky=tk.W)
        self._new_value_var = tk.IntVar(value=5)
        self._spinbox = ttk.Spinbox(edit_frame, from_=2, to=5, textvariable=self._new_value_var, width=6, state="disabled")
        self._spinbox.grid(row=0, column=1, padx=8, pady=6, sticky=tk.W)

        ttk.Label(edit_frame, text="Новый комментарий:").grid(row=1, column=0, padx=8, pady=6, sticky=tk.W)
        self._new_comment_var = tk.StringVar()
        self._comment_entry = ttk.Entry(edit_frame, textvariable=self._new_comment_var, width=40, state="disabled")
        self._comment_entry.grid(row=1, column=1, padx=8, pady=6, sticky=tk.W)

        self._save_btn = ttk.Button(edit_frame, text="Сохранить изменения", command=self._save, state="disabled")
        self._save_btn.grid(row=2, column=0, columnspan=2, pady=10)

        self._status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self._status_var, foreground="green").pack(anchor=tk.W, padx=10, pady=4)

    def refresh(self) -> None:
        """Сбрасывает форму при обновлении данных."""
        self._current_grade = None
        self._id_var.set("")
        self._info_var.set("Введите ID оценки и нажмите «Найти».")
        self._set_form_state("disabled")

    def _find(self) -> None:
        """Ищет оценку по введённому ID и заполняет форму редактирования."""
        raw = self._id_var.get().strip()
        if not raw.isdigit():
            messagebox.showwarning("Предупреждение", "Введите числовой ID оценки.")
            return

        grade = self.repo.getGradeById(int(raw))
        if grade is None:
            messagebox.showinfo("Не найдено", f"Оценка с ID {raw} не существует.")
            self._current_grade = None
            self._set_form_state("disabled")
            return

        student = self.repo.getStudentById(grade.studentId)
        discipline = self.repo.getDisciplineById(grade.disciplineId)
        teacher = self.repo.getTeacherById(grade.teacherId)

        self._current_grade = grade
        self._info_var.set(
            f"ID {grade.id}  |  {student.fullName if student else '?'}  |  "
            f"{discipline.name if discipline else '?'}  |  "
            f"{grade.assessmentType}  |  Оценка: {grade.value}  |  "
            f"Дата: {grade.date}  |  Преподаватель: {teacher.fullName if teacher else '?'}"
        )
        self._new_value_var.set(grade.value)
        self._new_comment_var.set(grade.comment)
        self._set_form_state("normal")
        self._status_var.set("")

    def _save(self) -> None:
        """Сохраняет изменения в репозиторий."""
        if self._current_grade is None:
            return

        teacher = self.repo.getTeacherById(self._current_grade.teacherId)
        if teacher is None:
            messagebox.showerror("Ошибка", "Преподаватель оценки не найден.")
            return

        success = teacher.editGrade(
            self._current_grade.id,
            self._new_value_var.get(),
            self._new_comment_var.get().strip(),
            self.repo,
        )

        if success:
            self._status_var.set(f"Оценка ID {self._current_grade.id} успешно обновлена.")
            self._current_grade = None
            self._set_form_state("disabled")
            self._id_var.set("")
            self._info_var.set("Введите ID оценки и нажмите «Найти».")
            self.on_change()
        else:
            messagebox.showerror("Ошибка", "Не удалось сохранить изменения.")

    def _set_form_state(self, state: str) -> None:
        """Включает или отключает поля формы редактирования.

        Args:
            state: Состояние виджетов — «normal» или «disabled».
        """
        self._spinbox.config(state=state)
        self._comment_entry.config(state=state)
        self._save_btn.config(state=state)
