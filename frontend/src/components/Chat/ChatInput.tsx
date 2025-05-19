import SendIcon from '../common/SendIcon';

interface ChatInputProps {
  query: string;
  isStreaming: boolean;
  onQueryChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onSubmit: () => void;
}

const ChatInput: React.FC<ChatInputProps> = ({
  query,
  isStreaming,
  onQueryChange,
  onSubmit
}) => {
  return (
    <div className='query-input-area'>
      <textarea
        className='query-textarea'
        value={query}
        onChange={onQueryChange}
        placeholder="Send a message..."
        rows={1}
        disabled={isStreaming}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            onSubmit();
          }
        }}
      />
      <button
        className='submit-chat-button'
        onClick={onSubmit}
        disabled={isStreaming || !query.trim()}
      >
        <SendIcon />
      </button>
    </div>
  );
};

export default ChatInput; 