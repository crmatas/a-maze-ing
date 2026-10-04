from typing import Optional, Tuple
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode
from typing import Annotated

class Config(BaseSettings):
    width: int
    height: int
    entry: Annotated[Tuple[int, int], NoDecode]
    exit: Annotated[Tuple[int, int], NoDecode]
    perfect: bool = True
    seed: Optional[int] = None
    algorithm: Optional[str] = None

    # Configuración para indicarle qué archivo leer
    model_config = SettingsConfigDict(
        env_file="config.txt",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignora claves extra que no estén en la clase
    )

    @field_validator("entry", "exit", mode="before")
    @classmethod
    def parse_coords(cls, v):
        if isinstance(v, str):
            # Convierte "10,20" -> (10, 20)
            return tuple(map(int, v.split(",")))
        return v


# Se lee y valida automáticamente al instanciar
config = Config()
print(config.entry)  # (10, 20)
print(config.width)  # 800 (convertido a int)
print(config.exit)  # (30, 40)
print(config.perfect)  # True
print(config.seed)  # None
print(config.algorithm)  # None