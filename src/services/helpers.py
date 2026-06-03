def getSessionId(user_id: str) -> str:
    import random
    return str((random.random() * 100) + "".join(random.shuffle(user_id.split(""))))