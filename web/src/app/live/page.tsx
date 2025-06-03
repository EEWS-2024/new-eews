'use server';

export default async function LivePage() {
    return (
        <div className={'w-full h-screen bg-gray-900'}>
            <div className={'flex items-center justify-center h-full'}>
                <h1 className={'text-4xl text-white font-bold'}>Live Page</h1>
            </div>
        </div>
    )
}