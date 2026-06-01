# PRD — work-support 개인 운영 배포/보안/백업 계획

## 1. 목적
work-support를 개인 업무 문서·프로젝트·경력 자산을 관리하는 로컬/개인 운영 서비스로 안전하게 운영한다. 초기 목표는 “혼자 쓰는 안정적 self-hosted 앱”이며, 다중 사용자 SaaS 운영은 목표가 아니다.

## 2. 운영 원칙
1. **Local-first, private-by-default**: 기본 배포는 loopback 또는 개인 VPN 뒤에 둔다.
2. **Backup before automation**: 자동화·AI 기능보다 백업/복구 검증을 먼저 완료한다.
3. **No public secret exposure**: OpenAI key, DB password, report/auth token은 브라우저 번들·Git·로그에 노출하지 않는다.
4. **Evidence-preserving recovery**: 장애 시 DB와 업로드 원본 파일의 시점 정합성을 맞춘다.
5. **Simple before HA**: 개인용 MVP는 단일 서버 + 정기 백업 + 복구 리허설을 우선한다. 고가용성/클러스터는 후속.

## 3. 권장 배포 아키텍처

### 3.1 1차 권장: 단일 서버 Docker Compose
- 서버: 개인 NAS, 홈서버, 소형 VPS 중 하나.
- 외부 접근: 기본 금지. 필요 시 Tailscale/WireGuard/VPN 또는 reverse proxy + 인증을 둔다.
- Compose 파일:
  - `compose.yaml`: 공통 정의.
  - `compose.prod.yaml`: 운영 override. 개발용 bind mount와 reload 제거, restart policy, read-only where possible, backup sidecar/cron 추가.
- 네트워크:
  - DB는 외부 port publish 금지.
  - frontend/backend만 reverse proxy 내부 network에 연결.
  - localhost 개발용 port binding과 운영 binding을 분리.

### 3.2 운영 디렉토리
```text
/opt/work-support/
├─ app/                 # 배포된 repo or release bundle
├─ env/                 # chmod 600, .git 밖
├─ secrets/             # Docker secrets source files, chmod 600
├─ data/postgres/       # Docker named volume or bind mount
├─ data/uploads/        # 업로드 원본 파일
├─ backups/postgres/    # pg_dump archive
├─ backups/uploads/     # upload snapshot/archive
├─ backups/manifests/   # backup checksums + metadata
└─ logs/                # exported app/proxy/backup logs
```

## 4. Docker Compose 운영 계획

### P0 compose hardening
- 개발용 `--reload`, source bind mount, `.next` dev volume은 운영 compose에서 제거.
- backend/frontend image는 build 후 immutable tag로 배포한다.
- `db` service는 internal network only.
- healthcheck:
  - db: `pg_isready`.
  - backend: `/health`.
  - frontend: HTTP 200 smoke.
- restart: `unless-stopped`.
- resource guard: 개인 서버 사양에 맞춰 memory/cpu limits를 문서화.
- upgrade 절차:
  1. backup 생성 및 restore 가능성 확인.
  2. 새 image build/pull.
  3. `docker compose -f compose.yaml -f compose.prod.yaml up -d`.
  4. healthcheck와 smoke test.
  5. 실패 시 이전 image tag로 rollback.

## 5. 환경변수/secret 관리

### 5.1 분리 정책
- `.env.example`: 샘플만, 실제 secret 금지.
- 운영 `.env`: `/opt/work-support/env/work-support.env`, chmod 600.
- 강한 secret은 Docker Compose secrets 또는 host secret file 사용.
- 브라우저로 전달되는 `NEXT_PUBLIC_*`에는 secret 금지.

### 5.2 필수 secret
- `POSTGRES_PASSWORD`
- `DATABASE_URL` 또는 개별 DB credential
- `OPENAI_API_KEY`
- 앱 인증 secret/session secret
- backup encryption passphrase 또는 age/sops key

### 5.3 회전 기준
- 최초 운영 전 모든 dev 기본값 교체.
- OpenAI key: 유출 의심 즉시 revoke/replace.
- DB password/session secret: 분기별 또는 접근자 변경 시 회전.
- `.env` 수정 후 `docker compose config`로 interpolation 확인.

## 6. 인증/접근 제어 계획

### 6.1 개인 운영 최소 인증
- 현재 local header/token guard는 운영 인증이 아니다.
- 운영 전 최소한 다음 중 하나를 적용한다.
  1. reverse proxy basic auth + VPN 제한: 가장 단순한 개인 운영용.
  2. 앱 내 단일 사용자 로그인: HttpOnly Secure SameSite cookie session.
  3. OAuth/OIDC: Google/GitHub 등, 단일 allowlist 계정.
- 선택 기준:
  - LAN/VPN only: reverse proxy + basic auth 가능.
  - 인터넷 노출: OIDC 또는 앱 세션 인증 필수.

### 6.2 세션 보안
- cookie: HttpOnly, Secure, SameSite=Lax/Strict.
- session id는 충분한 entropy, server-side invalidation 가능.
- login rate limit과 audit log.
- CSRF: cookie 기반 mutation API는 CSRF token 또는 SameSite/Origin 검증.
- owner boundary: 모든 DB query에 owner_id/principal filter 유지.

## 7. PostgreSQL 백업 계획

### 7.1 P0: 매일 logical backup
- 매일 새벽 `pg_dump -Fc` archive format.
- 보존:
  - 일별 14일.
  - 주별 8주.
  - 월별 12개월.
- dump 대상: application database.
- global objects/roles가 필요해지면 `pg_dumpall --globals-only` 추가.
- backup metadata:
  - timestamp, git/release tag, DB image version, schema checksum, dump size, sha256, command exit code.

### 7.2 P1: PITR가 필요한 경우
- 문서/경력 데이터 손실 허용치가 낮아지면 `pg_basebackup` + WAL archiving로 전환.
- WAL archive storage는 업로드 백업과 같은 원격 저장소에 versioning/immutability 적용.
- PITR runbook은 별도 복구 리허설을 통과해야 운영 활성화.

### 7.3 Restore 리허설
- 월 1회 별도 임시 DB container에서 restore.
- 검증:
  - DB 접속 가능.
  - 핵심 table count.
  - 최근 프로젝트/문서/업무 로그 조회.
  - app smoke test.
- restore 실패 시 그 backup 세대는 invalid로 표시하고 이전 세대 확인.

## 8. 업로드 파일 백업 계획

### 8.1 대상
- `storage/uploads` 또는 운영 `/opt/work-support/data/uploads`.
- 원본 파일, 추출 텍스트/파생 파일이 파일시스템에 저장될 경우 포함.

### 8.2 방식
- DB backup 직후 업로드 파일 snapshot 생성.
- 파일 백업은 `rsync --delete --checksum` 또는 `tar` archive + sha256 manifest.
- 원격 복제: S3-compatible bucket, Backblaze B2, NAS snapshot 중 하나.
- encryption at rest: rclone crypt, restic, borg, age/sops 등 중 하나 선택.

### 8.3 정합성
- 가장 단순한 P0: 짧은 maintenance window에서 app write 중지 → DB dump → uploads snapshot → app 재개.
- 무중단이 필요해지면 upload object versioning + DB snapshot timestamp를 manifest에 저장.
- 복구 시 DB와 uploads manifest timestamp가 같은 backup set인지 확인한다.

## 9. 로그 관리/감사

### 9.1 로그 종류
- app access log: method, path, status, latency, request id.
- app audit log: login, export, document upload/download, delete, backup/restore action.
- AI log: model, prompt version, token/cost estimate, status, error. 원문 민감정보는 저장하지 않음.
- backup log: start/end, file names, sha256, remote sync result.
- reverse proxy log: IP, TLS, status.

### 9.2 보존/민감정보
- raw app/proxy logs: 30일.
- audit/backup logs: 1년.
- 로그에는 OpenAI key, DB password, document full text, resume export full content를 남기지 않는다.
- request id로 장애 추적 가능하게 한다.

## 10. 장애 복구 기준

### 10.1 목표치
- RPO P0: 최대 24시간 데이터 손실.
- RTO P0: 4시간 내 개인 운영 복구.
- P1 목표: RPO 1시간, RTO 1시간. PITR/remote backup 검증 후 적용.

### 10.2 장애 등급
- SEV1: DB 손상/서버 디스크 장애/모든 접속 불가/데이터 삭제 사고.
- SEV2: 업로드 파일 일부 손실/AI 처리 실패 지속/로그인 불가.
- SEV3: 특정 리포트/export 실패/UI 일부 오류.

### 10.3 복구 절차
1. 신규 write 중지 또는 서비스 내림.
2. 장애 시각과 영향 범위 기록.
3. 최신 정상 backup set 선택.
4. DB restore.
5. uploads restore.
6. env/secrets 확인.
7. app health/smoke.
8. 샘플 프로젝트/문서/export 확인.
9. 사후 기록: 원인, 복구 시간, 손실 범위, 재발 방지.

## 11. 운영 점검표

### 매일
- container health 확인.
- 전날 backup 성공 여부 확인.
- 디스크 사용률 확인.

### 매주
- backup remote sync 확인.
- restore dry-run 일부 자동화 결과 확인.
- 로그에서 반복 에러 확인.

### 매월
- 전체 restore 리허설.
- dependency/image update 검토.
- secret rotation 필요성 점검.
- export/backup 파일 암호화 상태 확인.

## 12. 단계별 실행 로드맵

### Phase 0 — 공개 전 필수
- 운영 compose override 작성.
- dev 기본 secret 교체.
- DB 외부 port 비공개.
- daily pg_dump + uploads backup script/runbook.
- restore rehearsal 1회 통과.
- 인증 방식 결정 및 적용.

### Phase 1 — 개인 운영 안정화
- reverse proxy TLS/VPN 구성.
- audit log와 request id 도입.
- backup manifest/checksum 자동 검증.
- 월 1회 restore drill calendar 등록.

### Phase 2 — 데이터 중요도 증가 시
- PITR/WAL archiving.
- encrypted remote backup + lifecycle policy.
- app-level session auth/OIDC.
- backup/restore 자동 테스트 container.

## 13. 승인 기준
- 실제 운영 secret이 repo에 없다.
- DB와 uploads를 같은 backup set으로 복구할 수 있다.
- 복구 리허설에서 핵심 화면/API smoke가 통과한다.
- 인증 없이 외부에서 앱에 접근할 수 없다.
- backup 실패가 하루 이상 조용히 방치되지 않는다.
- 장애 복구 runbook을 보고 4시간 내 복구할 수 있다.

## 14. 외부 기준 근거
- Docker 공식 문서는 운영 Compose에서 앱 코드 bind mount 제거, 환경별 설정 변경, restart policy, log aggregator 같은 production override를 권장하므로 `compose.prod.yaml` 분리를 운영 기본값으로 둔다.
- Docker Compose 환경변수 문서는 민감정보를 environment 변수에 넣을 때 주의하고 secrets 사용을 고려하라고 안내하므로, `.env`는 비밀 최소화·권한 제한·브라우저 노출 금지 원칙으로 관리한다.
- Docker Compose secrets는 서비스에 명시적으로 grant된 secret만 접근 가능하므로 DB 비밀번호·세션 secret·API key는 가능한 secret file 기반으로 전달한다.
- PostgreSQL 공식 문서는 백업 방식을 SQL dump, filesystem-level backup, continuous archiving으로 구분하므로 P0는 `pg_dump -Fc`, P1는 `pg_basebackup` + WAL archiving/PITR로 단계화한다.
- PostgreSQL PITR 문서는 WAL archiving이 특정 시점 복구를 가능하게 하지만 `pg_dump`/`pg_dumpall`은 WAL replay용 파일시스템 백업이 아니라고 설명하므로, PITR 전환 시 logical dump만으로 충분하다고 가정하지 않는다.
- OWASP 인증/세션 지침은 session identifier가 예측 어렵고 사용자·접근제어와 묶여야 함을 강조하므로, 인터넷 노출 전에는 token header 임시 guard가 아니라 VPN/reverse proxy auth 또는 앱 세션/OIDC를 적용한다.

## 15. Architect Review 반영 — 운영 기본값 확정

### 15.1 외부 노출/Auth 하드 게이트
- **현재 header/token guard는 운영 인증으로 인정하지 않는다.** 개발·로컬 보조 장치일 뿐이며 외부 노출 보안 경계가 아니다.
- 인증 구현 전 허용 노출 범위:
  - `localhost` 또는 LAN 내부 단일 장비.
  - 개인 VPN(Tailscale/WireGuard 등) 뒤에서만 접근.
  - reverse proxy basic auth를 함께 둘 수 있으나, 인터넷 공개 인증의 대체재로 보지 않는다.
- 인터넷 공개 접근 하드 게이트:
  - 앱 내 단일 사용자 세션 인증 또는 OIDC allowlist 계정 적용 전까지 금지.
  - 모든 mutation/export/download/upload API에 동일 principal 확인 전까지 금지.
  - `NEXT_PUBLIC_*`로 token, owner id, API key, DB credential을 전달하면 배포 실패로 처리한다.

### 15.2 Canonical Backup Set Protocol
개인 MVP P0는 짧은 downtime을 허용하고 **write quiesce 방식**으로 DB와 uploads 정합성을 보장한다.

#### Backup set 상태
- `pending`: backup 시작, 아직 검증 전.
- `complete`: DB dump, uploads archive, checksum, manifest 작성 완료.
- `restore_verified`: 임시 restore 리허설 통과.
- `invalid`: 중간 실패, checksum 불일치, restore 실패, timestamp 불일치.

#### P0 backup 순서
1. backup manifest를 `pending`으로 생성한다.
2. backend/frontend를 maintenance 또는 stop 상태로 전환한다. 현재 maintenance mode가 없으면 `docker compose stop backend frontend`를 기본값으로 한다.
3. DB container는 유지한 채 `pg_dump -Fc` logical dump를 생성한다.
4. uploads 디렉토리를 `tar` archive 또는 `rsync` snapshot으로 복사한다.
5. DB dump와 uploads archive 각각 sha256, byte size, file count를 기록한다.
6. manifest를 `complete`로 갱신한다.
7. backend/frontend를 재기동한다.
8. 실패한 단계가 있으면 manifest를 `invalid`로 남기고 해당 backup set은 restore 후보에서 제외한다.
9. 월 1회 또는 release 전 restore rehearsal을 통과한 backup set만 `restore_verified`로 승격한다.

#### Manifest 필수 필드
```json
{
  "backup_set_id": "YYYYMMDDTHHMMSSZ",
  "status": "pending|complete|restore_verified|invalid",
  "started_at": "ISO-8601",
  "completed_at": "ISO-8601|null",
  "app_release": "git-sha-or-release-tag",
  "compose_files": ["compose.yaml", "compose.prod.yaml"],
  "postgres_image": "postgres:<version>",
  "database_name": "work_support",
  "db_dump_path": "...",
  "db_dump_sha256": "...",
  "uploads_archive_path": "...",
  "uploads_sha256": "...",
  "uploads_file_count": 0,
  "schema_checksum": "...",
  "restore_tested_at": "ISO-8601|null",
  "notes": ""
}
```

### 15.3 Secret 관리 기본값
- 기본 운영 방식은 **host-owned secret files + Compose secrets mount**로 한다.
  - 위치: `/opt/work-support/secrets/`.
  - 권한: directory `700`, files `600`, owner는 배포 사용자.
  - compose는 필요한 service에만 secret을 grant한다.
- `.env`는 non-secret config와 secret file path만 담는 것을 목표로 한다.
- 앱이 아직 `_FILE` 패턴을 지원하지 않는 secret은 전환 전까지 `/opt/work-support/env/work-support.env`에 server-only로 보관할 수 있으나, 이 예외는 운영 debt로 기록하고 `NEXT_PUBLIC_*`에는 절대 넣지 않는다.
- backup encryption 기본값은 **restic repository + age 또는 repository password secret file** 중 하나로 고정한다. 초기 개인 운영은 restic을 권장한다.
- secret 회전 runbook:
  1. 새 secret file 생성 및 권한 확인.
  2. compose config 검증.
  3. service 재기동.
  4. 이전 secret revoke/delete.
  5. secret이 logs/browser bundle에 노출되지 않았는지 scan.

### 15.4 로그/프라이버시 구현 규칙
- Docker log driver 기본값: `json-file` + `max-size=10m`, `max-file=5` 또는 동등한 logrotate 정책.
- app/proxy logs는 request/response body를 저장하지 않는다.
- 문서 원문, 추출 텍스트 전문, resume/export 본문, OpenAI prompt 전문, OpenAI API key, DB password는 로그 금지.
- request id는 reverse proxy → frontend/backend → app log에 전파한다.
- AI 작업 로그는 model, prompt version, token/cost estimate, status, error code만 기록한다.
- 주간 점검에서 다음 패턴을 로그에서 검색한다: `OPENAI_API_KEY`, `postgres://`, `DATABASE_URL`, `BEGIN PRIVATE KEY`, 문서 샘플 고유문구 1~2개.

### 15.5 Recovery owner / failback 계약
- Recovery owner: 개인 운영자 본인. 대리 운영자가 생기면 `/opt/work-support/RUNBOOK.md`에 연락처·권한·secret 접근 위치를 명시한다.
- 복구 완료 조건:
  1. DB restore 성공 및 migration/schema checksum 일치.
  2. uploads restore 성공 및 manifest checksum 일치.
  3. secret/env 로드 성공.
  4. `/health` 통과.
  5. 최근 프로젝트 1개, 문서 1개, export/report 1개 샘플 조회 통과.
  6. 인증 없는 접근 차단 확인.
  7. 복구 시작/종료 시각, RPO/RTO, 손실 범위 기록.
- failback/rollback 조건:
  - restore된 DB와 uploads backup set id가 다름.
  - checksum 불일치.
  - 인증 우회 가능.
  - 핵심 샘플 조회 실패.
  - 이 경우 서비스 공개를 중단하고 이전 `restore_verified` backup set 또는 이전 image tag로 되돌린다.
