"use client";

import { LogOut, MessageSquarePlus, PanelLeftClose, PanelLeft } from "lucide-react";
import type { Conversation } from "@/types";
import { cn, formatTime } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface ChatSidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onLogout: () => void;
  userName: string;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export function ChatSidebar({
  conversations,
  activeId,
  onSelect,
  onNewChat,
  onLogout,
  userName,
  collapsed,
  onToggleCollapse,
}: ChatSidebarProps) {
  return (
    <aside
      className={cn(
        "flex flex-col border-r border-surface-border bg-surface-raised transition-all duration-300",
        collapsed ? "w-16" : "w-72",
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-surface-border">
        {!collapsed && (
          <div className="min-w-0">
            <p className="text-sm font-semibold truncate">BRD Agent</p>
            <p className="text-xs text-gray-500 truncate">{userName}</p>
          </div>
        )}
        <button
          onClick={onToggleCollapse}
          className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-400 hover:text-white hover:bg-surface-overlay transition-colors"
        >
          {collapsed ? (
            <PanelLeft className="h-4 w-4" />
          ) : (
            <PanelLeftClose className="h-4 w-4" />
          )}
        </button>
      </div>

      {/* New chat */}
      <div className="p-3">
        <Button
          onClick={onNewChat}
          variant="secondary"
          className={cn("w-full", collapsed && "!px-0")}
          size="sm"
        >
          <MessageSquarePlus className="h-4 w-4" />
          {!collapsed && "New conversation"}
        </Button>
      </div>

      {/* Conversation list */}
      {!collapsed && (
        <div className="flex-1 overflow-y-auto px-3 space-y-1">
          {conversations.length === 0 ? (
            <p className="text-xs text-gray-500 text-center py-8">
              No conversations yet
            </p>
          ) : (
            conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => onSelect(conv.id)}
                className={cn(
                  "w-full text-left rounded-xl px-3 py-2.5 transition-all duration-150",
                  activeId === conv.id
                    ? "bg-accent/15 text-white border border-accent/20"
                    : "text-gray-400 hover:bg-surface-overlay hover:text-gray-200",
                )}
              >
                <p className="text-sm font-medium truncate">{conv.title}</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {formatTime(conv.updated_at)}
                </p>
              </button>
            ))
          )}
        </div>
      )}

      {/* Logout */}
      <div className="p-3 border-t border-surface-border">
        <Button
          onClick={onLogout}
          variant="ghost"
          className={cn("w-full text-gray-400", collapsed && "!px-0")}
          size="sm"
        >
          <LogOut className="h-4 w-4" />
          {!collapsed && "Sign out"}
        </Button>
      </div>
    </aside>
  );
}
