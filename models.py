import json

from beanie import Document, Indexed
from datetime import datetime



class Users(Document):
    username: Indexed(str)
    password: str

    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "users"

class InstaUsers(Document):
    user_id: Indexed(str)
    instagram_id: Indexed(str)
    username: Indexed(str)
    cookies: str

    created_at: datetime = datetime.utcnow()

    class Settings:
        name = "insta_users"

    def cookies_to_dict(self):
        return json.loads(self.cookies)