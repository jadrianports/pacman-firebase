# Cloud Functions Deploy Checklist (Manual Console Model)

> **Deploy model:** Both functions (`submit_score`, `get_leaderboard`) are **Gen2 Cloud
> Functions / Cloud Run**, deployed **manually via the Google Cloud Console** in region
> **`asia-southeast1`**. They use the raw `functions_framework` + `firebase_admin` stack —
> **NOT** the `firebase-functions` Python SDK. That means secrets, max-instances, and deploy
> config are set through the **Cloud Run / GCF Gen2 runtime controls in the Console**, never
> via SDK decorators (`@https_fn.on_request(secrets=[...])` / `SecretParam` do **not** apply
> to this project).

**Live function URLs (asia-southeast1):**

| Function | URL |
|----------|-----|
| `submit_score` | `https://pacman-991339031546.asia-southeast1.run.app` |
| `get_leaderboard` | `https://get-leaderboard-991339031546.asia-southeast1.run.app` |

**Runtime env vars the code reads (read at CALL time, never at import):**

| Env var | Function(s) | Source | Default behavior |
|---------|-------------|--------|------------------|
| `LEADERBOARD_HMAC_SECRET` | both | Secret Manager secret `leaderboard-hmac-secret` (version `latest`), referenced as env var | Required for signature verification (`leaderboard_crypto.verify_signature`) |
| `REQUIRE_SIGNATURE` | `submit_score` | Plain runtime env var | `false` during the P4→P5 grace window; flip to `true` only after Phase 5 ships |

---

## SECRET HANDLING — READ FIRST

> **The HMAC secret VALUE is NEVER committed to git.** This file documents only the
> *procedure* to generate and store it. Do **not** paste a generated secret value into this
> file, into source, or into any committed artifact.
>
> **Phase 5 shared-secret seam:** the Phase 5 signed client build embeds the **identical**
> secret string so its HMAC signatures verify server-side. After you generate the value in
> Step 1, **keep it safe** (e.g. in a password manager) — Phase 5 will need the exact same
> string. If the value is lost, you must regenerate it AND re-issue it to both functions AND
> the Phase 5 client build (they must always match).

---

## Ordered Deploy Checklist

### Step 1 — Create the Secret Manager secret `leaderboard-hmac-secret`

Generate a 32-byte random hex value locally using the Python stdlib (do **not** invent one
by hand, do **not** commit it):

```bash
# Generates a 64-char hex string. Keep the OUTPUT safe; it is NOT stored in git.
.venv/Scripts/python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Then, in **Console → Security → Secret Manager → Create secret**:

- **Name:** `leaderboard-hmac-secret`
- **Secret value:** paste the hex string printed above
- Create the secret (a first version `1` / `latest` is created automatically).

The secret value lives ONLY in Secret Manager (and your safe copy for Phase 5). It is not in
git, not in the function config surface, and must never be logged.

### Step 2 — Reference the secret as env var `LEADERBOARD_HMAC_SECRET` on BOTH functions

For **each** of `submit_score` and `get_leaderboard`:

- Console → the function → **Edit** → **Runtime, build, connections and security settings** →
  **Variables & Secrets** (Secrets section) → **Reference a secret**:
  - **Environment variable name:** `LEADERBOARD_HMAC_SECRET`
  - **Secret:** `leaderboard-hmac-secret`
  - **Version:** `latest`
  - **Exposed as:** environment variable (NOT mounted as a file)
- When prompted, **grant** the function's runtime service account the role
  `roles/secretmanager.secretAccessor` (least privilege — only this secret). The Console
  offers this grant inline when you add the reference.

The code reads `os.environ["LEADERBOARD_HMAC_SECRET"]` at call time, so the reference must
exist on **both** functions before they verify signatures.

### Step 3 — Set the grace flag `REQUIRE_SIGNATURE=false` on `submit_score`

- Console → `submit_score` → **Edit** → **Variables & Secrets** → **Runtime environment
  variables** → add:
  - **Name:** `REQUIRE_SIGNATURE`
  - **Value:** `false`

This is a **plain** env var (not a secret). `false` is the P4→P5 grace setting: the server
**accepts unsigned** submissions (and logs them) but **always rejects an invalid signature**.
Flip `REQUIRE_SIGNATURE` to `true` **only after** the Phase 5 signed client has shipped and
friends have updated their exe (D-02) — flipping early would reject every already-shipped
unsigned client.

### Step 4 — Set Maximum number of instances to 3–5 on BOTH functions (D-11)

For **each** of `submit_score` and `get_leaderboard`:

- Console → the function → **Edit** → **Runtime, build, connections and security settings** →
  **Runtime** → **Maximum number of instances** → set to **3–5**.

The Gen2 default is **100** (effectively uncapped for a friends-scale board) — that is the
flood/cost blast-radius D-11 caps. A small max-instances bound (3–5) is the relevant lever;
no per-request rate limiting is added in this phase (accepted residual).

### Step 5 — Create the weekly composite index `week_id ASC, score DESC`

The weekly read query in `get_leaderboard`
(`where("week_id","==",cur).order_by("score", DESCENDING)`) requires a Firestore **composite
index** on the `weekly` collection:

- **Collection:** `weekly`
- **Fields:** `week_id` **ASC**, then `score` **DESC**

Create it via **Console → Firestore → Indexes → Composite → Create index**, OR follow the
**auto-generated link** Firestore emits in the error/logs on the first weekly query. **Wait
for the index status to become `Enabled`** before relying on the weekly board.

### Step 6 — Redeploy BOTH functions from the updated source (asia-southeast1)

For **each** of `submit_score` and `get_leaderboard`:

- Console → the function → **Edit** → deploy from the updated source (the hardened Plan 01–03
  code) in **`asia-southeast1`** → **Deploy** and wait for the revision to go live.

Both functions must be redeployed so the new HMAC/grace/weekly code is actually serving.

---

## Verify After Deploy (manual smoke checks)

Run these against the live URLs once Steps 1–6 are complete and the index is `Enabled`.
Replace `<URL>` with the function URLs above. (These verify behavior only — they never reveal
the secret.)

1. **Unsigned submission accepted under grace** (`REQUIRE_SIGNATURE=false`):
   a `POST` to `submit_score` with a valid body and **no** `signature` field returns `200`
   (and the server logs `unsigned submission accepted (grace period)`).

2. **Invalid signature rejected** (always, even in grace):
   a `POST` to `submit_score` with a **bogus** `signature` field returns `401`
   (`{"success": false, "error": "Invalid signature"}`).

3. **Param-less weekly board returns:**
   a `GET` to `get_leaderboard` with **no** `scope` param returns `200` with the current
   week's board — an `entries` array of `{initials, score}` objects only (no `machine_id`,
   no `week_id`). This is the index-backed weekly path (default `scope=week`).

If the param-less GET errors with a missing-index message, the composite index from Step 5 is
not yet `Enabled` — wait for it to finish building and retry.

---

## Actual deploy path used (Cloud Run via gcloud — faster than the Console clicks above)

> **Recorded 2026-06-19 from the live Phase 4 deploy.** The two functions are **Cloud Run
> services** (`pacman` = `submit_score` code, `get-leaderboard` = `get_leaderboard` code), so
> the Console steps above map 1:1 to `gcloud run deploy` from **Cloud Shell**. This is the
> real, faster path; the Console click-path above remains an equivalent fallback. The runtime
> service account is `991339031546-compute@developer.gserviceaccount.com` (granted
> `roles/secretmanager.secretAccessor` on `leaderboard-hmac-secret`).

```bash
# submit_score service (pacman): secret + grace flag + flood cap
gcloud run deploy pacman \
  --source=cloud_functions/submit_score --function=submit_score \
  --region=asia-southeast1 --allow-unauthenticated --max-instances=5 \
  --update-secrets=LEADERBOARD_HMAC_SECRET=leaderboard-hmac-secret:latest \
  --update-env-vars=REQUIRE_SIGNATURE=false

# get_leaderboard service: secret + flood cap (no REQUIRE_SIGNATURE env var)
gcloud run deploy get-leaderboard \
  --source=cloud_functions/get_leaderboard --function=get_leaderboard \
  --region=asia-southeast1 --allow-unauthenticated --max-instances=5 \
  --update-secrets=LEADERBOARD_HMAC_SECRET=leaderboard-hmac-secret:latest
```

The weekly composite index (Step 5) is still created via Console → Firestore → Indexes (or the
auto-link). Live revisions from this deploy: `pacman-00005-7rk` and `get-leaderboard-00003-fzk`,
each serving 100% traffic; `weekly` index id `CICAgOjXh4EK` (Enabled).

---

## Notes

- **No CLI in this deploy model** — every operation above is a Console action. There is no
  in-repo deploy artifact and no `firebase deploy` step for these functions.
- **Both functions share `leaderboard_crypto.py`** (byte-identical copy in each function dir),
  so both read `LEADERBOARD_HMAC_SECRET` the same way.
- **Never log or echo the secret value.** The grace-accept log line truncates `machine_id`
  and never includes the secret.
