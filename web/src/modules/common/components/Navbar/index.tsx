'use client'

import {usePathname} from "next/navigation";

export default function Navbar() {
    const pathname = usePathname()
    return (
        <header className={'w-full flex items-center bg-transparent px-4 py-2 z-10 gap-6'}>
            <h1 className={'font-bold text-white text-3xl'}>GUNCANG</h1>
            <nav className={'flex gap-6 w-1/12'}>
                <a href={'/live'} className={`text-white hover:text-gray-400 ${pathname.includes('live') && 'font-bold'}`}>Live</a>
                <a href={'/archive'} className={`text-white hover:text-gray-400 ${pathname.includes('archive') && 'font-bold'}`}>Archive</a>
            </nav>
        </header>
    )
}
