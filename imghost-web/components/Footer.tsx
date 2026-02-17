"use client";

import Link from "next/link";

export default function Footer() {
    return (
        <footer className="w-full mt-8 text-[10px] text-zinc-700 uppercase tracking-[0.2em]">
            <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col sm:flex-row items-center justify-between gap-2">
            <nav className="flex items-center gap-4">
                <Link href="/terms" className="text-zinc-500 hover:text-accent">Terms</Link>
                <Link href="/privacy" className="text-zinc-500 hover:text-accent">Privacy</Link>
                <a href="mailto:hi@speedhawks.online" className="text-zinc-500">Contact</a>
            </nav>
            <div className="text-zinc-500 text-xs">© {new Date().getFullYear()} ImgHost / SpeedHawks</div>
            </div>
        </footer>
    );
}