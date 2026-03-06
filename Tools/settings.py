"""F5 TMOS 연결 설정 관리"""

import base64
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv


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


def _parse_bool(value: Optional[str], default: bool = False) -> bool:
    """문자열을 boolean으로 변환"""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _parse_int(value: Optional[str], default: int = 20) -> int:
    """문자열을 integer로 변환"""
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _load_env():
    """환경변수 파일 로드"""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)


def _endpoint_from_env(host_key: str, port_key: str, auth_key: str, 
                       verify_key: str, timeout_key: str, default_port: int) -> EndpointSettings:
    """환경변수에서 설정 값 읽기"""
    _load_env()
    
    host = os.getenv(host_key, "").strip()
    auth = os.getenv(auth_key, "").strip()
    port = _parse_int(os.getenv(port_key), default_port)
    verify_tls = _parse_bool(os.getenv(verify_key), False)
    timeout_seconds = _parse_int(os.getenv(timeout_key), 20)

    if not host or not auth:
        raise ValueError(f"TMOS 연결 정보 부족: {host_key}, {auth_key} 확인 필요")

    return EndpointSettings(
        host=host,
        port=port,
        auth_basic_b64=auth,
        verify_tls=verify_tls,
        timeout_seconds=timeout_seconds,
    )


@lru_cache(maxsize=1)
def get_endpoint_settings(kind: str = "TMOS") -> EndpointSettings:
    """TMOS 설정 조회 (환경변수 기준)"""
    return _endpoint_from_env(
        host_key="TMOS_HOST",
        port_key="TMOS_PORT",
        auth_key="TMOS_AUTH_BASIC_B64",
        verify_key="TMOS_VERIFY_TLS",
        timeout_key="TMOS_TIMEOUT_SECONDS",
        default_port=443,
    )


def build_endpoint_settings(
    host: Optional[str] = None,
    port: Optional[int] = None,
    auth_b64: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    verify_tls: Optional[bool] = None,
    timeout_seconds: Optional[int] = None,
) -> EndpointSettings:
    """요청 단위 연결 정보로 EndpointSettings 생성. 누락된 값은 환경변수로 채움.
    다중 장비·계정 변경 시 호출마다 다른 host/username/password 전달 가능.
    """
    if auth_b64 is None and username is not None and password is not None:
        auth_b64 = base64.b64encode(f"{username}:{password}".encode()).decode()
    # 전부 넘어오면 env 불필요
    if host and auth_b64:
        return EndpointSettings(
            host=host.strip(),
            port=port if port is not None else 443,
            auth_basic_b64=auth_b64.strip(),
            verify_tls=verify_tls if verify_tls is not None else False,
            timeout_seconds=timeout_seconds if timeout_seconds is not None else 20,
        )
    # 일부만 넘어오면 나머지는 env
    defaults = get_endpoint_settings("TMOS")
    out_host = (host or defaults.host).strip()
    out_auth = (auth_b64 or defaults.auth_basic_b64).strip()
    if not out_host or not out_auth:
        raise ValueError("TMOS 연결 정보 부족: host와 인증( auth_b64 또는 username+password ) 필요. 또는 환경변수 TMOS_HOST, TMOS_AUTH_BASIC_B64 설정.")
    return EndpointSettings(
        host=out_host,
        port=port if port is not None else defaults.port,
        auth_basic_b64=out_auth,
        verify_tls=verify_tls if verify_tls is not None else defaults.verify_tls,
        timeout_seconds=timeout_seconds if timeout_seconds is not None else defaults.timeout_seconds,
    )


