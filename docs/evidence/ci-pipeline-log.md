# หลักฐาน CI pipeline ที่ทำงานจริง

> ดึงจาก GitHub Actions run จริงด้วย `gh run view` ไม่ใช่พิมพ์เอง
> ดูสดได้ที่ https://github.com/kit-sinlapasa/sme-inventory-system/actions/workflows/ci.yml

## Run ล่าสุดบน `main`

```

✓ main CI · 32799271168
Triggered via push about 6 minutes ago

JOBS
✓ backend-test in 1m40s (ID 97656807038)
✓ frontend-build in 15s (ID 97656807173)

ANNOTATIONS
! Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout@v4, actions/setup-python@v5. For more information see: https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/
backend-test: .github#2

! Node.js 20 is deprecated. The following actions target Node.js 20 but are being forced to run on Node.js 24: actions/checkout@v4, actions/setup-node@v4. For more information see: https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/
frontend-build: .github#2


For more information about a job, try: gh run view --job=<job-id>
View this run on GitHub: https://github.com/kit-sinlapasa/sme-inventory-system/actions/runs/32799271168
```

## Log จริงของ job `backend-test`

```
backend-test	Run actions/checkout@v4	﻿2026-08-25T01:53:54.2023408Z Node 20 is being deprecated. This workflow is running with Node 24 by default. If you need to temporarily use Node 20, you can set the ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION=true environment variable. For more information see: https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.2031252Z ##[group]Run actions/checkout@v4
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.2031713Z with:
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.2031968Z   repository: kit-sinlapasa/sme-inventory-system
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.2097603Z   token: ***
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.2097849Z   ssh-strict: true
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.2098070Z   ssh-user: git
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.2098290Z   persist-credentials: true
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.2098831Z   clean: true
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.2099061Z   sparse-checkout-cone-mode: true
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.2099318Z   fetch-depth: 1
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.2099515Z   fetch-tags: false
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.2099722Z   show-progress: true
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.2099967Z   lfs: false
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.2100187Z   submodules: false
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.2100491Z   set-safe-directory: true
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.2100767Z   allow-unsafe-pr-checkout: false
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.2102197Z ##[endgroup]
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.3141045Z Syncing repository: kit-sinlapasa/sme-inventory-system
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.3143006Z ##[group]Getting Git version info
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.3143782Z Working directory is '/home/runner/work/sme-inventory-system/sme-inventory-system'
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.3144807Z [command]/usr/bin/git version
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.3191076Z git version 2.55.0
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.3214396Z ##[endgroup]
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.3232367Z Temporarily overriding HOME='/home/runner/work/_temp/f9c94c2b-383d-4d1e-902f-afce87b2cddc' before making global git config changes
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.3234008Z Adding repository directory to the temporary git global config as a safe directory
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.3239475Z [command]/usr/bin/git config --global --add safe.directory /home/runner/work/sme-inventory-system/sme-inventory-system
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.3301157Z Deleting the contents of '/home/runner/work/sme-inventory-system/sme-inventory-system'
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.3305826Z ##[group]Initializing the repository
backend-test	Run actions/checkout@v4	2026-08-25T01:53:54.3312272Z [command]/usr/bin/git init /home/runner/work/sme-inventory-system/sme-inventory-system
```
