'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'theme-dark' | 'theme-catppuccin' | 'theme-macchiato' | 'theme-nordic' | 'theme-gruvbox' | 'theme-dracula' | 'theme-tokyo';

interface ThemeContextType {
    theme: Theme;
    setThemeState: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
    const [theme, setThemeState] = useState<Theme>('theme-dark');

    useEffect(() => {
        const savedTheme = localStorage.getItem('theme') as Theme;
        if (savedTheme) {
            setThemeState(savedTheme);
        }
    }, []);

    useEffect(() => {
        document.documentElement.classList.remove(
            'theme-dark',
            'theme-catppuccin',
            'theme-macchiato',
            'theme-nordic',
            'theme-gruvbox',
            'theme-dracula',
            'theme-tokyo'
        );

        document.documentElement.classList.add(theme);
        localStorage.setItem('theme', theme);
    }, [theme]);


    return (
        <ThemeContext.Provider value={{ theme, setThemeState }}>
            {children}
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error('usethemTheme must be uesd within ThemeProvider');
    }
    return context;
}