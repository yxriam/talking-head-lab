import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FrameTrace｜视频生成痕迹实验室",
  description: "四种可解释方法检查视频异常，全程在浏览器本地完成。",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
