import { useTheme } from '../../context/ThemeContext';
import owlImage from '../../assets/CoReader-icon.png';

interface OwlLogoProps {
  size?: number | string;
  className?: string;
  responsive?: boolean;
}

const OwlLogo: React.FC<OwlLogoProps> = ({ 
  size = 120, 
  className = '', 
  responsive = false 
}) => {
  const { theme } = useTheme();
  
  // Determine sizing based on responsive prop
  const containerStyle = responsive 
    ? {
        width: '100%',
        maxWidth: typeof size === 'number' ? `${size}px` : size,
        height: 'auto',
        aspectRatio: '1',
        minWidth: '60px', // Minimum size for small screens
      }
    : {
        width: typeof size === 'number' ? `${size}px` : size,
        height: typeof size === 'number' ? `${size}px` : size,
      };
  
  return (
    <div 
      className={`owl-logo ${className}`}
      style={{ 
        ...containerStyle,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transition: 'all 0.3s ease'
      }}
    >
      <img 
        src={owlImage}
        alt="CoReader Owl Logo"
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
          filter: theme === 'dark' ? 'brightness(0.9)' : 'none',
          // Ensure transparent background is preserved
          backgroundColor: 'transparent',
          // Smooth scaling transition
          transition: 'filter 0.3s ease, transform 0.2s ease',
        }}
        onLoad={(e) => {
          // Ensure the image maintains its transparent background
          const img = e.target as HTMLImageElement;
          img.style.backgroundColor = 'transparent';
        }}
      />
    </div>
  );
};

export default OwlLogo; 