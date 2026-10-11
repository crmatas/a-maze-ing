from typing import Optional, Tuple
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode
from typing import Annotated


class Config(BaseSettings):
    width: int
    height: int
    entry: Annotated[Tuple[int, int], NoDecode]
    exit: Annotated[Tuple[int, int], NoDecode]
    output_file: Annotated[str, NoDecode]
    perfect: bool = True
    seed: Optional[int] = None
    algorithm: Optional[str] = None

    # Configuración para indicarle qué archivo leer
    model_config = SettingsConfigDict(
        env_file_encoding="utf-8",
        extra="ignore",  # Ignora claves extra que no estén en la clase
    )

    @field_validator("entry", "exit", mode="before")
    @classmethod
    def parse_coords(cls, value):
        if isinstance(value, str):
            return tuple(map(int, value.split(",")))
        return value

    @field_validator("algorithm", mode="after")
    @classmethod
    def parse_algorithm(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value or value == "":
            return None
        value = " ".join(value.split())
        return value
