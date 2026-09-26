import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agentropy — Agent observability, minus the noise",
  description:
    "Simple, beautiful observability for AI agents. We turn what your agents do into insights and predictions.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-zinc-50 text-zinc-900 antialiased">
        {children}
      </body>
    </html>
  );
}
