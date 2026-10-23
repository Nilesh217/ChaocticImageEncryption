import React, { useState } from 'react';

export default function App() {
  const [file, setFile] = useState(null);
  const [originalPreview, setOriginalPreview] = useState(null);
  const [resultPreview, setResultPreview] = useState(null);
  const [action, setAction] = useState('encrypt');
  const [x0, setX0] = useState(0.479);
  const [r, setR] = useState(3.999);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setOriginalPreview(URL.createObjectURL(selected));
      setResultPreview(null);
      setError(null);
    }
  };

  const handleProcess = async () => {
    if (!file) {
      setError("Please select an image first.");
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('action', action);
    formData.append('x0', x0);
    formData.append('r', r);

    try {
      const res = await fetch('http://localhost:8000/api/process', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Execution failed');
      }

      const blob = await res.blob();
      const outputUrl = URL.createObjectURL(blob);
      setResultPreview(outputUrl);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center py-12 px-4">
      <div className="max-w-4xl w-full space-y-8">
        <header className="border-b border-slate-800 pb-4">
          <h1 className="text-3xl font-bold tracking-tight text-indigo-400">
            Chaotic Cipher Engine
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time image permutation & diffusion via nonlinear dynamical systems
          </p>
        </header>

        {/* Controls Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 bg-slate-900 border border-slate-800 p-6 rounded-xl">
          <div>
            <label className="block text-xs font-semibold uppercase text-slate-400 mb-2">Operation</label>
            <select
              value={action}
              onChange={(e) => setAction(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
            >
              <option value="encrypt">Encrypt</option>
              <option value="decrypt">Decrypt</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase text-slate-400 mb-2">Seed (x₀ ∈ (0, 1))</label>
            <input
              type="number"
              step="0.0001"
              value={x0}
              onChange={(e) => setX0(parseFloat(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase text-slate-400 mb-2">Parameter (r ∈ [3.57, 4.0])</label>
            <input
              type="number"
              step="0.001"
              value={r}
              onChange={(e) => setR(parseFloat(e.target.value))}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={handleProcess}
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-150 h-10"
            >
              {loading ? "Processing..." : `Run ${action === 'encrypt' ? 'Encryption' : 'Decryption'}`}
            </button>
          </div>
        </div>

        {/* File Ingestion */}
        <div className="bg-slate-900 border border-dashed border-slate-700 rounded-xl p-6 text-center">
          <input
            type="file"
            accept="image/png, image/jpeg, image/bmp"
            onChange={handleFileChange}
            className="hidden"
            id="file-upload"
          />
          <label htmlFor="file-upload" className="cursor-pointer text-sm text-indigo-400 hover:text-indigo-300">
            {file ? file.name : "Click to select or drag and drop an image (.png, .jpg, .bmp)"}
          </label>
        </div>

        {error && (
          <div className="p-3 bg-red-950 border border-red-800 text-red-300 text-sm rounded-lg">
            {error}
          </div>
        )}

        {/* Image Comparison */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col items-center">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">Input Image</h3>
            <div className="h-64 w-full flex items-center justify-center bg-slate-950 rounded-lg overflow-hidden">
              {originalPreview ? (
                <img src={originalPreview} alt="Original" className="max-h-full max-w-full object-contain" />
              ) : (
                <span className="text-xs text-slate-600">No image loaded</span>
              )}
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col items-center">
            <h3 className="text-sm font-semibold text-slate-300 mb-3">Processed Output</h3>
            <div className="h-64 w-full flex items-center justify-center bg-slate-950 rounded-lg overflow-hidden">
              {resultPreview ? (
                <img src={resultPreview} alt="Result" className="max-h-full max-w-full object-contain" />
              ) : (
                <span className="text-xs text-slate-600">Awaiting execution</span>
              )}
            </div>
            {resultPreview && (
              <a
                href={resultPreview}
                download={`processed_${Date.now()}.png`}
                className="mt-3 text-xs text-indigo-400 hover:underline"
              >
                Download Ciphertext PNG
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
