# Deploying Lunrea

Think of it as two buildings: the **API** (Flask + PostgreSQL, the vault) and the **PWA** (the React front door people install). Set up storage and deploy the API first, because the PWA needs its address.

## 1. Push to GitHub

```bash
cd ~/Lunrea
git init && git add . && git commit -m "Lunrea PWA ready"
# create an empty repo on github.com, then:
git remote add origin https://github.com/<you>/lunrea.git
git push -u origin main
```

`.gitignore` already keeps `.env`, `venv/`, `uploads/` and `node_modules/` out.

## 2. Create the media bucket (Cloudflare R2)

Think of R2 as a warehouse for photos, separate from the server, so redeploys never wipe them.

1. Sign up at dash.cloudflare.com (the free plan works; R2 asks for a payment card on file, and its free allowance is 10 GB of storage. Check Cloudflare's current pricing page).
2. **R2 Object Storage > Create bucket**, name it `lunrea-media`. Leave it **private** (do not enable public access: Lunrea checks who you are before serving each file).
3. **R2 > Manage API tokens > Create API token**, permission **Object Read & Write**, limited to that bucket. Copy the **Access Key ID** and **Secret Access Key** (shown once).
4. Your **Account ID** is on the R2 overview page.

## 3. Deploy the API on Render

1. render.com, **New > Blueprint**, pick your repo. It reads `render.yaml` and creates the web service and the PostgreSQL database.
2. Fill the prompted variables: `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET` (`lunrea-media`). Leave `CORS_ORIGINS` for step 5.
3. Wait for the deploy. On every start it runs `flask db upgrade` (your migrations) and then `gunicorn`.
4. Open `https://<your-api>.onrender.com/`. You should see `{"application": "Lunrea", ...}`.

Notes:
- `SECRET_KEY` and `JWT_SECRET_KEY` are generated for you.
- Without the four `R2_*` variables the API falls back to local disk, which is wiped on each redeploy. Always set them in production.
- Free Render web services sleep when idle, so the first request after a pause can take about a minute. Render's free database tier has time limits, so check its current terms before relying on it for real memories.
- Photos you already uploaded locally keep working in development. To move them to R2, upload them again, or ask me for a one-off migration script.

## 4. Deploy the PWA on Netlify

1. netlify.com, **Add new site > Import from Git**, pick the same repo. `frontend/netlify.toml` sets the build.
2. **Site settings > Environment variables**, add:
   `VITE_API_URL = https://<your-api>.onrender.com` (no trailing slash)
3. Deploy. Your site is at `https://<name>.netlify.app`.

(Vercel and Cloudflare Pages also work: root directory `frontend`, build `npm run build`, output `dist`, same `VITE_API_URL` variable.)

## 5. Connect them

In Render, on the `lunrea-api` service, set `CORS_ORIGINS = https://<name>.netlify.app` and redeploy. Until you do, the browser blocks the PWA from calling the API.

## 6. Install it

- **Android/Chrome:** open the site, tap **Install Lunrea** (or menu > Install app).
- **iPhone/Safari:** Share > **Add to Home Screen**.
- **Desktop Chrome/Edge:** install icon in the address bar.

## Checks

- Chrome DevTools > Application > Manifest shows no errors, and Service Workers shows `sw.js` activated.
- Register a user, set a PIN, create an album, delete it. Its chapters now delete with it.
- The camera and microphone need HTTPS, which Netlify and Render provide.

## Local development (unchanged)

```bash
cd ~/Lunrea && source venv/bin/activate && pip install -r requirements.txt
flask --app run.py db upgrade && python3 run.py
cd frontend && npm install && npm run dev
```
