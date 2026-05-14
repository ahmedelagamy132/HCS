from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
import httpx
import os
import json
import tempfile
import asyncio
import base64
import logging

logger = logging.getLogger("ai")
logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/api", tags=["ai"])

OLLAMA_BASE = "http://127.0.0.1:11434"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@router.get("/models")
async def get_models():
    models = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{OLLAMA_BASE}/api/tags")
            if res.status_code == 200:
                data = res.json()
                for m in data.get("models", []):
                    name = m["name"]
                    if any(k in name.lower() for k in ("vl", "vision", "llava", "moondream", "gemma3", "phi3", "bakllava")):
                        cat = "Vision Model"
                    elif "embed" in name:
                        cat = "Embedding Model"
                    else:
                        cat = "Text Generation"
                    models.append({
                        "id": name,
                        "name": name.split(":")[0].upper(),
                        "version": name.split(":")[1] if ":" in name else "latest",
                        "category": cat,
                        "size": f"{m['size'] / 1024**3:.1f} GB",
                        "status": "Running",
                    })
    except Exception:
        pass

    models.append({
        "id": "dlc-gait-pose",
        "name": "GAIT & POSE ANALYSIS",
        "version": "v2.0",
        "category": "Vision Model",
        "size": "2.4 GB",
        "status": "Running",
    })
    return models


class AnalyzeRequest(BaseModel):
    model: str = "llava"
    prompt: str = "Analyze this image."
    image: Optional[str] = None


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    payload = {"model": req.model, "prompt": req.prompt, "stream": False}
    if req.image:
        payload["images"] = [req.image]
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(f"{OLLAMA_BASE}/api/generate", json=payload)
            if not res.is_success:
                detail = f"Ollama error: {res.status_code}"
                try:
                    err_body = res.json()
                    err_msg = err_body.get("error", "")
                    detail = f"Ollama error: {err_msg}" if err_msg else detail
                except Exception:
                    detail = f"Ollama error: {res.status_code} {res.text[:300]}"
                raise HTTPException(status_code=502, detail=detail)
            data = res.json()
            if "error" in data:
                raise HTTPException(status_code=502, detail=f"Ollama error: {data['error']}")
            return {"response": data.get("response", "")}
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Cannot reach Ollama: {e}")


def extract_frames_opencv(video_path, interval=1.0, max_frames=25, resolution="640x480",
                          quality=80, start_time=0.0, end_time=None):
    import cv2
    import numpy as np

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    if end_time is None or end_time <= 0:
        end_time = duration

    start_frame = int(start_time * fps) if fps > 0 else 0
    end_frame = int(end_time * fps) if fps > 0 else total_frames

    w, h = resolution.split("x")
    w, h = int(w), int(h)

    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]

    frames = []
    frame_num = 0
    last_extracted_time = -999.0
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

    while len(frames) < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        current_time = frame_num / fps if fps > 0 else 0

        if frame_num < start_frame:
            frame_num += 1
            continue

        if current_time > end_time:
            break

        if (current_time - last_extracted_time) >= interval:
            frame_resized = cv2.resize(frame, (w, h), interpolation=cv2.INTER_AREA)
            _, buf = cv2.imencode(".jpg", frame_resized, encode_params)
            b64 = base64.b64encode(buf.tobytes()).decode("utf-8")
            frames.append({
                "frame_index": frame_num,
                "timestamp": round(current_time, 2),
                "image_base64": b64,
            })
            last_extracted_time = current_time

        frame_num += 1

    cap.release()
    video_info = {
        "fps": round(fps, 2),
        "total_frames": total_frames,
        "duration": round(duration, 2),
        "extracted_count": len(frames),
        "resolution": f"{w}x{h}",
        "quality": quality,
        "interval": interval,
    }
    return frames, video_info


@router.post("/analyze-video")
async def analyze_video(
    file: UploadFile = File(...),
    model: str = Form("moondream:latest"),
    prompt: str = Form("Analyze this image."),
    frame_interval: float = Form(1.0),
    max_frames: int = Form(25),
    resolution: str = Form("640x480"),
    quality: int = Form(80),
    start_time: float = Form(0.0),
    end_time: float = Form(0.0),
    analysis_mode: str = Form("aggregate"),
):
    tmp_dir = tempfile.mkdtemp(prefix="hcs_frames_")
    safe_name = file.filename.replace(" ", "_")
    input_path = os.path.join(tmp_dir, safe_name)

    contents = await file.read()
    with open(input_path, "wb") as f:
        f.write(contents)

    logger.info(f"Received video: {safe_name} ({len(contents)} bytes), model={model}, "
                f"interval={frame_interval}, max_frames={max_frames}, "
                f"resolution={resolution}, quality={quality}, "
                f"start={start_time}, end={end_time}, mode={analysis_mode}")

    try:
        effective_end = end_time if end_time > 0 else None
        frames, video_info = extract_frames_opencv(
            input_path,
            interval=frame_interval,
            max_frames=max_frames,
            resolution=resolution,
            quality=quality,
            start_time=start_time,
            end_time=effective_end,
        )
    except Exception as e:
        logger.error(f"Frame extraction failed: {e}")
        if os.path.exists(input_path):
            os.remove(input_path)
        raise HTTPException(status_code=500, detail=f"Frame extraction failed: {str(e)}")

    logger.info(f"Extracted {len(frames)} frames from video (info: {video_info})")

    if not frames:
        if os.path.exists(input_path):
            os.remove(input_path)
        raise HTTPException(status_code=400, detail="No frames could be extracted from the video.")

    if analysis_mode == "single":
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "images": [frames[0]["image_base64"]],
        }
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                res = await client.post(f"{OLLAMA_BASE}/api/generate", json=payload)
                if not res.is_success:
                    try:
                        err_body = res.json()
                        err_msg = err_body.get("error", "")
                    except Exception:
                        err_msg = res.text[:300]
                    raise HTTPException(status_code=502, detail=f"Ollama error: {err_msg}")
                data = res.json()
                if "error" in data:
                    raise HTTPException(status_code=502, detail=f"Ollama error: {data['error']}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Cannot reach Ollama: {e}")

        if os.path.exists(input_path):
            os.remove(input_path)

        return {
            "mode": "single",
            "response": data.get("response", ""),
            "video_info": video_info,
            "frames_sent": 1,
        }

    per_frame_results = []
    for i, frame in enumerate(frames):
        frame_prompt = f"[Frame {i+1}/{len(frames)} at {frame['timestamp']}s] {prompt}"
        payload = {
            "model": model,
            "prompt": frame_prompt,
            "stream": False,
            "images": [frame["image_base64"]],
        }
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                res = await client.post(f"{OLLAMA_BASE}/api/generate", json=payload)
                if not res.is_success:
                    try:
                        err_body = res.json()
                        err_msg = err_body.get("error", "")
                    except Exception:
                        err_msg = res.text[:300]
                    per_frame_results.append({
                        "frame_index": frame["frame_index"],
                        "timestamp": frame["timestamp"],
                        "image_base64": frame["image_base64"],
                        "error": err_msg,
                    })
                    continue
                data = res.json()
                if "error" in data:
                    per_frame_results.append({
                        "frame_index": frame["frame_index"],
                        "timestamp": frame["timestamp"],
                        "image_base64": frame["image_base64"],
                        "error": data["error"],
                    })
                    continue
                per_frame_results.append({
                    "frame_index": frame["frame_index"],
                    "timestamp": frame["timestamp"],
                    "image_base64": frame["image_base64"],
                    "response": data.get("response", ""),
                })
        except httpx.RequestError as e:
            per_frame_results.append({
                "frame_index": frame["frame_index"],
                "timestamp": frame["timestamp"],
                "image_base64": frame.get("image_base64", ""),
                "error": str(e),
            })

    successful = [r for r in per_frame_results if "response" in r]
    errors = [r for r in per_frame_results if "error" in r]

    if os.path.exists(input_path):
        os.remove(input_path)

    if analysis_mode == "per_frame":
        return {
            "mode": "per_frame",
            "video_info": video_info,
            "frames_sent": len(frames),
            "results": per_frame_results,
            "errors_count": len(errors),
        }

    combined = ""
    for r in successful:
        ts = r["timestamp"]
        combined += f"\n--- Frame at {ts}s ---\n{r['response'].strip()}\n"

    if errors:
        combined += f"\n[{len(errors)} frame(s) produced errors]"

    first_image = frames[0]["image_base64"] if frames else None

    return {
        "mode": "aggregate",
        "response": combined.strip(),
        "video_info": video_info,
        "frames_sent": len(frames),
        "successful_frames": len(successful),
        "errors_count": len(errors),
        "first_frame_image": first_image,
    }


@router.post("/analyze-direct-dlc")
async def analyze_direct_dlc(file: UploadFile = File(...)):
    testing_dir = os.path.join(ROOT, "testing_videos")
    os.makedirs(testing_dir, exist_ok=True)

    safe_name = f"{int(asyncio.get_event_loop().time() * 1000)}-{file.filename.replace(' ', '_')}"
    input_path = os.path.join(testing_dir, safe_name)

    contents = await file.read()
    with open(input_path, "wb") as f:
        f.write(contents)

    conda_exe = r"C:\Users\ahmed\anaconda3\Scripts\conda.exe"
    script_path = os.path.join(ROOT, "ml_scripts", "analyze_video_dlc.py")
    cmd = f'"{conda_exe}" run -p "E:\\DEEPLABCUT2" python "{script_path}" "{input_path}" --shuffle 4'

    try:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=ROOT,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode("utf-8", errors="replace")

        import re
        match = re.search(r"__DLC_JSON_RESULT__=(.*)", output)
        if not match:
            raise HTTPException(status_code=500, detail="DLC script ran but produced no JSON output.")

        result = json.loads(match.group(1).strip())
        output_vid = result.get("output_video_path", "")
        final_url = ""
        if output_vid:
            rel = output_vid.replace(ROOT, "").replace("\\", "/")
            final_url = rel if rel.startswith("/") else "/" + rel

        return {
            "status": "success",
            "download_url": final_url,
            "behavior_statistics": result.get("behavior_statistics"),
            "total_frames": result.get("total_frames"),
            "fps": result.get("fps"),
            "message": "Analysis complete.",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))