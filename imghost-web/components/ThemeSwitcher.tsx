'use client';

import { useTheme } from '@/components/ThemeProvider';
import { Palette } from 'lucide-react';
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const themes = [
    { id: 'theme-dark', name:'Neon Red', color: '#ff0000'},
    { id: 'theme-catppuccin', name:'Catppuccin', color: '#cba6f7'},
    { id: 'theme-macchiato', name:'Macchiato', color: '#ed8796'},
    { id: 'theme-nordic', name:'Nordic', color: '#88c0d0'},
    { id: 'theme-gruvbox', name:'Gruvbox', color: '#fe8019'},
    { id: 'theme-dracula', name:'Dracula', color: '#ff79c6'},
    { id: 'theme-tokyo', name:'Tokyo', color: '#7aa2f7'}
    ]

export function ThemeSwitcher() {
    const { theme, setThemeState } = useTheme();
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className='relative'>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="p-2 rounded-lg border border-border hover:border-accent transition-all"
                title='Change them'
            >
             <Palette className='w-4 h-4 text-zinc-400 hover:text-accent transition-colors' />
            </button>

            <AnimatePresence>
                {isOpen && (
                    <>
                    <div className='fixed inset-0 z-10' onClick={() => setIsOpen(false)}></div>
                    <motion.div
                    initial={{ opacity:0, scale:0.95, y: -4 }}
                    animate={{ opacity:1, scale:1, y: 0 }}
                    exit={{ opacity:0, scale:0.95, y:-4 }}
                    transition={{ duration: 0.15 }}
                    className='absolute top-full right-0 mt-2 z-20 bg-zinc-950 border border-zinc-800 rounded-xl p-3 shadow-2xl min-w[180px]'
                    >
                     <div className='text-[10px] uppercase tracking-widest text-zinc-500 font-bold mb-3'>
                        Select Theme
                     </div>
                     <div className='space-y-1'>
                        {themes.map((t) => (
                            <button key={t.id} onClick={() => {
                                setThemeState(t.id as any);
                                setIsOpen(false);
                            }}
                            className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs transition-all ${
                                theme === t.id 
                                ? 'bg-accent text-white'
                                : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
                            }`}
                            >
                                <div className='w-3 h-3 rounded-full border border-zinc-700' style={{ backgroundColor: t.color }} />
                                {t.name}
                            </button>
                        ))}
                     </div>
                    </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
}