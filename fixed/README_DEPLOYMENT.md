# Deployment Guide — Streamlit Community Cloud + MongoDB Atlas

## What was actually broken (and fixed)

| # | File | Problem | Fix |
|---|------|---------|-----|
| 1 | `requirements.txt.txt` | Wrong filename — Streamlit Cloud won't recognize it | Renamed to `requirements.txt`, removed unused `pyperclip` |
| 2 | `database.py` | MongoDB URI hardcoded to `mongodb://localhost:27017/` — only works on your own machine | Now reads `MONGODB_URI` from `st.secrets` (Cloud) or env var (local), with a clear error if missing |
| 3 | `encryption.py` | **Real bug**: the Fernet key was being base64-decoded *twice*. `Fernet.generate_key()` already returns an encoded key — decoding it again either crashes (`Incorrect padding`) or silently corrupts the key | Key is now used as-is (encoded to bytes only, no extra decode) |
| 4 | `encryption.py` | A working fallback Fernet key was hardcoded directly in the source file — anyone with repo access (e.g. on public GitHub) could decrypt every password ever stored | Removed entirely. App now refuses to start (`st.stop()`) until you set a real key via secrets or env var |
| 5 | `clipboard_manager.py` | Used `pyperclip`, which copies to the **server's** OS clipboard. Streamlit Cloud is a headless container with no clipboard — this would crash with `PyperclipException` | Rewritten to copy into the **visitor's browser** clipboard via JavaScript (`navigator.clipboard`), which works the same locally and deployed |
| 6 | `demo.py` | "Copy Password" button ran a `time.sleep(1)` loop for a countdown — blocks the entire server thread on every click, for every user, on a shared deployment | Removed the blocking loop; success message shown instantly instead |
| 7 | `scripts/backup_database.py` | Hardcoded `mongodb://localhost:27017/password_manager` for `mongodump` | Now reuses the same resolved connection string as the rest of the app (still a local-only utility script — see note below) |
| 8 | *(new)* `.gitignore` | Nothing prevented committing real secrets | Added — excludes `.streamlit/secrets.toml` and `.env` |
| 9 | *(new)* `.streamlit/secrets.toml.example` | No template existed | Added as a reference; **never commit the real `secrets.toml`** |

I tested all of this by actually running `streamlit run demo.py` headlessly and confirming it boots with HTTP 200 and no import/runtime errors, and by round-tripping the encryption fix (`encrypt → decrypt` produces the original password).

## What I did NOT change

- `demo.py`'s overall structure, auth flow, and 2FA logic — these were already a normal, working Streamlit app and didn't need restructuring.
- A few other small `time.sleep(1)`/`time.sleep(2)` calls tied to specific UI transitions (e.g. account-lockout messages) — these are short and action-triggered rather than per-click blocking loops, so I left them alone.

## ⚠️ Security note (please read)

This app encrypts passwords at rest with Fernet (symmetric encryption) and hashes user account passwords with bcrypt — both reasonable choices. But before putting *real* passwords into this and exposing it on a public `*.streamlit.app` URL, be aware of a few things I can't fix for you because they're architectural/judgment calls, not bugs:

- **Anyone with your `ENCRYPTION_KEY` can decrypt every stored password.** Treat that key like a master password. Losing it means losing access to everything; leaking it means everything is exposed.
- **Streamlit Community Cloud apps are public by default** unless you enable viewer authentication (a paid feature) or otherwise restrict access. A typo'd or guessed URL could expose your login screen to strangers.
- There's no rate-limiting/IP-based lockout beyond what's already in the app's own `MAX_ATTEMPTS` logic, and no audit logging of access.
- I'd suggest treating this as a personal/learning project rather than a place to store your actual banking or email passwords, unless you (or someone with security expertise) reviews it more thoroughly first.

I'm happy to help further if you want to discuss any of these trade-offs, but I won't write code specifically intended to weaken or bypass any of this app's security mechanisms.

---

## Step-by-step deployment

### 1. Set up MongoDB Atlas (free tier)

1. Sign up at https://www.mongodb.com/cloud/atlas/register
2. Create a free **M0** cluster
3. **Database Access** → add a database user (save the username/password)
4. **Network Access** → add IP `0.0.0.0/0` (Streamlit Cloud has no fixed IP)
5. **Connect** → "Drivers" → copy the connection string:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
6. Insert the database name before the `?`:
   ```
   mongodb+srv://myuser:mypass@cluster0.xxxxx.mongodb.net/password_manager?retryWrites=true&w=majority
   ```

### 2. Generate your encryption key (do this locally, once)

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Save this somewhere safe (e.g. a password manager you already trust). You'll paste it into Streamlit Cloud's secrets — never into a file you commit to GitHub.

### 3. Push to GitHub

```bash
git init
git add .
git commit -m "Fix deployment issues for Streamlit Cloud"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

(`.gitignore` already excludes `.streamlit/secrets.toml` and `.env`, so your real secrets won't accidentally get pushed.)

### 4. Deploy on Streamlit Community Cloud

1. Go to https://share.streamlit.io → "New app"
2. Pick your repo, branch `main`, main file path `demo.py`
3. Before clicking deploy (or right after, via **Settings → Secrets**), paste:
   ```toml
   MONGODB_URI = "mongodb+srv://myuser:mypass@cluster0.xxxxx.mongodb.net/password_manager?retryWrites=true&w=majority"
   ENCRYPTION_KEY = "the-key-you-generated-in-step-2"
   ```
4. Deploy.

### 5. First-time setup after deploying

Visit your deployed app once, then go to the admin creation page to create your first admin user — see `pages/create_admin.py` for the exact flow already built into the app.

### Local development

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit .streamlit/secrets.toml with your real Atlas URI + encryption key
pip install -r requirements.txt
streamlit run demo.py
```
