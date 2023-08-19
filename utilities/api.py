import time, random, nacl.secret
from base64 import urlsafe_b64encode

import httpx

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from utilities.responses import ErrorResponse

PREPACKSIZE = 4
KEYSIZE = 32
SEALEDKEYSIZE = KEYSIZE + 48  # 32 bytes key + 16 bytes tag



class InstaAPI:
    BASE_API_URL = "https://www.instagram.com/api/v1"
    SHARED_DATA_URL = "https://www.instagram.com/data/shared_data/"

    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"


    async def shared_data(self, session):
        resp = await session.get(self.SHARED_DATA_URL)
        data = resp.json()

        key_id = int(data["encryption"]["key_id"])
        pub_key = data["encryption"]["public_key"]
        csrf_token = data["config"]["csrf_token"]
        return key_id, pub_key, csrf_token

    def encrypt_message(self, key, msg, aad):
        cipher = AESGCM(key)
        nonce = bytes([0] * 12)
        return cipher.encrypt(nonce, msg, aad)

    def pack(self, key_id, sealed_key, encrypted_message):
        buffer = bytearray()
        buffer.append(1)
        buffer.append(int(key_id))
        buffer.append(len(sealed_key) & 0xFF)
        buffer.append((len(sealed_key) >> 8) & 0xFF)
        buffer.extend(sealed_key)
        buffer.extend(encrypted_message[-16:])
        buffer.extend(encrypted_message[:-16])
        return buffer


    def seal_key(self, key, pk):
        sealed_box = nacl.secret.SecretBox(pk)
        sealed_key = sealed_box.encrypt(key)
        return sealed_key

    def enc_password(self, key_id, public_key, password):
        parsed_public_key = bytes.fromhex(public_key)
        current_time = str(int(time.time())).encode("utf-8").rjust(10, b"0")
        message_key = bytes([random.randint(0, 255) for _ in range(KEYSIZE)])
        encrypted_message = self.encrypt_message(message_key, password.encode("utf-8"), current_time)
        sealed_key = self.seal_key(message_key, parsed_public_key)
        packed = self.pack(key_id, sealed_key, encrypted_message)
        encoded_package = urlsafe_b64encode(packed).decode("utf-8")
        time_as_string = current_time.decode("utf-8")
        return f"#PWD_INSTAGRAM_BROWSER:10:{time_as_string}:{encoded_package}"

    async def login(self, username: str, password: str):
        session = httpx.AsyncClient()
        key_id, pub_key, csrf_token = await self.shared_data(session)
        data = { 
            "username": username,
            "enc_password": self.enc_password(key_id, pub_key, password),
            "queryParams": "{}",
            "trustedDeviceRecords": "{}",
            "optIntoOneTap": "false",
        }
        headers = {
            "User-Agent": self.USER_AGENT,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.instagram.com/",
            "x-csrftoken": csrf_token,
        }
        response = await session.post(
            f"{self.BASE_API_URL}/web/accounts/login/ajax/",
            data=data,
            headers=headers,
        )
        if not response.status_code == 200:
            raise ErrorResponse(
                "There was an problem with your request",
                status_code=500
            )
        json = response.json()
        if json.get("error_type", "") == "generic_request_error":
            raise ErrorResponse(
                "There was an problem with your request",
                status_code=500
            )
        if not json.get("status", "") == "ok" or not json.get("authenticated"):
            raise ErrorResponse(
                "Invalid username or password",
                status_code=400
            )
        else:
            return {key: value for key, value in response.cookies.items()}

    async def fetch_followers(self, instagram_id: str, cookies: str):
        header = {
            "user-agent": self.USER_AGENT,
            "x-ig-app-id": "936619743392459",
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_API_URL}/friendships/{instagram_id}/followers/",
                cookies=cookies,
                headers=header,
            )
            data = response.json()
            print(data)
            if response.status_code == 200:
                if data["status"] == "ok":
                    return data["users"]
            else:
                raise ErrorResponse(
                    message="There was an error while fetching followers",
                    status_code=400
                )