import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Kanbix AI Help Center",
  description: "Customer Success Agent Dashboard & Support Portal",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
