"use client";

import { usePathname } from "next/navigation";
import Footer from "./Footer";

export default function FootWrapper() {
    const pathname = usePathname() || "";
    const hiddenOn = ["/terms", "/privacy"];
    if (hiddenOn.includes(pathname)) return null;
    return <Footer />;
}