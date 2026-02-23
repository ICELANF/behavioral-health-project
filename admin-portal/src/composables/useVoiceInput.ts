import { ref } from 'vue'

const SpeechRecognitionClass =
  typeof window !== 'undefined'
    ? (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    : null

export function useVoiceInput() {
  const isSupported = !!SpeechRecognitionClass
  const isRecording = ref(false)
  const transcript = ref('')

  let recognition: any = null

  function startRecording() {
    if (!SpeechRecognitionClass || isRecording.value) return
    recognition = new SpeechRecognitionClass()
    recognition.lang = 'zh-CN'
    recognition.continuous = true
    recognition.interimResults = true

    recognition.onresult = (event: any) => {
      let t = ''
      for (let i = 0; i < event.results.length; i++) {
        t += event.results[i][0].transcript
      }
      transcript.value = t
    }

    recognition.onerror = () => {
      isRecording.value = false
    }

    recognition.onend = () => {
      isRecording.value = false
    }

    recognition.start()
    isRecording.value = true
  }

  function stopRecording() {
    if (recognition) {
      try { recognition.stop() } catch {}
      recognition = null
    }
    isRecording.value = false
  }

  function toggleRecording() {
    if (isRecording.value) {
      stopRecording()
    } else {
      transcript.value = ''
      startRecording()
    }
  }

  return {
    isSupported,
    isRecording,
    transcript,
    startRecording,
    stopRecording,
    toggleRecording,
  }
}
