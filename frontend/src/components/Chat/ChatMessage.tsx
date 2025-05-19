import type { ChatMessage as ChatMessageType } from '../../types';

interface ChatMessageProps {
  message: ChatMessageType;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  return (
    <div className={`message-wrapper ${message.type}-message-wrapper`}>
      <div className={`message ${message.type}-message`}>
        <div className="message-content">
          {message.content.split('\n').map((line, index) => (
            <span key={index}>
              {line}
              {index === message.content.split('\n').length - 1 ? '' : <br/>}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage; 