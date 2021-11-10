import collections
import operator
from decimal import Decimal
from operator import itemgetter

import firebase_admin
import requests
from firebase_admin import credentials, auth
from firebase_admin.auth import UserNotFoundError
from flask import Blueprint, abort, request, jsonify
from collections import defaultdict

from sqlalchemy import asc, desc, func

from database.EventDatabase import EventDatabase
from database.ExerciseDatabase import ExerciseDatabase
from database.ExercisePocketDatabase import ExercisePocketDatabase
from database.LessonDatabase import LessonDatabase
from database.TransitionDatabase import TransitionDatabase
from database.WordDatabase import WordDatabase
from src.pasaa_transition_manager import transition_passed, create_transition_failed
from src.pasaa_user_manager import is_duplicate_user, get_user_from_uid, register, get_user, edit_detail
from src.static.shared_database import database
from src.tools import tools
from src.tools.tools import *
from src.tools.HttpStatus import HttpStatus

pasaa_api = Blueprint('pasaa_api', __name__)


@pasaa_api.route("/", methods=['GET', 'POST'])
def main():
    return verify_return("Pasaa API Connected")


@pasaa_api.route("/line_login", methods=['GET', 'POST'])
def line_login():
    try:
        if request.method == 'POST':
            contents = request.json

            accessToken = contents['accessToken']
            channelId = contents['channelId']
            userId = contents['userId']
            displayName = contents['displayName']
            profileImage = contents['profileImage']

            if accessToken is None:
                return verify_return(code=HttpStatus.bad_request_400,
                                     message="No accessToken was specified in the request")
            if channelId is None:
                return verify_return(code=HttpStatus.bad_request_400,
                                     message="No channelId was specified in the request")
            if userId is None:
                return verify_return(code=HttpStatus.bad_request_400, message="No userId was specified in the request")
            if displayName is None:
                return verify_return(code=HttpStatus.bad_request_400,
                                     message="No displayName was specified in the request")
            if profileImage is None:
                return verify_return(code=HttpStatus.bad_request_400,
                                     message="No profileImage was specified in the request")
            # if email is None:
            #    return verify_return(code=HttpStatus.bad_request_400, message="No email was specified in the request")

            url = "https://api.line.me/oauth2/v2.1/verify?access_token=" + str(accessToken)
            response = requests.get(url=url)
            print(response.text)
            if response is not None:
                line_response = response.json()
                response_client_id = line_response['client_id']
                if response_client_id != channelId:
                    return verify_return(code=HttpStatus.bad_request_400, message="ChannelId mismatched")

                additional_claims = {
                    'premiumAccount': True
                }

                user = auth.get_user(userId)
                customToken = auth.create_custom_token(user.uid, additional_claims)

                final_result = {
                    "customToken": customToken.decode("utf-8")
                }

                print(final_result)
                return jsonify(final_result)
            return verify_return(code=HttpStatus.bad_request_400, message="POST ONLY")
        else:
            return verify_return(code=HttpStatus.bad_request_400, message="response is None")
    except UserNotFoundError as user:
        additional_claims = {
            'premiumAccount': True
        }

        contents = request.json
        userId = contents['userId']
        displayName = contents['displayName']
        profileImage = contents['profileImage']

        email = userId + "@line.com"

        user = auth.create_user(
            email=email,
            uid=userId,
            display_name=displayName,
            photo_url=profileImage
        )
        customToken = auth.create_custom_token(user.uid, additional_claims)

        final_result = {
            "customToken": customToken.decode("utf-8")
        }
        return jsonify(final_result)
    except Exception as e:
        print(e)
        return verify_return(code=HttpStatus.bad_request_400, message=e)


@pasaa_api.route("/all_lesson", methods=['GET'])
def get_all_lesson():
    lesson_database = LessonDatabase.query
    lesson_database = lesson_database.filter(LessonDatabase.type.contains("FREE"))
    lesson_database = lesson_database.filter(LessonDatabase.status.contains("RELEASE"))
    lesson_database = lesson_database.filter(LessonDatabase.delete.is_(False))
    lesson_database = lesson_database.order_by(desc(LessonDatabase.number))

    lessons = lesson_database.all()

    result = []
    for lesson in lessons:
        word_database = WordDatabase.query
        word_database = word_database.filter(WordDatabase.lessonId.contains(lesson.id))
        word_database = word_database.filter(WordDatabase.delete.is_(False))

        count = word_database.count()
        if count is not None:
            if count > 0:
                result.append(lesson.menu)

    # real_result = jsonify([i.menu for i in result])
    result_json = jsonify(result)

    return verify_return(result_json)


@pasaa_api.route("/exercise/<userId>/all", methods=['GET'])
def get_all_exercise_from_user(userId):
    lesson_database = LessonDatabase.query
    lesson_database = lesson_database.filter(LessonDatabase.type.contains("FREE"))
    lesson_database = lesson_database.filter(LessonDatabase.status.contains("RELEASE"))
    lesson_database = lesson_database.filter(LessonDatabase.delete.is_(False))
    lesson_database = lesson_database.order_by(desc(LessonDatabase.number))

    lessons = lesson_database.all()

    available_lessons = []
    for lesson in lessons:
        exercise_database = ExerciseDatabase.query
        exercise_database = exercise_database.filter(ExerciseDatabase.lessonId.contains(lesson.id))
        exercise_database = exercise_database.filter(ExerciseDatabase.delete.is_(False))
        count = exercise_database.count()
        print(count)
        if count is not None:
            if count > 0:
                available_lessons.append(lesson)

    pocket_database = get_all_pocket_from_user(userId, isScore=True)
    pocket = pocket_database.all()
    result_pocket = [i.detail for i in pocket]
    result_exercise = [i.menu for i in available_lessons]

    result = {
        "exercise": result_exercise, "pockets": result_pocket
    }

    return verify_return(jsonify(result))


@pasaa_api.route("/<key>/word/count", methods=['GET'])
def get_count_word_from_lesson(key):
    word_database = WordDatabase.query

    word_database = word_database.filter(WordDatabase.lessonId.contains(key))

    word_database = word_database.filter(WordDatabase.delete.is_(False))

    count = word_database.count()

    if count is not None:
        return verify_return({"lessonId": key, "count": count})
    return verify_return(code=HttpStatus.no_content_204, message="Not found")


@pasaa_api.route("/<key>/exercise/count", methods=['GET'])
def get_count_exercise_from_lesson(key):
    exercise_database = ExerciseDatabase.query

    exercise_database = exercise_database.filter(ExerciseDatabase.lessonId.contains(key))

    exercise_database = exercise_database.filter(ExerciseDatabase.delete.is_(False))

    count = exercise_database.count()

    if count is not None:
        return verify_return({"lessonId": key, "count": count})
    return verify_return(code=HttpStatus.no_content_204, message="Not found")


@pasaa_api.route("/<key>/word", methods=['GET'])
def get_all_word_from_lesson(key):
    word_database = WordDatabase.query

    word_database = word_database.filter(WordDatabase.lessonId.contains(key))

    word_database = word_database.filter(WordDatabase.delete.is_(False))
    word_database = word_database.order_by(asc(WordDatabase.number))

    words = word_database.all()
    result = jsonify([i.menu for i in words])

    return verify_return(result)


@pasaa_api.route("/<key>/word/first", methods=['GET'])
def get_first_word_from_lesson(key):
    word_database = filter_word_on_lesson(key)

    word_database = word_database.order_by(asc(WordDatabase.number))

    word = word_database.first().detail

    word['previous'] = False
    word['next'] = next_word(key, word['number']) is not None

    word.pop('number')

    return verify_return(word)


@pasaa_api.route("/word/<currentWordId>", methods=['GET'])
def get_some_word_from_lesson(currentWordId):
    current = get_current_word(currentWordId)

    if current is not None:
        current['previous'] = (previous_word(current['lessonId'], current['number']) is not None)
        current['next'] = (next_word(current['lessonId'], current['number']) is not None)
        current.pop('number')

        return verify_return(current)
    return verify_return(code=HttpStatus.no_content_204, message="Not found word")


@pasaa_api.route("/word/<currentWordId>/next", methods=['GET'])
def get_next_some_word_from_lesson(currentWordId):
    current = get_current_word(currentWordId)
    word = next_word(current['lessonId'], current['number'])

    if word is not None:
        word['previous'] = True
        word['next'] = (word is not None)
        word.pop('number')

        return verify_return(word)
    return verify_return(code=HttpStatus.no_content_204, message="Not found word")


@pasaa_api.route("/word/<currentWordId>/previous", methods=['GET'])
def get_previous_some_word_from_lesson(currentWordId):
    current = get_current_word(currentWordId)
    word = previous_word(current['lessonId'], current['number'])

    if word is not None:
        word['previous'] = (word is not None)
        word['next'] = True
        word.pop('number')

        return verify_return(word)
    return verify_return(code=HttpStatus.no_content_204, message="Not found word")


def get_current_word(wordId):
    word_database = WordDatabase.query
    word = word_database.get(wordId)
    return word.detail if word is not None else None


def previous_word(lessonId, number: int):
    word_database = filter_word_on_lesson(lessonId)

    if number is not None:
        word_database = word_database.filter(WordDatabase.number < number)

    word_database = word_database.order_by(desc(WordDatabase.number))

    word = word_database.first()

    return word.detail if word is not None else None


def next_word(lessonId, number: int):
    word_database = filter_word_on_lesson(lessonId)

    if number is not None:
        word_database = word_database.filter(WordDatabase.number > number)

    word_database = word_database.order_by(asc(WordDatabase.number))

    word = word_database.first()

    return word.detail if word is not None else None


def filter_word_on_lesson(lessonId):
    word_database = WordDatabase.query
    word_database = word_database.filter(WordDatabase.lessonId.contains(lessonId))

    word_database = word_database.filter(WordDatabase.delete.is_(False))

    return word_database


# Exercise
@pasaa_api.route("/<key>/exercise", methods=['GET'])
def get_all_exercise_from_lesson(key):
    exercise_database = filter_exercise_on_lesson(key)

    exercise_database = exercise_database.order_by(asc(ExerciseDatabase.number))

    exercise = exercise_database.all()
    result = jsonify([i.menu for i in exercise])

    return verify_return(result)


@pasaa_api.route("/<key>/exercise/<userId>", methods=['GET'])
def get_exercise_from_lesson_with_log(key, userId):
    exercise_database = filter_exercise_on_lesson(key)
    exercise_database = exercise_database.order_by(asc(ExerciseDatabase.number))

    transition_database = filter_log_from_pocket_exercise_by_user(lessonId=key, userId=userId)
    # pocket_database = get_all_pocket_from_user(userId, isScore=True)

    exercise = exercise_database.all()
    transition = transition_database.all()
    result_exercise = [i.menu for i in exercise]
    result_transition = [i.detail for i in transition]

    result = {
        "exercise": result_exercise, "log": result_transition
    }

    return jsonify(result)


@pasaa_api.route("/log/<userId>/<lessonId>", methods=['GET'])
def get_log_user_by_lesson(lessonId, userId):
    transition_database = filter_log_exercise_by_user(lessonId=lessonId, userId=userId)

    transition = transition_database.all()
    result_transition = [i.detail for i in transition]

    return jsonify(result_transition)


@pasaa_api.route("/log/<userId>", methods=['GET'])
def get_log_user(userId):
    transition_database = filter_log_transitions_by_user(userId=userId)

    transition = transition_database.all()
    result_transition = [i.detail for i in transition]

    return jsonify(result_transition)


@pasaa_api.route("/<key>/exercise/first", methods=['GET'])
def get_first_exercise_from_lesson(key):
    exercise_database = filter_exercise_on_lesson(key)

    exercise_database = exercise_database.order_by(asc(ExerciseDatabase.number))

    exercise = exercise_database.first().detail

    exercise['previous'] = False
    exercise['next'] = next_exercise(key, exercise['number']) is not None

    exercise.pop('number')

    return verify_return(exercise)


@pasaa_api.route("/<userId>/exercise/<lessonId>/start/<type>", methods=['GET'])
def start_exercise_from_lesson(lessonId, userId, type):
    pocket = ExercisePocketDatabase(exerciseId=lessonId, userId=userId, type=type)

    if type == "SCORE":
        transition_database = filter_log_from_pocket_exercise_by_user(lessonId=lessonId, userId=userId, pocketId=None,
                                                                      isScore=True)

        transition_count = transition_database.count()

        if transition_count > 0:
            transition = transition_database.all()
            pocket_database = find_success_pocket_of_exercise_by_user(lessonId=lessonId, userId=userId, pocketId=None,
                                                                      isScore=True)

            pocket = pocket_database.first()

            result_transition = [i.detail for i in transition]
            result_pocket = pocket.detail

            result = {
                "transition": result_transition,
                "pocket": result_pocket
            }

            return verify_return(data=jsonify(result), code=HttpStatus.accepted_202)

    exercise_database = filter_exercise_on_lesson(lessonId)
    exercise_database = exercise_database.order_by(asc(ExerciseDatabase.number))

    exercise = exercise_database.first().detail

    exercise['previous'] = False
    exercise['next'] = next_exercise(lessonId, exercise['number']) is not None

    exercise.pop('number')
    exercise['quesEng'] = ""

    database.session.add(pocket)
    database.session.commit()

    result = {
        "data": exercise,
        "pocket": pocket.detail
    }

    return verify_return(data=jsonify(result), code=HttpStatus.ok_200)


@pasaa_api.route("/exercise/<currentExerciseId>", methods=['GET'])
def get_some_exercise_from_lesson(currentExerciseId):
    current = get_current_exercise(currentExerciseId)

    if current is not None:
        current['previous'] = (previous_exercise(current['lessonId'], current['number']) is not None)
        current['next'] = (next_exercise(current['lessonId'], current['number']) is not None)
        current.pop('number')

        return verify_return(current)
    return verify_return(code=HttpStatus.no_content_204, message="Not found exercise")


@pasaa_api.route("/exercise/<currentExerciseId>/next", methods=['GET'])
def get_next_some_exercise_from_lesson(currentExerciseId):
    current = get_current_exercise(currentExerciseId)
    exercise = next_exercise(current['lessonId'], current['number'])
    previous = previous_exercise(current['lessonId'], current['number'])

    if exercise is not None:
        exercise['previous'] = True
        exercise['next'] = (exercise is not None)
        exercise['quesEng'] = ""
        exercise.pop('number')

        return verify_return(exercise)
    elif previous is not None:
        return verify_return(code=HttpStatus.accepted_202, message="Finished")
    return verify_return(code=HttpStatus.no_content_204, message="Not found exercise")


@pasaa_api.route("/version/<platform>", methods=['GET'])
def version(platform):

    id = ""
    if platform == "IOS":
        id = "c657743a-43b5-41a8-a0cb-2e2874ab957c"
    if platform == "ANDROID":
        id = "01bb431d-2c56-4fb4-98f3-3d97c6e1d740"

    if len(id) > 0:

        word_database = WordDatabase.query
        word_database = word_database.get(id)

        if word_database is not None:
            update_info = {
                "number": word_database.number,
                "code": word_database.read
            }

            return verify_return(jsonify(update_info))
        else:
            return verify_return(code=HttpStatus.no_content_204, message="Not found exercise")
    else :
        return verify_return(code=HttpStatus.bad_request_400, message="BAD REQUEST")

@pasaa_api.route("/exercise/<currentExerciseId>/previous", methods=['GET'])
def get_previous_some_exercise_from_lesson(currentExerciseId):
    current = get_current_exercise(currentExerciseId)
    exercise = previous_exercise(current['lessonId'], current['number'])

    if exercise is not None:
        exercise['previous'] = (exercise is not None)
        exercise['next'] = True
        exercise['quesEng'] = ""
        exercise.pop('number')

        return verify_return(exercise)
    return verify_return(code=HttpStatus.no_content_204, message="Not found exercise")


@pasaa_api.route("/exercise/receive", methods=['GET', 'POST'])
def receive_exercise():
    if request.method == 'POST':
        contents = request.json
        answer = contents['answer']

        pocketId = contents['pocketId']

        current = get_current_exercise_for_receive(contents['exerciseId'])
        print(current)
        if current['answer'] == int(answer):
            transition_passed(userId=contents['userId'], exerciseId=current['id'], pocketId=pocketId)
            exercise = next_exercise(current['lessonId'], current['number'])
            previous = previous_exercise(current['lessonId'], current['number'])

            if exercise is not None:
                exercise['previous'] = True
                exercise['next'] = (exercise is not None)
                exercise.pop('number')

                return verify_return(exercise)
            elif previous is not None:
                pocket = get_pocket(pocketId)
                pocket.success = True

                score = get_score_from_pocket_id(pocketId)
                pocket.score = score

                if pocket.type == "TIME" or pocket.type == "EVENT":
                    time = contents['time']
                    pocket.time = int(time)
                    point = _calculatePoint(pocket.exerciseId, pocket.score, pocket.time)
                    pocket.point = point

                if pocket.type == "SCORE":
                    pocket.point = score

                database.session.add(pocket)
                database.session.commit()

                transition_database = filter_log_from_pocket_exercise_by_user(userId=contents['userId'],
                                                                              lessonId=current['lessonId'],
                                                                              pocketId=pocket.id)

                transition = transition_database.all()

                result_transition = [i.detail for i in transition]
                result_pocket = pocket.detail

                result = {
                    "transition": result_transition,
                    "pocket": result_pocket
                }

                return verify_return(data=jsonify(result), code=HttpStatus.accepted_202)
            return verify_return(code=HttpStatus.no_content_204, message="Not found exercise")
        else:
            create_transition_failed(userId=contents['userId'], exerciseId=current['id'], pocketId=pocketId)
            if contents['force_next'] is not None:
                if bool(contents['force_next']):
                    exercise = next_exercise(current['lessonId'], current['number'])
                    previous = previous_exercise(current['lessonId'], current['number'])
                    if exercise is not None:
                        exercise['previous'] = True
                        exercise['next'] = (exercise is not None)
                        exercise.pop('number')

                        return verify_return(exercise)
                    elif previous is not None:

                        pocket = get_pocket(pocketId)
                        pocket.success = True

                        score = get_score_from_pocket_id(pocketId)
                        pocket.score = score

                        if pocket.type == "TIME":
                            time = contents['time']
                            pocket.time = int(time)
                            point = _calculatePoint(pocket.exerciseId, pocket.score, pocket.time)
                            pocket.point = point

                        if pocket.type == "SCORE":
                            pocket.point = score

                        database.session.add(pocket)
                        database.session.commit()

                        transition_database = filter_log_from_pocket_exercise_by_user(userId=contents['userId'],
                                                                                      lessonId=current['lessonId'],
                                                                                      pocketId=pocket.id)
                        transition = transition_database.all()

                        result_transition = [i.detail for i in transition]
                        result_pocket = pocket.detail

                        result = {
                            "transition": result_transition,
                            "pocket": result_pocket
                        }

                        return verify_return(data=jsonify(result), code=HttpStatus.accepted_202)
                    return verify_return(code=HttpStatus.no_content_204, message="Not found exercise")
            return verify_return(code=HttpStatus.not_acceptable_406, message="Incorrect")

    return verify_return(code=HttpStatus.bad_request_400, message="POST ONLY")


@pasaa_api.route("/get_user", methods=['GET', 'POST'])
def getUserFromDatabase():
    # try:
    if request.method == 'POST':
        contents = request.json

        name = contents['name'] if 'name' in contents else None
        uid = contents['uid'] if 'uid' in contents else None
        type = contents['type'] if 'type' in contents else None
        image = contents['image'] if 'image' in contents else None

        duplicate = is_duplicate_user(uid)
        print(duplicate)
        if duplicate:
            user = get_user_from_uid(uid)
            return jsonify(user)
        else:
            user = register(name, uid, type, image)
            print(user)
            return jsonify(user)
    else:
        return verify_return(code=HttpStatus.bad_request_400, message="GET ONLY")


# except Exception as e:
#    print(e)
#    return verify_return(code=HttpStatus.bad_request_400, message=e)


def get_current_exercise(exerciseId):
    exercise_database = ExerciseDatabase.query
    exercise = exercise_database.get(exerciseId)
    if exercise is not None:
        exercise.quesEng = ""
    return exercise.detail if exercise is not None else None


def get_current_exercise_for_receive(exerciseId):
    exercise_database = ExerciseDatabase.query
    exercise = exercise_database.get(exerciseId)
    if exercise is not None:
        exercise.quesEng = ""
    return exercise.receive_detail if exercise is not None else None


def previous_exercise(lessonId, number: int):
    exercise_database = filter_exercise_on_lesson(lessonId)

    if number is not None:
        exercise_database = exercise_database.filter(ExerciseDatabase.number < number)

    exercise_database = exercise_database.order_by(desc(ExerciseDatabase.number))

    exercise = exercise_database.first()
    if exercise is not None:
        exercise.quesEng = ""

    return exercise.detail if exercise is not None else None


def next_exercise(lessonId, number: int):
    exercise_database = filter_exercise_on_lesson(lessonId)

    if number is not None:
        exercise_database = exercise_database.filter(ExerciseDatabase.number > number)

    exercise_database = exercise_database.order_by(asc(ExerciseDatabase.number))

    exercise = exercise_database.first()
    if exercise is not None:
        exercise.quesEng = ""

    return exercise.detail if exercise is not None else None


def filter_exercise_on_lesson(lessonId):
    exercise_database = ExerciseDatabase.query
    exercise_database = exercise_database.filter(ExerciseDatabase.lessonId.contains(lessonId))

    exercise_database = exercise_database.filter(ExerciseDatabase.delete.is_(False))

    return exercise_database


def get_pocket(pocketId):
    exercise_pocket_database = ExercisePocketDatabase.query
    exercise_pocket_database = exercise_pocket_database.get(pocketId)

    return exercise_pocket_database


def filter_log_exercise_by_user(lessonId, userId):
    transition_database = TransitionDatabase.query
    transition_database = transition_database.join(ExerciseDatabase,
                                                   TransitionDatabase.exerciseId == ExerciseDatabase.id)
    transition_database = transition_database.filter(ExerciseDatabase.lessonId.contains(lessonId))
    transition_database = transition_database.filter(TransitionDatabase.userId.contains(userId))
    transition_database = transition_database.order_by(asc(TransitionDatabase.createdAt))

    # transition_database = transition_database.filter(ExerciseDatabase.delete.is_(False))

    return transition_database


def filter_log_from_pocket_exercise_by_user(lessonId, userId, pocketId, isScore: bool = False):
    transition_database = TransitionDatabase.query
    transition_database = transition_database.join(ExercisePocketDatabase,
                                                   TransitionDatabase.pocketId == ExercisePocketDatabase.id)
    if isScore:
        transition_database = transition_database.filter(ExercisePocketDatabase.type.contains("SCORE"))
    transition_database = transition_database.filter(ExercisePocketDatabase.success.is_(True))

    if pocketId is not None:
        transition_database = transition_database.filter(TransitionDatabase.pocketId.contains(pocketId))
    else:
        transition_database = transition_database.filter(ExercisePocketDatabase.userId.contains(userId))
        transition_database = transition_database.filter(ExercisePocketDatabase.exerciseId.contains(lessonId))

    transition_database = transition_database.order_by(asc(TransitionDatabase.createdAt))

    # transition_database = transition_database.filter(ExerciseDatabase.delete.is_(False))

    return transition_database


def find_success_pocket_of_exercise_by_user(lessonId, userId, pocketId, isScore: bool = False):
    exercise_pocket_database = ExercisePocketDatabase.query
    exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.exerciseId.contains(lessonId))
    if isScore:
        exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.type.contains("SCORE"))
    exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.success.is_(True))
    exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.userId.contains(userId))

    if pocketId is not None:
        exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.id.contains(pocketId))

    return exercise_pocket_database


def get_score_from_pocket_id(pocketId):
    transition_database = TransitionDatabase.query

    transition_database = transition_database.filter(TransitionDatabase.pocketId.contains(pocketId))
    transition_database = transition_database.filter(TransitionDatabase.passed.is_(True))
    transition_database = transition_database.filter(TransitionDatabase.opened.is_(True))
    transition_database = transition_database.filter(TransitionDatabase.failed.is_(False))

    return transition_database.count()


def get_all_pocket_from_user(userId, isScore: bool):
    exercise_pocket_database = ExercisePocketDatabase.query

    exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.userId.contains(userId))
    if isScore is not None:
        exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.type.contains("SCORE"))
        exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.success.is_(True))

    return exercise_pocket_database


def filter_log_transitions_by_user(userId):
    transition_database = TransitionDatabase.query
    transition_database = transition_database.filter(TransitionDatabase.userId.contains(userId))

    return transition_database


@pasaa_api.route("/lesson_upload", methods=['GET', 'POST'])
def lesson_upload():
    if request.method == 'POST':
        data = request.json

        row = LessonDatabase(data=data)

        database.session.add(row)
        database.session.commit()

    return verify_return("Upload successful")


@pasaa_api.route("/word_upload", methods=['GET', 'POST'])
def word_upload():
    if request.method == 'POST':
        data = request.json

        row = WordDatabase(data=data)

        database.session.add(row)
        database.session.commit()

    return verify_return("Upload successful")


@pasaa_api.route("/exercise_upload", methods=['GET', 'POST'])
def exercise_upload():
    if request.method == 'POST':
        data = request.json

        row = ExerciseDatabase(data=data)

        database.session.add(row)
        database.session.commit()

    return verify_return("Upload successful")


# RANK
@pasaa_api.route("/rank/score", methods=['GET'])
def get_rank_score():
    a = database.session.query(ExercisePocketDatabase.userId, func.sum(ExercisePocketDatabase.score)).filter(
        ExercisePocketDatabase.success.is_(True)).filter(ExercisePocketDatabase.type.contains("SCORE")).group_by(
        ExercisePocketDatabase.userId).all()
    listRank = []
    for i in a:
        rank = {
            "userId": i[0],
            "score": i[1]
        }
        listRank.append(rank)
    return verify_return(jsonify(listRank))


@pasaa_api.route("/rank/time", methods=['GET'])
def get_rank_time():
    a = database.session.query(ExercisePocketDatabase.userId, func.sum(ExercisePocketDatabase.point)).filter(
        ExercisePocketDatabase.success.is_(True)).filter(ExercisePocketDatabase.type.contains("TIME")).group_by(
        ExercisePocketDatabase.userId).all()
    listRank = []
    for i in a:
        rank = {
            "userId": i[0],
            "point": i[1]
        }
        listRank.append(rank)
    return verify_return(jsonify(listRank))


@pasaa_api.route("/<userId>/edit", methods=['GET', 'POST'])
def edit_user(userId):
    if request.method == 'POST':
        contents = request.json
        name = contents['name'] if 'name' in contents else None
        image = contents['image'] if 'image' in contents else None

        edit_detail(userId, name, image)
        return verify_return(code=HttpStatus.ok_200, message="SUCCESSFUL")

    else:
        return verify_return(code=HttpStatus.bad_request_400, message="POST ONLY")


# EVENT
@pasaa_api.route("/event/all", methods=['GET'])
def get_all_event():
    event_database = EventDatabase.query
    event = event_database.all()

    result_event = [i.detail for i in event]

    return jsonify(result_event)


@pasaa_api.route("/event/all_with_rank", methods=['GET'])
def get_all_event_with_rank():
    event_database = EventDatabase.query
    event_database = event_database.order_by(asc(EventDatabase.createdAt))

    event = event_database.all()

    rank_database = database.session.query(ExercisePocketDatabase.userId,
                                           func.sum(ExercisePocketDatabase.point)).filter(
        ExercisePocketDatabase.success.is_(True)).group_by(
        ExercisePocketDatabase.userId).all()

    listRank = []
    for i in rank_database:
        rank = {
            "userId": i[0],
            "point": i[1]
        }
        listRank.append(rank)

    result_event = [i.detail for i in event]

    result = {
        "ranks": listRank,
        "events": result_event
    }

    return jsonify(result)


@pasaa_api.route("/event/all/<userId>", methods=['GET'])
def get_all_event_with_rank_and_userId(userId):
    event_database = EventDatabase.query
    event_database = event_database.order_by(desc(EventDatabase.createdAt))
    event_database = event_database.filter(EventDatabase.delete.is_(False))

    event = event_database.all()

    rank_database = database.session.query(ExercisePocketDatabase.userId,
                                           func.sum(ExercisePocketDatabase.point)).filter(
        ExercisePocketDatabase.success.is_(True)).group_by(
        ExercisePocketDatabase.userId).all()

    user_detail = get_user(userId)

    me = {
        "detail": user_detail.detail,
        "point": 0.0
    }

    listRank = []
    for i in rank_database:
        id = i[0]
        user_raw = get_user(id)
        user = user_raw.detail

        event_score = get_user_event_score(id)
        TWOPLACES = Decimal(10) ** -2

        user_score = Decimal(i[1]).quantize(TWOPLACES)

        real_score = event_score + user_score

        if user_raw.id == userId:
            # me['detail'] = user
            # me['point'] = i[1]
            me['point'] = str(real_score)

        rank = {
            "user": user,
            # "point": i[1]
            "point": float(real_score)
        }
        listRank.append(rank)

    # result_event = [i.detail for i in event]

    a = sorted(listRank, key=lambda k: k['point'])
    b = sorted(listRank, key=itemgetter('point'))
    listRank.sort(key=lambda k: float(k['point']))

    print(a)
    print(b)
    print(listRank)

    result_event = []

    for i in event:
        exercise_pocket_database = ExercisePocketDatabase.query
        exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.exerciseId.contains(i.id))
        exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.success.is_(True))
        count = exercise_pocket_database.count()
        poc = exercise_pocket_database.filter(ExercisePocketDatabase.userId.contains(userId)).count()

        detail = i.detail

        detail['count'] = count
        detail['passed'] = poc > 0
        result_event.append(detail)

    result = {
        "me": me,
        "ranks": listRank,
        "events": result_event
    }

    return jsonify(result)


def get_user_event_score(userId):
    exercise_pocket_database = ExercisePocketDatabase.query
    exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.userId.contains(str(userId)))
    exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.success.is_(True))
    exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.type.contains("EVENT"))
    exercise_pocket = exercise_pocket_database.all()

    score = 0
    TWOPLACES = Decimal(10) ** -2

    for i in exercise_pocket:
        score += Decimal(i.score).quantize(TWOPLACES)

    return score


@pasaa_api.route("/event/<eventId>/rank", methods=['GET'])
def get_event_rank(eventId):
    exercise_pocket_database = ExercisePocketDatabase.query
    exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.exerciseId.contains(eventId))
    exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.success.is_(True))
    exercise_pocket_database = exercise_pocket_database.order_by(asc(ExercisePocketDatabase.score))
    exercise_pocket = exercise_pocket_database.all()

    result = []

    d = defaultdict(list)

    for item in exercise_pocket:
        small = item.small
        user_detail = get_user(item.userId).detail

        small['detail'] = user_detail
        small.pop('userId', None)

        d[item.score].append(small)

    od = collections.OrderedDict(sorted(d.items(), reverse=True))

    for key, value in od.items():
        newlist = sorted(value, key=lambda k: k['time'])
        result.extend(newlist)

    return verify_return(data=jsonify(result), code=HttpStatus.ok_200)


@pasaa_api.route("/event/<eventId>/<userId>/detail", methods=['GET'])
def show_event_detail_from_user(eventId, userId):
    exercise_pocket_database = get_duplicate_event_from_exercise_pocket_database(eventId=eventId, userId=userId)
    pocket_duplicate = exercise_pocket_database.count() > 0
    if pocket_duplicate:
        result_pocket = exercise_pocket_database.detail
        return verify_return(data=jsonify(result_pocket), code=HttpStatus.accepted_202)
    return verify_return(code=HttpStatus.no_content_204, message="Not found detail")


@pasaa_api.route("/event/<eventId>/<userId>/start", methods=['GET'])
def start_event(eventId, userId):
    exercise_pocket_database = get_duplicate_event_from_exercise_pocket_database(eventId=eventId, userId=userId)
    pocket_duplicate = exercise_pocket_database.count() > 0
    if pocket_duplicate:
        pocket = exercise_pocket_database.first()
        result_pocket = pocket.detail
        return verify_return(data=jsonify(result_pocket), code=HttpStatus.accepted_202)
    lessonId = _get_lessonId_from_event(eventId)
    pocket = ExercisePocketDatabase(exerciseId=eventId, userId=userId, type="EVENT")

    exercise_database = filter_exercise_on_lesson(lessonId)
    exercise_database = exercise_database.order_by(asc(ExerciseDatabase.number))

    exercise = exercise_database.first().detail

    exercise['previous'] = False
    exercise['next'] = next_exercise(lessonId, exercise['number']) is not None
    exercise.pop('number')
    exercise['quesEng'] = ""
    database.session.add(pocket)
    database.session.commit()
    result = {
        "data": exercise,
        "pocket": pocket.detail
    }
    return verify_return(data=jsonify(result), code=HttpStatus.ok_200)


def get_duplicate_event_from_exercise_pocket_database(eventId, userId):
    exercise_pocket_database = ExercisePocketDatabase.query
    exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.exerciseId.contains(eventId))
    exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.success.is_(True))
    exercise_pocket_database = exercise_pocket_database.filter(ExercisePocketDatabase.userId.contains(userId))

    return exercise_pocket_database


def _get_lessonId_from_event(eventId):
    return EventDatabase.query.get(eventId).lessonId


def _calculatePoint(lessonId, score, time):
    exercise_database = ExerciseDatabase.query
    exercise_database = exercise_database.filter(ExerciseDatabase.lessonId.contains(lessonId))
    exercise_database = exercise_database.filter(ExerciseDatabase.delete.is_(False))
    count = exercise_database.count()
    return ((count / time) * score) * (count / 5)


def _calculatePointEvent(lessonId, score, time):
    exercise_database = ExerciseDatabase.query
    exercise_database = exercise_database.filter(ExerciseDatabase.lessonId.contains(lessonId))
    exercise_database = exercise_database.filter(ExerciseDatabase.delete.is_(False))
    count = exercise_database.count()
    return ((count / time) * score) * (count / 3)


@pasaa_api.route("/admin", methods=['GET'])
def getByAdmin():
    lesson_database = LessonDatabase.query.filter(LessonDatabase.delete.is_(False)).all()
    event_database = EventDatabase.query.filter(EventDatabase.delete.is_(False)).all()

    # result_lesson = []
    '''for i in lesson_database:
        word_database = WordDatabase.query.filter(WordDatabase.lessonId.contains(i.id)).all()
        exercise_database = ExerciseDatabase.query.filter(ExerciseDatabase.lessonId.contains(i.id)).all()

        lesson_result = {
            "word": [j.detail for j in word_database],
            "exercise_database": [j.detail for j in exercise_database]
        }

        result_lesson.append(lesson_result)
    '''

    result_lesson = [i.detail for i in lesson_database]
    result_event = [i.detail for i in event_database]

    result = {
        "lesson": result_lesson,
        "event": result_event
    }
    return jsonify(result)


@pasaa_api.route("/admin/<lessonId>", methods=['GET'])
def getByLessonAdmin(lessonId):
    lesson = LessonDatabase.query.get(lessonId)

    word_database = WordDatabase.query.filter(WordDatabase.lessonId.contains(lessonId)).filter(
        WordDatabase.delete.is_(False)).all()
    exercise_database = ExerciseDatabase.query.filter(ExerciseDatabase.lessonId.contains(lessonId)).filter(
        ExerciseDatabase.delete.is_(False)).all()

    result = {
        "detail": lesson.detail,
        "word": [j.detail for j in word_database],
        "exercise": [j.more_detail for j in exercise_database]
    }

    return jsonify(result)


# Management Lesson
@pasaa_api.route("/admin/lesson/add", methods=['GET', 'POST'])
def add_lesson():
    if request.method == 'POST':
        contents = request.json
        nameThai = contents['nameThai'] if 'nameThai' in contents else None
        nameEng = contents['nameEng'] if 'nameEng' in contents else None
        # number = contents['number'] if 'number' in contents else None
        cover = contents['cover'] if 'cover' in contents else None

        lesson_database = LessonDatabase.query
        number = lesson_database.count() + 1

        if nameThai is not None and nameEng is not None and number is not None and cover is not None:
            lesson = LessonDatabase(nameThai=nameThai, nameEng=nameEng, number=number, cover=cover)

            database.session.add(lesson)
            database.session.commit()

            return verify_return(code=HttpStatus.ok_200, message="SUCCESSFUL")
        return verify_return(code=HttpStatus.bad_request_400, message="NONE")
    else:
        return verify_return(code=HttpStatus.bad_request_400, message="POST ONLY")


@pasaa_api.route("/admin/lesson/<lessonId>", methods=['GET', 'POST'])
def edit_lesson(lessonId):
    if request.method == 'POST':
        lesson = LessonDatabase.query.get(lessonId)

        if lesson is not None:
            contents = request.json
            if 'nameThai' in contents:
                lesson.nameThai = contents['nameThai']
            if 'nameEng' in contents:
                lesson.nameEng = contents['nameEng']
            if 'number' in contents:
                lesson.number = contents['number']
            if 'cover' in contents:
                lesson.cover = contents['cover']
            if 'status' in contents:
                lesson.status = contents['status']

            database.session.add(lesson)
            database.session.commit()

            return verify_return(code=HttpStatus.ok_200, message="SUCCESSFUL")
        return verify_return(code=HttpStatus.bad_request_400, message="NOT FOUND")
    else:
        return verify_return(code=HttpStatus.bad_request_400, message="POST ONLY")


@pasaa_api.route("/admin/lesson/<lessonId>/delete", methods=['GET', 'POST'])
def delete_lesson(lessonId):
    if request.method == 'POST':
        lesson = LessonDatabase.query.get(lessonId)
        if lesson is not None:
            lesson.delete = True

            database.session.add(lesson)
            database.session.commit()

            return verify_return(code=HttpStatus.ok_200, message="SUCCESSFUL")
        return verify_return(code=HttpStatus.bad_request_400, message="NOT FOUND")
    else:
        return verify_return(code=HttpStatus.bad_request_400, message="POST ONLY")


# Management Word
@pasaa_api.route("/admin/word/add", methods=['GET', 'POST'])
def add_word():
    if request.method == 'POST':
        contents = request.json
        lessonId = contents['lessonId'] if 'lessonId' in contents else None
        cover = contents['cover'] if 'cover' in contents else None
        nameEng = contents['nameEng'] if 'nameEng' in contents else None
        nameThai = contents['nameThai'] if 'nameThai' in contents else None
        read = contents['read'] if 'read' in contents else None

        # number = contents['number'] if 'number' in contents else None
        word_database = WordDatabase.query
        word_database = word_database.filter(WordDatabase.lessonId.contains(lessonId))
        number = word_database.count() + 1

        if lessonId is not None and cover is not None and nameEng is not None and nameThai is not None and read is not None and number is not None:
            word = WordDatabase(lessonId=lessonId, cover=cover, nameEng=nameEng, nameThai=nameThai, read=read,
                                number=number)

            database.session.add(word)
            database.session.commit()

            return verify_return(code=HttpStatus.ok_200, message="SUCCESSFUL")
        return verify_return(code=HttpStatus.bad_request_400, message="NONE")
    else:
        return verify_return(code=HttpStatus.bad_request_400, message="POST ONLY")


@pasaa_api.route("/admin/word/<wordId>", methods=['GET', 'POST'])
def edit_word(wordId):
    if request.method == 'POST':
        word = WordDatabase.query.get(wordId)

        if word is not None:
            contents = request.json
            if 'lessonId' in contents:
                word.lessonId = contents['lessonId']
            if 'cover' in contents:
                word.cover = contents['cover']
            if 'nameEng' in contents:
                word.nameEng = contents['nameEng']
            if 'nameThai' in contents:
                word.nameThai = contents['nameThai']
            if 'read' in contents:
                word.read = contents['read']
            if 'number' in contents:
                word.number = contents['number']

            database.session.add(word)
            database.session.commit()

            return verify_return(code=HttpStatus.ok_200, message="SUCCESSFUL")
        return verify_return(code=HttpStatus.bad_request_400, message="NOT FOUND")
    else:
        return verify_return(code=HttpStatus.bad_request_400, message="POST ONLY")


@pasaa_api.route("/admin/word/<wordId>/delete", methods=['GET', 'POST'])
def delete_word(wordId):
    if request.method == 'POST':
        word = WordDatabase.query.get(wordId)
        if word is not None:
            word.delete = True

            database.session.add(word)
            database.session.commit()

            return verify_return(code=HttpStatus.ok_200, message="SUCCESSFUL")
        return verify_return(code=HttpStatus.bad_request_400, message="NOT FOUND")
    else:
        return verify_return(code=HttpStatus.bad_request_400, message="POST ONLY")


# Management Exercise
@pasaa_api.route("/admin/exercise/add", methods=['GET', 'POST'])
def add_exercise():
    if request.method == 'POST':
        contents = request.json

        lessonId = contents['lessonId'] if 'lessonId' in contents else None
        ansOne = contents['ansOne'] if 'ansOne' in contents else None
        ansTwo = contents['ansTwo'] if 'ansTwo' in contents else None
        cover = contents['cover'] if 'cover' in contents else None
        quesEng = contents['quesEng'] if 'quesEng' in contents else None
        quesThai = contents['quesThai'] if 'quesThai' in contents else None
        # number = contents['number'] if 'number' in contents else None

        exercise_database = ExerciseDatabase.query
        exercise_database = exercise_database.filter(ExerciseDatabase.lessonId.contains(lessonId))
        number = exercise_database.count() + 1

        answer = contents['answer'] if 'answer' in contents else None

        if lessonId is not None and ansOne is not None and ansTwo is not None and cover is not None and quesThai is not None and number is not None and answer is not None:
            exercise = ExerciseDatabase(lessonId=lessonId, ansOne=ansOne, ansTwo=ansTwo, cover=cover, quesEng=quesEng,
                                        quesThai=quesThai, number=number, answer=answer)

            database.session.add(exercise)
            database.session.commit()

            return verify_return(code=HttpStatus.ok_200, message="SUCCESSFUL")
        return verify_return(code=HttpStatus.bad_request_400, message="NONE")
    else:
        return verify_return(code=HttpStatus.bad_request_400, message="POST ONLY")


@pasaa_api.route("/admin/exercise/<exerciseId>", methods=['GET', 'POST'])
def edit_exercise(exerciseId):
    if request.method == 'POST':
        exercise = ExerciseDatabase.query.get(exerciseId)

        if exercise is not None:
            contents = request.json
            if 'lessonId' in contents:
                exercise.lessonId = contents['lessonId']
            if 'ansOne' in contents:
                exercise.ansOne = contents['ansOne']
            if 'ansTwo' in contents:
                exercise.ansTwo = contents['ansTwo']
            if 'cover' in contents:
                exercise.cover = contents['cover']
            if 'quesEng' in contents:
                exercise.quesEng = contents['quesEng']
            if 'quesThai' in contents:
                exercise.quesThai = contents['quesThai']
            if 'number' in contents:
                exercise.number = contents['number']
            if 'answer' in contents:
                exercise.answer = contents['answer']

            database.session.add(exercise)
            database.session.commit()

            return verify_return(code=HttpStatus.ok_200, message="SUCCESSFUL")
        return verify_return(code=HttpStatus.bad_request_400, message="NOT FOUND")
    else:
        return verify_return(code=HttpStatus.bad_request_400, message="POST ONLY")


@pasaa_api.route("/admin/exercise/<exerciseId>/delete", methods=['GET', 'POST'])
def delete_exercise(exerciseId):
    if request.method == 'POST':
        exercise = ExerciseDatabase.query.get(exerciseId)
        if exercise is not None:
            exercise.delete = True

            database.session.add(exercise)
            database.session.commit()

            return verify_return(code=HttpStatus.ok_200, message="SUCCESSFUL")
        return verify_return(code=HttpStatus.bad_request_400, message="NOT FOUND")
    else:
        return verify_return(code=HttpStatus.bad_request_400, message="POST ONLY")


# Management Event
@pasaa_api.route("/admin/event/add", methods=['GET', 'POST'])
def add_event():
    if request.method == 'POST':
        contents = request.json
        name = contents['name'] if 'name' in contents else None
        description = contents['description'] if 'description' in contents else None
        image = contents['image'] if 'image' in contents else None
        lessonId = contents['lessonId'] if 'lessonId' in contents else None

        if name is not None and description is not None and image is not None and lessonId is not None:
            event = EventDatabase(name=name, description=description, image=image, lessonId=lessonId)

            database.session.add(event)
            database.session.commit()

            return verify_return(code=HttpStatus.ok_200, message="SUCCESSFUL")
        return verify_return(code=HttpStatus.bad_request_400, message="NONE")
    else:
        return verify_return(code=HttpStatus.bad_request_400, message="POST ONLY")


@pasaa_api.route("/admin/event/<eventId>", methods=['GET', 'POST'])
def edit_event(eventId):
    if request.method == 'POST':
        event = EventDatabase.query.get(eventId)

        if event is not None:
            contents = request.json
            if 'name' in contents:
                event.name = contents['name']
            if 'description' in contents:
                event.description = contents['description']
            if 'image' in contents:
                event.image = contents['image']
            if 'lessonId' in contents:
                event.lessonId = contents['lessonId']
            if 'available' in contents:
                event.available = bool(contents['available'])

            database.session.add(event)
            database.session.commit()

            return verify_return(code=HttpStatus.ok_200, message="SUCCESSFUL")
        return verify_return(code=HttpStatus.bad_request_400, message="NOT FOUND")
    else:
        return verify_return(code=HttpStatus.bad_request_400, message="POST ONLY")


@pasaa_api.route("/admin/event/<eventId>/delete", methods=['GET', 'POST'])
def delete_event(eventId):
    if request.method == 'POST':
        event = EventDatabase.query.get(eventId)
        if event is not None:
            event.delete = True

            database.session.add(event)
            database.session.commit()

            return verify_return(code=HttpStatus.ok_200, message="SUCCESSFUL")
        return verify_return(code=HttpStatus.bad_request_400, message="NOT FOUND")
    else:
        return verify_return(code=HttpStatus.bad_request_400, message="POST ONLY")
