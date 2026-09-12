"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ChatArea } from "@/components/chat/chat-area";
import { ChatSidebar } from "@/components/chat/chat-sidebar";
import { getConversations, getMessages, sendMessage } from "@/lib/api/chat";
import { useAuthStore } from "@/stores/auth-store";
import type { Conversation, Message } from "@/types";

export default function ChatPage() {
  const router = useRouter();
  const { user, token, logout, isAuthenticated } = useAuthStore();

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
    }
  }, [isAuthenticated, router]);

  const loadConversations = useCallback(async () => {
    if (!token) return;
    try {
      const data = await getConversations(token);
      setConversations(data.conversations);
    } catch {
      /* silently fail on load */
    }
  }, [token]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const loadMessages = useCallback(
    async (conversationId: string) => {
      if (!token) return;
      setLoadingMessages(true);
      try {
        const data = await getMessages(token, conversationId);
        setMessages(data.messages);
      } catch {
        setMessages([]);
      } finally {
        setLoadingMessages(false);
      }
    },
    [token],
  );

  function handleSelectConversation(id: string) {
    setActiveConversationId(id);
    loadMessages(id);
  }

  function handleNewChat() {
    setActiveConversationId(null);
    setMessages([]);
  }

  async function handleSend(text: string, files: File[]) {
    if (!token) return;

    const response = await sendMessage(
      token,
      text || null,
      files,
      activeConversationId,
    );

    setActiveConversationId(response.conversation.id);
    setMessages((prev) => [...prev, response.message]);
    await loadConversations();
  }

  function handleLogout() {
    logout();
    router.replace("/login");
  }

  if (!user || !token) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <ChatSidebar
        conversations={conversations}
        activeId={activeConversationId}
        onSelect={handleSelectConversation}
        onNewChat={handleNewChat}
        onLogout={handleLogout}
        userName={user.full_name}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed((c) => !c)}
      />
      <main className="flex flex-1 flex-col min-w-0">
        <ChatArea
          messages={messages}
          onSend={handleSend}
          loading={loadingMessages}
          isNewChat={!activeConversationId}
        />
      </main>
    </div>
  );
}
