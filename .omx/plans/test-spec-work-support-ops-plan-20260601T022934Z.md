# Test Spec — work-support 운영 계획 검증 기준

## 문서 검증
- Docker Compose 운영 override가 dev bind mount/reload를 제거하는지 확인.
- DB service가 운영에서 외부 port를 publish하지 않는지 확인.
- `NEXT_PUBLIC_*`에 secret이 없는지 확인.
- `.env.example`에는 샘플만 있고 실제 secret이 없는지 secret scan.

## 백업 검증
- `pg_dump -Fc` command가 성공하고 sha256 manifest가 생성된다.
- uploads backup command가 성공하고 file count/checksum manifest가 생성된다.
- backup set metadata가 DB dump와 uploads snapshot을 같은 timestamp로 묶는다.
- 보존 정책이 old backup을 삭제하기 전 최소 1개 restore-verified backup을 남긴다.

## 복구 리허설
- 임시 PostgreSQL container에 최신 dump restore.
- uploads snapshot을 임시 경로에 restore.
- app이 임시 DB/uploads로 boot.
- `/health`, report/export 핵심 API, 최근 프로젝트/문서 샘플 조회 통과.
- restore time을 기록해 RTO 4시간 목표 안에 들어오는지 확인.

## 보안 검증
- 외부 네트워크에서 DB port 접근 불가.
- 인증 없는 app 접근 차단.
- cookie/session 도입 시 HttpOnly/Secure/SameSite 확인.
- 로그에 OpenAI key, DB password, document full text가 남지 않는지 샘플 검사.

## 장애 훈련
- DB container 삭제/volume 손상 가정.
- uploads 일부 삭제 가정.
- 잘못된 배포 rollback 가정.
- 각 시나리오별 runbook 수행 가능 여부와 실제 소요시간 기록.

## 운영 승인 게이트
- 공개 접근 전: 인증/접근제어, DB port 비공개, secret scan, backup/restore rehearsal이 모두 완료되어야 한다.
- 백업 성공 판정은 “파일 생성”이 아니라 restore dry-run + checksum 검증까지 포함한다.
- 운영 문서에는 RPO/RTO, backup retention, restore owner, 장애 등급, rollback 기준이 명시되어야 한다.

## Architect Review 반영 검증
- 인증 전 외부 노출이 `localhost/LAN/VPN-only`로 제한되어 있는지 운영 문서에서 확인한다.
- 인터넷 공개 조건에는 앱 세션/OIDC, principal filter, `NEXT_PUBLIC_*` secret 금지가 모두 포함되어야 한다.
- backup set manifest가 `pending|complete|restore_verified|invalid` 상태와 DB/uploads checksum을 모두 포함하는지 확인한다.
- backup 중 write quiesce 방식이 명시되어 있고, maintenance mode가 없을 때 backend/frontend stop 절차가 있는지 확인한다.
- secret 기본 경로가 `/opt/work-support/secrets/`이고 권한 `700/600` 및 Compose secrets grant 정책이 명시되어 있는지 확인한다.
- log rotation, no-body logging, 민감정보/문서 원문 금지, request id 전파가 명시되어 있는지 확인한다.
- recovery owner, 복구 완료 조건, failback/rollback 조건이 문서화되어 있는지 확인한다.
