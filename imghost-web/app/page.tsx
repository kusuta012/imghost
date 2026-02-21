"use client";

import React, { useState, useEffect } from "react";
import { Upload, Copy, Check, AlertCircle, Loader2, Globe, Plus, Timer, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";

const API_BASE = process.env.NEXT_PUBLIC_API_URL;

const PRESETS = [
  { label: "1h", value: 60 },
  { label: "6h", value: 360 },
  { label: "12h", value: 720 },
  { label: "24h", value: 1440 },
];

const PRESET_VALUES = PRESETS.map((p) => p.value);

interface UploadResult {
  url: string;
  size?: number;
  expires_at?: string;
}

async function compressImage(file: File): Promise<File> {
  return new Promise((resolve) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      const img = new Image();
      img.src = e.target?.result as string;

      img.onload = () => {
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");

        if (!ctx) {
          resolve(file);
          return;
        }

        let width = img.width;
        let height = img.height;
        const MAX_DIMENSION = 2500;

        if (width > MAX_DIMENSION || height > MAX_DIMENSION) {
          if (width > height) {
            height = (MAX_DIMENSION / width) * height;
            width = MAX_DIMENSION;
          } else {
            width = (MAX_DIMENSION / height) * width;
            height = MAX_DIMENSION;
          }
        }

        canvas.width = width;
        canvas.height = height;
        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob(
          (blob) => {
            if (!blob) {
              resolve(file);
              return;
            }

            if (blob.size < file.size) {
              const compressedFile = new File(
                [blob],
                file.name.replace(/\.[^.]+$/, ".webp"),
                { type: "image/webp" }
              );
              console.log(
                `Compressed: ${(file.size / 1024).toFixed(1)}KB → ${(blob.size / 1024).toFixed(1)}KB`
              );
              resolve(compressedFile);
            } else {
              resolve(file);
            }
          },
          "image/webp",
          0.85
        );
      };

      img.onerror = () => resolve(file);
    };

    reader.onerror = () => resolve(file);
    reader.readAsDataURL(file);
  });
}

export default function Home() {
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<UploadResult[]>([]);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [health, setHealth] = useState<"ok" | "error" | "loading">("loading");
  const [compressing, setCompressing] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [expiresMinutes, setExpiresMinutes] = useState<number>(1440);
  const [showExpiry, setShowExpiry] = useState(false);
  const [customInput, setCustomInput] = useState<string>("");
  const [inputError, setInputError] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then((res) => (res.ok ? setHealth("ok") : setHealth("error")))
      .catch(() => setHealth("error"));
  }, []);

  useEffect(() => {
    const handlePaste = async (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;

      const imageFiles: File[] = [];

      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.type.startsWith("image/")) {
          const file = item.getAsFile();
          if (file) imageFiles.push(file);
        }
      }

      if (imageFiles.length > 0) {
        e.preventDefault();
        await processFiles(imageFiles);
      }
    };

    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
  }, []);

  const snapToPreset = (value: number) => {
    const SNAP_DISTANCE = 20;
    for (const preset of PRESET_VALUES) {
      if (Math.abs(value - preset) <= SNAP_DISTANCE) return preset;
    }
    return value;
  };

  const processFiles = async (fileList: File[]) => {
    const oversized = fileList.filter((f) => f.size > 15 * 1024 * 1024);
    if (oversized.length > 0) {
      setError(`${oversized.length} files exceed 15MB limit`);
      return;
    }

    if (fileList.length > 10) {
      setError("Maximum 10 files per upload");
      return;
    }

    setCompressing(true);
    setError(null);

    const compressedFiles = await Promise.all(fileList.map((file) => compressImage(file)));

    setFiles(compressedFiles);
    setCompressing(false);
    setProgress(0);
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files;
    if (!selected) return;
    await processFiles(Array.from(selected));
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files).filter((file) =>
      file.type.startsWith("image/")
    );

    if (droppedFiles.length > 0) {
      await processFiles(droppedFiles);
    }
  };

  const onUpload = async () => {
    if (files.length === 0) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    if (!Number.isNaN(expiresMinutes)) {
      formData.append("expires_minutes", String(expiresMinutes));
    }

    console.log("Sending expires_minutes:", expiresMinutes);


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
        setResults(data as UploadResult[]);
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

  const formatExpiry = (mins: number) => {
    const rounded = Math.round(mins);
    if (rounded < 60) return `${rounded}m`;
    const hours = Math.round(rounded / 60);
    if (rounded % 60 === 0) return `${hours}h`;
    return `${(rounded / 60).toFixed(1)}h`;
  };

  const clampValue = (value: number) => {
    return Math.max(5, Math.min(1440, Math.round(value)));
  };

  const handleCustomInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const rawValue = e.target.value;
    setCustomInput(rawValue);

    const numValue = parseInt(rawValue);

    if (rawValue === "") {
      return;
    }

    if (isNaN(numValue) || numValue < 5 || numValue > 1440) {
      setInputError(true);
      setTimeout(() => setInputError(false), 300);
    } else {
      setInputError(false);
    }

    if (!isNaN(numValue)) {
      const clamped = clampValue(numValue);
      setExpiresMinutes(clamped);
    }
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = parseInt(e.target.value);
    const snapped = snapToPreset(raw);

    setExpiresMinutes(snapped);
    setCustomInput("");
  };

  const handlePresetClick = (value: number) => {
    setExpiresMinutes(value);
    setCustomInput("");
  };

  return (
    <main className="flex-1 flex flex-col items-center justify-center p-6 space-y-6">
      <div className="flex flex-col items-center">
        <div className="flex items-center gap-3"> 
        <h1 className="text-4xl font-bold tracking-tighter neon-glow">
          IMG<span className="text-accent">HOST</span>
        </h1>
         <ThemeSwitcher />
        </div>
        <div className="flex items-center space-x-2 text-xs uppercase tracking-widest text-[var(--bg-accent)] opacity-70 mt-2 ml-[-36px]">
          <Globe className={`w-3 h-3 ${health === "ok" ? "text-green-500" : "text-accent"}`} />
          <span>System {health === "ok" ? "Operational" : "Degraded"}</span>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-4xl bg-card border border-border rounded-2xl p-8 shadow-[var(--shadow-neon)]"
      >
        <AnimatePresence mode="wait">
          {results.length === 0 ? (
            <motion.div key="upload" exit={{ opacity: 0, scale: 0.95 }} className="space-y-4">
              <label
                className={`group relative flex flex-col items-center justify-center w-full h-96 border-2 border-dashed rounded-xl cursor-pointer transition-colors ${
                  isDragging ? "border-accent bg-accent/10" : "border-border hover:border-accent"
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
              >
                {compressing ? (
                  <div className="text-center p-4">
                    <Loader2 className="w-8 h-8 text-accent animate-spin mx-auto mb-2" />
                    <p className="text-accent font-medium">Compressing images.....</p>
                    <p className="text-zinc-500 text-xs mt-1">optimizing for faster upload</p>
                  </div>
                ) : files.length > 0 ? (
                  <div className="text-center p-4">
                    <p className="text-accent font-medium">{files.length} Files Selected</p>
                    <p className="text-zinc-500 text-xs mt-1">
                      {(files.reduce((sum, f) => sum + f.size, 0) / 1024 / 1024).toFixed(1)} MB total
                    </p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center space-y-3">
                    <Upload className="w-16 h-16 text-[var(--bg-accent)] opacity-50 group-hover:text-accent group-hover:opacity-100 transition-colors" />
                    <p className="text-[var(--bg-accent)] opacity-50 text-sm">
                      {isDragging ? "Drag images here" : "Drop images or click to browse"}
                    </p>
                    <p className="text-[var(--bg-accent)] opacity-50 text-xs">Max 15MB</p>
                  </div>
                )}
                <input
                  type="file"
                  className="hidden"
                  onChange={handleFileChange}
                  accept="image/*"
                  multiple
                  disabled={compressing}
                />
              </label>

              <div className="relative flex items-center justify-between gap-3">
                <button
                  onClick={() => setShowExpiry((v) => !v)}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-[11px] uppercase tracking-widest font-bold transition-all border whitespace-nowrap ${
                    showExpiry
                      ? "border-accent text-accent bg-accent/10"
                      : "border-border text-zinc-400 hover:opacity-80 hover:text-zinc-300"
                  }`}
                >
                  <Timer className="w-3.5 h-3.5" />
                  <span>Expires: {formatExpiry(expiresMinutes)}  ▼</span>
                </button>

                <AnimatePresence>
                  {showExpiry && (
                    <>
                      <div className="fixed inset-0 z-10" onClick={() => setShowExpiry(false)} />
                      <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: -4 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: -4 }}
                        transition={{ duration: 0.15 }}
                        className="absolute bottom-full left-0 mb-2 z-20 w-64 bg-zinc-950 border border-border rounded-xl p-4 shadow-2xl space-y-4"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] uppercase tracking-widest text-zinc-500 font-bold">
                            Auto-delete after
                          </span>
                          <button onClick={() => setShowExpiry(false)}>
                            <X className="w-3 h-3 text-zinc-600 hover:text-zinc-400 transition-colors" />
                          </button>
                        </div>

                        <div className="flex gap-1.5">
                          {PRESETS.map(({ label, value }) => (
                            <button
                              key={value}
                              onClick={() => handlePresetClick(value)}
                              className={`flex-1 py-1.5 rounded-lg text-xs font-bold transition-all border relative overflow-hidden ${
                                expiresMinutes === value && customInput === ""
                                  ? "bg-accent text-white border-accent"
                                  : "bg-zinc-900 text-zinc-400 border-border hover:opacity-80"
                              }`}
                            >
                              {label}
                            </button>
                          ))}
                        </div>

                        <div className="space-y-2">
                          <div className="relative w-full">
                            <input
                              type="range"
                              min="5"
                              max="1440"
                              step="1"
                              value={expiresMinutes}
                              onChange={handleSliderChange}
                              className="w-full appearance-none cursor-pointer h-[6px] rounded-full"
                              style={{
                                background: `linear-gradient(to right,
                                  var(--color-accent) 0%,
                                  var(--color-accent) ${((expiresMinutes - 5) / (1440 - 5)) * 100}%,
                                  var(--color-border) ${((expiresMinutes - 5) / (1440 - 5)) * 100}%,
                                  var(--color-border) 100%)`
                              }}
                            />
                          </div>

                          <div className="relative h-3 mt-1">
                            {[
                              { label: "5m", value: 5 },
                              { label: "6h", value: 360 },
                              { label: "12h", value: 720 },
                              { label: "24h", value: 1440 },
                            ].map(({ label, value }) => {
                              const percent = ((value - 5) / (1440 - 5)) * 100;

                              return (
                                <span
                                  key={value}
                                  className="absolute text-[8px] font-medium text-zinc-700 uppercase -translate-x-1/2"
                                  style={{ left: `${percent}%` }}
                                >
                                  {label}
                                </span>
                              );
                            })}
                          </div>
                        </div>

                        <div className="flex items-center gap-2 pt-1 border-t border-border">
                          <span className="text-[10px] text-zinc-600">Custom</span>
                          <input
                            type="number"
                            min={5}
                            max={1440}
                            placeholder={String(expiresMinutes)}
                            value={customInput}
                            onChange={handleCustomInputChange}
                            className={`flex-1 bg-zinc-900 border rounded-lg px-2 py-1 text-xs text-zinc-200 text-center focus:outline-none transition-all ${
                              inputError ? "border-accent animate-shake" : "border-zinc-700 focus:border-accent"
                            }`}
                          />
                          <span className="text-[10px] text-zinc-600">min</span>
                        </div>
                      </motion.div>
                    </>
                  )}
                </AnimatePresence>

                <button
                  disabled={files.length === 0 || uploading || compressing}
                  onClick={onUpload}
                  className="flex-1 bg-accent hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-[var(--color-card)] text-white font-bold py-3 rounded-xl transition-all flex items-center justify-center shadow-[var(--shadow-neon)]"
                >
                  {uploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <span>UPLOAD</span>}
                </button>
              </div>

              {uploading && (
                <div className="space-y-2">
                  <div className="w-full bg-zinc-800 rounded h-2">
                    <div
                      className="h-2 bg-accent rounded transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    />
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
            </motion.div>
          ) : (
            <motion.div
              key="result"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="space-y-6"
            >
              <div className="space-y-4 max-h-100 overflow-y-auto pr-2">
                {results.map((res, index) => (
                  <div key={index} className="space-y-2 p-3 border border-border rounded-xl bg-black/50">
                    <div className="relative aspect-video rounded-lg overflow-hidden border border-border bg-zinc-900 mb-2">
                      <img src={res.url} alt={`Upload ${index}`} className="object-contain w-full h-full" />
                    </div>
                    <div className="flex items-center space-x-2">
                      <input
                        readOnly
                        value={res.url}
                        className="flex-1 bg-black border border-border rounded-lg px-3 py-2 text-[10px] text-zinc-400 focus:outline-none"
                      />
                      <button
                        onClick={() => copyToClipboard(res.url, index)}
                        className="p-2 hover:text-accent transition-colors"
                      >
                        {copiedIndex === index ? (
                          <Check className="w-4 h-4 text-green-500" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                    {res.expires_at && (
                      <div className="text-[10px] text-zinc-500 mt-1">
                        Expires: {new Date(res.expires_at).toLocaleString()}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="space-y-4">
                <div className="bg-accent/5 p-3 rounded-lg border border-accent/20 text-center">
                  <p className="text-xs text-[var(--bg-accent)]">Links will expire in {formatExpiry(expiresMinutes)}</p>
                </div>

                <button
                  onClick={() => {
                    setResults([]);
                    setFiles([]);
                    setProgress(0);
                  }}
                  className="w-full bg-accent hover:brightness-80 border border-border text-white py-3 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 shadow-[var(--shadow-neon)]"
                >
                  <Plus className="w-4 h-4" />
                  <span>UPLOAD MORE</span>
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </main>
  );
}
