import io
import time
import numpy as np
import pywt
from scipy import fft
from PIL import Image

class ChaoticDRPEEngine:
    @staticmethod
    def generate_logistic(x0: float, r: float, length: int, discard: int = 1000) -> np.ndarray:
        """
        Generates chaotic logistic map sequence: x_{n+1} = r * x_n * (1 - x_n).
        Discards initial transient iterations to ensure chaotic regime.
        """
        total_len = length + discard
        seq = np.empty(total_len, dtype=np.float64)
        seq[0] = x0
        for i in range(1, total_len):
            x = r * seq[i - 1] * (1.0 - seq[i - 1])
            # Clamp to prevent numeric divergence out of (0, 1)
            seq[i] = min(max(x, 1e-12), 1.0 - 1e-12)
        return seq[discard:]

    @staticmethod
    def generate_sine(x0: float, length: int, discard: int = 1000) -> np.ndarray:
        """
        Generates chaotic sine map sequence: x_{n+1} = sin(pi * x_n).
        Discards initial transient iterations.
        """
        total_len = length + discard
        seq = np.empty(total_len, dtype=np.float64)
        seq[0] = x0
        for i in range(1, total_len):
            x = np.sin(np.pi * seq[i - 1])
            seq[i] = min(max(x, 1e-12), 1.0 - 1e-12)
        return seq[discard:]

    @staticmethod
    def generate_phase_mask(seq1: np.ndarray, seq2: np.ndarray, h: int, w: int) -> np.ndarray:
        """Generates 2D complex exponential phase mask exp(j * 2 * pi * theta)."""
        p1 = seq1[:h * w].reshape((h, w))
        p2 = seq2[:h * w].reshape((h, w))
        combined = (p1 + p2 + p1 * p2) % 1.0
        return np.exp(1j * 2.0 * np.pi * combined)

    @staticmethod
    def drpe_encrypt(coeff: np.ndarray, pm1: np.ndarray, pm2: np.ndarray) -> np.ndarray:
        """Double Random Phase Encoding (DRPE) in the 2D-FFT domain."""
        step1 = fft.ifft2(fft.fft2(coeff) * pm1)
        return fft.ifft2(fft.fft2(step1) * pm2)

    @staticmethod
    def drpe_decrypt(encrypted: np.ndarray, pm1: np.ndarray, pm2: np.ndarray) -> np.ndarray:
        """Exact inverse DRPE with conjugate phase masks."""
        step1 = fft.ifft2(fft.fft2(encrypted) * pm2.conj())
        return np.real(fft.ifft2(fft.fft2(step1) * pm1.conj()))

    @classmethod
    def apply_diffusion(cls, coeff: np.ndarray, key_seq: np.ndarray) -> np.ndarray:
        """Applies complex-plane diffusion to DRPE output."""
        h, w = coeff.shape
        diff = key_seq[:h * w].reshape((h, w))
        diff_range = np.ptp(diff)
        diff = 0.1 + 1.0 * (diff - np.min(diff)) / (diff_range + 1e-10)
        return (np.real(coeff) * diff) + 1j * (np.imag(coeff) * (1.2 - diff))

    @classmethod
    def remove_diffusion(cls, coeff: np.ndarray, key_seq: np.ndarray) -> np.ndarray:
        """Inverses complex-plane diffusion."""
        h, w = coeff.shape
        diff = key_seq[:h * w].reshape((h, w))
        diff_range = np.ptp(diff)
        diff = 0.1 + 1.0 * (diff - np.min(diff)) / (diff_range + 1e-10)
        return (np.real(coeff) / diff) + 1j * (np.imag(coeff) / (1.2 - diff))

    @staticmethod
    def compute_metrics(original: np.ndarray, encrypted_vis: np.ndarray) -> dict:
        """Computes Shannon entropy, adjacent pixel correlations, NPCR, and UACI."""
        def entropy(arr: np.ndarray) -> float:
            hist = np.histogram(arr.flatten(), bins=256, range=[0, 256])[0]
            prob = hist / np.sum(hist)
            prob = prob[prob > 0]
            return float(-np.sum(prob * np.log2(prob)))

        def correlation(arr: np.ndarray, direction: str) -> float:
            if direction == 'horizontal':
                p, a = arr[:, :-1].flatten(), arr[:, 1:].flatten()
            elif direction == 'vertical':
                p, a = arr[:-1, :].flatten(), arr[1:, :].flatten()
            else:
                p, a = arr[:-1, :-1].flatten(), arr[1:, 1:].flatten()
            
            std_p = np.std(p)
            std_a = np.std(a)
            if std_p == 0 or std_a == 0:
                return 0.0
            corr = np.corrcoef(p.astype(np.float64), a.astype(np.float64))[0, 1]
            return float(corr) if not np.isnan(corr) else 0.0

        orig_flat = original.flatten().astype(np.float64)
        enc_flat = encrypted_vis.flatten().astype(np.float64)
        npcr = float(np.sum(orig_flat != enc_flat) / orig_flat.size * 100.0)
        uaci = float(np.sum(np.abs(orig_flat - enc_flat)) / (orig_flat.size * 255.0) * 100.0)

        return {
            "original_entropy": round(entropy(original), 4),
            "encrypted_entropy": round(entropy(encrypted_vis), 4),
            "corr_horizontal": round(correlation(encrypted_vis, 'horizontal'), 4),
            "corr_vertical": round(correlation(encrypted_vis, 'vertical'), 4),
            "corr_diagonal": round(correlation(encrypted_vis, 'diagonal'), 4),
            "npcr": round(npcr, 2),
            "uaci": round(uaci, 2)
        }
