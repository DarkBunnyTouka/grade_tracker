"""Тесты репозитория GradeRepository."""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from models import Grade, Search
from repository import GradeRepository


# ------------------------------------------------------------------ #
# Вспомогательные данные                                              #
# ------------------------------------------------------------------ #

SEED = {
    "students": [
        {"id": 1, "fullName": "Арзамасов Сергей Дмитриевич", "email": "a@a.ru",
         "passwordHash": "h1", "graduateBookNumber": "23-001", "group": "САУ-23-1б"},
        {"id": 2, "fullName": "Иванова Мария Петровна", "email": "i@i.ru",
         "passwordHash": "h2", "graduateBookNumber": "23-002", "group": "САУ-23-1б"},
    ],
    "teachers": [
        {"id": 1, "fullName": "Русских Елена Романовна", "email": "r@r.ru",
         "passwordHash": "th1", "department": "Каф. ПИ", "position": "Доцент"},
    ],
    "disciplines": [
        {"id": 1, "name": "Программная инженерия", "semester": 4, "assessmentType": "экзамен"},
        {"id": 2, "name": "Базы данных", "semester": 3, "assessmentType": "зачёт"},
    ],
    "groups": [
        {"id": 1, "name": "САУ-23-1б", "specialty": "Автоматизация",
         "enrollmentYear": 2023, "studentIds": [1, 2]},
    ],
    "grades": [
        {"id": 1, "value": 5, "assessmentType": "экзамен", "date": "2024-06-15",
         "comment": "Отлично", "studentId": 1, "disciplineId": 1, "teacherId": 1},
        {"id": 2, "value": 4, "assessmentType": "зачёт", "date": "2024-06-18",
         "comment": "", "studentId": 2, "disciplineId": 2, "teacherId": 1},
        {"id": 3, "value": 3, "assessmentType": "экзамен", "date": "2024-06-15",
         "comment": "Удовл.", "studentId": 2, "disciplineId": 1, "teacherId": 1},
    ],
}


@pytest.fixture
def repo(tmp_path):
    """Создаёт временный репозиторий с тестовыми данными."""
    data_file = tmp_path / "test_data.json"
    data_file.write_text(json.dumps(SEED, ensure_ascii=False), encoding="utf-8")
    return GradeRepository(str(data_file))


@pytest.fixture
def empty_repo(tmp_path):
    """Создаёт пустой репозиторий без файла."""
    return GradeRepository(str(tmp_path / "new_data.json"))


# ------------------------------------------------------------------ #
# Инициализация                                                       #
# ------------------------------------------------------------------ #

class TestInit:
    def test_load_on_init(self, repo):
        assert len(repo.getStudents()) == 2
        assert len(repo.getTeachers()) == 1

    def test_empty_repo_no_file(self, empty_repo):
        assert empty_repo.getStudents() == []
        assert empty_repo.getGrades() if False else empty_repo.findGrades(Search()) == []


# ------------------------------------------------------------------ #
# addGrade / removeGrade                                              #
# ------------------------------------------------------------------ #

class TestAddRemove:
    def test_add_grade(self, repo):
        before = len(repo.findGrades(Search()))
        g = Grade(id=repo.nextGradeId(), value=4, assessmentType="КР",
                  studentId=1, disciplineId=2, teacherId=1)
        repo.addGrade(g)
        after = len(repo.findGrades(Search()))
        assert after == before + 1

    def test_add_grade_persists(self, repo):
        """После addGrade данные записываются в файл."""
        g = Grade(id=repo.nextGradeId(), value=5, assessmentType="практика",
                  studentId=1, disciplineId=1, teacherId=1)
        repo.addGrade(g)

        # Загружаем заново из файла
        repo2 = GradeRepository(repo.filePath)
        grades = repo2.findGrades(Search())
        assert any(gr.id == g.id for gr in grades)

    def test_remove_grade_success(self, repo):
        result = repo.removeGrade(1)
        assert result is True
        assert repo.getGradeById(1) is None

    def test_remove_grade_not_found(self, repo):
        result = repo.removeGrade(9999)
        assert result is False

    def test_next_grade_id(self, repo):
        nid = repo.nextGradeId()
        assert nid == 4  # максимальный существующий id = 3

    def test_next_grade_id_empty(self, empty_repo):
        assert empty_repo.nextGradeId() == 1


# ------------------------------------------------------------------ #
# findGrades                                                          #
# ------------------------------------------------------------------ #

class TestFindGrades:
    def test_find_all(self, repo):
        grades = repo.findGrades(Search())
        assert len(grades) == 3

    def test_find_by_student_name(self, repo):
        criteria = Search(studentName="Арзамасов")
        grades = repo.findGrades(criteria)
        assert len(grades) == 1
        assert grades[0].studentId == 1

    def test_find_by_student_name_case_insensitive(self, repo):
        criteria = Search(studentName="арзамасов")
        grades = repo.findGrades(criteria)
        assert len(grades) == 1

    def test_find_by_discipline(self, repo):
        criteria = Search(disciplineName="Программная инженерия")
        grades = repo.findGrades(criteria)
        assert len(grades) == 2

    def test_find_by_semester(self, repo):
        criteria = Search(semester=3)
        grades = repo.findGrades(criteria)
        assert len(grades) == 1
        assert grades[0].disciplineId == 2

    def test_find_by_assessment_type(self, repo):
        criteria = Search(assessmentType="экзамен")
        grades = repo.findGrades(criteria)
        assert len(grades) == 2

    def test_find_by_assessment_type_case_insensitive(self, repo):
        criteria = Search(assessmentType="ЭКЗАМЕН")
        grades = repo.findGrades(criteria)
        assert len(grades) == 2

    def test_find_combined(self, repo):
        criteria = Search(studentName="Иванова", assessmentType="зачёт")
        grades = repo.findGrades(criteria)
        assert len(grades) == 1
        assert grades[0].value == 4

    def test_find_no_match(self, repo):
        criteria = Search(studentName="Несуществующий")
        grades = repo.findGrades(criteria)
        assert grades == []


# ------------------------------------------------------------------ #
# saveToJSON / loadFromJSON                                           #
# ------------------------------------------------------------------ #

class TestPersistence:
    def test_save_load_roundtrip(self, repo, tmp_path):
        new_path = str(tmp_path / "output.json")
        repo.saveToJSON(new_path)

        repo2 = GradeRepository(new_path)
        assert len(repo2.findGrades(Search())) == 3
        assert len(repo2.getStudents()) == 2

    def test_save_creates_dir(self, tmp_path):
        nested = str(tmp_path / "sub" / "data.json")
        r = GradeRepository.__new__(GradeRepository)
        r.filePath = nested
        r._data = {"students": [], "teachers": [], "disciplines": [], "grades": [], "groups": []}
        r.saveToJSON(nested)
        assert os.path.exists(nested)

    def test_load_updates_data(self, repo, tmp_path):
        new_file = tmp_path / "other.json"
        minimal = {"students": [], "teachers": [], "disciplines": [], "grades": [], "groups": []}
        new_file.write_text(json.dumps(minimal), encoding="utf-8")
        repo.loadFromJSON(str(new_file))
        assert repo.findGrades(Search()) == []


# ------------------------------------------------------------------ #
# Геттеры                                                             #
# ------------------------------------------------------------------ #

class TestGetters:
    def test_get_students(self, repo):
        students = repo.getStudents()
        assert len(students) == 2
        names = [s.fullName for s in students]
        assert "Арзамасов Сергей Дмитриевич" in names

    def test_get_teachers(self, repo):
        teachers = repo.getTeachers()
        assert len(teachers) == 1
        assert teachers[0].position == "Доцент"

    def test_get_disciplines(self, repo):
        disciplines = repo.getDisciplines()
        assert len(disciplines) == 2

    def test_get_groups(self, repo):
        groups = repo.getGroups()
        assert len(groups) == 1
        assert groups[0].name == "САУ-23-1б"

    def test_get_student_by_id_found(self, repo):
        s = repo.getStudentById(1)
        assert s is not None
        assert s.fullName == "Арзамасов Сергей Дмитриевич"

    def test_get_student_by_id_not_found(self, repo):
        assert repo.getStudentById(9999) is None

    def test_get_discipline_by_id(self, repo):
        d = repo.getDisciplineById(1)
        assert d.name == "Программная инженерия"

    def test_get_discipline_by_id_not_found(self, repo):
        assert repo.getDisciplineById(9999) is None

    def test_get_teacher_by_id(self, repo):
        t = repo.getTeacherById(1)
        assert t.fullName == "Русских Елена Романовна"

    def test_get_teacher_by_id_not_found(self, repo):
        assert repo.getTeacherById(9999) is None

    def test_get_grade_by_id(self, repo):
        g = repo.getGradeById(2)
        assert g.value == 4

    def test_get_grade_by_id_not_found(self, repo):
        assert repo.getGradeById(9999) is None
