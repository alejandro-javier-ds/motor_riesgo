import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "../components/Providers";
import { ThemeToggle } from "../components/ThemeToggle";

export const metadata: Metadata = {
  title: "Estudio sobre Patrones de Toma de Decisiones Cotidianas",
  description: "Investigación académica — SENATI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body>
        <Providers>
          <ThemeToggle />
          {children}
        </Providers>
      </body>
    </html>
  );
}