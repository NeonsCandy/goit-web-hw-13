from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str = "developeer@gmail.com"
    POSTGRES_PASSWORD: str = "avalon12"
    POSTGRES_DB: str = "contacts_db"
    POSTGRES_PORT: int = 5432
    SECRET_KEY: str = "super_secret_key"
    ALGORITHM: str = "HS256"
    CLOUDINARY_NAME: str = "milmy1gs"
    CLOUDINARY_API_KEY: str = "456846788827515"
    CLOUDINARY_API_SECRET: str = "bfnr2Nhb71D2bztBFMEdpnwnGP8"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    class Config:
        env_file = None

settings = Settings()