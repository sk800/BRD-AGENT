"use client";

import { CheckCircle2, AlertCircle, FileSearch } from "lucide-react";
import type { ExtractedDocument, ExtractionError } from "@/types";
import { cn } from "@/lib/utils";

function formatElementContent(content: string | Record<string, unknown>): string {
  if (typeof content === "string") return content;
  return JSON.stringify(content, null, 2);
}

interface ExtractionPreviewProps {
  status?: string | null;
  extractedDocuments?: ExtractedDocument[];
  extractionErrors?: ExtractionError[];
}

export function ExtractionPreview({
  status,
  extractedDocuments = [],
  extractionErrors = [],
}: ExtractionPreviewProps) {
  if (!status || status === "skipped") return null;

  const isSuccess = status === "done";
  const isPartial = status === "partial";

  return (
    <div className="rounded-xl border border-surface-border bg-surface-overlay/80 p-3 space-y-3 max-w-md">
      <div className="flex items-center gap-2">
        {isSuccess || isPartial ? (
          <CheckCircle2
            className={cn(
              "h-4 w-4 shrink-0",
              isPartial ? "text-yellow-400" : "text-green-400",
            )}
          />
        ) : (
          <AlertCircle className="h-4 w-4 shrink-0 text-red-400" />
        )}
        <div className="flex items-center gap-2 min-w-0">
          <FileSearch className="h-3.5 w-3.5 text-accent shrink-0" />
          <p className="text-xs font-medium text-gray-300">
            Extraction {status}
            {extractedDocuments.length > 0 &&
              ` · ${extractedDocuments.length} file(s)`}
          </p>
        </div>
      </div>

      {extractedDocuments.map((doc) => {
        const elements = doc.extraction?.elements ?? [];

        return (
          <div
            key={doc.attachment_id}
            className="rounded-lg bg-surface-raised border border-surface-border p-2.5 space-y-2"
          >
            <p className="text-xs font-medium text-accent truncate">
              {doc.original_filename ?? "Uploaded file"}
            </p>
            <div className="space-y-1.5 max-h-40 overflow-y-auto">
              {elements.slice(0, 5).map((element) => (
                <div key={element.element_id} className="text-xs">
                  <span className="text-gray-500 uppercase tracking-wide">
                    {element.type}
                  </span>
                  <p className="text-gray-300 mt-0.5 whitespace-pre-wrap line-clamp-3">
                    {formatElementContent(element.content)}
                  </p>
                </div>
              ))}
              {elements.length > 5 && (
                <p className="text-xs text-gray-500">
                  +{elements.length - 5} more elements
                </p>
              )}
              {elements.length === 0 && (
                <p className="text-xs text-gray-500">No elements extracted.</p>
              )}
            </div>
          </div>
        );
      })}

      {extractionErrors.map((error, index) => (
        <p key={`${error.attachment_id ?? "error"}-${index}`} className="text-xs text-red-400">
          {error.original_filename ?? "File"}: {error.error}
        </p>
      ))}
    </div>
  );
}
