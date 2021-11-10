from marshmallow_sqlalchemy import SQLAlchemySchema
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.static.shared_database import database
from src.tools import tools


class ExercisePocketDatabase(database.Model):
    __tablename__ = "Exercise_Pocket_Database"
    __bind_key__ = "2bear"

    id = database.Column(database.Text(), primary_key=True, unique=True, nullable=False)
    exerciseId = database.Column(database.Text(), nullable=False)
    userId = database.Column(database.Text(), nullable=False)
    success = database.Column(database.Boolean, default=False)
    createdAt = database.Column(database.DateTime(timezone=True), nullable=False)
    type = database.Column(database.Text(), nullable=False)
    score = database.Column(database.Integer, nullable=False, default=0)
    time = database.Column(database.Integer, nullable=False, default=0)
    point = database.Column(database.Float, nullable=False, default=0.0)


    def __init__(self, userId, exerciseId, type):
        self.id = str(uuid.uuid4())
        self.createdAt = tools.current_datetime_with_timezone()
        self.userId = userId
        self.success = False
        self.exerciseId = exerciseId
        self.type = type
        self.score = 0
        self.time = 0
        self.point = 0.0

    @property
    def detail(self):
        return {
            "id": self.id,
            "createdAt": self.createdAt,
            "userId": self.userId,
            "success": self.success,
            "exerciseId": self.exerciseId,
            "type": self.type,
            "score": self.score,
            "time": self.time,
            "point": self.point
        }

    @property
    def small(self):
        return {
            "userId": self.userId,
            "score": self.score,
            "time": self.time,
            "createdAt": self.createdAt,
        }


class ExercisePocketDatabaseSchema(SQLAlchemySchema):
    class Meta:
        model = ExercisePocketDatabase
