import { useTheme } from '../../context/ThemeContext';

const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  return (
    <label htmlFor="themeToggle" className="theme-toggle-switch">
      <input
        id="themeToggle"
        type="checkbox"
        checked={theme === 'dark'}
        onChange={toggleTheme}
      />
      <span className="toggle-track">
        <span className="toggle-thumb"></span>
        <span className="emoji-sun">😎</span>
        <span className="emoji-moon">😴</span>
      </span>
    </label>
  );
};

export default ThemeToggle; 