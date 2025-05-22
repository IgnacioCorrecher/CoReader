import { useRef } from 'react';
import type { ChatMessage as ChatMessageType } from '../../types';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';

const HamburgerIcon = ({ color = 'currentColor' }) => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="3" y1="12" x2="21" y2="12"></line>
    <line x1="3" y1="6" x2="21" y2="6"></line>
    <line x1="3" y1="18" x2="21" y2="18"></line>
  </svg>
);

const ChevronLeftIcon = ({ color = 'currentColor' }) => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="15 18 9 12 15 6"></polyline>
  </svg>
);

interface ChatContainerProps {
  messages: ChatMessageType[];
  query: string;
  isStreaming: boolean;
  onQueryChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onSubmit: () => void;
  onFileChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  isUploadingFile: boolean;
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
  isAnyFileActive: boolean;
}

const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  query,
  isStreaming,
  onQueryChange,
  onSubmit,
  onFileChange,
  isUploadingFile,
  isSidebarOpen,
  onToggleSidebar,
  isAnyFileActive
}) => {
  const chatEndRef = useRef<HTMLDivElement>(null);

  return (
    <div className={`main-content ${isSidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
      <button 
        onClick={onToggleSidebar} 
        className="sidebar-toggle-button"
        title={isSidebarOpen ? "Close sidebar" : "Open sidebar"}
      >
        {isSidebarOpen ? <ChevronLeftIcon /> : <HamburgerIcon />}
      </button>
      {messages.length === 0 ? (
        <div className="welcome-screen">
          <h1>CoReader</h1>
          <p>Ask me anything about your uploaded documents!</p>
        </div>
      ) : (
        <div className='chat-messages-container'>
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          <div ref={chatEndRef} />
        </div>
      )}

      <ChatInput
        query={query}
        isStreaming={isStreaming}
        onQueryChange={onQueryChange}
        onSubmit={onSubmit}
        onFileChange={onFileChange}
        isUploadingFile={isUploadingFile}
        isAnyFileActive={isAnyFileActive}
      />
    </div>
  );
};

export default ChatContainer; 