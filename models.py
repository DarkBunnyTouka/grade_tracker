"""Модели предметной области для ИС учёта успеваемости студентов."""

from abc import ABC, abstractmethod
import datetime
from typing import List, Optional


class User(ABC):
    """Абстрактный базовый класс пользователя системы.

    Attributes:
        id: Уникальный идентификатор.
        fullName: Полное имя пользователя.
        email: Адрес электронной почты.
        passwordHash: Хэш пароля.
    """

    def __init__(self, id: int, fullName: str, email: str, passwordHash: str) -> None:
        """Инициализирует пользователя.

        Args:
            id: Уникальный идентификатор.
            fullName: Полное имя.
            email: Электронная почта.
            passwordHash: Хэш пароля.
        """
        self.id = id
        self.fullName = fullName
        self.email = email
        self.passwordHash = passwordHash

    @property
    @abstractmethod
    def role(self) -> str:
        """Роль пользователя в системе (Student/Teacher)."""

    def to_dict(self) -> dict:
        """Сериализует объект в словарь.

        Returns:
            Словарь с атрибутами пользователя.
        """
        return {
            "id": self.id,
            "fullName": self.fullName,
            "email": self.email,
            "passwordHash": self.passwordHash,
        }


class Student(User):
    """Студент — пользователь с доступом к просмотру своих оценок.

    Attributes:
        graduateBookNumber: Номер зачётной книжки.
        group: Название группы.
    """

    def __init__(
        self,
        id: int,
        fullName: str,
        email: str,
        passwordHash: str,
        graduateBookNumber: str,
        group: str,
    ) -> None:
        """Инициализирует студента.

        Args:
            id: Уникальный идентификатор.
            fullName: Полное имя.
            email: Электронная почта.
            passwordHash: Хэш пароля.
            graduateBookNumber: Номер зачётной книжки.
            group: Название группы.
        """
        super().__init__(id, fullName, email, passwordHash)
        self.graduateBookNumber = graduateBookNumber
        self.group = group

    def getGrades(self, repo) -> List["Grade"]:
        """Возвращает список оценок студента из репозитория.

        Args:
            repo: Экземпляр GradeRepository.

        Returns:
            Список объектов Grade, принадлежащих данному студенту.
        """
        criteria = Search(studentName=self.fullName)
        return repo.findGrades(criteria)

    def getRating(self, repo) -> float:
        """Вычисляет средний балл студента.

        Args:
            repo: Экземпляр GradeRepository.

        Returns:
            Средний балл (float). Возвращает 0.0, если оценок нет.
        """
        grades = self.getGrades(repo)
        if not grades:
            return 0.0
        return round(sum(g.value for g in grades) / len(grades), 2)

    @property
    def role(self) -> str:
        """Роль: студент."""
        return "Student"

    def to_dict(self) -> dict:
        """Сериализует объект в словарь.

        Returns:
            Словарь с атрибутами студента.
        """
        d = super().to_dict()
        d["graduateBookNumber"] = self.graduateBookNumber
        d["group"] = self.group
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Student":
        """Создаёт объект Student из словаря.

        Args:
            data: Словарь с атрибутами.

        Returns:
            Экземпляр Student.
        """
        return cls(
            id=data["id"],
            fullName=data["fullName"],
            email=data["email"],
            passwordHash=data["passwordHash"],
            graduateBookNumber=data["graduateBookNumber"],
            group=data["group"],
        )


class Teacher(User):
    """Преподаватель — пользователь, имеющий право выставлять и редактировать оценки.

    Attributes:
        department: Название кафедры.
        position: Должность.
    """

    def __init__(
        self,
        id: int,
        fullName: str,
        email: str,
        passwordHash: str,
        department: str,
        position: str,
    ) -> None:
        """Инициализирует преподавателя.

        Args:
            id: Уникальный идентификатор.
            fullName: Полное имя.
            email: Электронная почта.
            passwordHash: Хэш пароля.
            department: Кафедра.
            position: Должность.
        """
        super().__init__(id, fullName, email, passwordHash)
        self.department = department
        self.position = position

    def submitGrade(self, grade: "Grade", repo) -> None:
        """Выставляет оценку студенту через репозиторий.

        Args:
            grade: Объект Grade для добавления.
            repo: Экземпляр GradeRepository.
        """
        repo.addGrade(grade)

    def editGrade(self, gradeId: int, newValue: int, comment: str, repo) -> bool:
        """Редактирует существующую оценку.

        Args:
            gradeId: Идентификатор оценки.
            newValue: Новое значение оценки (2–5).
            comment: Новый комментарий.
            repo: Экземпляр GradeRepository.

        Returns:
            True, если оценка найдена и обновлена; False, если не найдена.
        """
        grades = repo.findGrades(Search())
        for g in grades:
            if g.id == gradeId:
                g.value = newValue
                g.comment = comment
                repo.saveToJSON(repo.filePath)
                return True
        return False

    @property
    def role(self) -> str:
        """Роль: преподаватель."""
        return "Teacher"

    def to_dict(self) -> dict:
        """Сериализует объект в словарь.

        Returns:
            Словарь с атрибутами преподавателя.
        """
        d = super().to_dict()
        d["department"] = self.department
        d["position"] = self.position
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Teacher":
        """Создаёт объект Teacher из словаря.

        Args:
            data: Словарь с атрибутами.

        Returns:
            Экземпляр Teacher.
        """
        return cls(
            id=data["id"],
            fullName=data["fullName"],
            email=data["email"],
            passwordHash=data["passwordHash"],
            department=data["department"],
            position=data["position"],
        )


class Grade:
    """Оценка студента по дисциплине.

    Attributes:
        id: Уникальный идентификатор.
        value: Значение оценки (2–5).
        assessmentType: Тип контроля (экзамен, зачёт, КР, практика).
        date: Дата выставления.
        comment: Комментарий преподавателя.
        studentId: ID студента.
        disciplineId: ID дисциплины.
        teacherId: ID преподавателя.
    """

    def __init__(
        self,
        id: int,
        value: int,
        assessmentType: str,
        studentId: int,
        disciplineId: int,
        teacherId: int,
        comment: str = "",
        date: Optional[str] = None,
    ) -> None:
        """Инициализирует оценку.

        Args:
            id: Уникальный идентификатор.
            value: Значение оценки (2–5).
            assessmentType: Тип контроля.
            studentId: ID студента.
            disciplineId: ID дисциплины.
            teacherId: ID преподавателя.
            comment: Комментарий (по умолчанию пустой).
            date: Дата в формате ISO (по умолчанию сегодня).
        """
        self.id = id
        self.value = value
        self.assessmentType = assessmentType
        self.studentId = studentId
        self.disciplineId = disciplineId
        self.teacherId = teacherId
        self.comment = comment
        self.date = date if date is not None else str(datetime.date.today())

    def to_dict(self) -> dict:
        """Сериализует объект в словарь.

        Returns:
            Словарь с атрибутами оценки.
        """
        return {
            "id": self.id,
            "value": self.value,
            "assessmentType": self.assessmentType,
            "date": self.date,
            "comment": self.comment,
            "studentId": self.studentId,
            "disciplineId": self.disciplineId,
            "teacherId": self.teacherId,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Grade":
        """Создаёт объект Grade из словаря.

        Args:
            data: Словарь с атрибутами.

        Returns:
            Экземпляр Grade.
        """
        return cls(
            id=data["id"],
            value=data["value"],
            assessmentType=data["assessmentType"],
            studentId=data["studentId"],
            disciplineId=data["disciplineId"],
            teacherId=data["teacherId"],
            comment=data.get("comment", ""),
            date=data.get("date"),
        )


class Discipline:
    """Учебная дисциплина.

    Attributes:
        id: Уникальный идентификатор.
        name: Название дисциплины.
        semester: Номер семестра.
        assessmentType: Тип итогового контроля.
    """

    def __init__(self, id: int, name: str, semester: int, assessmentType: str) -> None:
        """Инициализирует дисциплину.

        Args:
            id: Уникальный идентификатор.
            name: Название.
            semester: Семестр.
            assessmentType: Тип контроля.
        """
        self.id = id
        self.name = name
        self.semester = semester
        self.assessmentType = assessmentType

    def to_dict(self) -> dict:
        """Сериализует объект в словарь.

        Returns:
            Словарь с атрибутами дисциплины.
        """
        return {
            "id": self.id,
            "name": self.name,
            "semester": self.semester,
            "assessmentType": self.assessmentType,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Discipline":
        """Создаёт объект Discipline из словаря.

        Args:
            data: Словарь с атрибутами.

        Returns:
            Экземпляр Discipline.
        """
        return cls(
            id=data["id"],
            name=data["name"],
            semester=data["semester"],
            assessmentType=data["assessmentType"],
        )


class Group:
    """Учебная группа, содержащая студентов.

    Attributes:
        id: Уникальный идентификатор.
        name: Название группы (например, «САУ-23-1б»).
        specialty: Направление подготовки.
        enrollmentYear: Год поступления.
        _studentIds: Список ID студентов группы.
    """

    def __init__(
        self,
        id: int,
        name: str,
        specialty: str,
        enrollmentYear: int,
        studentIds: Optional[List[int]] = None,
    ) -> None:
        """Инициализирует группу.

        Args:
            id: Уникальный идентификатор.
            name: Название группы.
            specialty: Специальность.
            enrollmentYear: Год поступления.
            studentIds: Список ID студентов (по умолчанию пустой).
        """
        self.id = id
        self.name = name
        self.specialty = specialty
        self.enrollmentYear = enrollmentYear
        self._studentIds: List[int] = studentIds if studentIds is not None else []

    def addStudent(self, student: Student) -> None:
        """Добавляет студента в группу.

        Args:
            student: Объект Student для добавления.
        """
        if student.id not in self._studentIds:
            self._studentIds.append(student.id)

    def removeStudent(self, studentId: int) -> bool:
        """Удаляет студента из группы по его ID.

        Args:
            studentId: Идентификатор студента.

        Returns:
            True, если студент найден и удалён; False, если не найден.
        """
        if studentId in self._studentIds:
            self._studentIds.remove(studentId)
            return True
        return False

    @property
    def studentIds(self) -> List[int]:
        """Возвращает копию списка ID студентов группы."""
        return list(self._studentIds)

    def to_dict(self) -> dict:
        """Сериализует объект в словарь.

        Returns:
            Словарь с атрибутами группы.
        """
        return {
            "id": self.id,
            "name": self.name,
            "specialty": self.specialty,
            "enrollmentYear": self.enrollmentYear,
            "studentIds": self._studentIds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Group":
        """Создаёт объект Group из словаря.

        Args:
            data: Словарь с атрибутами.

        Returns:
            Экземпляр Group.
        """
        return cls(
            id=data["id"],
            name=data["name"],
            specialty=data["specialty"],
            enrollmentYear=data["enrollmentYear"],
            studentIds=data.get("studentIds", []),
        )


class Search:
    """Критерий поиска оценок.

    Attributes:
        studentName: Имя студента (подстрока, регистронезависимо).
        disciplineName: Название дисциплины (подстрока, регистронезависимо).
        semester: Номер семестра (None — все семестры).
        assessmentType: Тип контроля (None — все типы).
    """

    def __init__(
        self,
        studentName: str = "",
        disciplineName: str = "",
        semester: Optional[int] = None,
        assessmentType: str = "",
    ) -> None:
        """Инициализирует критерий поиска.

        Args:
            studentName: Фильтр по имени студента.
            disciplineName: Фильтр по названию дисциплины.
            semester: Фильтр по семестру.
            assessmentType: Фильтр по типу контроля.
        """
        self.studentName = studentName
        self.disciplineName = disciplineName
        self.semester = semester
        self.assessmentType = assessmentType
