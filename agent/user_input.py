import re

from pydantic import BaseModel, field_validator


re_http_link = re.compile("http[s]://")


class UserInput(BaseModel):
    subsystem_name: str


class HttpLinkInput(UserInput):
    linux_kernel_c_file_http_link: str
    syzkaller_syzlang_file_http_link: str
    syzkaller_test_seed_program_http_link: str

    @field_validator('*', mode='before')
    @classmethod
    def http_validator(cls, value: str) -> str:
        if not re_http_link.match(value):
            raise ValueError(f"invalid http link {value}")
        return value
