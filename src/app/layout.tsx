/* eslint-disable @next/next/no-img-element */
import "./globals.css"
import type { ReactNode } from "react"

export const metadata = {
  title: "CADGen AI - Text-to-3D CAD Platform",
  description: "Generate parametric 3D CAD models from natural language prompts",
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
