import type { Metadata } from "next";
import VideoLab from "./VideoLab";

export const metadata: Metadata = {
  title: "FrameTrace｜视频生成痕迹实验室",
  description: "在浏览器本地检查视频的时序、运动与频域异常，不上传原始视频。",
};

export default function Home() {
  return <VideoLab />;
}
