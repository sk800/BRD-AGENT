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

export interface ExtractionError {
  attachment_id?: string | null;
  original_filename?: string | null;
  error: string;
}

export interface ExtractedDocument {
  attachment_id: string;
  original_filename?: string | null;
  extraction: {
    document: {
      document_id: string;
      filename: string;
      file_type: string;
    };
    elements: Array<{
      element_id: string;
      type: string;
      content: string | Record<string, unknown>;
      location?: Record<string, unknown>;
    }>;
  };
}

export interface Message {
  id: string;
  conversation_id: string;
  role: string;
  text: string | null;
  attachments: Attachment[];
  extraction_status?: string | null;
  extracted_documents?: ExtractedDocument[];
  extraction_errors?: ExtractionError[];
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
