"""F5 TMOS 연결 설정 (요청 단위로만 사용, 저장소/파일 없음)"""

import base64
from dataclasses import dataclass
from typing import Optional, Dict

# .env / devices 파일 로드 제거 — mgmt IP·계정·비밀번호는 호출 시마다 인자로 전달


@dataclass(frozen=True)
class EndpointSettings:
    """TMOS 연결 설정"""
    host: str
    port: int
    auth_basic_b64: str
    verify_tls: bool
    timeout_seconds: int

    @property
    def base_url(self) -> str:
        return f"https://{self.host}:{self.port}"

    @property
    def headers(self) -> Dict:
        return {
            "Authorization": f"Basic {self.auth_basic_b64}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }


def _parse_bool(value: Optional[bool], default: bool = False) -> bool:
    if value is None:
        return default
    return bool(value)


def build_endpoint_settings(
    host: Optional[str] = None,
    port: Optional[int] = None,
    auth_b64: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    verify_tls: Optional[bool] = None,
    timeout_seconds: Optional[int] = None,
) -> EndpointSettings:
    """요청 단위 연결 정보로 EndpointSettings 생성. mgmt IP·계정·비밀번호는 호출 시마다 전달해야 함."""
    if auth_b64 is None and username is not None and password is not None:
        auth_b64 = base64.b64encode(f"{username}:{password}".encode()).decode()
    if not (host and host.strip()) or not (auth_b64 and auth_b64.strip()):
        raise ValueError(
            "TMOS 연결 정보가 필요합니다. host와 인증(auth_b64 또는 username+password)을 모두 입력해 주세요."
        )
    return EndpointSettings(
        host=host.strip(),
        port=port if port is not None else 443,
        auth_basic_b64=auth_b64.strip(),
        verify_tls=_parse_bool(verify_tls, False),
        timeout_seconds=timeout_seconds if timeout_seconds is not None else 20,
    )
