import { useRef } from 'react';
import type { ChatMessage as ChatMessageType } from '../../types';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';

interface ChatContainerProps {
  messages: ChatMessageType[];
  query: string;
  isStreaming: boolean;
  onQueryChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onSubmit: () => void;
}

const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  query,
  isStreaming,
  onQueryChange,
  onSubmit
}) => {
  const chatEndRef = useRef<HTMLDivElement>(null);

  return (
    <div className='main-content'>
      {messages.length === 0 ? (
        <div className="welcome-screen">
          <h1>RAG Application</h1>
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
      />
    </div>
  );
};

export default ChatContainer; 