export interface UploadedFile {
  id: string;
  name: string;
  isActive: boolean;
}

export interface ChatMessage {
  id: string;
  type: 'user' | 'ai';
  content: string;
}

export type Theme = 'light' | 'dark'; 