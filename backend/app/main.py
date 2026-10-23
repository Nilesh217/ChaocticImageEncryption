# backend/app/main.py
import io
import numpy as np
from PIL import Image
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI(title="Chaotic Image Encryption API")

# Configure CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def generate_logistic_keystream(x0: float, r: float, size: int) -> np.ndarray:
    """Generates an 8-bit keystream from Logistic Map: x_{n+1} = r * x_n * (1 - x_n)."""
    # Discard transient iterations
    for _ in range(500):
        x0 = r * x0 * (1.0 - x0)
    
    seq = np.empty(size, dtype=np.float64)
    x = x0
    for i in range(size):
        x = r * x * (1.0 - x)
        seq[i] = x
    return np.floor(seq * 256).astype(np.uint8)

@app.post("/api/process")
async def process_image(
    file: UploadFile = File(...),
    action: str = Form("encrypt"),  # "encrypt" or "decrypt"
    x0: float = Form(...),
    r: float = Form(...)
):
    if not (0.0 < x0 < 1.0):
        raise HTTPException(status_code=400, detail="Seed x0 must be in range (0, 1)")
    if not (3.57 <= r <= 4.0):
        raise HTTPException(status_code=400, detail="Parameter r must be in range [3.57, 4.0] for chaotic behavior")

    try:
        contents = await file.read()
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
        img_arr = np.array(pil_image, dtype=np.uint8)
        
        flat_arr = img_arr.flatten()
        keystream = generate_logistic_keystream(x0, r, flat_arr.size)
        
        # Symmetric bitwise diffusion (XOR is self-inverting)
        processed_flat = np.bitwise_xor(flat_arr, keystream)
        processed_arr = processed_flat.reshape(img_arr.shape)
        
        # Write output back to memory buffer as lossless PNG
        out_img = Image.fromarray(processed_arr)
        buf = io.BytesIO()
        out_img.save(buf, format="PNG")
        buf.seek(0)
        
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
