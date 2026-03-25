import React, { useState, useRef, useEffect } from 'react'
import {
  Send, Mic, MicOff, ArrowLeft, AlertTriangle,
  Activity, User, MessageSquare, ShieldAlert,
  ShieldCheck, Heart, X
} from 'lucide-react'
import axios from 'axios'
import '../styles/index.css'

const API_BASE = 'http://127.0.0.1:8000/api/v1'

const WELCOME = `Xin chào! 👋 Tôi là **MedPilot**, trợ lý AI về da liễu.

Tôi có thể giúp bạn:
• Giải thích các triệu chứng da liễu thường gặp
• Cung cấp thông tin về bệnh da, nguyên nhân, phòng ngừa
• Hướng dẫn chăm sóc da và khi nào nên đi khám

Bạn có câu hỏi gì không?`

const DANGER_KW = ['tự mua thuốc','mua thuốc','uống thuốc gì','bôi thuốc','dùng thuốc','kem gì','thuốc nào','liều lượng','tự điều trị']

function formatMessage(text) {
  return text.split('\n').map((line, i) => {
    const parts = line.split(/(\*\*[^*]+\*\*)/)
    return (
      <p key={i} className={i > 0 ? 'mt-1' : ''}>
        {parts.map((p, j) =>
          p.startsWith('**') && p.endsWith('**')
            ? <strong key={j}>{p.slice(2,-2)}</strong>
            : p
        )}
      </p>
    )
  })
}

function PatientChat({ onLogout }) {
  const [messages, setMessages] = useState([{ role: 'assistant', content: WELCOME }])
  const [input, setInput] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [medWarning, setMedWarning] = useState(false)
  const [showDisclaimer, setShowDisclaimer] = useState(true)

  const bottomRef = useRef(null)
  const mediaRef  = useRef(null)
  const chunksRef = useRef([])
  const textareaRef = useRef(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const hasDanger = text => DANGER_KW.some(k => text.toLowerCase().includes(k))

  const send = async () => {
    if (!input.trim() || isLoading) return
    const msg = input.trim()
    setInput('')
    if (hasDanger(msg)) setMedWarning(true)

    setMessages(p => [...p, { role: 'user', content: msg }, { role: 'assistant', content: 'loading' }])
    setIsLoading(true)

    try {
      const res = await axios.post(`${API_BASE}/query`, { query: msg, user_role: 'patient' }, { timeout: 300000 })
      setMessages(p => {
        const a = [...p]
        if (a[a.length-1].content === 'loading') a[a.length-1] = { role:'assistant', content: res.data.answer }
        return a
      })
    } catch {
      setMessages(p => {
        const a = [...p]
        if (a[a.length-1].content === 'loading') a[a.length-1] = {
          role:'assistant',
          content:'Xin lỗi, tôi gặp sự cố. Vui lòng thử lại.\n\nNếu bạn lo lắng về tình trạng da, hãy đến khám bác sĩ da liễu để được tư vấn chính xác.'
        }
        return a
      })
    } finally { setIsLoading(false) }
  }

  const startRec = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaRef.current = new MediaRecorder(stream)
      chunksRef.current = []
      mediaRef.current.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      mediaRef.current.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        stream.getTracks().forEach(t => t.stop())
        try {
          const form = new FormData()
          form.append('file', blob, 'audio.webm')
          const r = await axios.post(`${API_BASE}/speech/transcribe`, form, {
            headers: { 'Content-Type': 'multipart/form-data' }, timeout: 120000
          })
          setInput(r.data.transcript || '')
          textareaRef.current?.focus()
        } catch { alert('Không thể chuyển giọng nói thành văn bản. Vui lòng nhập tay.') }
      }
      mediaRef.current.start()
      setIsRecording(true)
    } catch { alert('Không thể truy cập microphone.') }
  }
  const stopRec = () => {
    if (mediaRef.current && isRecording) { mediaRef.current.stop(); setIsRecording(false) }
  }
  const onKey = e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">

      {/* Header */}
      <header className="bg-white border-b border-slate-200 px-6 py-3.5 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-emerald-100 flex items-center justify-center">
            <Activity className="w-5 h-5 text-emerald-600" />
          </div>
          <div>
            <h1 className="font-bold text-slate-900 text-sm">MedPilot — Chatbot Da Liễu</h1>
            <p className="text-xs text-slate-400">Trả lời câu hỏi về bệnh da — chỉ mang tính giáo dục</p>
          </div>
        </div>
        <button className="btn-ghost text-xs" onClick={onLogout}>
          <ArrowLeft className="w-4 h-4" /> Đổi vai trò
        </button>
      </header>

      {/* Med warning banner */}
      {medWarning && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2 text-red-700">
            <ShieldAlert className="w-4 h-4 flex-shrink-0" />
            <p className="text-xs"><strong>Lưu ý quan trọng:</strong> Không tự mua thuốc. Chỉ dùng thuốc theo đơn của bác sĩ da liễu.</p>
          </div>
          <button onClick={() => setMedWarning(false)} className="text-red-400 hover:text-red-600"><X className="w-3.5 h-3.5" /></button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-6 px-4">
        <div className="max-w-2xl mx-auto space-y-4">

          {/* Disclaimer card */}
          {showDisclaimer && (
            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3 animate-fade-up">
              <ShieldCheck className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <p className="text-xs text-amber-800 leading-relaxed">
                  <strong>Tuyên bố miễn trách:</strong> MedPilot chỉ cung cấp thông tin giáo dục, không thay thế tư vấn bác sĩ và không kê đơn thuốc. Nếu có triệu chứng nghiêm trọng, hãy đến cơ sở y tế ngay.
                </p>
              </div>
              <button onClick={() => setShowDisclaimer(false)} className="text-amber-400 hover:text-amber-600 flex-shrink-0"><X className="w-3.5 h-3.5" /></button>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-up`}>
              {m.role === 'assistant' && (
                <div className="w-7 h-7 rounded-xl bg-emerald-100 flex items-center justify-center mr-2 flex-shrink-0 mt-1">
                  <Heart className="w-3.5 h-3.5 text-emerald-600" />
                </div>
              )}
              <div className={m.role === 'user' ? 'bubble-user' : 'bubble-ai'}>
                {m.content === 'loading' ? (
                  <div className="flex items-center gap-2 text-slate-400">
                    <span className="dot-bounce w-2 h-2 bg-slate-400 rounded-full inline-block" />
                    <span className="dot-bounce w-2 h-2 bg-slate-400 rounded-full inline-block" />
                    <span className="dot-bounce w-2 h-2 bg-slate-400 rounded-full inline-block" />
                    <span className="text-xs ml-1">Đang xử lý...</span>
                  </div>
                ) : (
                  <div className="leading-relaxed">
                    {m.role === 'assistant' && m.content.toLowerCase().includes('đi khám') && (
                      <div className="flex items-center gap-1 text-emerald-600 text-xs font-medium mb-1.5">
                        <ShieldCheck className="w-3.5 h-3.5" /> Khuyến nghị gặp bác sĩ
                      </div>
                    )}
                    {formatMessage(m.content)}
                  </div>
                )}
              </div>
              {m.role === 'user' && (
                <div className="w-7 h-7 rounded-xl bg-blue-100 flex items-center justify-center ml-2 flex-shrink-0 mt-1">
                  <User className="w-3.5 h-3.5 text-blue-600" />
                </div>
              )}
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Safety bar */}
      <div className="bg-amber-50 border-t border-amber-100 px-6 py-2">
        <div className="max-w-2xl mx-auto flex items-center gap-2 text-amber-700">
          <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
          <p className="text-xs">Thông tin chỉ mang tính giáo dục. Triệu chứng nghiêm trọng → đến cơ sở y tế ngay.</p>
        </div>
      </div>

      {/* Input */}
      <div className="bg-white border-t border-slate-200 px-4 py-4">
        <div className="max-w-2xl mx-auto">
          <div className="flex items-end gap-2">
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                id="chat-input"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={onKey}
                placeholder="Nhập câu hỏi về da liễu..."
                className="input resize-none pr-3 leading-relaxed"
                rows={1}
                style={{ maxHeight: '120px' }}
              />
            </div>
            <button
              id="mic-btn"
              onClick={isRecording ? stopRec : startRec}
              className={`btn-icon transition-colors ${isRecording ? 'bg-red-100 text-red-600 hover:bg-red-200' : ''}`}
              title={isRecording ? 'Dừng ghi âm' : 'Ghi âm'}
            >
              {isRecording
                ? <MicOff className="w-5 h-5 animate-recording" style={{animation:'recording-ring 1.5s ease-in-out infinite'}} />
                : <Mic className="w-5 h-5" />}
            </button>
            <button
              id="send-btn"
              onClick={send}
              disabled={!input.trim() || isLoading}
              className="btn-success disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
          <p className="text-xs text-slate-400 mt-2 text-center">Enter gửi · Shift+Enter xuống dòng</p>
        </div>
      </div>
    </div>
  )
}

export default PatientChat
