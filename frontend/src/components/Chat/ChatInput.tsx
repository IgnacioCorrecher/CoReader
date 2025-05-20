import SendIcon from '../common/SendIcon';
import AttachmentIcon from '../common/AttachmentIcon';

interface ChatInputProps {
  query: string;
  isStreaming: boolean;
  onQueryChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  onSubmit: () => void;
  onFileChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  isUploadingFile: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({
  query,
  isStreaming,
  onQueryChange,
  onSubmit,
  onFileChange,
  isUploadingFile
}) => {
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    onFileChange(event);
    // Reset the input value so the same file can be selected again
    event.target.value = '';
  };

  return (
    <div className='query-input-area'>
      <input 
        type="file" 
        id="file-upload"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
        accept=".txt,.pdf,.doc,.docx"
        disabled={isUploadingFile}
      />
      <label 
        htmlFor="file-upload" 
        style={{ 
          cursor: isUploadingFile ? 'wait' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          padding: '10px',
          color: isUploadingFile ? 'var(--button-disabled-bg)' : 'var(--text-secondary)',
          borderRadius: '50%',
          transition: 'all 0.3s ease',
          position: 'relative',
          overflow: 'hidden',
          opacity: isUploadingFile ? 0.6 : 1
        }}
        onMouseEnter={(e) => {
          if (!isUploadingFile) {
            const target = e.currentTarget;
            target.style.backgroundColor = 'var(--accent-color)';
            target.style.color = 'white';
            target.style.transform = 'scale(1.1)';
            target.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.15)';
          }
        }}
        onMouseLeave={(e) => {
          if (!isUploadingFile) {
            const target = e.currentTarget;
            target.style.backgroundColor = 'transparent';
            target.style.color = 'var(--text-secondary)';
            target.style.transform = 'scale(1)';
            target.style.boxShadow = 'none';
          }
        }}
      >
        <AttachmentIcon />
      </label>
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
        style={{
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '10px',
          color: 'var(--text-secondary)',
          backgroundColor: 'transparent',
          border: 'none',
          borderRadius: '50%',
          transition: 'all 0.3s ease',
          position: 'relative',
          overflow: 'hidden',
          width: '44px',
          height: '44px',
        }}
        onMouseEnter={(e) => {
          if (!e.currentTarget.disabled) {
            const target = e.currentTarget;
            target.style.backgroundColor = 'var(--accent-color)';
            target.style.color = 'white';
            target.style.transform = 'scale(1.1)';
            target.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.15)';
          }
        }}
        onMouseLeave={(e) => {
          if (!e.currentTarget.disabled) {
            const target = e.currentTarget;
            target.style.backgroundColor = 'transparent';
            target.style.color = 'var(--text-secondary)';
            target.style.transform = 'scale(1)';
            target.style.boxShadow = 'none';
          }
        }}
      >
        <SendIcon />
      </button>
    </div>
  );
};

export default ChatInput; 