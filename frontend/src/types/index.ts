export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  token_type: string;
}

export interface Attachment {
  id: string;
  filename: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: string;
  text: string | null;
  attachments: Attachment[];
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface SendMessageResponse {
  conversation: Conversation;
  message: Message;
}

export interface ConversationListResponse {
  conversations: Conversation[];
}

export interface MessageListResponse {
  conversation_id: string;
  messages: Message[];
}
