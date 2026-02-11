"use client";

import React, { useState, useEffect } from "react";
import { Upload, Copy, Check, AlertCircle, Loader2, Globe, Plus } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const API_BASE = process.env.NEXT_PUBLIC_API_URL;

interface UploadResult {
  url: string;
}

export default function Home() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<UploadResult[]>([]);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [health, setHealth] = useState<"ok" | "error" | "loading">("loading");

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((res) => (res.ok ? setHealth("ok") : setHealth("error")))
      .catch(() => setHealth("error"));
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files;
    if (!selected) return;

    setFiles(Array.from(selected));
    setError(null);
    setProgress(0);
  };

  const onUpload = async () => {
    if (files.length === 0) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/upload`);

    xhr.upload.onprogress = (e) => {
      if (!e.lengthComputable) return;
      const percent = Math.round((e.loaded / e.total) * 100);
      setProgress(percent);
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        const data = JSON.parse(xhr.responseText);
        setResults(data);
        setProgress(100);
      } else {
        setError("Upload failed");
      }
      setUploading(false);
    };

    xhr.onerror = () => {
      setError("Network error during upload");
      setUploading(false);
    };

    xhr.send(formData);
  };

  const copyToClipboard = (url: string, index: number) => {
    navigator.clipboard.writeText(url);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6 space-y-8">
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold tracking-tighter neon-glow">
          IMG<span className="text-accent">HOST</span>
        </h1>
        <div className="flex items-center justify-center space-x-2 text-[10px] uppercase tracking-widest text-zinc-500">
          <Globe className={`w-3 h-3 ${health === "ok" ? "text-green-500" : "text-accent"}`} />
          <span>System {health === "ok" ? "Operational" : "Degraded"}</span>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md bg-card border border-border rounded-2xl p-8 shadow-neon"
      >
        <AnimatePresence mode="wait">
          {results.length === 0 ? (
            <motion.div key="upload" exit={{ opacity: 0, scale: 0.95 }} className="space-y-4">
              <label className="group relative flex flex-col items-center justify-center w-full h-48 border-2 border-dashed border-zinc-800 rounded-xl cursor-pointer hover:border-accent transition-colors">
                {files.length > 0 ? (
                  <div className="text-center p-4">
                    <p className="text-accent font-medium">{files.length} Files Selected</p>
                    <p className="text-zinc-500 text-xs mt-1">Ready for upload</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center space-y-3">
                    <Upload className="w-8 h-8 text-zinc-600 group-hover:text-accent transition-colors" />
                    <p className="text-zinc-400 text-sm">Drop images or click to browse</p>
                  </div>
                )}
                <input type="file" className="hidden" onChange={handleFileChange} accept="image/*" multiple />
              </label>

              {uploading && (
                <div className="space-y-2">
                  <div className="w-full bg-zinc-800 rounded h-2">
                    <div className="h-2 bg-accent rounded" style={{ width: `${progress}%` }} />
                  </div>
                  <p className="text-xs text-zinc-500 text-center">Uploading... {progress}%</p>
                </div>
              )}

              {error && (
                <div className="flex items-center space-x-2 text-accent text-xs bg-accent/10 p-3 rounded-lg border border-accent/20">
                  <AlertCircle className="w-4 h-4" />
                  <span>{error}</span>
                </div>
              )}

              <button
                disabled={files.length === 0 || uploading}
                onClick={onUpload}
                className="w-full bg-accent hover:bg-red-700 disabled:bg-zinc-800 disabled:text-zinc-500 text-white font-bold py-3 rounded-xl transition-all flex items-center justify-center space-x-2 shadow-lg"
              >
                {uploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <span>UPLOAD</span>}
              </button>
            </motion.div>
          ) : (
            <motion.div key="result" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="space-y-6">
              <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2">
                {results.map((res, index) => (
                  <div key={index} className="space-y-2 p-3 border border-border rounded-xl bg-black/50">
                    <div className="relative aspect-video rounded-lg overflow-hidden border border-zinc-800 bg-zinc-900 mb-2">
                      <img src={res.url} alt={`Upload ${index}`} className="object-contain w-full h-full" />
                    </div>
                    <div className="flex items-center space-x-2">
                      <input
                        readOnly
                        value={res.url}
                        className="flex-1 bg-black border border-zinc-800 rounded-lg px-3 py-2 text-[10px] text-zinc-400 focus:outline-none"
                      />
                      <button onClick={() => copyToClipboard(res.url, index)} className="p-2 hover:text-accent transition-colors">
                        {copiedIndex === index ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              <div className="space-y-4">
                <div className="bg-accent/5 p-3 rounded-lg border border-accent/20 text-center">
                  <p className="text-[9px] text-zinc-500">Links will expire in 24 hours</p>
                </div>

                <button
                  onClick={() => {
                    setResults([]);
                    setFiles([]);
                    setProgress(0);
                  }}
                  className="w-full bg-zinc-900 hover:bg-zinc-800 text-white py-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center space-x-2"
                >
                  <Plus className="w-4 h-4" />
                  <span>UPLOAD MORE</span>
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      <footer className="text-[10px] text-zinc-700 uppercase tracking-[0.2em]">
        SPEEDDD HAWKSSS
      </footer>
    </main>
  );
}
