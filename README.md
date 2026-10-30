# ClipMerge — full codebase, local testing, and Docker-free deployment

ClipMerge is a Next.js/TypeScript browser audio editor with an optional Python FastAPI worker for importing audio from YouTube videos that you have permission to download. It supports multiple clips, per-clip timestamps, clip ordering, fade in/out, volume, crossfade or silence between clips, browser preview, and **MP3 (192 kbps) / WAV export**.

**Important:** YouTube does not provide a general-purpose official audio download API. You must have rights and authorization to download the material, and comply with the applicable service terms. Some YouTube URLs cannot be extracted, particularly from hosting-provider IPs. The app works with locally uploaded audio even if YouTube extraction fails.

## What you need

- Node.js **20.9+** and npm (Node 22 LTS recommended)
- Python **3.11+** for the optional import backend
- Git and a GitHub account to deploy
- A Vercel account for the frontend
- **One** Railway or Render account for the Python backend
- **No Docker or Nginx required**
- FFmpeg for local backend processing, either on your PATH or provided by the Python `imageio-ffmpeg` dependency. The deployed Railway setup installs system FFmpeg; Render uses a bundled FFmpeg executable.

No database, login, API key, or paid media API is required for this prototype. Hosting services may charge for compute or impose free-plan limits.

## Folder structure

```
app/                    Next.js page, layout, styles
lib/audio.ts            Web Audio rendering and WAV/MP3 encoding
worker/main.py          FastAPI /extract and /health endpoints
worker/requirements.txt Python dependencies
worker/nixpacks.toml    Railway Nixpacks build
worker/render-build.sh  Render Python build
worker/render.yaml      Render Blueprint configuration
worker/start.sh         Start API on platform PORT
.env.example            Frontend environment variable example
DEPLOY-NO-DOCKER.md     Additional deployment notes
```

## A. Run the frontend locally (Windows/macOS/Linux)

From the project root:

```bash
npm install
cp .env.example .env.local  # Windows PowerShell: Copy-Item .env.example .env.local
npm run dev
```

Open **http://localhost:3000**. You can already upload local audio, trim it, add effects, preview, and export MP3/WAV **without running the backend**.

For a production build check:

```bash
npm run lint
npm run build
npm run start
```

## B. Run the YouTube import backend locally (no Docker)

Open a second terminal:

```bash
cd worker
python -m venv .venv
```

Activate the environment:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- Windows CMD: `.venv\Scripts\activate.bat`
- macOS/Linux: `source .venv/bin/activate`

Then:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8080
```

The default CORS origin is `http://localhost:3000`. If the backend is running on another port, update `.env.local` in the **project root** and restart Next.js:

```env
NEXT_PUBLIC_AUDIO_API_URL=http://localhost:8080
```

Check backend health:

```bash
curl http://127.0.0.1:8080/health
```

Expected: `{"ok":true}`. FastAPI documentation: `http://127.0.0.1:8080/docs`.

**Windows note:** If `python` is unavailable, try `py -3.11` for the virtual environment command. If PowerShell blocks activation, use CMD or run `.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8080` directly. You do not need Docker.

## C. Test the editor end to end

1. Open `http://localhost:3000`.
2. Upload **two** audio files that you own (MP3 or WAV are best for testing).
3. Check that each file appears in **Audio sources** and creates a clip.
4. Change the first clip to `00:02`–`00:08`, the second to `00:01`–`00:06` (use files long enough for those ranges).
5. Set first clip fade in to 1 second, second clip fade out to 1 second.
6. Reorder the clips with the arrow controls.
7. Set crossfade to 1 second, leaving silence gap at 0.
8. Click **Preview mix** and listen.
9. Choose **MP3 · 192 kbps**, click **Export MP3**, and play the downloaded file.
10. Choose **WAV**, click **Export WAV**, and play that file.
11. Test validation: set a clip end timestamp beyond its source duration; the UI should show an error rather than export.
12. Optional authorized YouTube test: paste an eligible URL in the YouTube section, tick the rights confirmation, click **Extract audio from YouTube**, and verify the imported file appears in the source list. YouTube extraction may fail due to source restrictions, terms, or platform blocking even when your app is configured correctly.

A simple backend request example (replace the URL with a video you are authorized to download):

```bash
curl -L -X POST http://127.0.0.1:8080/extract \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://www.youtube.com/watch?v=YOUR_VIDEO_ID","authorized":true}' \
  --output imported.mp3
```

On Windows PowerShell, use `curl.exe` rather than the `curl` alias. A non-200 response will not be a playable MP3; inspect the response status and JSON error first.

## D. Push the project to GitHub

Create an empty repository at https://github.com/new named `clipmerge`. In the project root:

```bash
git init
git add .
git commit -m "Initial ClipMerge app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/clipmerge.git
git push -u origin main
```

Never commit `.env.local`, private credentials, or downloaded media. `.gitignore` excludes local environment files.

## E. Deploy the Python backend on Railway (no Docker)

1. Open https://railway.com, create a project, and choose **Deploy from GitHub repo**.
2. Select the ClipMerge repository.
3. Set **Root Directory** to `/worker`.
4. Choose **Nixpacks** if available. `worker/nixpacks.toml` installs Python 3.11, FFmpeg, and Node 22, then Python dependencies. If Railway only offers Railpack, its build settings differ; configure a build with system FFmpeg or use Render below.
5. Set **Start Command** to `sh start.sh` if not auto-detected.
6. In **Variables**, add `ALLOWED_ORIGINS=https://YOUR-VERCEL-APP.vercel.app,http://localhost:3000`. Replace the placeholder after Vercel deployment.
7. Deploy and generate a public HTTPS domain in **Networking**.
8. Visit `https://YOUR-RAILWAY-DOMAIN/health`. It should return `{"ok":true}`.

Railway injects `PORT`; do not hardcode a public port. No Nginx setup is required.

## F. Alternative: deploy the Python backend on Render (no Docker)

1. Open https://dashboard.render.com and select **New → Web Service**.
2. Connect the ClipMerge GitHub repository.
3. Configure **Root Directory**: `worker`; **Runtime**: Python.
4. Set **Build Command**: `bash render-build.sh`.
5. Set **Start Command**: `sh start.sh`.
6. Set **Health Check Path**: `/health`.
7. Add `ALLOWED_ORIGINS=https://YOUR-VERCEL-APP.vercel.app,http://localhost:3000`.
8. Deploy, then visit `https://YOUR-RENDER-DOMAIN/health`.

Alternatively, use the included `worker/render.yaml` as a starting point for a Render Blueprint. **Caution:** Render's Python environment may not include system `ffprobe`. The bundled `imageio-ffmpeg` executable is passed to yt-dlp, but some post-processing cases may need both `ffmpeg` and `ffprobe`. If extraction fails, prefer Railway with system FFmpeg or install both binaries on Render. Render instances can also sleep or time out depending on plan.

## G. Deploy the Next.js frontend on Vercel

1. Open https://vercel.com/new.
2. Import the same GitHub repository.
3. Keep **Framework Preset: Next.js** and **Root Directory: `.`** (repository root).
4. Add environment variable **`NEXT_PUBLIC_AUDIO_API_URL`** with the **HTTPS Railway or Render worker domain**, e.g. `https://clipmerge-audio.up.railway.app` (no trailing slash).
5. Deploy or redeploy after changing the environment variable.
6. Copy your production Vercel domain and update the worker's `ALLOWED_ORIGINS` variable to include it. Redeploy/restart the worker if needed.
7. Test the live website and backend `/health` endpoint, then repeat the local editor tests.

**CORS troubleshooting:** `ALLOWED_ORIGINS` must contain the exact scheme and hostname of the frontend, no path or trailing slash. Vercel preview deployments may use different origins; explicitly allow the previews you intend to use.

## H. How the system works

- Uploaded audio is decoded and processed entirely in the browser using the Web Audio API. The audio isn't uploaded to the Python backend.
- A YouTube import sends a permitted URL to the FastAPI backend. The backend uses yt-dlp and FFmpeg to generate a temporary MP3, streams it to the browser, and deletes the temporary directory after delivery.
- Trimming, fades, crossfade, mixing, MP3 and WAV encoding occur in the browser, not on Railway/Render.
- A project-settings JSON download contains **only the editing configuration**, not the original audio. There is currently no project JSON re-import feature.

## I. Limits and production-readiness

- The UI limits each uploaded audio file to **100 MB** and combined exports to **30 minutes**; browser RAM and device speed can impose tighter limits.
- YouTube imports have a 120-second backend timeout and size limits; longer videos may fail.
- YouTube changes its site frequently. yt-dlp may need updates and additional JS-runtime dependencies; cloud-provider IPs may be blocked. No guaranteed support for all videos.
- The importer currently has **no user authentication, rate limiting, job queue, or per-user quotas**. Do **not** launch it as an unrestricted public downloader. Add authentication, limits, logging, and abuse protection first.
- The authorization checkbox is a user assertion, **not proof of permission**.
- Temporary media lives on the backend's ephemeral filesystem. The service is not designed for durable file storage.
- `NEXT_PUBLIC_` environment variables are publicly exposed to browsers. Never put secrets in them.
- Crossfade is a basic gain-envelope implementation; it is not loudness-normalized. Export quality should be checked by listening.
- If npm installation/build fails, check Node version, install dependencies, and inspect the first error message. The code was not verified with a full production deployment in this environment.

## J. Common errors

| Error | What to check |
|---|---|
| `YouTube backend not configured` | Set `NEXT_PUBLIC_AUDIO_API_URL` and restart/redeploy Next.js |
| Browser CORS error | Correct `ALLOWED_ORIGINS` to exactly match frontend URL |
| `/health` fails | Check worker deployment logs, startup command, and injected `PORT` |
| YouTube 422 error | URL rights, restrictions, hosting IP blocking, yt-dlp updates, FFmpeg/ffprobe availability |
| Extraction timeout | Source length, backend CPU/RAM, network and 120-second timeout |
| MP3 export slow | Shorten clips; browser-based encoding uses device CPU |
| `npm run build` fails | Confirm Node 20.9+, reinstall dependencies and review TypeScript errors |

## K. Useful commands

```bash
# Frontend dev
npm run dev
# Frontend typecheck
npm run lint
# Frontend production build
npm run build
# Backend health
curl http://127.0.0.1:8080/health
# Backend syntax check
python -m py_compile worker/main.py
```

For additional hosting notes, see `DEPLOY-NO-DOCKER.md`.
