# Ôn tập sáu phase theo Intern Roadmap

Mục tiêu là hiểu và tự vận hành project, không chỉ chép câu lệnh.
Bảng này phân biệt phần đã thực hành với kiến thức cần giải thích.
Học theo luồng: **lệnh thay đổi gì → kiểm tra bằng gì → lỗi thì đọc ở đâu**.

## Phase 1 — Linux fundamentals

**Nơi học:** Ubuntu WSL. Source app nằm trên ổ F qua /mnt/f; dấu ~ là home
của user Linux, khác home của PowerShell Windows.

| Chủ đề | Ý nghĩa / bài thực hành |
|---|---|
| pwd, ls -la, cd, mkdir -p | Biết vị trí, xem cả file ẩn, chuyển/tạo thư mục |
| Đường dẫn /, ~, ., .. | Tuyệt đối, home, thư mục hiện tại và cha |
| cat, less, head, tail -f | Đọc file ngắn, dài, đầu/cuối và log đang ghi |
| Vim | i để nhập; Esc; :wq lưu/thoát; :q! bỏ thay đổi; / tìm; :set ff=unix |
| User/group, whoami, id | UID/GID và các nhóm của user |
| Quyền rwx | File: đọc/ghi/chạy; directory: liệt kê/thay đổi/traverse |
| chmod 644 / 744 | 644: owner rw, group/other r; 744 thêm x cho owner |
| ./hello.sh vs bash hello.sh | Chạy trực tiếp cần x và shebang; bash đọc file cần quyền đọc |
| Process: ps, pgrep, kill | PID, parent/child; SIGTERM cho cơ hội dừng, không dùng kill -9 ngay |
| Foreground/background | Ctrl+C dừng foreground; & chạy nền; $! là PID job vừa chạy |
| stdout/stderr | > ghi stdout, >> nối thêm, 2>&1 gộp stderr vào stdout |
| Exit code | $? là mã lệnh gần nhất; 0 thành công, khác 0 là lỗi theo chương trình |
| Pipe | stdout lệnh trước trở thành stdin lệnh sau |
| grep, wc, awk | Lọc log, đếm dòng, tổng hợp kết quả; ví dụ đếm HTTP khác 200 |
| Shell variable / export | Biến shell không tự truyền cho process con; export tạo environment |
| VAR=value command | Giá trị chỉ áp dụng cho lệnh đó, không đổi giá trị shell lâu dài |
| set -euo pipefail | Phát hiện nhiều lỗi sớm; -e có ngoại lệ trong if/&&/||, không thay kiểm tra lỗi |
| free, df, du | RAM, dung lượng filesystem, dung lượng cây thư mục; đĩa ảo WSL không bằng ổ C còn trống |
| ip addr / ip route | Địa chỉ interface, subnet, default gateway |
| DNS / getent | Tên → IP; localhost có thể gồm IPv4 127.0.0.1 và IPv6 ::1 |
| TCP/IP/port | IP tìm máy; port tìm dịch vụ; ss -ltnp xem process đang listen |
| 0.0.0.0 | Địa chỉ bind mọi interface IPv4, không phải địa chỉ đích để người dùng truy cập |
| HTTP / curl | Method, path, header, status/body; -i in header, -v xem trao đổi, -f báo lỗi HTTP |
| Git | working tree → git add/index → commit → remote push; commit chưa đồng nghĩa đã lên server |

Bài đã làm: script health với timeout/exit code; process Python và logs; permission
lab; network/DNS; HTTP 404 so với connection refused; export cho process con.
File trên /mnt/f có thể thể hiện quyền khác filesystem Linux: bài chmod đã làm
trong home Ubuntu để quan sát rõ quyền Linux.

Git cần nắm: status, diff, diff --cached, log, remote -v, branch/upstream,
pull --ff-only, commit, push, revert. LF/CRLF kiểm soát bằng .gitattributes.
File ignored nhưng đã tracked vẫn được Git theo dõi; ignore không xóa lịch sử.

Tự kiểm tra: giải thích tại sao curl nhận 404 có thể exit 0, nhưng thêm -f lại
exit 22; tại sao dùng export thì bash con mới nhận biến; tại sao phải xác định PID
trước khi kill.

## Phase 2 — Docker và registry

| Khái niệm | Cần giải thích được |
|---|---|
| Container vs VM | Container chia sẻ kernel host Linux; VM có guest kernel riêng |
| Image vs container | Image là các lớp và metadata; container là instance có process và writable layer |
| Docker daemon | Client gửi API tới daemon; daemon quản lý image, container, network, volume |
| Dockerfile | FROM, WORKDIR, COPY, RUN, ENV, USER, EXPOSE, CMD |
| RUN vs CMD | RUN thực hiện lúc build; CMD là lệnh mặc định lúc chạy container |
| EXPOSE vs publish | EXPOSE là metadata; -p/Compose ports mới publish port lên host |
| Build context / .dockerignore | Chỉ gửi file cần build; loại .git, .env, logs và cache |
| Layers / cache | Thay COPY source không nên làm cài dependency lại nếu requirements không đổi |
| Multi-stage | Builder chuẩn bị /opt/venv; runtime chỉ nhận phần cần chạy |
| Non-root | USER appuser UID 10001; quyền file vẫn phải cho user đó đọc/import được |
| Env | Cùng image khác cấu hình; env không phải nơi bảo mật tuyệt đối |
| stdout logs | Runtime ghi log ra stdout/stderr để Docker/Kubernetes thu thập |
| Compose | Khai báo services, dependencies, network, volume bằng YAML |
| depends_on + healthy | Hỗ trợ thứ tự startup; không tự giải quyết mọi lỗi dependency sau startup |
| Volume | Tách data khỏi writable layer; down giữ volume, down -v xóa volume |
| Registry/project/robot | Nơi lưu image, ranh giới repo/quyền; push robot khác pull robot |
| Tag / digest | Tag là tên có thể trỏ lại; sha256 digest định danh nội dung manifest |
| TLS | CA được tin cậy + SAN đúng tên/IP + thời hạn đúng; không chỉ đúng mật khẩu |
| Kaniko | Build Dockerfile trong container không cần gọi Docker daemon |
| Docker executor + Kaniko | Runner vẫn dùng Docker để tạo job; bước build Kaniko không dùng socket daemon |

Đã làm: single-stage → multi-stage, Gunicorn gthread, user appuser, app+DB Compose,
readiness DB failure/recovery, dữ liệu sống qua recreate, Harbor TLS/private robot,
push/pull và deploy pinned digest. Xem Dockerfile, compose.yaml, compose.harbor.yaml.

Kaniko đang dùng community fork osscontainertools được pin digest trong CI.
Không gọi đây là bản Google gốc còn được duy trì.
Biết docker ps -a, logs, exec, inspect, image ls, tag, push, pull, system df;
không dùng prune --volumes khi chưa xác định dữ liệu cần giữ.

Tự kiểm tra: giải thích vì sao docker tag không build image mới; tại sao CLI curl
tin CA rồi mà Docker/K3s/Kaniko vẫn có thể báo x509; vì sao image build thành công
nhưng appuser runtime vẫn crash.

## Phase 3 — Kubernetes core

**Nơi học:** context k3d-intern-lab. k8s/staging là bài manifest viết tay;
repo devops-demo-gitops mới là cấu hình đang được Argo quản lý.

| Thành phần | Vai trò / quan sát |
|---|---|
| API server | Cổng API cho kubectl và controllers |
| Scheduler | Chọn node phù hợp cho Pod chưa có node |
| Controllers | Liên tục đưa trạng thái thực về desired state |
| etcd | Datastore control-plane phổ biến; học khái niệm, không triển khai HA etcd |
| K3s lab datastore | Cluster một server này dùng SQLite mặc định |
| kubelet | Agent node bảo đảm các container Pod chạy và báo trạng thái |
| containerd | Container runtime của K3s; khác Docker daemon Desktop |
| Pod | Đơn vị chạy/scheduling; các container trong Pod dùng chung network namespace |
| ReplicaSet | Duy trì số Pod; Deployment quản lý ReplicaSet và rollout |
| Deployment | App stateless, replica, revision và rolling update |
| StatefulSet | Identity ổn định postgres-0, storage claim theo replica |
| ClusterIP Service | IP/DNS ổn định và selector tới Pod sẵn sàng |
| NodePort | Mở port trên node; kiến thức bổ sung, không phải route chính của lab |
| LoadBalancer | Cần implementation cung cấp external entry; không tự có cloud load balancer |
| Ingress | Rule HTTP host/path; Traefik thực hiện routing tới Service |
| ConfigMap | Cấu hình không mật; env lấy lúc Pod tạo, sửa ConfigMap không tự đổi env process cũ |
| Secret | Truyền credentials; base64 không phải mã hóa bảo mật |
| Namespace / quota | Tách tên và giới hạn tài nguyên; không tự tạo network isolation |
| Requests / limits | Requests phục vụ scheduling; CPU limit có thể throttle, vượt memory limit có thể OOMKilled |
| PV / PVC / StorageClass | PV là storage, PVC yêu cầu, StorageClass xác định cấp phát |
| local-path | Storage gắn node; không đồng nghĩa có backup hoặc chịu mất node |
| startupProbe | Cho app thời gian khởi động trước readiness/liveness |
| readinessProbe /ready | Không sẵn sàng thì ngừng nhận Service traffic; không tự restart container |
| livenessProbe /health | Fail đủ ngưỡng thì kubelet restart container |
| RollingUpdate | maxUnavailable=0, maxSurge=1; minReadySeconds=5 trước available |
| Termination | preStop sleep5, grace45 cho drain; cần capacity và kiểm thử, không bảo đảm tuyệt đối zero downtime |

Luồng thật: Browser → host port 8088 → k3d serverlb → Traefik → ClusterIP
Service → ready Pod Gunicorn → Service postgres → PostgreSQL → PVC.

kubectl cần nắm: config current-context; apply/dry-run; get -o wide/yaml/jsonpath;
describe; logs/--previous; exec; rollout status/history; events; kustomize.
Luôn chỉ rõ context/namespace khi vận hành nhiều môi trường.

Đã làm: hai replicas, ConfigMap/Secret, quota, probes, PVC; recreate DB Pod và kiểm tra
persistence; self-heal và rollout có drain. Control-plane theory, NodePort và cloud
LoadBalancer là phần giải thích bổ sung, không ghi CV rằng đã xây hệ thống HA.

Nguồn: [Service types](https://kubernetes.io/docs/concepts/services-networking/service/),
[probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/).

## Phase 4 — GitLab CI

**Đã có pipeline thật**, không chỉ YAML hoặc lệnh Kaniko chạy tay.

| Nội dung | Trong project |
|---|---|
| Pipeline / stage / job | Pipeline theo commit; stage nhóm thứ tự; job là tác vụ chạy trên Runner |
| Runner / executor | Runner nhận job; Docker executor tạo container môi trường job |
| YAML | Indent quyết định cấu trúc; stage, image, script, needs, rules |
| test | pytest 14 case; mock DB unit tests + temporary Git integration tests |
| build | Kaniko đọc Dockerfile, push Harbor; tag commit SHA/branch |
| rules | Publish/update GitOps chỉ trên default branch |
| needs | build chờ test; update nhận artifact build |
| Variables | Giá trị cấu hình; protected chỉ cấp theo điều kiện branch/tag |
| File variable | HARBOR_CA_CRT là đường dẫn file tạm trong job, không phải trực tiếp nội dung CA |
| Masked/hidden | Giảm lộ log/UI; vẫn không chống script độc hại có quyền đọc secret |
| Expansion | Tắt cho robot username chứa $ và secret cần giữ nguyên ký tự |
| Cache | Tăng tốc dependency, có thể thiếu; local Runner cache không phải release output |
| Artifacts | Output job: JUnit, digest, dotenv; có thời hạn lưu |
| JUnit | Report hiển thị test ở GitLab, không thay exit code pytest |
| CI_JOB_TOKEN | Credential tạm cho push GitOps sau khi cấu hình quyền cross-project |
| resource_group | Serialize update staging từ project này |
| Stale check | Bỏ pipeline source cũ nếu default branch đã tiến lên |
| Normal push | Conflict remote bị từ chối; không force push để ghi đè commit khác |

Đọc .gitlab-ci.yml, ci/update_gitops.sh, ci/update_gitops_image.py và tests/.
Theo dõi commit source → build digest artifact → commit GitOps → image trên Deployment.
14 test gồm 8 case ứng dụng và 6 case automation; test DB được mock, readiness live
đã kiểm tra riêng trên PostgreSQL thật.

Nguồn: [GitLab pipelines](https://docs.gitlab.com/ci/pipelines/),
[JUnit reports](https://docs.gitlab.com/ci/testing/unit_test_reports/),
[job token](https://docs.gitlab.com/ci/jobs/ci_job_token/).

## Phase 5 — GitOps và Argo CD

| Nội dung | Trong project |
|---|---|
| Desired state | GitOps repo lưu cấu hình mong muốn có lịch sử |
| Split repos | App repo build/test; GitOps repo quyết định môi trường chạy digest nào |
| Pull deployment | Argo trong cluster đọc Git và reconcile; CI chỉ push Git, không apply cluster |
| Application | repoURL, targetRevision=main, path overlay, destination |
| AppProject | Giới hạn source repo, namespace đích và loại resource |
| Kustomize base | Manifest dùng chung, hạn chế sao chép |
| Overlay | Namespace, APP_ENV, image digest và host riêng từng môi trường |
| Auto-sync | Staging nhận thay đổi Git tự động |
| Self-heal | Sửa drift live; đã thử scale3 rồi tự trở về2 |
| Prune | Xóa tài nguyên không còn trong desired state; auto-prune lab đang tắt |
| Manual Sync | Prod chỉ apply khi người vận hành review và Sync |
| Synced / OutOfSync | Cấu hình live có khớp target manifests không |
| Healthy / Degraded | Sức khỏe resources; không chứng minh đang chạy commit mới nhất |
| Revision | Kiểm tra commit đích trước khi kết luận release hoàn tất |
| Git revert | Rollback bền vững bằng desired state mới có lịch sử |
| Image Updater | Roadmap ghi optional; chưa triển khai, CI đang update digest trực tiếp |

Argo chỉ cần quyền đọc GitOps repo; CI chỉ cần quyền cập nhật cấu hình.
Credentials được provision ngoài Git; không nhúng token vào Application hay remote URL.
Không dùng Force/Replace để giải quyết một thao tác Sync thông thường.

Nguồn: [Argo auto-sync/self-heal](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/),
[Kustomize](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/).

## Phase 6 — Capstone và hồ sơ

Bằng chứng đã xác nhận:

1. Sửa HTML và push source.
2. GitLab chạy 14 test, build/push image, update_staging commit digest.
3. Argo nhận đúng revision và tự deploy staging; prod vẫn nội dung cũ.
4. Promote cùng digest vào prod, manual Sync.
5. Hai Application Synced/Healthy; prod /ready=200, environment=prod và giao diện mới.
6. Đã có incident rollout lỗi, RCA và Git revert recovery thực tế.
7. README, setup, runbook, demo và CV notes đóng gói để người khác review.

Thực hành cần tự làm lại trước phỏng vấn: đọc một job log lỗi, tìm image digest,
đối chiếu GitOps revision, kiểm tra đúng host prod, giải thích rollback và giới hạn
database. Không đọc thuộc một danh sách công cụ mà không chỉ ra vai trò trong luồng.

Các phần chưa làm và không ghi nhận là đã hoàn thành: Image Updater, cloud HA,
etcd HA, network policy, DB role hardening, backup/restore drill, migration,
centralized monitoring. Đây là hướng mở rộng sau capstone, không phải điều kiện
bắt buộc thêm để kể project hiện tại.
