import uuid

from marshmallow_sqlalchemy import SQLAlchemySchema

from src.static.shared_database import database
from src.tools import tools


class TransitionDatabase(database.Model):
    __tablename__ = "Transition_Database"
    __bind_key__ = "pasaad"

    id = database.Column(database.Text(), primary_key=True, unique=True, nullable=False)
    userId = database.Column(database.Text(), nullable=False)
    createdAt = database.Column(database.DateTime(timezone=True), nullable=False)
    exerciseId = database.Column(database.Text(), nullable=False)
    pocketId = database.Column(database.Text(), nullable=False)

    failed = database.Column(database.Boolean, default=False)
    passed = database.Column(database.Boolean, default=False)
    opened = database.Column(database.Boolean, default=False)

    def __init__(self, userId, exerciseId,pocketId, failed, passed, opened):
        self.id = str(uuid.uuid4())
        self.createdAt = tools.current_datetime_with_timezone()
        self.userId = userId
        self.pocketId = pocketId
        self.exerciseId = exerciseId
        self.failed = failed
        self.passed = passed
        self.opened = opened

    @property
    def detail(self):
        return {
            "id": self.id,
            "exerciseId": self.exerciseId,
            "pocketId":self.pocketId,
            "failed": self.failed,
            "passed": self.passed,
            "opened": self.opened,
            "createdAt": self.createdAt
        }


class TransitionDatabaseSchema(SQLAlchemySchema):
    class Meta:
        model = TransitionDatabase
