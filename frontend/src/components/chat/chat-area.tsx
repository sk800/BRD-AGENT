"use client";

import { useEffect, useRef } from "react";
import { Bot, FileText, Sparkles } from "lucide-react";
import type { Message } from "@/types";
import { MessageBubble } from "./message-bubble";
import { ChatInput } from "./chat-input";

interface ChatAreaProps {
  messages: Message[];
  onSend: (text: string, files: File[]) => Promise<void>;
  loading?: boolean;
  isNewChat?: boolean;
}

export function ChatArea({
  messages,
  onSend,
  loading,
  isNewChat,
}: ChatAreaProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-1 flex-col min-h-0">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        {isNewChat && messages.length === 0 ? (
          <div className="flex h-full items-center justify-center p-8">
            <div className="text-center max-w-lg animate-fade-in">
              <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-accent/10 border border-accent/20">
                <Sparkles className="h-8 w-8 text-accent" />
              </div>
              <h2 className="text-2xl font-bold mb-3">
                What requirements can I help with?
              </h2>
              <p className="text-gray-400 mb-8 leading-relaxed">
                Describe your project needs, upload requirement documents, or ask
                me to help draft a Business Requirements Document.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {[
                  {
                    icon: FileText,
                    title: "Upload documents",
                    desc: "PDF, DOCX, images — any format",
                  },
                  {
                    icon: Bot,
                    title: "Describe requirements",
                    desc: "Chat naturally about your project",
                  },
                ].map(({ icon: Icon, title, desc }) => (
                  <div
                    key={title}
                    className="rounded-xl border border-surface-border bg-surface-overlay p-4 text-left"
                  >
                    <Icon className="h-5 w-5 text-accent mb-2" />
                    <p className="text-sm font-medium">{title}</p>
                    <p className="text-xs text-gray-500 mt-1">{desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl px-4 py-6 space-y-6">
            {loading && messages.length === 0 ? (
              <div className="flex items-center justify-center py-20">
                <div className="flex items-center gap-3 text-gray-400">
                  <div className="h-2 w-2 rounded-full bg-accent animate-pulse-soft" />
                  <div className="h-2 w-2 rounded-full bg-accent animate-pulse-soft [animation-delay:0.2s]" />
                  <div className="h-2 w-2 rounded-full bg-accent animate-pulse-soft [animation-delay:0.4s]" />
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <ChatInput onSend={onSend} disabled={loading} />
    </div>
  );
}
