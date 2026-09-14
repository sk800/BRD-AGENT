"use client";

import { FileIcon, FileImage, FileSpreadsheet, FileText } from "lucide-react";
import type { Attachment, Message } from "@/types";
import { cn, formatFileSize, formatTime } from "@/lib/utils";
import { ExtractionPreview } from "./extraction-preview";

function AttachmentIcon({ mimeType }: { mimeType: string }) {
  if (mimeType.startsWith("image/"))
    return <FileImage className="h-4 w-4 text-blue-400" />;
  if (mimeType.includes("pdf"))
    return <FileText className="h-4 w-4 text-red-400" />;
  if (mimeType.includes("sheet") || mimeType.includes("excel"))
    return <FileSpreadsheet className="h-4 w-4 text-green-400" />;
  return <FileIcon className="h-4 w-4 text-gray-400" />;
}

function AttachmentChip({ attachment }: { attachment: Attachment }) {
  return (
    <div className="flex items-center gap-2.5 rounded-xl bg-surface-overlay border border-surface-border px-3 py-2 max-w-xs">
      <AttachmentIcon mimeType={attachment.mime_type} />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium truncate">{attachment.original_filename}</p>
        <p className="text-xs text-gray-500">{formatFileSize(attachment.size_bytes)}</p>
      </div>
    </div>
  );
}

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex animate-slide-up",
        isUser ? "justify-end" : "justify-start",
      )}
    >
      <div
        className={cn(
          "max-w-[75%] space-y-2",
          isUser ? "items-end" : "items-start",
        )}
      >
        {message.text && (
          <div
            className={cn(
              "rounded-2xl px-4 py-3 text-sm leading-relaxed",
              isUser
                ? "bg-accent text-white rounded-br-md"
                : "bg-surface-overlay border border-surface-border text-gray-200 rounded-bl-md",
            )}
          >
            {message.text}
          </div>
        )}

        {message.attachments.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {message.attachments.map((attachment) => (
              <AttachmentChip key={attachment.id} attachment={attachment} />
            ))}
          </div>
        )}

        <ExtractionPreview
          status={message.extraction_status}
          extractedDocuments={message.extracted_documents}
          extractionErrors={message.extraction_errors}
        />

        <p className="text-xs text-gray-500 px-1">
          {formatTime(message.created_at)}
        </p>
      </div>
    </div>
  );
}
