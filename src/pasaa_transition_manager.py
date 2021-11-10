from database.TransitionDatabase import TransitionDatabase
from src.static.shared_database import database


def create_translation(userId: str, exerciseId: str, failed: bool, passed: bool, opened: bool,pocketId :str):
    if not is_duplicate_transition(userId, exerciseId,pocketId):
        transition = TransitionDatabase(userId=userId, exerciseId=exerciseId, failed=failed, passed=passed,
                                        opened=opened,pocketId=pocketId)
        database.session.add(transition)
        database.session.commit()
        return 200
    return 400


def create_transition_passed(userId: str, exerciseId: str,pocketId :str):
    if not is_duplicate_transition(userId, exerciseId,pocketId):
        transition = TransitionDatabase(userId=userId, exerciseId=exerciseId, failed=False, passed=True, opened=True,pocketId=pocketId)
        database.session.add(transition)
        database.session.commit()
        return 200
    transition_passed(userId, exerciseId)
    return 200


def create_transition_failed(userId: str, exerciseId: str,pocketId :str):
    if not is_duplicate_transition(userId, exerciseId,pocketId):
        transition = TransitionDatabase(userId=userId, exerciseId=exerciseId, failed=True, passed=False, opened=True,pocketId=pocketId)
        database.session.add(transition)
        database.session.commit()
        return 200
    return 400


def transition_passed(userId: str, exerciseId: str,pocketId :str):
    transition_database = TransitionDatabase.query
    transition_database = transition_database.filter(TransitionDatabase.pocketId.contains(pocketId))

    transition_database = transition_database.filter(TransitionDatabase.userId.contains(userId))
    transition_database = transition_database.filter(TransitionDatabase.exerciseId.contains(exerciseId))

    transition = transition_database.first()

    if transition is not None:
        transition.passed = True
        database.session.add(transition)
        database.session.commit()
    else:
        create_transition_passed(userId=userId, exerciseId=exerciseId,pocketId=pocketId)


def is_duplicate_transition(userId: str, exerciseId: str,pocketId :str):
    transition_database = TransitionDatabase.query
    transition_database = transition_database.filter(TransitionDatabase.pocketId.contains(pocketId))
    transition_database = transition_database.filter(TransitionDatabase.userId.contains(userId))
    transition_database = transition_database.filter(TransitionDatabase.exerciseId.contains(exerciseId))

    transition = transition_database.first()

    return transition is not None
