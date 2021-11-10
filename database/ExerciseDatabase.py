from marshmallow_sqlalchemy import SQLAlchemySchema
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.static.shared_database import database


class ExerciseDatabase(database.Model):
    __tablename__ = "Exercise_Database"
    __bind_key__ = "2bear"

    id = database.Column(database.Text(), primary_key=True, unique=True, nullable=False)
    lessonId = database.Column(database.Text(), nullable=False)

    ansOne = database.Column(database.Text(), nullable=True)
    ansTwo = database.Column(database.Text(), nullable=True)
    cover = database.Column(database.Text(), nullable=True)
    quesEng = database.Column(database.Text(), nullable=True)
    quesThai = database.Column(database.Text(), nullable=True)

    number = database.Column(database.Integer, nullable=True)
    answer = database.Column(database.Integer, nullable=True)

    delete = database.Column(database.Boolean, nullable=True)

    def __init__(self, lessonId, ansOne, ansTwo, cover, quesEng, quesThai, number, answer):
        self.id = str(uuid.uuid4())
        self.lessonId = lessonId
        self.ansOne = ansOne
        self.ansTwo = ansTwo
        self.cover = cover
        self.quesEng = ""
        self.quesThai = quesThai
        self.number = number
        self.answer = answer
        self.delete = False

    @property
    def menu(self):
        return {
            "id": self.id,
            "lessonId": self.lessonId,
            "cover": self.cover,
            "quesEng": self.quesEng,
            "quesThai": self.quesThai,
            "number": self.number,
        }

    @property
    def detail(self):
        return {
            "id": self.id,
            "lessonId": self.lessonId,
            "cover": self.cover,
            "quesEng": self.quesEng,
            "quesThai": self.quesThai,
            "ansOne": self.ansOne,
            "ansTwo": self.ansTwo,
            "number": self.number
        }

    @property
    def more_detail(self):
        return {
            "id": self.id,
            "lessonId": self.lessonId,
            "cover": self.cover,
            "quesEng": self.quesEng,
            "quesThai": self.quesThai,
            "ansOne": self.ansOne,
            "ansTwo": self.ansTwo,
            "number": self.number,
            "answer": self.answer,
        }

    @property
    def receive_detail(self):
        return {
            "id": self.id,
            "lessonId": self.lessonId,
            "answer": self.answer,
            "number": self.number

        }


class ExerciseDatabaseSchema(SQLAlchemySchema):
    class Meta:
        model = ExerciseDatabase
