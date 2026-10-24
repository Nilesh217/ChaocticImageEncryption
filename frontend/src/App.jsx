import React, { useState } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function App() {
  const [activeTab, setActiveTab] = useState('encrypt');
  const [file, setFile] = useState(null);
  const [x0Log, setX0Log] = useState(0.123456789);
  const [rLog, setRLog] = useState(3.99);
  const [x0Sine, setX0Sine] = useState(0.987654321);

  const [loading, setLoading] = useState(false);
  const [inputPreview, setInputPreview] = useState(null);
  const [resultPreview, setResultPreview] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setError(null);
      if (activeTab === 'encrypt') {
        setInputPreview(URL.createObjectURL(selected));
      } else {
        setInputPreview(null);
      }
    }
  };

  const handleExecute = async () => {
    if (!file) {
      setError("Please select an input file first.");
      return;
    }
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('x0_log', x0Log);
    formData.append('r_log', rLog);
    formData.append('x0_sine', x0Sine);

    const endpoint = activeTab === 'encrypt' ? '/api/encrypt' : '/api/decrypt';

    try {
      const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Operation failed");

      if (activeTab === 'encrypt') {
        setResultPreview(data.preview_base64);
        setFileId(data.file_id);
        setMetrics(data.metrics);
      } else {
        setResultPreview(data.decrypted_base64);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center py-10 px-4">
      <div className="max-w-5xl w-full space-y-6">
        
        {/* Navigation / Header */}
        <div className="flex justify-between items-center border-b border-slate-800 pb-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-indigo-400">
              DWT-DRPE Chaotic Cipher
            </h1>
            <p className="text-xs text-slate-400">Optical DRPE + Wavelet Transform + Complex Diffusion</p>
          </div>
          <div className="flex bg-slate-900 border border-slate-800 rounded-lg p-1">
            <button
              onClick={() => { setActiveTab('encrypt'); setResultPreview(null); setFile(null); setInputPreview(null); }}
              className={`px-4 py-1.5 rounded-md text-xs font-semibold ${activeTab === 'encrypt' ? 'bg-indigo-600 text-white' : 'text-slate-400'}`}
            >
              Encryption
            </button>
            <button
              onClick={() => { setActiveTab('decrypt'); setResultPreview(null); setFile(null); setInputPreview(null); }}
              className={`px-4 py-1.5 rounded-md text-xs font-semibold ${activeTab === 'decrypt' ? 'bg-indigo-600 text-white' : 'text-slate-400'}`}
            >
              Decryption
            </button>
          </div>
        </div>

        {/* Parameter Key Controls */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-900 border border-slate-800 p-4 rounded-xl">
          <div>
            <label className="text-xs text-slate-400 font-mono">Logistic Seed (x₀)</label>
            <input
              type="number"
              step="0.000000001"
              value={x0Log}
              onChange={(e) => setX0Log(parseFloat(e.target.value))}
              className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm font-mono focus:border-indigo-500 outline-none"
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 font-mono">Logistic Param (r)</label>
            <input
              type="number"
              step="0.01"
              value={rLog}
              onChange={(e) => setRLog(parseFloat(e.target.value))}
              className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm font-mono focus:border-indigo-500 outline-none"
            />
          </div>
          <div>
            <label className="text-xs text-slate-400 font-mono">Sine Map Seed (x₀)</label>
            <input
              type="number"
              step="0.000000001"
              value={x0Sine}
              onChange={(e) => setX0Sine(parseFloat(e.target.value))}
              className="mt-1 w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-sm font-mono focus:border-indigo-500 outline-none"
            />
          </div>
        </div>

        {/* File Dropzone */}
        <div className="border border-dashed border-slate-800 bg-slate-900/50 rounded-xl p-6 text-center">
          <input
            type="file"
            id="file-input"
            accept={activeTab === 'encrypt' ? 'image/*' : '.npz'}
            onChange={handleFileChange}
            className="hidden"
          />
          <label htmlFor="file-input" className="cursor-pointer text-sm text-indigo-400 hover:text-indigo-300">
            {file ? file.name : (activeTab === 'encrypt' ? "Select Image (.png, .jpg, .bmp)" : "Select Cipher Payload (.npz)")}
          </label>
        </div>

        {/* Action Button */}
        <button
          onClick={handleExecute}
          disabled={loading}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-white font-medium py-2.5 rounded-xl transition duration-150 text-sm"
        >
          {loading ? "Computing Wavelet DRPE Pipeline..." : (activeTab === 'encrypt' ? "Encrypt Image" : "Decrypt Payload")}
        </button>

        {error && <div className="p-3 bg-red-950 border border-red-900 text-red-300 text-xs rounded-lg">{error}</div>}

        {/* Metrics Grid */}
        {metrics && activeTab === 'encrypt' && (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-7 gap-3 bg-slate-900 border border-slate-800 p-4 rounded-xl text-center">
            <div>
              <div className="text-[10px] uppercase text-slate-500">Orig Entropy</div>
              <div className="text-sm font-mono font-bold text-slate-200">{metrics.original_entropy}</div>
            </div>
            <div>
              <div className="text-[10px] uppercase text-slate-500">Cipher Entropy</div>
              <div className="text-sm font-mono font-bold text-indigo-400">{metrics.encrypted_entropy}</div>
            </div>
            <div>
              <div className="text-[10px] uppercase text-slate-500">Corr (H)</div>
              <div className="text-sm font-mono font-bold text-slate-200">{metrics.corr_horizontal}</div>
            </div>
            <div>
              <div className="text-[10px] uppercase text-slate-500">Corr (V)</div>
              <div className="text-sm font-mono font-bold text-slate-200">{metrics.corr_vertical}</div>
            </div>
            <div>
              <div className="text-[10px] uppercase text-slate-500">Corr (Diag)</div>
              <div className="text-sm font-mono font-bold text-slate-200">{metrics.corr_diagonal}</div>
            </div>
            {metrics.npcr !== undefined && (
              <div>
                <div className="text-[10px] uppercase text-slate-500">NPCR</div>
                <div className="text-sm font-mono font-bold text-indigo-400">{metrics.npcr}%</div>
              </div>
            )}
            {metrics.uaci !== undefined && (
              <div>
                <div className="text-[10px] uppercase text-slate-500">UACI</div>
                <div className="text-sm font-mono font-bold text-indigo-400">{metrics.uaci}%</div>
              </div>
            )}
          </div>
        )}

        {/* Previews */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col items-center">
            <span className="text-xs font-semibold text-slate-400 mb-2">Input Source</span>
            <div className="h-64 w-full flex items-center justify-center bg-slate-950 rounded-lg overflow-hidden">
              {inputPreview ? (
                <img src={inputPreview} alt="Source" className="max-h-full max-w-full object-contain" />
              ) : (
                <span className="text-xs text-slate-600">{activeTab === 'decrypt' ? 'Cipher archive loaded' : 'No image loaded'}</span>
              )}
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col items-center">
            <span className="text-xs font-semibold text-slate-400 mb-2">
              {activeTab === 'encrypt' ? 'Visual Subband Mosaic' : 'Reconstructed Image'}
            </span>
            <div className="h-64 w-full flex items-center justify-center bg-slate-950 rounded-lg overflow-hidden">
              {resultPreview ? (
                <img src={resultPreview} alt="Result" className="max-h-full max-w-full object-contain" />
              ) : (
                <span className="text-xs text-slate-600">Awaiting processing</span>
              )}
            </div>

            {activeTab === 'encrypt' && fileId && (
              <a
                href={`${API_BASE_URL}/api/download/${fileId}`}
                className="mt-3 text-xs text-indigo-400 hover:text-indigo-300 underline font-medium"
              >
                Download Lossless Cipher Payload (.npz)
              </a>
            )}

            {activeTab === 'decrypt' && resultPreview && (
              <a
                href={resultPreview}
                download="reconstructed_image.png"
                className="mt-3 text-xs text-indigo-400 hover:text-indigo-300 underline font-medium"
              >
                Download Reconstructed Lossless PNG
              </a>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
