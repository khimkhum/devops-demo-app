# CV và chuẩn bị phỏng vấn

Chỉ ghi các phần có thể mở code, chạy demo hoặc giải thích được.
Tên "prod" trong project là môi trường mô phỏng production trên máy cá nhân.

## English CV entry

**Personal Project — CI/CD and GitOps Delivery Lab**
Python, Flask, PostgreSQL, Docker, Harbor, Kubernetes/K3s, GitLab CI, Kaniko, Argo CD, Kustomize

- Built a three-job GitLab CI pipeline with 14 automated tests, Kaniko image
  publishing to a private TLS-enabled Harbor registry, and digest-based staging
  updates in a separate GitOps repository.
- Configured Argo CD automatic staging reconciliation and manual production
  promotion on a local K3s cluster, with non-root application containers,
  health/readiness probes, resource quotas and persistent PostgreSQL storage.
- Diagnosed a runtime file-permission failure after a successful build, recovered
  through Git revert, and added a non-root dependency import check; documented
  deployment verification, promotion and rollback procedures.

Repository: https://github.com/khimkhum/devops-demo-app
Add the public GitOps URL only after publishing and verifying that repository.

## Bản tiếng Việt

**Dự án cá nhân — CI/CD và GitOps cho ứng dụng Flask**

- Xây pipeline GitLab gồm test, build và cập nhật GitOps; chạy 14 test, build
  bằng Kaniko, lưu image tại Harbor có TLS và triển khai theo digest.
- Cấu hình Argo CD tự đồng bộ staging, promote prod thủ công trên K3s local;
  ứng dụng chạy non-root, có probes, quota và PostgreSQL lưu dữ liệu qua PVC.
- Phân tích lỗi permission làm container crash sau build, khôi phục bằng Git revert
  và bổ sung kiểm tra dependency dưới runtime user; viết runbook vận hành/rollback.

Không ghi "production HA", "enterprise platform", cloud deployment hoặc tỷ lệ uptime
chưa đo. 60/60 request trong bài rollout là kết quả của một thử nghiệm ngắn, không
phải uptime SLA. Không tự đặt phần trăm cải thiện build khi chưa có benchmark.

## Giới thiệu trong 60–90 giây

"Em làm một lab DevOps để hiểu cả đường đi của bản phát hành. Ứng dụng Flask dùng
PostgreSQL, đóng gói multi-stage và chạy bằng user không phải root. Khi push lên
GitLab, Runner chạy 14 test, Kaniko build image rồi push Harbor. Job cuối lấy
digest cập nhật repo GitOps riêng; Argo CD tự deploy staging. Sau khi kiểm tra,
em promote cùng digest sang prod và Sync thủ công.

Một lỗi đáng nhớ là CI build xanh nhưng container mới crash vì package Gunicorn
không đọc được dưới appuser. Em kiểm tra quyền file, revert cấu hình về image tốt,
sửa umask và thêm kiểm tra import dưới runtime user. Em đã demo thay HTML, thấy
staging mới trong khi prod cũ, rồi promote để prod nhận bản mới.

Đây là cluster một node trên WSL, chưa có node HA hoặc backup/restore drill.
Em có README, pipeline, manifest và runbook để giải thích từng bước."

## Câu hỏi thường gặp

| Câu hỏi | Ý chính nên trả lời và chỉ code |
|---|---|
| Vì sao dùng GitOps? | Desired state có history/review; Argo pull/reconcile; CI không cầm kubeconfig |
| Vì sao tách hai repo? | Tách source/build với environment release decision; prod không tự chạy mọi commit |
| Vì sao digest? | Tag đổi đích được; digest giữ đúng image đã kiểm tra; prod dùng cùng artifact |
| Build xanh sao vẫn lỗi? | Build không tự test đầy đủ runtime; umask tạo root700, UID10001 không import được |
| Readiness khác liveness? | ready quyết định nhận traffic; live quyết định restart; DB fail không nên restart app liên tục |
| Rollout giữ service bằng gì? | 2 replicas, maxUnavailable0, surge1, readiness, minReadySeconds và termination drain |
| Synced + Healthy đủ chưa? | Cần đối chiếu revision mới, image digest thực tế, đúng route/môi trường và HTTP readiness |
| PVC có phải backup? | Không; giữ qua Pod recreate nhưng local-path phụ thuộc node, cần backup/restore riêng |
| CI secret xử lý thế nào? | Protected/masked/file variables, robot quyền phù hợp; token không commit/in remote URL |
| Có dùng Docker daemon không? | Runner Docker executor dùng daemon mở job; Kaniko build bên trong không cần daemon API |
| Rollback làm thế nào? | Revert đúng release commit, push, Argo sync; prod manual; dữ liệu/schema không tự rollback |
| Hạn chế lớn nhất? | 1 node, private LAN registry/CA, storage local, chưa network policy/DB least privilege/monitoring |

## Trước khi gửi CV

- Mở GitHub ở cửa sổ đăng xuất để kiểm tra repo public và README mới.
- Kiểm tra ảnh CI, các link docs và lệnh Compose quickstart.
- Giữ attribution Tooplate, mô tả rõ phần tự làm là backend và chuỗi delivery.
- Không đưa token, .env, private key, kubeconfig hay ảnh chứa credential lên repo.
- Tập demo theo [DEMO](DEMO.md), đọc [RUNBOOK](RUNBOOK.md) khi cần chẩn đoán.
