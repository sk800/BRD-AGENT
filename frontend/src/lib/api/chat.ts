import type {
  ConversationListResponse,
  MessageListResponse,
  SendMessageResponse,
} from "@/types";
import { apiRequest } from "./client";

export async function sendMessage(
  token: string,
  text: string | null,
  files: File[],
  conversationId?: string | null,
): Promise<SendMessageResponse> {
  const formData = new FormData();
  if (text) formData.append("text", text);
  if (conversationId) formData.append("conversation_id", conversationId);
  files.forEach((file) => formData.append("files", file));

  return apiRequest<SendMessageResponse>(
    "/api/v1/chat/messages",
    { method: "POST", body: formData },
    token,
  );
}

export async function getConversations(
  token: string,
): Promise<ConversationListResponse> {
  return apiRequest<ConversationListResponse>(
    "/api/v1/chat/conversations",
    {},
    token,
  );
}

export async function getMessages(
  token: string,
  conversationId: string,
): Promise<MessageListResponse> {
  return apiRequest<MessageListResponse>(
    `/api/v1/chat/conversations/${conversationId}/messages`,
    {},
    token,
  );
}
