'use client';

import dynamic from 'next/dynamic';

const NetworkGraph = dynamic(() => import('@/components/NetworkGraph'), { ssr: false });

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <h1 className="text-4xl font-bold mb-8">Email Network Graph</h1>
      <div className="w-full max-w-5xl border rounded-lg shadow-lg bg-white overflow-hidden text-black">
        <NetworkGraph />
      </div>
    </main>
  );
}
