export interface UploadedFile {
  id: string;
  name: string;
  isActive: boolean;
}

export interface Citation {
  content: string;
  filename: string;
  file_id: string;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'ai';
  content: string;
  citations?: Citation[];
}

export type Theme = 'light' | 'dark'; 