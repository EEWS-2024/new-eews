'use client'

import {useParams} from "next/navigation";
import Link from "next/link";

export default function Navbar() {
    const {streamType} = useParams()
    return (
        <header className={'w-full flex items-center bg-transparent px-4 py-2 z-10 gap-6 text-white'}>
            <h1 className={'font-bold text-3xl'}>GUNCANG</h1>
            <nav className={'flex gap-2 w-1/12'}>
                <Link href={'/live'} className={`hover:text-gray-400 rounded-lg py-1 px-4 ${streamType === 'live' && 'font-bold bg-indigo-600'}`}>Live</Link>
                <Link href={'/archive'} className={`hover:text-gray-400 rounded-lg py-1 px-4 ${streamType === 'archive' && 'font-bold bg-indigo-600'}`}>Archive</Link>
            </nav>
        </header>
    )
}
