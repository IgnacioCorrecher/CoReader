interface ToastProps {
  message: string;
  isVisible: boolean;
}

const Toast: React.FC<ToastProps> = ({ message, isVisible }) => {
  if (!isVisible) return null;
  
  return (
    <div className="toast-notification">
      {message}
    </div>
  );
};

export default Toast; 