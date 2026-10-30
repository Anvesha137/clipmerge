import './globals.css';
import type { Metadata } from 'next';
export const metadata: Metadata = {title:'ClipMerge — Audio Studio',description:'Trim, arrange, fade and merge your own audio files in your browser.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
