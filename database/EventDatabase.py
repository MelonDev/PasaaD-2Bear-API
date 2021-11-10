from marshmallow_sqlalchemy import SQLAlchemySchema
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.static.shared_database import database
from src.tools import tools

class EventDatabase(database.Model):
    __tablename__ = "Event_Database"
    __bind_key__ = "2bear"

    id = database.Column(database.Text(), primary_key=True, unique=True, nullable=False)
    name = database.Column(database.Text(), nullable=False)
    description = database.Column(database.Text(), nullable=False)
    image = database.Column(database.Text(), nullable=False)
    lessonId = database.Column(database.Text(), nullable=False)
    createdAt = database.Column(database.DateTime(timezone=True), nullable=False)
    startAt = database.Column(database.DateTime(timezone=True), nullable=True)
    endAt = database.Column(database.DateTime(timezone=True), nullable=True)
    available = database.Column(database.Boolean, default=True)
    delete = database.Column(database.Boolean, default=False)


    def __init__(self, name, description, image, lessonId):
        self.id = str(uuid.uuid4())
        self.createdAt = tools.current_datetime_with_timezone()
        self.name = name
        self.description = description
        self.image = image
        self.lessonId = lessonId
        self.available = True
        self.delete = False

    @property
    def detail(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "image": self.image,
            "lessonId": self.lessonId,
            "createdAt": self.createdAt,
            "available" :self.available,
            "delete":self.delete
        }


class EventDatabaseSchema(SQLAlchemySchema):
    class Meta:
        model = EventDatabase
