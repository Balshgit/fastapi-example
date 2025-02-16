from dataclasses import dataclass


@dataclass(slots=True)
class UpdateUserRequestDTO:
    username: str
    first_name: str
    last_name: str
    email: str


@dataclass(slots=True)
class UserDTO:
    id: int
    username: str
    first_name: str | None
    last_name: str | None
    email: str
    is_active: bool
