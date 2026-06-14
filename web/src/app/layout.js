import "./globals.css";

export const metadata = {
  title: "qwerty | Autonomous AI VPS Manager",
  description:
    "qwerty is an autonomous AI VPS manager. See every session in realtime and audit connection snapshots the moment they occur. Run dry-run commands and teach system memories in simple language.",
  keywords: "VPS manager, AI terminal, SSH automation, server management, Claude AI",
  openGraph: {
    title: "qwerty | Autonomous AI VPS Manager",
    description: "See every session in realtime and audit connection snapshots the moment they occur.",
    type: "website",
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="min-h-screen">
      <body>{children}</body>
    </html>
  );
}
