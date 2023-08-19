import inspect, sys, logging, hashlib, random

import motor

from beanie import init_beanie, Document

from config import DB_HOST, DB_USERNAME, DB_PASSWORD, DB_NAME



logger = logging.getLogger(__name__)



def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_digits(length=10):
    return "".join([str(random.randint(0, 9)) for _ in range(length)])


def inspect_models():
    import models
    
    models = []
    for name, obj in inspect.getmembers(sys.modules["models"]):
        if inspect.isclass(obj):
            if issubclass(obj, Document):
                models.append(obj)
    return models

async def init_database(is_srv=False):
    logger.info("Connecting to database...")
    if is_srv:
        protocol = "mongodb+srv"
    else:
        protocol = "mongodb"
    client_db = motor.motor_asyncio.AsyncIOMotorClient(
        f"{protocol}://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/?retryWrites=true&w=majority",
    )
    try:
        info = await client_db.server_info()

        if info["ok"] == 1.0:
            models = inspect_models()

            await init_beanie(
                database= client_db[DB_NAME],
                document_models= models
            )
            logger.info("Database is alive. MongoDB version: " + info["version"] + f"\n - {len(models)} models were activated in the database!")
            return client_db[DB_NAME]
        else:
            logger.warning("Database is not alive!")
            logger.info("Exiting...")
            sys.exit(1)

    except Exception as e:
        logger.warning("Could not connect to database!")
        logger.info("Exiting...")
        sys.exit(1)