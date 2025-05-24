import type { ChatMessage as ChatMessageType } from '../../types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Citations from './Citations';

interface ChatMessageProps {
  message: ChatMessageType;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  return (
    <div className={`message-wrapper ${message.type}-message-wrapper`}>
      <div className={`message ${message.type}-message`}>
        <div className="message-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
          {message.type === 'ai' && message.citations && (
            <Citations citations={message.citations} />
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage; 