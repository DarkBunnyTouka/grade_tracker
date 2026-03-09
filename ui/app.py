"""Главное окно приложения с вкладками (ttk.Notebook)."""

import tkinter as tk
from tkinter import ttk

from repository import GradeRepository
from ui.view_tab import ViewTab
from ui.submit_tab import SubmitTab
from ui.edit_tab import EditTab
from ui.report_tab import ReportTab

DATA_PATH = "data/data.json"


class App(tk.Tk):
    """Главное окно ИС учёта успеваемости студентов.

    Содержит четыре вкладки:
    1. Просмотр успеваемости
    2. Выставление оценки
    3. Редактирование оценки
    4. Формирование отчёта
    """

    def __init__(self) -> None:
        """Инициализирует окно, загружает репозиторий и создаёт вкладки."""
        super().__init__()
        self.title("ИС учёта успеваемости студентов")
        self.geometry("900x600")
        self.resizable(True, True)

        self.repo = GradeRepository(DATA_PATH)

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self.view_tab = ViewTab(notebook, self.repo)
        self.submit_tab = SubmitTab(notebook, self.repo, on_change=self._refresh)
        self.edit_tab = EditTab(notebook, self.repo, on_change=self._refresh)
        self.report_tab = ReportTab(notebook, self.repo)

        notebook.add(self.view_tab, text="  Просмотр успеваемости  ")
        notebook.add(self.submit_tab, text="  Выставление оценки  ")
        notebook.add(self.edit_tab, text="  Редактирование оценки  ")
        notebook.add(self.report_tab, text="  Формирование отчёта  ")

    def _refresh(self) -> None:
        """Обновляет все вкладки после изменения данных."""
        self.view_tab.refresh()
        self.submit_tab.refresh()
        self.edit_tab.refresh()
        self.report_tab.refresh()
