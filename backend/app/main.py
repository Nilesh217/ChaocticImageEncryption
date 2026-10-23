# backend/app/main.py
import base64
import io
import uuid
import numpy as np
import pywt
from PIL import Image
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

try:
    from crypto_engine import ChaoticDRPEEngine
except ImportError:
    from app.crypto_engine import ChaoticDRPEEngine

app = FastAPI(title="Chaotic Wavelet DRPE API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary memory cache for binary file download
CIPHER_CACHE: dict[str, bytes] = {}

@app.post("/api/encrypt")
async def encrypt_pipeline(
    file: UploadFile = File(...),
    x0_log: float = Form(0.123456789),
    r_log: float = Form(3.99),
    x0_sine: float = Form(0.987654321)
):
    try:
        raw_bytes = await file.read()
        pil_img = Image.open(io.BytesIO(raw_bytes)).convert("L")
        img = np.array(pil_img, dtype=np.uint8)
        h, w = img.shape
        total_pixels = h * w

        # 1. 2D Haar DWT: Decomposition into (Ca, Ch, Cv, Cd)
        Ca, (Ch, Cv, Cd) = pywt.dwt2(img, 'haar')
        coeffs = [Ca, Ch, Cv, Cd]
        shapes = [c.shape for c in coeffs]
        coeff_sizes = [c.size for c in coeffs]
        total_coeff_size = sum(coeff_sizes)
        offsets = [0, Ca.size, Ca.size + Ch.size, Ca.size + Ch.size + Cv.size]
        seq_length = max(total_pixels, total_coeff_size)

        # 2. Sequences generation
        log_seq = ChaoticDRPEEngine.generate_logistic(x0_log, r_log, seq_length)
        sine_seq = ChaoticDRPEEngine.generate_sine(x0_sine, seq_length)
        diffusion_seq = ChaoticDRPEEngine.generate_logistic(x0_log + 0.001, r_log, seq_length)

        # 3. DRPE + Complex-Plane Diffusion
        encrypted_coeffs = []
        for coeff, (h_s, w_s), offset in zip(coeffs, shapes, offsets):
            pm1 = ChaoticDRPEEngine.generate_phase_mask(log_seq[offset:], sine_seq[offset:], h_s, w_s)
            pm2 = ChaoticDRPEEngine.generate_phase_mask(sine_seq[offset:], log_seq[offset:], h_s, w_s)
            enc = ChaoticDRPEEngine.drpe_encrypt(coeff, pm1, pm2)
            enc = ChaoticDRPEEngine.apply_diffusion(enc, diffusion_seq[offset:offset + coeff.size])
            encrypted_coeffs.append(enc)

        # 4. Assemble visual preview mosaic
        Ca_enc, Ch_enc, Cv_enc, Cd_enc = encrypted_coeffs
        mosaic_h = shapes[0][0] + shapes[2][0]
        mosaic_w = shapes[0][1] + shapes[1][1]
        vis_mosaic = np.zeros((mosaic_h, mosaic_w), dtype=np.float64)
        vis_mosaic[:shapes[0][0], :shapes[0][1]] = np.abs(Ca_enc)
        vis_mosaic[:shapes[1][0], shapes[0][1]:shapes[0][1] + shapes[1][1]] = np.abs(Ch_enc)
        vis_mosaic[shapes[0][0]:shapes[0][0] + shapes[2][0], :shapes[2][1]] = np.abs(Cv_enc)
        vis_mosaic[shapes[0][0]:shapes[0][0] + shapes[3][0], shapes[2][1]:shapes[2][1] + shapes[3][1]] = np.abs(Cd_enc)
        vis_mosaic = vis_mosaic[:h, :w]

        ptp_val = np.ptp(vis_mosaic)
        vis_norm = (255 * (vis_mosaic - np.min(vis_mosaic)) / (ptp_val + 1e-10)).astype(np.uint8)

        # 5. Pack true payload -> .npz (Ca, Ch, Cv, Cd + shape)
        npz_buffer = io.BytesIO()
        np.savez_compressed(
            npz_buffer, 
            Ca=Ca_enc, Ch=Ch_enc, Cv=Cv_enc, Cd=Cd_enc, 
            original_shape=np.array([h, w])
        )
        file_id = str(uuid.uuid4())
        CIPHER_CACHE[file_id] = npz_buffer.getvalue()

        # 6. Convert preview to base64
        preview_buf = io.BytesIO()
        Image.fromarray(vis_norm).save(preview_buf, format="PNG")
        b64_preview = base64.b64encode(preview_buf.getvalue()).decode("utf-8")

        metrics = ChaoticDRPEEngine.compute_metrics(img, vis_norm)

        return {
            "status": "success",
            "file_id": file_id,
            "preview_base64": f"data:image/png;base64,{b64_preview}",
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{file_id}")
async def download_cipher(file_id: str):
    if file_id not in CIPHER_CACHE:
        raise HTTPException(status_code=404, detail="Payload expired or missing")
    return Response(
        content=CIPHER_CACHE[file_id],
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename=cipher_{file_id[:8]}.npz"}
    )

@app.post("/api/decrypt")
async def decrypt_pipeline(
    file: UploadFile = File(...),
    x0_log: float = Form(0.123456789),
    r_log: float = Form(3.99),
    x0_sine: float = Form(0.987654321)
):
    try:
        contents = await file.read()
        archive = np.load(io.BytesIO(contents))
        Ca_enc, Ch_enc, Cv_enc, Cd_enc = archive['Ca'], archive['Ch'], archive['Cv'], archive['Cd']
        h, w = archive['original_shape']
        total_pixels = h * w

        encrypted = [Ca_enc, Ch_enc, Cv_enc, Cd_enc]
        total_coeff_size = sum(c.size for c in encrypted)
        seq_length = max(total_pixels, total_coeff_size)

        log_seq = ChaoticDRPEEngine.generate_logistic(x0_log, r_log, seq_length)
        sine_seq = ChaoticDRPEEngine.generate_sine(x0_sine, seq_length)
        diffusion_seq = ChaoticDRPEEngine.generate_logistic(x0_log + 0.001, r_log, seq_length)

        offsets = [0, Ca_enc.size, Ca_enc.size + Ch_enc.size, Ca_enc.size + Ch_enc.size + Cv_enc.size]
        
        decrypted = []
        for enc, offset in zip(encrypted, offsets):
            h_s, w_s = enc.shape
            pm1 = ChaoticDRPEEngine.generate_phase_mask(log_seq[offset:], sine_seq[offset:], h_s, w_s)
            pm2 = ChaoticDRPEEngine.generate_phase_mask(sine_seq[offset:], log_seq[offset:], h_s, w_s)
            clean = ChaoticDRPEEngine.remove_diffusion(enc, diffusion_seq[offset:offset + enc.size])
            dec_coeff = ChaoticDRPEEngine.drpe_decrypt(clean, pm1, pm2)
            decrypted.append(dec_coeff)

        reconstructed = pywt.idwt2((decrypted[0], (decrypted[1], decrypted[2], decrypted[3])), 'haar')[:h, :w]
        reconstructed = np.clip(np.round(reconstructed), 0, 255).astype(np.uint8)

        buf = io.BytesIO()
        Image.fromarray(reconstructed).save(buf, format="PNG")
        b64_rec = base64.b64encode(buf.getvalue()).decode("utf-8")

        return {"status": "success", "decrypted_base64": f"data:image/png;base64,{b64_rec}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
