# F5 TMOS Generic API 가이드 — 모든 설정 생성/수정/삭제

기본·표준 설정 외 **F5 iControl REST API 스펙의 모든 엔드포인트**를 MCP 도구로 호출할 수 있습니다.  
[API Reference](https://clouddocs.f5.com/api/icontrol-rest/APIRef.html)에서 path와 속성을 확인한 뒤 `tm_get_tool`, `tm_post_tool`, `tm_patch_tool`, `tm_put_tool`, `tm_delete_tool` 로 자연어 요청을 처리합니다.

---

## 1. Generic 도구 (5개)

| 도구 | HTTP | 용도 |
|------|------|------|
| `tm_get_tool(path)` | GET | 컬렉션 목록 또는 단일 리소스 조회 |
| `tm_post_tool(path, body)` | POST | 리소스 생성 또는 액션 실행 |
| `tm_patch_tool(path, body)` | PATCH | 리소스 일부 속성 수정 |
| `tm_put_tool(path, body)` | PUT | 리소스 전체 교체 |
| `tm_delete_tool(path)` | DELETE | 리소스 삭제 |

- **path**: `tm` 하위 경로. 앞에 `/mgmt/tm/` 는 붙이지 않아도 됨.  
  - 컬렉션: `ltm/pool`, `net/vlan`, `sys/syslog`  
  - 단일 리소스: `ltm/pool/~Common~my_pool`, `net/vlan/~Common~vlan100`  
  - 파티션은 `~partition~name` 형식 (예: `~Common~`).
- **body**: API 스펙의 속성(camelCase). clouddocs 각 리소스 페이지의 Properties 표 참고.

---

## 2. API 네임스페이스 (path 접두어)

[APIRef](https://clouddocs.f5.com/api/icontrol-rest/APIRef.html) 기준 주요 네임스페이스입니다. 각 하위 경로는 clouddocs에서 상세 스펙 확인.

| path 접두어 | 설명 | 예시 path |
|-------------|------|-----------|
| **ltm** | LTM (로드밸런싱) | ltm/pool, ltm/virtual, ltm/node, ltm/snatpool, ltm/policy, ltm/rule |
| **net** | 네트워크 | net/vlan, net/self, net/route, net/arp, net/interface, net/route-domain |
| **sys** | 시스템 | sys/syslog, sys/dns, sys/ntp, sys/db, sys/management-route, sys/global-settings |
| **cm** | 클러스터/HA | cm/device, cm/device-group, cm/add-to-trust, cm/traffic-group |
| **auth** | 인증 | auth/user, auth/partition, auth/password-policy, auth/ldap, auth/radius-server |
| **gtm** | GTM | gtm/server, gtm/datacenter, gtm/wideip |
| **analytics** | 분석 | analytics/report |
| **apm** | APM | apm/application, apm/access-info |
| **ilx** | iRules LX | ilx/workspace, ilx/plugin |
| **util** | 유틸 | util/bash (tmsh 실행 등) |

---

## 3. list / create / update / delete / get_one (resource_path 지원)

표준·기본 설정 외 **모든 리소스**에 대해 공통 CRUD 도구를 쓸 수 있습니다. **resource_path**로 API 경로를 지정합니다.

| 도구 | 용도 | 예시 |
|------|------|------|
| `list_tool(resource_path=...)` | 목록 조회 | `resource_path="net/vlan"`, `"net/self"`, `"ltm/pool"` |
| `create_tool(url_body={...}, resource_path=...)` | 생성 | `resource_path="net/vlan"`, url_body에 name, tag 등 |
| `get_one_tool(object_name=..., resource_path=...)` | 단일 조회 | `object_name="vlan100"`, `resource_path="net/vlan"` |
| `update_tool(object_name=..., url_body={...}, resource_path=...)` | 수정 | PATCH 해당 리소스 |
| `delete_tool(object_name=..., resource_path=...)` | 삭제 | DELETE 해당 리소스 |
| `show_stats_tool(object_name=..., resource_path=...)` | 통계 | ltm pool/virtual 등 (net은 미지원 시 404) |

- **resource_path** 없이 **object_type**만 주면 기존처럼 **ltm** 하위로 처리 (예: `object_type="pool"` → ltm/pool).
- **partition** 기본값은 Common. 다른 파티션은 `partition="파티션명"` 지정.

---

## 4. 자연어 → 도구 사용 예

- **"풀 목록 조회"** → `list_tool(resource_path="ltm/pool")` 또는 `tm_get_tool(path="ltm/pool")`
- **"VLAN 목록 조회"** → `list_tool(resource_path="net/vlan")`
- **"Self IP 목록"** → `list_tool(resource_path="net/self")`
- **"풀 my_pool 생성, round-robin"** → `create_tool(resource_path="ltm/pool", url_body={"name":"my_pool","loadBalancingMode":"round-robin"})` 또는 `tm_post_tool(path="ltm/pool", body={...})`
- **"VLAN 100 생성"** → `create_tool(resource_path="net/vlan", url_body={"name":"vlan100","tag":100,...})` (APIRef net/vlan 참고)
- **"vlan100 삭제"** → `delete_tool(resource_path="net/vlan", object_name="vlan100")`
- **"vlan100 한 건 조회"** → `get_one_tool(resource_path="net/vlan", object_name="vlan100")`
- **"my_pool 삭제"** → `delete_tool(resource_path="ltm/pool", object_name="my_pool")` 또는 `tm_delete_tool(path="ltm/pool/~Common~my_pool")`
- **"기존 풀 my_pool 로드밸런싱 방식만 변경"** → `update_tool(resource_path="ltm/pool", object_name="my_pool", url_body={"loadBalancingMode":"least-connections-node"})`

리소스 **생성 시**는 컬렉션 path에 POST, **수정/삭제 시**는 리소스 path(파티션+이름 포함)를 사용합니다.

---

## 5. 리소스 path 형식

- **Common 파티션**: `~Common~리소스이름` (예: `ltm/pool/~Common~my_pool`)
- **다른 파티션**: `~partition명~리소스이름`
- **하위 컬렉션**: 예) `ltm/pool/~Common~my_pool/members` → 멤버 목록/추가

clouddocs 각 API 페이지의 "Resource URI"를 보면 `~resource id` 형식이 나옵니다.

---

## 6. AI 사용 시 권장 흐름

1. **요청 이해**: 사용자 자연어로 원하는 설정(생성/수정/삭제/조회) 파악.
2. **스펙 확인**: [APIRef](https://clouddocs.f5.com/api/icontrol-rest/APIRef.html)에서 해당 리소스(ltm, net, sys 등) 페이지로 이동해 Collection/Resource URI, Methods, Properties 확인.
3. **도구 선택**: GET → tm_get_tool, 생성 → tm_post_tool, 일부 수정 → tm_patch_tool, 전체 교체 → tm_put_tool, 삭제 → tm_delete_tool.
4. **path/body 결정**: path는 tm 하위 경로, body는 스펙의 속성명(camelCase)으로 구성.
5. **호출 후 결과 확인**: 오류 시 status_code, body 메시지로 원인 파악 후 path/body 수정 재시도.

이 흐름으로 **기본·표준 설정을 제외한 F5의 모든 설정**을 자연어로 요청하고, API 스펙에 맞춰 생성/수정/삭제할 수 있습니다.
