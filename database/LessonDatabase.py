from marshmallow_sqlalchemy import SQLAlchemySchema
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.static.shared_database import database


class LessonDatabase(database.Model):
    __tablename__ = "Lesson_Database"
    __bind_key__ = "2bear"

    id = database.Column(database.Text(), primary_key=True, unique=True, nullable=False)
    nameThai = database.Column(database.Text(), nullable=True)
    nameEng = database.Column(database.Text(), nullable=True)
    number = database.Column(database.Integer, nullable=True)
    price = database.Column(database.Integer, nullable=True, default=0)
    delete = database.Column(database.Boolean, default=False)
    type = database.Column(database.Text(), nullable=True, default="FREE")
    status = database.Column(database.Text(), nullable=True, default="DRAFT")
    cover = database.Column(database.Text(), nullable=True, default="")

    def __init__(self, nameThai, nameEng, number, cover):
        self.id = str(uuid.uuid4())
        self.nameThai = nameThai
        self.nameEng = nameEng
        self.number = number
        self.price = 0
        self.delete = False
        self.type = "FREE"
        self.status = "RELEASE"
        self.cover = cover

    @property
    def menu(self):
        return {
            "id": self.id,
            "nameThai": self.nameThai,
            "nameEng": self.nameEng,
            "cover": self.cover,
            "number": self.number
        }

    @property
    def detail(self):
        return {
            "id": self.id,
            "nameThai": self.nameThai,
            "nameEng": self.nameEng,
            "cover": self.cover,
            "number": self.number,
            "delete": self.delete
        }


class LessonDatabaseSchema(SQLAlchemySchema):
    class Meta:
        model = LessonDatabase
