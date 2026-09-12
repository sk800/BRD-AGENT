"use client";

import { useCallback, useRef, useState } from "react";
import { Paperclip, Send, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn, formatFileSize } from "@/lib/utils";

interface ChatInputProps {
  onSend: (text: string, files: File[]) => Promise<void>;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [text, setText] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [sending, setSending] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const canSend = (text.trim() || files.length > 0) && !sending && !disabled;

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    const fileArray = Array.from(newFiles);
    setFiles((prev) => {
      const existing = new Set(prev.map((f) => f.name + f.size));
      const unique = fileArray.filter((f) => !existing.has(f.name + f.size));
      return [...prev, ...unique].slice(0, 10);
    });
  }, []);

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  async function handleSend() {
    if (!canSend) return;
    setSending(true);
    try {
      await onSend(text.trim(), files);
      setText("");
      setFiles([]);
      if (textareaRef.current) textareaRef.current.style.height = "auto";
    } finally {
      setSending(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleTextareaInput(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setText(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 160) + "px";
  }

  return (
    <div className="border-t border-surface-border bg-surface-raised/50 backdrop-blur-xl p-4">
      <div className="mx-auto max-w-3xl">
        {/* File previews */}
        {files.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {files.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="flex items-center gap-2 rounded-xl bg-surface-overlay border border-surface-border px-3 py-2 text-sm animate-fade-in"
              >
                <Paperclip className="h-3.5 w-3.5 text-accent shrink-0" />
                <span className="truncate max-w-[150px]">{file.name}</span>
                <span className="text-gray-500 text-xs">{formatFileSize(file.size)}</span>
                <button
                  onClick={() => removeFile(index)}
                  className="ml-1 text-gray-500 hover:text-white transition-colors"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Input area */}
        <div
          className={cn(
            "gradient-border rounded-2xl bg-surface-overlay transition-all duration-200",
            dragOver && "ring-2 ring-accent/40",
          )}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            if (e.dataTransfer.files.length) addFiles(e.dataTransfer.files);
          }}
        >
          <div className="flex items-end gap-2 p-3">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={disabled || sending}
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-gray-400 hover:text-accent hover:bg-accent/10 transition-all"
              title="Attach files"
            >
              <Paperclip className="h-5 w-5" />
            </button>

            <textarea
              ref={textareaRef}
              value={text}
              onChange={handleTextareaInput}
              onKeyDown={handleKeyDown}
              placeholder="Describe your requirements or attach documents..."
              disabled={disabled || sending}
              rows={1}
              className="flex-1 resize-none bg-transparent text-sm text-white placeholder:text-gray-500 focus:outline-none py-2.5 max-h-40"
            />

            <Button
              onClick={handleSend}
              disabled={!canSend}
              loading={sending}
              size="sm"
              className="shrink-0 h-10 w-10 !p-0 rounded-xl"
            >
              {!sending && <Send className="h-4 w-4" />}
            </Button>
          </div>
        </div>

        <p className="mt-2 text-center text-xs text-gray-600">
          Upload any format — PDF, DOCX, images, spreadsheets. Press Enter to send.
        </p>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => {
            if (e.target.files) addFiles(e.target.files);
            e.target.value = "";
          }}
        />
      </div>
    </div>
  );
}
