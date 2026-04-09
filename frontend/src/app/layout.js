import { Inter, Playfair_Display } from "next/font/google";
import "@/styles/globals.css";

const inter = Inter({ 
  subsets: ["latin"],
  variable: '--font-inter',
  display: 'swap',
});

const playfair = Playfair_Display({ 
  subsets: ["latin"],
  variable: '--font-playfair',
  display: 'swap',
});

export const metadata = {
  title: "Digital FTE — Intelligent Customer Success",
  description: "Enterprise CRM & Autonomous Agent",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${inter.variable} ${playfair.variable}`}>
      <body className="bg-background text-text antialiased min-h-screen flex flex-col">
        {children}
      </body>
    </html>
  );
}
