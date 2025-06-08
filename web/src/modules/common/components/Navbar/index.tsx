'use client'

export default function Navbar() {
    return (
        <header className={'w-full flex items-center fixed bg-transparent px-4 py-2 z-10 gap-6'}>
            <h1 className={'font-bold text-white text-3xl'}>GUNCANG</h1>
            <nav className={'flex gap-6 w-1/12'}>
                <a href={'/live'} className={'text-white hover:text-gray-400'}>Live</a>
                <a href={'/about'} className={'text-white hover:text-gray-400'}>About</a>
            </nav>
        </header>
    )
}
