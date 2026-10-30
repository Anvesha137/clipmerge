"""Authorized-video audio import service. Deploy separately from Vercel."""
import os, re, tempfile, subprocess
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.background import BackgroundTask
import shutil
import imageio_ffmpeg

app=FastAPI(title="ClipMerge authorized audio importer")
origins=[x.strip() for x in os.getenv('ALLOWED_ORIGINS','http://localhost:3000').split(',') if x.strip()]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=['POST','GET'],allow_headers=['Content-Type'])
class ImportRequest(BaseModel):
    url:str
    authorized:bool=False

@app.get('/health')
def health():return {'ok':True}

@app.post('/extract')
def extract(req:ImportRequest):
    if not req.authorized:raise HTTPException(403,'You must have rights or permission to download this audio.')
    u=urlparse(req.url)
    if u.scheme!='https' or u.hostname not in {'youtube.com','www.youtube.com','m.youtube.com','youtu.be','www.youtu.be'} or u.username or u.password:
        raise HTTPException(400,'Only HTTPS YouTube video URLs are accepted.')
    if len(req.url)>500:raise HTTPException(400,'URL too long.')
    directory=tempfile.mkdtemp(prefix='clipmerge-')
    out=str(Path(directory)/'audio.%(ext)s')
    try:
        command=['yt-dlp','--ffmpeg-location',shutil.which('ffmpeg') or imageio_ffmpeg.get_ffmpeg_exe(),'--no-playlist','--no-warnings','--no-progress','--max-filesize','25M','--socket-timeout','15','--retries','1','--extract-audio','--audio-format','mp3','--audio-quality','192K','--output',out,'--',req.url]
        result=subprocess.run(command,capture_output=True,text=True,timeout=120,check=False)
        if result.returncode!=0:raise HTTPException(422,'Could not import this video. It may be unavailable, restricted, or unsupported.')
        matches=list(Path(directory).glob('*.mp3'))
        if not matches:raise HTTPException(422,'No MP3 audio was produced.')
        file=matches[0]
        if file.stat().st_size>35*1024*1024:raise HTTPException(413,'Audio exceeds the 35 MB import limit.')
        return FileResponse(file,media_type='audio/mpeg',filename='youtube-audio.mp3',background=BackgroundTask(shutil.rmtree,directory,ignore_errors=True))
    except subprocess.TimeoutExpired:
        shutil.rmtree(directory, ignore_errors=True)
        raise HTTPException(504,'Audio extraction timed out.')
    finally:
        # FileResponse is streamed after returning; successful files are removed by BackgroundTask.
        if not list(Path(directory).glob('*.mp3')):shutil.rmtree(directory,ignore_errors=True)
