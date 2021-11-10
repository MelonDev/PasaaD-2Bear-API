
from src.static.shared_database import database, file_upload


@file_upload.Model
class blogModel(database.Model):
    __tablename__ = "blogs"
    __bind_key__ = "2bear"

    id = database.Column(database.Integer, primary_key=True)

    placeholder = file_upload.Column()
    file = file_upload.Column()
