import cv2
import numpy as np
import pytesseract
from PIL import Image

def sauvola_threshold(gray: np.ndarray, window_size: int = 25, k: float = 0.2) -> np.ndarray:
    gray_f = gray.astype(np.float64)
    mean = cv2.boxFilter(gray_f, ddepth=-1, ksize=(window_size, window_size))
    sq_mean = cv2.boxFilter(gray_f ** 2, ddepth=-1, ksize=(window_size, window_size))
    std = np.sqrt(np.maximum(sq_mean - mean ** 2, 0))
    thresh = mean * (1.0 + k * ((std / 128.0) - 1.0))
    binary = np.where(gray_f > thresh, 255, 0).astype(np.uint8)
    return binary

def preprocess_and_extract(image_source, mode: str = "NutriScan Adaptive Pipeline"):
    pil_image = Image.open(image_source).convert("RGB")
    img = np.array(pil_image)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    if mode == "Raw Image":
        processed = gray
    elif mode == "Global Otsu Thresholding":
        _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif mode == "Sauvola Local Binarization":
        upscaled = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        denoised = cv2.GaussianBlur(upscaled, (3, 3), 0)
        processed = sauvola_threshold(denoised, window_size=25, k=0.2)
    else:
        upscaled = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        denoised = cv2.bilateralFilter(upscaled, 9, 75, 75)
        processed = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
        )

    config = r"--oem 3 --psm 6"
    extracted_text = pytesseract.image_to_string(processed, config=config).strip()

    # Calculate average OCR word confidence
    data = pytesseract.image_to_data(processed, config=config, output_type=pytesseract.Output.DICT)
    confs = [int(c) for c in data["conf"] if str(c).isdigit() and int(c) >= 0]
    avg_conf = round(sum(confs) / len(confs), 1) if confs else 0.0

    return extracted_text, processed, avg_conf
