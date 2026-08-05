# ANTIGRAVITY PRO — VOIDMELODY VIENEU RECOVERY & CONTINUATION PROMPT

ROLE: AUTONOMOUS PRINCIPAL ENGINEERING RECOVERY AGENT

Bạn đang tiếp quản công việc tích hợp VieNeu-TTS vào VoidMelody từ một agent trước đã hết token.

Chỉ làm việc trong repository:

```text
https://github.com/voidstation-dev/void-melody
```

Không chỉnh sửa `void-studio`.
Không tạo branch hoặc PR trong `void-studio`.
Không phụ thuộc trạng thái của `void-studio`.

Nguồn VieNeu:

```text
https://github.com/pnnbao97/VieNeu-TTS
```

Mục tiêu:

1. kiểm tra chính xác VoidMelody đã làm tới đâu;
2. xác minh branch, commit, PR, CI, test và persistent state hiện tại;
3. xác định phase nào hoàn thành, phase nào đang dở, phase nào chưa bắt đầu;
4. không làm lại phần đã merge và verified;
5. tiếp tục đúng branch/phase đang dở;
6. hoàn thành toàn bộ plan còn lại;
7. chạy test;
8. independent review;
9. commit;
10. push;
11. tạo hoặc cập nhật Pull Request;
12. merge khi đủ quyền và gate;
13. tiếp tục phase kế tiếp mà không hỏi routine approval.

FULL RECOVERY AND CONTINUATION AUTHORIZATION GRANTED.

---

# 1. TÀI LIỆU BẮT BUỘC

Tìm và đọc toàn bộ các file sau nếu tồn tại:

```text
VOID_MELODY_VIENEU_IMPLEMENTATION_MASTER_PLAN.md
VIENEU_AUTOPILOT_STATE.md
VIENEU_DECISION_LOG.md
VIENEU_BLOCKERS.md
VIENEU_PHASE_*_COMPLETION_REPORT.md
VIENEU_PHASE_*_REVIEW.md
VIENEU_HANDOFF_RECOVERY_REPORT.md
```

Nếu master plan chưa được commit nhưng có trong local workspace, dùng bản local đó.

Thứ tự source of truth:

```text
code hiện tại
→ Git history
→ GitHub PR/CI
→ tests thực tế
→ persistent state files
→ completion reports
→ ghi chú hoặc chat cũ
```

Không tin report nếu code hoặc test thực tế không xác nhận.

---

# 2. RECOVERY AUDIT BẮT BUỘC

Trước khi sửa bất kỳ file nào, chạy:

```bash
git status
git branch --show-current
git remote -v
git fetch --all --prune
git log --oneline --decorate -n 50
git branch -a
git worktree list
git diff
git diff --staged
git stash list
```

Kiểm tra GitHub:

- open PRs;
- draft PRs;
- merged PRs;
- closed-unmerged PRs;
- CI status;
- review status;
- remote VieNeu branches;
- commits chưa merge;
- branch protection;
- auto-merge availability.

Kiểm tra repository:

- working tree sạch hay không;
- uncommitted changes;
- staged changes;
- current branch;
- local main HEAD;
- origin/main HEAD;
- branch phase đang dở;
- merge/rebase/cherry-pick đang dở;
- worktree cũ;
- state files có khớp repository không;
- dependency lockfiles có thay đổi chưa commit không.

Nếu có uncommitted changes:

1. không reset;
2. không checkout đè;
3. inspect toàn bộ diff;
4. xác định phase ownership;
5. backup bằng recovery branch hoặc patch;
6. ghi rõ vào recovery report;
7. tiếp tục trên branch phù hợp.

---

# 3. TẠO RECOVERY REPORT

Tạo hoặc cập nhật:

```text
VIENEU_HANDOFF_RECOVERY_REPORT.md
```

Report phải có:

```text
Repository
Audit timestamp
Local HEAD
origin/main HEAD
Current branch
Working tree state
Existing worktrees
Stashes
Open PRs
Merged PRs
Closed-unmerged PRs
Remote VieNeu branches
Uncommitted changes
Completed phases
Partially completed phases
Not-started phases
Tests verified as passing
Tests failing
Tests not yet run
Architecture deviations
License blockers
Packaging blockers
Exact current blocker
Exact next action
Recommended branch
```

Không bắt đầu implement trước khi recovery report hoàn tất.

---

# 4. QUY TẮC XÁC ĐỊNH TIẾN ĐỘ

Một phase chỉ được coi là DONE khi có đủ:

- code tồn tại;
- acceptance criteria đạt;
- tests bắt buộc pass;
- independent review APPROVE hoặc equivalent verified review;
- commit tồn tại;
- PR đã merge nếu phase yêu cầu merge.

Phân loại:

```text
report nói DONE nhưng code không có
→ NOT DONE

code có nhưng chưa test
→ PARTIAL

test fail
→ PARTIAL

PR đang mở
→ PARTIAL, tiếp tục branch đó

PR đã merge nhưng state cũ
→ DONE, cập nhật state

branch có commit chưa PR
→ PARTIAL, tiếp tục branch đó

phase đã merge và verified
→ không làm lại
```

---

# 5. PRODUCT TARGET

Cấu trúc sản phẩm:

```text
VoidMelody
├── Giọng hiện tại
│   └── giữ nguyên CapCut voice list và workflow hiện có
└── VieNeu
    ├── Giọng nói
    └── Nhân bản giọng
```

Tab Giọng hiện tại phải giữ:

- voice catalog;
- composer;
- speed;
- paste;
- import TXT;
- import folder;
- batch;
- queue;
- retry;
- reparse;
- playback;
- MP3/M4A download;
- existing SQLite jobs;
- existing audio paths;
- startup behavior.

Tab VieNeu hướng tới:

- VieNeu v3 Turbo;
- ONNX CPU INT8 mặc định;
- preset voices;
- Việt-Anh code-switching;
- reading styles;
- experimental emotion cues;
- single synthesis;
- streaming;
- batch;
- voice cloning;
- local model cache;
- offline use sau khi tải model;
- EXE/DMG không cần system Python.

---

# 6. KIẾN TRÚC BẮT BUỘC

Luồng:

```text
VoidMelody frontend
→ existing authenticated local API
→ thin FastAPI adapter
→ ProviderRegistry
→ reusable packages/vieneu-core
→ model manager
→ shared model instance
→ existing artifact/FFmpeg pipeline
```

`packages/vieneu-core` không được import:

- FastAPI;
- SQLAlchemy;
- VoidMelody queue;
- VoidMelody database models;
- Next.js;
- Tauri;
- app-global state.

Không được:

- thay thế tab cũ;
- trộn VieNeu voices vào CapCut catalog;
- tạo FastAPI server thứ hai;
- thêm localhost port mới;
- để React gọi VieNeu trực tiếp;
- load một VieNeu model cho mỗi queue worker;
- bundle model lớn vào installer bản đầu;
- copy unresolved CapCut assets sang phần VieNeu.

---

# 7. RESOURCE POLICY

Bắt buộc:

```text
CapCut concurrency: giữ behavior hiện tại
VieNeu CPU inference concurrency: 1
VieNeu GPU inference concurrency: 1
Model download concurrency: 1
Model load concurrency: 1
Voice cloning concurrency: 1
VieNeu model instance: singleton/shared
Batch parallelism: infer_batch bên trong model
```

Cancellation phải:

- giải phóng semaphore;
- dừng task;
- xóa temp files;
- không để job completed sai;
- không để partial voice profile;
- không block queue vô hạn.

---

# 8. PHASE RECOVERY

Đối chiếu với master plan và xác định trạng thái từng phase:

```text
Phase 0  Baseline và architecture
Phase 1  UI shell
Phase 2  reusable vieneu-core contracts
Phase 3  ProviderRegistry và database migration
Phase 4  runtime probe và model manager
Phase 5  preset voice TTS
Phase 6  styles và emotion cues
Phase 7  streaming preview
Phase 8  voice cloning
Phase 9  batch optimization
Phase 10 packaging EXE/DMG
Phase 11 performance/reliability/security
Phase 12 VOID STUDIO migration readiness
```

Không mặc định bắt đầu Phase 0.

Bắt đầu tại phase đầu tiên chưa đạt DONE criteria.

Nếu branch hiện tại thuộc phase đang dở:

- tiếp tục branch đó;
- không tạo branch mới trùng;
- sync latest main an toàn;
- không force-push.

Nếu phase chưa có branch:

- tạo branch theo master plan.

---

# 9. EXECUTION LOOP

Sau recovery audit, chạy liên tục:

```text
PLAN
→ IMPLEMENT
→ FORMAT
→ LINT
→ TYPECHECK
→ TEST
→ BUILD
→ INDEPENDENT REVIEW
→ FIX FINDINGS
→ RE-TEST
→ RE-REVIEW
→ COMMIT
→ PUSH
→ CREATE/UPDATE PR
→ VERIFY CI
→ MERGE KHI ĐỦ ĐIỀU KIỆN
→ SYNC MAIN
→ NEXT PHASE
```

Không hỏi routine approval.

Reviewer phải khác agent implement.

Tối đa ba review-fix cycles cho cùng blocker.

---

# 10. BRANCH VÀ PR RULES

Nếu branch phase đã tồn tại:

- tiếp tục branch đó;
- fetch và compare với origin;
- rebase/merge main an toàn;
- không force-push;
- giữ commit history rõ ràng.

Nếu branch chưa có:

```text
feat/vieneu-phase-0-baseline
feat/vieneu-phase-1-ui-shell
feat/vieneu-phase-2-core
feat/vieneu-phase-3-provider-registry
feat/vieneu-phase-4-model-manager
feat/vieneu-phase-5-preset-tts
feat/vieneu-phase-6-styles-emotions
feat/vieneu-phase-7-streaming
feat/vieneu-phase-8-voice-cloning
feat/vieneu-phase-9-batch
build/vieneu-phase-10-packaging
test/vieneu-phase-11-reliability
docs/vieneu-phase-12-void-studio-migration
```

Mỗi PR phải ghi:

```text
Scope
Current recovered state
What changed
What was intentionally not changed
Architecture compliance
Tests run
Results
Risks
Known limitations
Migration impact
License impact
Follow-up
```

Một major phase cho một PR.

---

# 11. TEST GATES

Frontend:

- install integrity;
- lint;
- typecheck;
- unit tests;
- component tests;
- accessibility tests;
- production build.

Python:

- formatter;
- lint;
- typecheck;
- unit tests;
- integration tests;
- import-isolation tests;
- migration tests.

Legacy regression:

- existing voice list;
- selected voice;
- create job;
- batch TXT/folder;
- retry;
- delete;
- reparse;
- playback;
- MP3;
- M4A;
- queue recovery;
- old DB upgrade.

VieNeu:

- model absent;
- download;
- interrupted download;
- checksum mismatch;
- low disk;
- corrupted cache;
- offline cached generation;
- singleton model;
- preset voice;
- styles;
- emotion tags;
- short/long text;
- cancel;
- retry;
- streaming stop;
- batch;
- partial failure;
- voice profile create;
- consent;
- preview;
- reuse;
- delete;
- failure cleanup.

Desktop/package:

- Tauri build;
- Windows clean-machine path khi environment hỗ trợ;
- macOS arm64 clean-machine path khi environment hỗ trợ;
- no system Python;
- no system FFmpeg;
- first-run model;
- restart;
- offline use;
- updater preserves cache/profile.

Không được:

- xóa test để pass;
- weaken assertion;
- đổi expected result sai;
- mock toàn bộ end-to-end rồi tuyên bố hoàn thành.

---

# 12. PERSISTENT STATE

Tạo hoặc cập nhật liên tục:

```text
VIENEU_AUTOPILOT_STATE.md
VIENEU_DECISION_LOG.md
VIENEU_BLOCKERS.md
```

State phải ghi:

```text
current phase
phase status
current branch
current worktree
local HEAD
origin/main HEAD
VieNeu source SHA
vieneu-core status
files owned
agents
commands
tests
review verdict
commit SHA
PR number
CI status
merge SHA
blockers
next action
timestamp
```

Repository và GitHub thực tế luôn ưu tiên hơn state cũ.

---

# 13. LICENSING

VieNeu:

- giữ Apache-2.0;
- pin source revision;
- pin model revision;
- attribution;
- third-party notices;
- dependency audit.

Legacy CapCut:

- licensing là gate riêng;
- không coi là cleared;
- không public release unresolved assets;
- hỗ trợ `vieneu-only` build nếu cần.

Không dùng VieNeu license để hợp thức hóa CapCut SDK hoặc Voice.json.

---

# 14. STOP CONDITIONS

Chỉ dừng hỏi khi:

1. thiếu signing secret/certificate;
2. GitHub bắt buộc human merge;
3. cần permission từ rights holder;
4. có destructive migration risk;
5. phải đổi architecture ngoài master plan;
6. cần paid account/resource;
7. security blocker không có safe fix;
8. cùng blocker thất bại sau ba cycles;
9. production release/tag đã sẵn sàng;
10. thiếu hardware/platform bắt buộc để verify.

Khi dừng, tạo:

```text
VIENEU_ANTIGRAVITY_DECISION_PACKET.md
```

Nội dung:

```text
blocker
evidence
current phase
branch
commit
PR
completed work
tests
safe options
recommended option
exact decision required
exact next command
```

---

# 15. PRODUCTION BOUNDARY

Được phép:

- release candidate branch;
- unsigned artifacts;
- packaging tests;
- draft release notes.

Không được tự:

- production tag;
- publish GitHub Release;
- dùng private signing key chưa được cấp;
- public release với unresolved licensing.

Dừng trước production publication.

---

# 16. FINAL REPORT

Khi hoàn thành phần có thể tự động làm, báo:

```text
Recovered starting state
Completed phases
Partially completed phases
Merged PRs
Open PRs
Branches
Commit SHAs
Current main SHA
Tests
Legacy regression
VieNeu feature status
Packaging status
Performance status
Security status
Licensing status
Known limitations
Remaining manual actions
Release blockers
```

---

# 17. START NOW

Bắt đầu ngay:

1. mở repository `void-melody`;
2. đọc master plan và state files;
3. fetch toàn bộ remote state;
4. audit branch, commit, PR và CI;
5. tạo `VIENEU_HANDOFF_RECOVERY_REPORT.md`;
6. xác định exact phase đang dở;
7. tiếp tục branch hiện tại hoặc tạo phase branch;
8. implement;
9. test;
10. independent review;
11. fix;
12. commit;
13. push;
14. tạo/cập nhật PR;
15. merge khi đủ quyền và gate;
16. tiếp tục phase kế tiếp;
17. không hỏi routine approval;
18. dừng trước production publication hoặc explicit stop condition.

FULL RECOVERY AND CONTINUATION AUTHORIZATION GRANTED.
