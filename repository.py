"""Репозиторий для хранения и поиска оценок с персистентностью через JSON."""

import json
import os
from typing import List

from models import Discipline, Grade, Group, Search, Student, Teacher


class GradeRepository:
    """Репозиторий оценок с CRUD-операциями и JSON-персистентностью.

    Хранит все сущности (студенты, преподаватели, дисциплины, группы, оценки)
    в едином JSON-файле.

    Attributes:
        filePath: Путь к JSON-файлу хранилища.
        _data: Словарь с данными в памяти.
    """

    def __init__(self, filePath: str) -> None:
        """Инициализирует репозиторий и загружает данные из файла.

        Args:
            filePath: Путь к JSON-файлу. Если файл не существует,
                      создаётся пустое хранилище.
        """
        self.filePath = filePath
        self._data: dict = {
            "students": [],
            "teachers": [],
            "disciplines": [],
            "grades": [],
            "groups": [],
        }
        if os.path.exists(filePath):
            self.loadFromJSON(filePath)

    # ------------------------------------------------------------------ #
    #  CRUD для оценок                                                     #
    # ------------------------------------------------------------------ #

    def addGrade(self, grade: Grade) -> None:
        """Добавляет оценку в репозиторий и сохраняет файл.

        Args:
            grade: Объект Grade для добавления.
        """
        self._data["grades"].append(grade.to_dict())
        self.saveToJSON(self.filePath)

    def removeGrade(self, id: int) -> bool:
        """Удаляет оценку по идентификатору.

        Args:
            id: Идентификатор оценки.

        Returns:
            True, если оценка найдена и удалена; False, если не найдена.
        """
        original_len = len(self._data["grades"])
        self._data["grades"] = [g for g in self._data["grades"] if g["id"] != id]
        if len(self._data["grades"]) < original_len:
            self.saveToJSON(self.filePath)
            return True
        return False

    def findGrades(self, criteria: Search) -> List[Grade]:
        """Ищет оценки по критерию.

        Фильтрует по имени студента, названию дисциплины, семестру и типу контроля.
        Все строковые сравнения — без учёта регистра, подстрочный поиск.

        Args:
            criteria: Объект Search с параметрами фильтрации.

        Returns:
            Список объектов Grade, удовлетворяющих критерию.
        """
        students = {s["id"]: s for s in self._data["students"]}
        disciplines = {d["id"]: d for d in self._data["disciplines"]}

        result: List[Grade] = []
        for gd in self._data["grades"]:
            student = students.get(gd["studentId"], {})
            discipline = disciplines.get(gd["disciplineId"], {})

            if criteria.studentName and criteria.studentName.lower() not in student.get("fullName", "").lower():
                continue
            if criteria.disciplineName and criteria.disciplineName.lower() not in discipline.get("name", "").lower():
                continue
            if criteria.semester is not None and discipline.get("semester") != criteria.semester:
                continue
            if criteria.assessmentType and criteria.assessmentType.lower() != gd.get("assessmentType", "").lower():
                continue

            result.append(Grade.from_dict(gd))
        return result

    # ------------------------------------------------------------------ #
    #  Персистентность                                                     #
    # ------------------------------------------------------------------ #

    def saveToJSON(self, path: str) -> None:
        """Сохраняет всё хранилище в JSON-файл.

        Args:
            path: Путь к файлу для сохранения.
        """
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def loadFromJSON(self, path: str) -> None:
        """Загружает хранилище из JSON-файла.

        Args:
            path: Путь к файлу для загрузки.
        """
        with open(path, "r", encoding="utf-8") as f:
            self._data = json.load(f)

    # ------------------------------------------------------------------ #
    #  Вспомогательные геттеры                                            #
    # ------------------------------------------------------------------ #

    def getStudents(self) -> List[Student]:
        """Возвращает список всех студентов.

        Returns:
            Список объектов Student.
        """
        return [Student.from_dict(s) for s in self._data["students"]]

    def getTeachers(self) -> List[Teacher]:
        """Возвращает список всех преподавателей.

        Returns:
            Список объектов Teacher.
        """
        return [Teacher.from_dict(t) for t in self._data["teachers"]]

    def getDisciplines(self) -> List[Discipline]:
        """Возвращает список всех дисциплин.

        Returns:
            Список объектов Discipline.
        """
        return [Discipline.from_dict(d) for d in self._data["disciplines"]]

    def getGroups(self) -> List[Group]:
        """Возвращает список всех учебных групп.

        Returns:
            Список объектов Group.
        """
        return [Group.from_dict(g) for g in self._data["groups"]]

    def getStudentById(self, studentId: int):
        """Возвращает студента по ID или None.

        Args:
            studentId: Идентификатор студента.

        Returns:
            Объект Student или None.
        """
        for s in self._data["students"]:
            if s["id"] == studentId:
                return Student.from_dict(s)
        return None

    def getDisciplineById(self, disciplineId: int):
        """Возвращает дисциплину по ID или None.

        Args:
            disciplineId: Идентификатор дисциплины.

        Returns:
            Объект Discipline или None.
        """
        for d in self._data["disciplines"]:
            if d["id"] == disciplineId:
                return Discipline.from_dict(d)
        return None

    def getTeacherById(self, teacherId: int):
        """Возвращает преподавателя по ID или None.

        Args:
            teacherId: Идентификатор преподавателя.

        Returns:
            Объект Teacher или None.
        """
        for t in self._data["teachers"]:
            if t["id"] == teacherId:
                return Teacher.from_dict(t)
        return None

    def getGradeById(self, gradeId: int):
        """Возвращает оценку по ID или None.

        Args:
            gradeId: Идентификатор оценки.

        Returns:
            Объект Grade или None.
        """
        for g in self._data["grades"]:
            if g["id"] == gradeId:
                return Grade.from_dict(g)
        return None

    def nextGradeId(self) -> int:
        """Генерирует следующий уникальный ID для оценки.

        Returns:
            Целое число, на 1 больше максимального существующего ID оценки.
        """
        if not self._data["grades"]:
            return 1
        return max(g["id"] for g in self._data["grades"]) + 1
