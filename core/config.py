from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://neondb_owner:npg_zmfCU4Eu6Wgt@ep-blue-rain-a5g5bimu.us-east-2.aws.neon.tech/neondb"
    SECRET_KEY: str = "cac6a3c76c7567aad69883781acebf1b3c4b1f320428883da873fe585494caa4b5470217ea4d3f12364dc6c562837db27b6664f98916a8af422f3cb89047bafa6ac44971c3f2ad2844d80c5cf9d447ce1917a9fe25040fd625763b4beba8fd57abe3514caa5b3acd7d1fa965351adc6aacd2c8ba3baec0c52337a5a42636b9d50d80be1e5bee5ba29c38ef8237f8542ee4ca38603777008aa306743f9f0570dffbfef5442914e507eb12baac2ae6e99d8566f6a4ef504bf5e010f0d8eaa24b8685c5ac6b9246c35b558c57f01da557ba96bd4e97b4db468d11f53931ce199b31bc8193e5c225cd3b00d2db308836d6cd4facf1a07287793a5a088760c7ffdd21"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 3000

    class Config:
        env_file = ".env"


settings = Settings()
