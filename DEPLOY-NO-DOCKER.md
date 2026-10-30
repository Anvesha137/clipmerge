# ClipMerge: Docker-free deployment

## Railway (recommended)

1. Push this repository to GitHub.
2. Railway → New Project → Deploy from GitHub repo.
3. In service Settings set **Root Directory** to `/worker`.
4. In Settings → Build choose **Nixpacks** (not Dockerfile). The included `worker/nixpacks.toml` installs Python, FFmpeg and Node.
5. In service Variables set `ALLOWED_ORIGINS=https://YOUR-FRONTEND.vercel.app,http://localhost:3000`.
6. In Settings → Networking generate a public domain; Railway supplies `PORT` automatically.
7. Test `https://YOUR-RAILWAY-DOMAIN/health` → `{"ok":true}`.
8. On Vercel set `NEXT_PUBLIC_AUDIO_API_URL=https://YOUR-RAILWAY-DOMAIN` (no trailing slash), then redeploy the frontend.

If Railway doesn't detect the Nixpacks config, explicitly set config file path to `nixpacks.toml` and builder to Nixpacks. If your Railway workspace only supports Railpack, choose a compatible builder or adapt the build to install FFmpeg and Python.

## Render (alternative)

1. Push repository to GitHub.
2. Render → New → Web Service → connect GitHub repo.
3. Set **Root Directory** `worker`, **Language** Python, **Build Command** `bash render-build.sh`, **Start Command** `sh start.sh`.
4. Set `ALLOWED_ORIGINS=https://YOUR-FRONTEND.vercel.app,http://localhost:3000`.
5. Choose an instance plan with enough memory and CPU for audio imports.
6. Deploy and test `https://YOUR-RENDER-DOMAIN/health`.
7. Set Vercel `NEXT_PUBLIC_AUDIO_API_URL=https://YOUR-RENDER-DOMAIN` and redeploy.

Render uses imageio-ffmpeg's packaged FFmpeg binary. Some yt-dlp postprocessing scenarios may also need `ffprobe`; test an authorized video end-to-end before production. Render `render.yaml` is included for blueprint deployments but manual settings above are sufficient.

## Local without Docker

Install Python 3.11+ and Node 20+.

Terminal A:
```
cd worker
python -m venv .venv
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8080
```
Terminal B (project root):
```
# create .env.local containing NEXT_PUBLIC_AUDIO_API_URL=http://localhost:8080
npm install
npm run dev
```

## Git commands
```
git init
git add .
git commit -m "ClipMerge Docker-free deployment"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/clipmerge.git
git push -u origin main
```
Create the empty GitHub repository before pushing. If the repo already exists, skip `git init` and `git remote add origin` as appropriate.

## Security / limitations

- Only import videos you have permission and rights to download, consistent with applicable terms.
- The backend has no authentication, abuse prevention, or rate limits: do not expose it as a public unrestricted downloader.
- YouTube may block data-center IPs or require updated yt-dlp, JavaScript support, or authentication. No hosting provider guarantees extraction.
- File processing is synchronous and has a 120-second timeout; add a queue, job authentication, limits, and observability before scaling.
- Allow CORS for exact Vercel origins, including any preview domain you intentionally use.
- No Nginx is needed: Render/Railway terminate HTTPS and proxy traffic to the app's `PORT`.
