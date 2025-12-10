export const lightTheme = {
  name: 'light',
  colors: {
    primary: '#0065c4ff', 
    secondary: '#000000ff', 
    background: '#d9ebeeb0',
    surface: '#ffffffff',
    text: '#000000ff', 
    textSecondary: '#292929ff', 
    border: '#5E524014', 
    error: '#C0152F',
    success: '#218091',
    warning: '#A84B2F',
  },
};

export const darkTheme = {
  name: 'dark',
  colors: {
    primary: '#32B8C6', // teal light
    secondary: '#A7A9A9', // gray
    background: '#1F2121', // charcoal dark
    surface: '#262828', // charcoal
    text: '#F5F5F5', // light gray
    textSecondary: '#A7A9A9', // gray
    border: '#7A7C7C4D', // gray with opacity
    error: '#FF5459',
    success: '#32B8C6',
    warning: '#E6816101',
  },
};

export const themeService = {
  getCurrentTheme: () => {
    const saved = localStorage.getItem('theme');
    if (saved) return saved === 'dark' ? darkTheme : lightTheme;
    
    // Check system preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    return prefersDark ? darkTheme : lightTheme;
  },

  setTheme: (themeName) => {
    localStorage.setItem('theme', themeName);
  },

  toggleTheme: () => {
    const current = themeService.getCurrentTheme();
    const newTheme = current.name === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', newTheme);
    return newTheme === 'dark' ? darkTheme : lightTheme;
  },

  isDarkMode: () => {
    const saved = localStorage.getItem('theme');
    if (saved) return saved === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  },
};

export const applyTheme = (theme) => {
  const root = document.documentElement;
  Object.entries(theme.colors).forEach(([key, value]) => {
    root.style.setProperty(`--color-${key}`, value);
  });
};

export default themeService;
