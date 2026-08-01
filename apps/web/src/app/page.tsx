import { PageContainer } from "@/components/app-shell/page-container"
import { TTSStudio } from "@/components/tts/tts-studio"

export default function HomePage() {
  return (
    <PageContainer>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Text to Speech Studio</h1>
        <p className="text-sm text-muted-foreground">Tạo giọng đọc tự nhiên từ văn bản</p>
      </div>
      <TTSStudio />
    </PageContainer>
  )
}
