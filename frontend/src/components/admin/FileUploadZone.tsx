'use client';

import { UploadCloud } from 'lucide-react';
import { useRef, useState } from 'react';

type FileUploadZoneProps = {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
};

export default function FileUploadZone({
  onFileSelect,
  selectedFile,
}: FileUploadZoneProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = (file: File | undefined) => {
    if (!file) {
      return;
    }
    onFileSelect(file);
  };

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          const file = event.dataTransfer.files?.[0];
          handleFile(file);
        }}
        className={`w-full rounded-[28px] border px-6 py-10 text-left transition ${
          isDragging
            ? 'border-black bg-[#ffd166] shadow-[0_18px_60px_rgba(0,0,0,0.12)]'
            : 'border-black/10 bg-white hover:border-black/20 hover:bg-[#fff7e8]'
        }`}
      >
        <div className="flex flex-col items-start gap-4 sm:flex-row sm:items-center">
          <div className="rounded-2xl bg-black p-3 text-white">
            <UploadCloud className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <p className="text-lg font-semibold text-black">
              Drag a PDF here or click to browse
            </p>
            <p className="text-sm text-black/60">
              PDFs only. This becomes the source file the system reads from.
            </p>
          </div>
        </div>
      </button>

      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={(event) => handleFile(event.target.files?.[0])}
      />

      {selectedFile ? (
        <div className="rounded-2xl border border-black/10 bg-[#fff9ef] px-4 py-3 text-sm text-black/70">
          Selected file: <span className="font-semibold text-black">{selectedFile.name}</span>
        </div>
      ) : null}
    </div>
  );
}
