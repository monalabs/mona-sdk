import os


AUTH_API_TOKEN_URL = os.environ.get(
    "MONA_SDK_AUTH_API_TOKEN_URL",
    "https://monalabs.frontegg.com/identity/resources/auth/v1/api-token",
)
REFRESH_TOKEN_URL = os.environ.get(
    "MONA_SDK_REFRESH_TOKEN_URL",
    "https://monalabs.frontegg.com/identity/resources/auth/v1/api-token/"
    "token/refresh",
)
CLIENT_CREDENTIALS_GRANT_TYPE = "client_credentials"
BASIC_HEADER = {"Content-Type": "application/json"}
URLENCODED_HEADER = {"Content-Type": "application/x-www-form-urlencoded"}


# todo I think that different classes should have different functions then









