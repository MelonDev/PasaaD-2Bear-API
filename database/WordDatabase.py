from marshmallow_sqlalchemy import SQLAlchemySchema
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.static.shared_database import database


class WordDatabase(database.Model):
    __tablename__ = "Word_Database"
    __bind_key__ = "2bear"

    id = database.Column(database.Text(), primary_key=True, unique=True, nullable=False)
    lessonId = database.Column(database.Text(), nullable=False)

    cover = database.Column(database.Text(), nullable=True)
    engSound = database.Column(database.Text(), nullable=True)
    nameEng = database.Column(database.Text(), nullable=True)
    nameThai = database.Column(database.Text(), nullable=True)
    read = database.Column(database.Text(), nullable=True)
    thaiSound = database.Column(database.Text(), nullable=True)
    delete = database.Column(database.Boolean, default=True)
    number = database.Column(database.Integer, nullable=True)

    def __init__(self, lessonId,cover,nameEng,nameThai,read,number):
        self.id = str(uuid.uuid4())
        self.lessonId = lessonId
        self.cover = cover
        self.engSound = None
        self.nameEng = nameEng
        self.nameThai = nameThai
        self.read = read
        self.thaiSound = None
        self.delete = False
        self.number = number

    @property
    def menu(self):
        return {
            "id": self.id,
            "lessonId": self.lessonId,
            "cover": self.cover,
            "nameEng": self.nameEng,
            "nameThai": self.nameThai,
            "number": self.number,
        }

    @property
    def detail(self):
        return {
            "id": self.id,
            "lessonId": self.lessonId,
            "cover": self.cover,
            "engSound": self.engSound,
            "nameEng": self.nameEng,
            "nameThai": self.nameThai,
            "thaiSound": self.thaiSound,
            "read": self.read,
            "number": self.number
        }


class WordDatabaseSchema(SQLAlchemySchema):
    class Meta:
        model = WordDatabase
