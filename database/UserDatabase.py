import uuid

from marshmallow_sqlalchemy import SQLAlchemySchema

from src.static.shared_database import database


class UserDatabase(database.Model):
    __tablename__ = "User_Database"
    __bind_key__ = "2bear"

    id = database.Column(database.Text(), primary_key=True, unique=True, nullable=False)
    uid = database.Column(database.Text(), unique=True, nullable=True)
    name = database.Column(database.Text(), nullable=True)
    image = database.Column(database.Text(), nullable=True)
    type = database.Column(database.Text(), nullable=True)
    admin = database.Column(database.Boolean, nullable=False)

    def __init__(self, uid, type, name, image):
        self.id = str(uuid.uuid4())
        self.uid = uid
        self.type = type
        self.name = name
        self.image = image
        self.admin = False

    @property
    def detail(self):
        return {
            "id": self.id,
            "uid": self.uid,
            "type": self.type,
            "name": self.name,
            "image": self.image,
            "admin": self.admin
        }

    @property
    def export(self):
        return {
            "id": self.id,
            "uid": self.uid,
            "type": self.type,
            "name": self.name,
            "image": self.image,
            "admin": self.admin
        }


class UserDatabaseSchema(SQLAlchemySchema):
    class Meta:
        model = UserDatabase
