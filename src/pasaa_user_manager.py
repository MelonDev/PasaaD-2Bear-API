from flask import request

from database.UserDatabase import UserDatabase
from src.static.shared_database import database


def register_from_content(contents):
    name = contents['name'] if 'name' in contents else None
    uid = contents['uid'] if 'uid' in contents else None
    type = contents['type'] if 'type' in contents else None
    image = contents['image'] if 'image' in contents else None
    if none_check(name) and none_check(uid) and none_check(type) and none_check(image):
        if not is_duplicate_user(uid):
            user = UserDatabase(name=name, uid=uid, image=image, type=type)
            database.session.add(user)
            database.session.commit()
            return user.detail

    return None


def register(name, uid, type, image):
    if none_check(name) and none_check(uid) and none_check(type) and none_check(image):
        if not is_duplicate_user(uid):
            user = UserDatabase(name=name, uid=uid, image=image, type=type)
            database.session.add(user)
            database.session.commit()
            return user.detail
    return None


def get_user_from_uid(uid):
    user_database = UserDatabase.query
    user_database = user_database.filter(
        UserDatabase.uid.contains(uid))
    user = user_database.first()
    return user.detail if user is not None else None


def get_user(id):
    user_database = UserDatabase.query
    user = user_database.get(id)
    return user


def is_duplicate_user(uid):
    user = get_user_from_uid(uid)
    return user is not None


def get_user_detail(id):
    return get_user(id).detail


def edit_detail(user_id, name, image):
    user = get_user(user_id)
    user.name = name if name is not None else user.name
    user.image = image if image is not None else user.image
    database.session.add(user)
    database.session.commit()
    return 200


def none_check(value):
    return value is not None
