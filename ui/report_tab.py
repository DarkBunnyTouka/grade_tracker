"""Вкладка «Формирование отчёта»."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List

from models import Grade, Search
from repository import GradeRepository


class ReportTab(ttk.Frame):
    """Вкладка формирования сводного отчёта по группе и семестру.

    Отображает оценки в виде таблицы и позволяет экспортировать их в TXT-файл.
    """

    def __init__(self, parent: ttk.Notebook, repo: GradeRepository) -> None:
        """Инициализирует вкладку отчёта.

        Args:
            parent: Родительский виджет (ttk.Notebook).
            repo: Репозиторий данных.
        """
        super().__init__(parent)
        self.repo = repo
        self._current_grades: List[Grade] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        """Создаёт элементы интерфейса вкладки."""
        # --- параметры отчёта ---
        params_frame = ttk.LabelFrame(self, text="Параметры отчёта")
        params_frame.pack(fill=tk.X, padx=10, pady=8)

        ttk.Label(params_frame, text="Группа:").grid(row=0, column=0, padx=8, pady=6, sticky=tk.W)
        self._group_var = tk.StringVar()
        self._group_cb = ttk.Combobox(params_frame, textvariable=self._group_var, width=25, state="readonly")
        self._group_cb.grid(row=0, column=1, padx=8, pady=6)

        ttk.Label(params_frame, text="Семестр:").grid(row=0, column=2, padx=8, pady=6, sticky=tk.W)
        self._sem_var = tk.StringVar()
        self._sem_cb = ttk.Combobox(params_frame, textvariable=self._sem_var, width=12, state="readonly")
        self._sem_cb.grid(row=0, column=3, padx=8, pady=6)

        btn_frame = ttk.Frame(params_frame)
        btn_frame.grid(row=1, column=0, columnspan=4, pady=6)
        ttk.Button(btn_frame, text="Сформировать", command=self._generate).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Экспорт в TXT", command=self._export_txt).pack(side=tk.LEFT, padx=6)

        # --- итоговая таблица ---
        table_frame = ttk.Frame(self)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        columns = ("student", "group", "discipline", "semester", "type", "value", "date", "teacher")
        self._tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)

        headers = {
            "student": ("Студент", 185),
            "group": ("Группа", 90),
            "discipline": ("Дисциплина", 175),
            "semester": ("Сем.", 50),
            "type": ("Тип контроля", 110),
            "value": ("Оценка", 60),
            "date": ("Дата", 90),
            "teacher": ("Преподаватель", 170),
        }
        for col, (heading, width) in headers.items():
            self._tree.heading(col, text=heading)
            self._tree.column(col, width=width, anchor=tk.CENTER if col in ("semester", "value", "date", "group") else tk.W)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self._status_var, foreground="gray").pack(anchor=tk.W, padx=10, pady=2)

    def refresh(self) -> None:
        """Обновляет списки групп и семестров."""
        groups = self.repo.getGroups()
        disciplines = self.repo.getDisciplines()

        self._group_cb["values"] = [""] + [g.name for g in groups]
        self._sem_cb["values"] = [""] + sorted({str(d.semester) for d in disciplines})

        self._group_var.set("")
        self._sem_var.set("")
        self._current_grades = []

    def _generate(self) -> None:
        """Формирует отчёт по выбранным параметрам."""
        group_name = self._group_var.get().strip()
        sem_text = self._sem_var.get().strip()

        # Собираем studentIds для выбранной группы
        groups = self.repo.getGroups()
        target_group = next((g for g in groups if g.name == group_name), None)

        # Строим критерии поиска
        criteria = Search(
            semester=int(sem_text) if sem_text else None,
        )
        all_grades = self.repo.findGrades(criteria)

        # Если группа выбрана — фильтруем по студентам группы
        if target_group is not None:
            student_ids = set(target_group.studentIds)
            all_grades = [g for g in all_grades if g.studentId in student_ids]

        self._current_grades = all_grades
        self._populate(all_grades)
        self._status_var.set(f"Записей в отчёте: {len(all_grades)}")

    def _populate(self, grades: List[Grade]) -> None:
        """Заполняет таблицу отчёта.

        Args:
            grades: Список объектов Grade для отображения.
        """
        for row in self._tree.get_children():
            self._tree.delete(row)

        for g in grades:
            student = self.repo.getStudentById(g.studentId)
            discipline = self.repo.getDisciplineById(g.disciplineId)
            teacher = self.repo.getTeacherById(g.teacherId)

            self._tree.insert("", tk.END, values=(
                student.fullName if student else "—",
                student.group if student else "—",
                discipline.name if discipline else "—",
                discipline.semester if discipline else "—",
                g.assessmentType,
                g.value,
                g.date,
                teacher.fullName if teacher else "—",
            ))

    def _export_txt(self) -> None:
        """Экспортирует текущий отчёт в TXT-файл по выбору пользователя."""
        if not self._current_grades:
            messagebox.showinfo("Информация", "Сначала сформируйте отчёт.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
            title="Сохранить отчёт",
        )
        if not path:
            return

        lines = [
            "Отчёт об успеваемости студентов",
            f"Группа: {self._group_var.get() or 'все'}",
            f"Семестр: {self._sem_var.get() or 'все'}",
            "-" * 90,
            f"{'Студент':<30} {'Дисциплина':<25} {'Сем.':<5} {'Тип':<12} {'Оценка':<8} {'Дата':<12} Преподаватель",
            "-" * 90,
        ]

        for g in self._current_grades:
            student = self.repo.getStudentById(g.studentId)
            discipline = self.repo.getDisciplineById(g.disciplineId)
            teacher = self.repo.getTeacherById(g.teacherId)
            lines.append(
                f"{(student.fullName if student else '—'):<30} "
                f"{(discipline.name if discipline else '—'):<25} "
                f"{(str(discipline.semester) if discipline else '—'):<5} "
                f"{g.assessmentType:<12} "
                f"{g.value:<8} "
                f"{g.date:<12} "
                f"{(teacher.fullName if teacher else '—')}"
            )

        lines.append("-" * 90)
        lines.append(f"Итого записей: {len(self._current_grades)}")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        self._status_var.set(f"Отчёт сохранён: {path}")
        messagebox.showinfo("Готово", f"Отчёт экспортирован в:\n{path}")
