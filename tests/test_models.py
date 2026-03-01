"""Тесты модельных классов."""

import sys
import os

# Добавляем корневую папку проекта в sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from models import User, Student, Teacher, Grade, Discipline, Group, Search


# ------------------------------------------------------------------ #
# Фикстуры                                                            #
# ------------------------------------------------------------------ #

@pytest.fixture
def student():
    return Student(
        id=1,
        fullName="Арзамасов Сергей Дмитриевич",
        email="arzamasov@stud.pnrpu.ru",
        passwordHash="hash1",
        graduateBookNumber="23-001",
        group="САУ-23-1б",
    )


@pytest.fixture
def teacher():
    return Teacher(
        id=1,
        fullName="Русских Елена Романовна",
        email="russkih@pnrpu.ru",
        passwordHash="thash1",
        department="Кафедра программной инженерии",
        position="Доцент",
    )


@pytest.fixture
def grade():
    return Grade(
        id=1,
        value=5,
        assessmentType="экзамен",
        studentId=1,
        disciplineId=1,
        teacherId=1,
        comment="Отлично",
        date="2024-06-15",
    )


@pytest.fixture
def discipline():
    return Discipline(id=1, name="Программная инженерия", semester=4, assessmentType="экзамен")


@pytest.fixture
def group(student):
    g = Group(id=1, name="САУ-23-1б", specialty="Автоматизация", enrollmentYear=2023)
    g.addStudent(student)
    return g


# ------------------------------------------------------------------ #
# User (абстрактный — тестируем через Student)                        #
# ------------------------------------------------------------------ #

class TestUser:
    def test_user_is_abstract(self):
        with pytest.raises(TypeError):
            User(1, "name", "email", "hash")  # нельзя создать напрямую

    def test_user_attributes_via_student(self, student):
        assert student.id == 1
        assert student.fullName == "Арзамасов Сергей Дмитриевич"
        assert student.email == "arzamasov@stud.pnrpu.ru"
        assert student.passwordHash == "hash1"


# ------------------------------------------------------------------ #
# Student                                                             #
# ------------------------------------------------------------------ #

class TestStudent:
    def test_creation(self, student):
        assert student.graduateBookNumber == "23-001"
        assert student.group == "САУ-23-1б"

    def test_to_dict(self, student):
        d = student.to_dict()
        assert d["id"] == 1
        assert d["graduateBookNumber"] == "23-001"
        assert d["group"] == "САУ-23-1б"
        assert "passwordHash" in d

    def test_from_dict(self):
        data = {
            "id": 2, "fullName": "Иванова Мария", "email": "iv@mail.ru",
            "passwordHash": "h", "graduateBookNumber": "23-002", "group": "ИВТ-22-1",
        }
        s = Student.from_dict(data)
        assert s.id == 2
        assert s.fullName == "Иванова Мария"
        assert s.group == "ИВТ-22-1"

    def test_get_grades_empty(self, student):
        """getGrades возвращает пустой список, если оценок нет."""
        class FakeRepo:
            def findGrades(self, criteria):
                return []

        grades = student.getGrades(FakeRepo())
        assert grades == []

    def test_get_grades_with_data(self, student, grade):
        """getGrades возвращает оценки через репозиторий."""
        class FakeRepo:
            def findGrades(self, criteria):
                return [grade]

        result = student.getGrades(FakeRepo())
        assert len(result) == 1
        assert result[0].value == 5

    def test_get_rating_empty(self, student):
        class FakeRepo:
            def findGrades(self, criteria):
                return []

        assert student.getRating(FakeRepo()) == 0.0

    def test_get_rating_with_grades(self, student):
        g1 = Grade(id=1, value=4, assessmentType="экзамен", studentId=1, disciplineId=1, teacherId=1)
        g2 = Grade(id=2, value=5, assessmentType="зачёт", studentId=1, disciplineId=2, teacherId=1)

        class FakeRepo:
            def findGrades(self, criteria):
                return [g1, g2]

        rating = student.getRating(FakeRepo())
        assert rating == 4.5


# ------------------------------------------------------------------ #
# Teacher                                                             #
# ------------------------------------------------------------------ #

class TestTeacher:
    def test_creation(self, teacher):
        assert teacher.department == "Кафедра программной инженерии"
        assert teacher.position == "Доцент"

    def test_to_dict(self, teacher):
        d = teacher.to_dict()
        assert d["department"] == "Кафедра программной инженерии"
        assert d["position"] == "Доцент"

    def test_from_dict(self):
        data = {
            "id": 2, "fullName": "Горбунов А.В.", "email": "g@mail.ru",
            "passwordHash": "h", "department": "Кафедра ИТ", "position": "Ассистент",
        }
        t = Teacher.from_dict(data)
        assert t.id == 2
        assert t.position == "Ассистент"

    def test_submit_grade(self, teacher, grade):
        """submitGrade вызывает repo.addGrade."""
        added = []

        class FakeRepo:
            def addGrade(self, g):
                added.append(g)

        teacher.submitGrade(grade, FakeRepo())
        assert len(added) == 1
        assert added[0].value == 5

    def test_edit_grade_success(self, teacher, grade):
        """editGrade находит оценку и обновляет значение."""
        saved = []

        class FakeRepo:
            filePath = "fake.json"

            def findGrades(self, criteria):
                return [grade]

            def saveToJSON(self, path):
                saved.append(path)

        result = teacher.editGrade(1, 3, "Пересдача", FakeRepo())
        assert result is True
        assert grade.value == 3
        assert grade.comment == "Пересдача"
        assert saved  # saveToJSON был вызван

    def test_edit_grade_not_found(self, teacher):
        """editGrade возвращает False, если оценка не найдена."""
        class FakeRepo:
            filePath = "fake.json"

            def findGrades(self, criteria):
                return []

            def saveToJSON(self, path):
                pass

        result = teacher.editGrade(999, 4, "", FakeRepo())
        assert result is False


# ------------------------------------------------------------------ #
# Grade                                                               #
# ------------------------------------------------------------------ #

class TestGrade:
    def test_creation(self, grade):
        assert grade.id == 1
        assert grade.value == 5
        assert grade.assessmentType == "экзамен"
        assert grade.studentId == 1
        assert grade.disciplineId == 1
        assert grade.teacherId == 1
        assert grade.comment == "Отлично"
        assert grade.date == "2024-06-15"

    def test_default_date(self):
        """Если дата не передана — подставляется сегодняшняя."""
        import datetime
        g = Grade(id=2, value=4, assessmentType="зачёт", studentId=1, disciplineId=1, teacherId=1)
        assert g.date == str(datetime.date.today())

    def test_to_dict(self, grade):
        d = grade.to_dict()
        assert d["id"] == 1
        assert d["value"] == 5
        assert d["date"] == "2024-06-15"
        assert d["studentId"] == 1

    def test_from_dict(self):
        data = {
            "id": 3, "value": 3, "assessmentType": "КР",
            "studentId": 2, "disciplineId": 2, "teacherId": 1,
            "comment": "Средне", "date": "2024-05-01",
        }
        g = Grade.from_dict(data)
        assert g.value == 3
        assert g.comment == "Средне"
        assert g.date == "2024-05-01"

    def test_from_dict_default_comment(self):
        data = {
            "id": 4, "value": 5, "assessmentType": "зачёт",
            "studentId": 1, "disciplineId": 1, "teacherId": 1,
        }
        g = Grade.from_dict(data)
        assert g.comment == ""


# ------------------------------------------------------------------ #
# Discipline                                                          #
# ------------------------------------------------------------------ #

class TestDiscipline:
    def test_creation(self, discipline):
        assert discipline.id == 1
        assert discipline.name == "Программная инженерия"
        assert discipline.semester == 4
        assert discipline.assessmentType == "экзамен"

    def test_to_dict(self, discipline):
        d = discipline.to_dict()
        assert d["semester"] == 4

    def test_from_dict(self):
        data = {"id": 2, "name": "Базы данных", "semester": 3, "assessmentType": "зачёт"}
        d = Discipline.from_dict(data)
        assert d.name == "Базы данных"
        assert d.semester == 3


# ------------------------------------------------------------------ #
# Group                                                               #
# ------------------------------------------------------------------ #

class TestGroup:
    def test_creation(self, group):
        assert group.name == "САУ-23-1б"
        assert group.specialty == "Автоматизация"
        assert group.enrollmentYear == 2023

    def test_add_student(self, group, student):
        """Студент уже добавлен фикстурой; повторное добавление игнорируется."""
        before = len(group.studentIds)
        group.addStudent(student)
        assert len(group.studentIds) == before  # дедупликация

    def test_add_new_student(self, group):
        new_s = Student(id=99, fullName="Новый", email="n@n.ru", passwordHash="h",
                        graduateBookNumber="0", group="X")
        group.addStudent(new_s)
        assert 99 in group.studentIds

    def test_remove_student(self, group, student):
        result = group.removeStudent(student.id)
        assert result is True
        assert student.id not in group.studentIds

    def test_remove_nonexistent(self, group):
        result = group.removeStudent(9999)
        assert result is False

    def test_to_dict(self, group, student):
        d = group.to_dict()
        assert student.id in d["studentIds"]
        assert d["enrollmentYear"] == 2023

    def test_from_dict(self):
        data = {"id": 2, "name": "ИВТ-22", "specialty": "ИВТ", "enrollmentYear": 2022, "studentIds": [4, 5]}
        g = Group.from_dict(data)
        assert g.name == "ИВТ-22"
        assert 4 in g.studentIds


# ------------------------------------------------------------------ #
# Search                                                              #
# ------------------------------------------------------------------ #

class TestSearch:
    def test_creation_empty(self):
        s = Search()
        assert s.studentName == ""
        assert s.disciplineName == ""
        assert s.semester is None
        assert s.assessmentType == ""

    def test_creation_full(self):
        s = Search(studentName="Арзамасов", disciplineName="Программная", semester=4, assessmentType="экзамен")
        assert s.studentName == "Арзамасов"
        assert s.semester == 4
        assert s.assessmentType == "экзамен"

    def test_partial_creation(self):
        s = Search(semester=3)
        assert s.semester == 3
        assert s.studentName == ""
        assert s.disciplineName == ""
