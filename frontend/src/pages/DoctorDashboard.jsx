import React, { useState, useRef } from 'react'
import {
  Mic, MicOff, Upload, FileAudio, User, Clock, MapPin,
  AlertCircle, Check, X, Edit3, Save, ArrowLeft, Loader2,
  MessageSquare, Stethoscope, Heart, Activity, ChevronDown,
  ChevronUp, AlertTriangle, Sparkles, ShieldAlert, RotateCcw,
  CheckCircle, XCircle, PlusCircle, Eye
} from 'lucide-react'
import axios from 'axios'
import { transcribeAudio } from '../services/api'
import '../styles/index.css'

const API_BASE = '/api/v1'

// Axios default headers for Ngrok tunnel
const NGROK_HEADERS = {
  'ngrok-skip-browser-warning': 'true',
  'User-Agent': 'MedPilot-Frontend/1.0'
}

// ─── Processing steps config ──────────────────────────────
const STEPS = [
  { key: 'upload',    label: 'Gửi audio lên server' },
  { key: 'stt',       label: 'Chuyển giọng nói → văn bản (Whisper)' },
  { key: 'extract',   label: 'Trích xuất thông tin y khoa (AI)' },
  { key: 'suggest',   label: 'Sinh gợi ý lâm sàng (AI)' },
]

// ─── Helpers ──────────────────────────────────────────────
const EMPTY_EXTRACT = {
  reason_for_visit: '', main_symptoms: [], onset_time: '',
  lesion_location: '', related_factors: [], medical_history: [],
  previous_treatment: [], missing_fields: [], summary: ''
}
const EMPTY_SUGGEST = {
  missing_fields: [], questions_to_ask: [], red_flags: [],
  differential_diagnosis: [], clinical_reminders: []
}

function AiTag() {
  return <span className="ai-tag"><Sparkles className="w-3 h-3" />AI</span>
}

function StatusBadge({ status }) {
  const map = {
    pending:   ['badge-pending', 'Chờ duyệt'],
    approved:  ['badge-green',   'Đã duyệt'],
    rejected:  ['badge-red',     'Huỷ'],
  }
  const [cls, label] = map[status] || map.pending
  return <span className={`badge ${cls}`}>{label}</span>
}

function FieldLabel({ label, missing, uncertain, icon: Icon }) {
  return (
    <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">
      {Icon && <Icon className="w-3.5 h-3.5" />}
      {label}
      {missing   && <span className="ml-1 text-amber-600 flex items-center gap-0.5"><AlertCircle className="w-3 h-3" />Thiếu</span>}
      {uncertain && <span className="ml-1 text-blue-500 flex items-center gap-0.5"><Eye className="w-3 h-3" />Chưa chắc</span>}
    </label>
  )
}

// ─── Main Component ───────────────────────────────────────
function DoctorDashboard({ onLogout }) {
  const [step, setStep]             = useState('idle')   // idle | recording | processing | reviewing
  const [patientCode, setPatientCode] = useState('')
  const [medicalRecord, setMedicalRecord] = useState('')
  const [audioFile, setAudioFile]   = useState(null)
  const [transcript, setTranscript] = useState('')
  const [draftNote, setDraftNote]   = useState('')
  const [extracted, setExtracted]   = useState(EMPTY_EXTRACT)
  const [edited, setEdited]         = useState({})
  const [suggestions, setSuggestions] = useState(EMPTY_SUGGEST)
  const [isRecording, setIsRecording] = useState(false)
  const [currentProcStep, setCurrentProcStep] = useState(0) // index in STEPS
  const [fieldStatus, setFieldStatus] = useState({})   // {fieldKey: 'approved'|'rejected'}
  const [expandedSection, setExpandedSection] = useState({ form: true, draft: true, suggest: true })
  const [saved, setSaved] = useState(false)

  const mediaRef = useRef(null)
  const chunksRef = useRef([])
  const fileInputRef = useRef(null)

  // ── Recording ──
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaRef.current = new MediaRecorder(stream)
      chunksRef.current = []
      mediaRef.current.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      mediaRef.current.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setAudioFile(blob)
        stream.getTracks().forEach(t => t.stop())
      }
      mediaRef.current.start()
      setIsRecording(true)
    } catch { alert('Không thể truy cập microphone. Kiểm tra quyền truy cập.') }
  }
  const stopRecording = () => {
    if (mediaRef.current && isRecording) { mediaRef.current.stop(); setIsRecording(false) }
  }
  const handleFile = e => {
    const f = e.target.files[0]
    if (!f) return
    const ok = ['audio/webm','audio/mp3','audio/wav','audio/m4a','audio/mpeg','audio/ogg']
      .some(t => f.type.includes(t.split('/')[1])) ||
      ['.webm','.mp3','.wav','.m4a','.ogg'].some(x => f.name.toLowerCase().endsWith(x))
    if (!ok) { alert('Chỉ chấp nhận file audio (.webm .mp3 .wav .m4a .ogg)'); return }
    if (f.size > 50 * 1024 * 1024) { alert('File quá 50MB'); return }
    setAudioFile(f)
  }

  const processAudio = async () => {
    if (!audioFile) return
    setStep('processing')
    setCurrentProcStep(0)

    try {
      // Step 1 – STT (PhoWhisper — gọi trực tiếp từ browser qua api.js)
      setCurrentProcStep(1)
      const tRes = await transcribeAudio(audioFile)
      const text = tRes.transcript || tRes.text || ''
      setTranscript(text)

      // Step 2 – Extract (send transcript to backend → LLM extraction)
      setCurrentProcStep(2)
      let exData = EMPTY_EXTRACT
      try {
        const eRes = await axios.post(`${API_BASE}/speech/extract`, {
          transcript: text,
          medical_record: medicalRecord
        }, {
          headers: { 'Content-Type': 'application/json', ...NGROK_HEADERS },
          timeout: 300000
        })
        // Response: { structured_data: {...}, transcript, success }
        const sd = eRes.data.structured_data || {}
        exData = { ...EMPTY_EXTRACT, ...sd }
      } catch (e) {
        console.warn('Extract failed, using empty fallback:', e.message)
      }
      setExtracted(exData)
      setEdited({})

      // Step 3 – Suggestions (via RAG query with doctor role)
      setCurrentProcStep(3)
      // --- 1. Populate Suggestions from Structured Rules (BACKEND) ---
      let sugs = {
        missing_fields: exData.missing_fields || [],
        questions_to_ask: (exData.questions_to_ask || []).map(q => q.trim()),
        red_flags: (exData.red_flags || []).map(rf => rf.trim()),
        differential_diagnosis: (exData.possible_considerations || []).map(c => ({
          name: c,
          likelihood: 'Quy tắc y khoa'
        })),
        clinical_reminders: (exData.clinical_reminders || []).map(r => r.trim()),
        alert_level: exData.alert_level || 'normal'
      }

      // --- 2. Try to supplement with RAG Query ---
      try {
        const symptoms = (exData.main_symptoms || []).join(', ')
        const q = [
          exData.reason_for_visit && `Lý do khám: ${exData.reason_for_visit}`,
          symptoms && `Triệu chứng: ${symptoms}`,
          exData.onset_time && `Thời gian: ${exData.onset_time}`,
          exData.lesion_location && `Vị trí tổn thương: ${exData.lesion_location}`,
        ].filter(Boolean).join('. ') || text.slice(0, 300)

        const sRes = await axios.post(`${API_BASE}/query`, {
          query: q,
          user_role: 'doctor',
          top_k: 5
        }, {
          headers: { 'Content-Type': 'application/json', ...NGROK_HEADERS },
          timeout: 60000 // Reduced timeout
        })

        const ans = sRes.data.answer || ''
        if (ans) {
          // Merge with existing suggestions
          const aiDx = buildDx(ans)
          aiDx.forEach(dx => {
            if (!sugs.differential_diagnosis.some(h => h.name === dx.name)) {
              sugs.differential_diagnosis.push(dx)
            }
          })

          sugs.questions_to_ask = [...new Set([...sugs.questions_to_ask, ...extractBullets(ans, ['hỏi thêm', 'câu hỏi', '?'])])]
          sugs.red_flags = [...new Set([...sugs.red_flags, ...extractBullets(ans, ['nguy hiểm', 'cấp cứu', 'nghiêm trọng', 'red flag'])])]
          sugs.clinical_reminders = [...new Set([...sugs.clinical_reminders, ...extractBullets(ans, ['lưu ý', 'nhắc', 'kiểm tra', 'cân nhắc'])])]
        }
      } catch (e) {
        console.warn('RAG Query skipped/failed:', e.message)
      }
      setDraftNote(exData.draft_notes || buildDraftNote(exData, text))
      setSuggestions(sugs)
      setFieldStatus({})
      setStep('reviewing')

    } catch (err) {
      alert('Lỗi xử lý: ' + (err.response?.data?.detail || err.message))
      setStep('recording')
    }
  }

  // Utilities for parsing LLM answer
  const extractBullets = (text, keywords) => {
    const lines = text.split(/[\n•\-]/).map(l => l.trim()).filter(l => l.length > 10)
    const scored = lines.map(l => {
      const lc = l.toLowerCase()
      return { l, score: keywords.filter(k => lc.includes(k)).length }
    })
    return scored.filter(x => x.score > 0).slice(0, 4).map(x => x.l)
  }
  const buildDx = (text) => {
    if (!text) return []
    const hits = []
    const patterns = [
      { kw: 'viêm da tiếp xúc', lk: 'Cao' },
      { kw: 'eczema|chàm', lk: 'Trung bình' },
      { kw: 'mề đay|nổi mề đay', lk: 'Thấp' },
      { kw: 'vảy nến|psoriasis', lk: 'Thấp' },
      { kw: 'nấm da|dermatophyt', lk: 'Trung bình' },
      { kw: 'ghẻ|scabies', lk: 'Trung bình' },
      { kw: 'thủy đậu|varicella', lk: 'Thấp' }
    ]
    
    // 1. Check predefined patterns first
    for (const p of patterns) {
      if (new RegExp(p.kw, 'i').test(text)) {
        hits.push({ name: p.kw.split('|')[0], likelihood: p.lk })
      }
    }
    
    // 2. Dynamically extract "CÓ THỂ là X" patterns from AI response
    const dynamicRegex = /(?:CÓ THỂ là|Gợi ý:|Chẩn đoán:|Nghi ngờ:)\s*([^\n.;()]+)/gi
    let match
    while ((match = dynamicRegex.exec(text)) !== null) {
      const name = match[1].trim()
      if (name.length > 5 && !hits.some(h => h.name.toLowerCase() === name.toLowerCase())) {
        hits.push({ name, likelihood: 'Cần cân nhắc' })
      }
      if (hits.length >= 5) break
    }

    return hits.length ? hits : [{ name: 'Chưa xác định – cần thêm thông tin', likelihood: 'N/A' }]
  }
  const buildDraftNote = (ex, tr) => `**Hồ sơ khám da liễu**
Bệnh nhân: ${patientCode || '(chưa điền)'}
Lý do khám: ${ex.reason_for_visit || '—'}
Triệu chứng: ${(ex.main_symptoms || []).join(', ') || '—'}
Thời gian xuất hiện: ${ex.onset_time || '—'}
Vị trí tổn thương: ${ex.lesion_location || '—'}
Yếu tố liên quan: ${(ex.related_factors || []).join(', ') || '—'}
Tiền sử: ${(ex.medical_history || []).join(', ') || '—'}
Điều trị trước: ${(ex.previous_treatment || []).join(', ') || '—'}

Tóm tắt AI: ${ex.summary || '—'}

Transcript (raw): ${tr.slice(0, 300)}${tr.length > 300 ? '…' : ''}`

  const fieldVal = k => (k in edited) ? edited[k] : (extracted[k] ?? '')
  const setField = (k, v) => setEdited(p => ({ ...p, [k]: v }))
  const isMissing = k => (suggestions.missing_fields || []).some(f => f.toLowerCase().includes(k.toLowerCase()))

  const approveField = (k, state) => setFieldStatus(p => ({ ...p, [k]: state }))
  const toggleSection = k => setExpandedSection(p => ({ ...p, [k]: !p[k] }))

  const saveConsultation = () => { setSaved(true); setTimeout(() => setStep('idle'), 1500) }
  const reset = () => {
    setStep('idle'); setAudioFile(null); setTranscript(''); setExtracted(EMPTY_EXTRACT)
    setEdited({}); setSuggestions(EMPTY_SUGGEST); setDraftNote(''); setPatientCode('')
    setMedicalRecord(''); setSaved(false)
  }

  // ────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-50 flex">

      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center mb-4">
          <Activity className="w-5 h-5 text-white" />
        </div>
        <button title="Khám mới" className={`sidebar-icon ${step !== 'reviewing' ? 'active' : ''}`} onClick={reset}>
          <Stethoscope className="w-5 h-5" />
        </button>
        <button title="Hồ sơ" className="sidebar-icon">
          <User className="w-5 h-5" />
        </button>
        <button title="Lịch sử" className="sidebar-icon">
          <MessageSquare className="w-5 h-5" />
        </button>
        <div className="mt-auto">
          <button title="Đổi vai trò" className="sidebar-icon" onClick={onLogout}>
            <ArrowLeft className="w-5 h-5" />
          </button>
        </div>
      </aside>

      {/* ── Main area ── */}
      <div className="ml-16 flex-1 flex flex-col min-h-screen">

        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <Stethoscope className="w-6 h-6 text-blue-600" />
            <div>
              <h1 className="font-bold text-slate-900">MedPilot — Chế độ Bác sĩ</h1>
              <p className="text-xs text-slate-400">Hỗ trợ khám da liễu — chỉ mang tính tham khảo</p>
            </div>
          </div>
          {patientCode && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-lg">
              <User className="w-4 h-4 text-blue-500" />
              <span className="text-sm font-medium text-blue-700">Mã BN: {patientCode}</span>
            </div>
          )}
        </header>

        {/* ─── IDLE ─── */}
        {step === 'idle' && (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="w-full max-w-md">
              <div className="card p-8 text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-5">
                  <FileAudio className="w-8 h-8 text-blue-600" />
                </div>
                <h2 className="text-xl font-bold text-slate-800 mb-2">Bắt đầu phiên khám mới</h2>
                <p className="text-slate-500 text-sm mb-6">Ghi âm hoặc tải lên audio hội thoại bác sĩ – bệnh nhân</p>
                <div className="space-y-3 text-left">
                  <div>
                    <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5 block">Mã bệnh nhân</label>
                    <input id="patient-code-input" className="input" placeholder="VD: BN-2024-001 (tùy chọn)"
                      value={patientCode} onChange={e => setPatientCode(e.target.value)} />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5 block">Hồ sơ bệnh án cũ (nếu có)</label>
                    <textarea className="input resize-none" rows={3} placeholder="Dán tóm tắt hồ sơ cũ vào đây..."
                      value={medicalRecord} onChange={e => setMedicalRecord(e.target.value)} />
                  </div>
                  <button id="start-consultation-btn" className="btn-primary w-full" onClick={() => setStep('recording')}>
                    <Stethoscope className="w-4 h-4" /> Bắt đầu ghi âm
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ─── RECORDING ─── */}
        {step === 'recording' && (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="w-full max-w-lg">
              <div className="card p-8">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="font-semibold text-slate-800">Ghi âm hội thoại</h2>
                  <button className="btn-ghost text-xs" onClick={() => setStep('idle')}><ArrowLeft className="w-4 h-4" />Quay lại</button>
                </div>

                {/* Mic button */}
                <div className="flex flex-col items-center gap-4 mb-8">
                  <button
                    id="mic-toggle-btn"
                    onClick={isRecording ? stopRecording : startRecording}
                    className={`w-28 h-28 rounded-full flex items-center justify-center transition-all duration-200 text-white text-opacity-90 ${
                      isRecording
                        ? 'bg-red-500 animate-recording hover:bg-red-600'
                        : 'bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-200'
                    }`}
                  >
                    {isRecording ? <MicOff className="w-10 h-10" /> : <Mic className="w-10 h-10" />}
                  </button>
                  {isRecording ? (
                    <div className="text-center">
                      <p className="font-semibold text-red-600 flex items-center gap-2">
                        <span className="dot-bounce w-2 h-2 bg-red-500 rounded-full inline-block" />
                        <span className="dot-bounce w-2 h-2 bg-red-500 rounded-full inline-block" />
                        <span className="dot-bounce w-2 h-2 bg-red-500 rounded-full inline-block" />
                        Đang ghi âm
                      </p>
                      <p className="text-slate-400 text-sm mt-1">Nhấn để dừng</p>
                    </div>
                  ) : (
                    <div className="text-center">
                      <p className="font-medium text-slate-600">Nhấn để bắt đầu ghi âm</p>
                      <p className="text-slate-400 text-sm mt-1">Hội thoại bác sĩ – bệnh nhân</p>
                    </div>
                  )}
                </div>

                {/* Upload */}
                <div className="border-t border-slate-100 pt-6">
                  <p className="text-xs text-slate-400 text-center mb-3 uppercase tracking-wide">Hoặc tải lên file audio</p>
                  <label className="flex flex-col items-center gap-2 p-4 border-2 border-dashed border-slate-200 rounded-xl cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors">
                    <Upload className="w-6 h-6 text-slate-400" />
                    <span className="text-sm text-slate-500">Chọn file .webm .mp3 .wav .m4a</span>
                    <input ref={fileInputRef} type="file" accept="audio/*" onChange={handleFile} className="hidden" />
                  </label>
                </div>

                {/* Audio preview + process */}
                {audioFile && !isRecording && (
                  <div className="mt-5 p-4 bg-slate-50 rounded-xl animate-fade-up">
                    <p className="text-xs text-slate-500 mb-2 font-medium">Audio đã sẵn sàng</p>
                    <audio controls src={URL.createObjectURL(audioFile)} className="w-full mb-3" />
                    <button id="process-audio-btn" className="btn-primary w-full" onClick={processAudio}>
                      <Loader2 className="w-4 h-4" /> Xử lý &amp; phân tích
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ─── PROCESSING ─── */}
        {step === 'processing' && (
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="w-full max-w-md card p-8">
              <div className="flex items-center gap-3 mb-8">
                <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center">
                  <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                </div>
                <div>
                  <h2 className="font-semibold text-slate-800">Đang xử lý</h2>
                  <p className="text-xs text-slate-400">Vui lòng không đóng tab này</p>
                </div>
              </div>
              <div className="space-y-3">
                {STEPS.map((s, i) => (
                  <div key={s.key} className={`status-step ${
                    i < currentProcStep ? 'done' : i === currentProcStep ? 'active' : 'pending'
                  }`}>
                    {i < currentProcStep
                      ? <CheckCircle className="w-4 h-4 flex-shrink-0" />
                      : i === currentProcStep
                      ? <Loader2 className="w-4 h-4 flex-shrink-0 animate-spin" />
                      : <div className="w-4 h-4 rounded-full border-2 border-slate-300 flex-shrink-0" />}
                    <span>{s.label}</span>
                  </div>
                ))}
              </div>
              <div className="mt-6 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full animate-progress" />
              </div>
            </div>
          </div>
        )}

        {/* ─── REVIEWING ─── */}
        {step === 'reviewing' && (
          <div className="flex-1 p-6">
            <div className="max-w-7xl mx-auto grid grid-cols-12 gap-5">

              {/* ── LEFT 8 cols ── */}
              <div className="col-span-8 space-y-4">

                {/* Transcript */}
                <div className="card">
                  <div className="card-header">
                    <div className="flex items-center gap-2">
                      <FileAudio className="w-4 h-4 text-blue-600" />
                      <span className="font-semibold text-slate-800 text-sm">Transcript</span>
                      <AiTag />
                    </div>
                    <StatusBadge status="approved" />
                  </div>
                  <div className="px-6 py-4 max-h-40 overflow-y-auto bg-slate-50 text-sm text-slate-700 leading-relaxed whitespace-pre-wrap rounded-b-2xl">
                    {transcript || '(Không có transcript)'}
                  </div>
                </div>

                {/* Extraction Form */}
                <div className="card">
                  <div className="card-header cursor-pointer" onClick={() => toggleSection('form')}>
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-blue-600" />
                      <span className="font-semibold text-slate-800 text-sm">Thông tin trích xuất</span>
                      <AiTag />
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusBadge status="pending" />
                      {expandedSection.form ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                    </div>
                  </div>

                  {expandedSection.form && (
                    <div className="px-6 py-5 space-y-5">

                      {/* Missing fields warning */}
                      {(suggestions.missing_fields || []).length > 0 && (
                        <div className="missing-box flex items-start gap-3">
                          <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                          <div>
                            <p className="text-xs font-semibold text-amber-800 mb-1">Thông tin còn thiếu — cần hỏi thêm</p>
                            <div className="flex flex-wrap gap-1.5">
                              {suggestions.missing_fields.map((f, i) => (
                                <span key={i} className="badge badge-yellow">{f}</span>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Section: Thông tin lâm sàng */}
                      <div>
                        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Thông tin lâm sàng hiện tại</p>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="col-span-2">
                            <FieldLabel label="Lý do khám" missing={isMissing('reason_for_visit')} />
                            <input className={`input ${isMissing('reason_for_visit') ? 'missing' : ''}`}
                              value={fieldVal('reason_for_visit')}
                              onChange={e => setField('reason_for_visit', e.target.value)} />
                          </div>
                          <div>
                            <FieldLabel label="Thời gian xuất hiện" icon={Clock} missing={isMissing('onset_time')} />
                            <input className={`input ${isMissing('onset_time') ? 'missing' : ''}`}
                              value={fieldVal('onset_time')}
                              onChange={e => setField('onset_time', e.target.value)} />
                          </div>
                          <div>
                            <FieldLabel label="Vị trí tổn thương" icon={MapPin} missing={isMissing('lesion_location')} />
                            <input className={`input ${isMissing('lesion_location') ? 'missing' : ''}`}
                              value={fieldVal('lesion_location')}
                              onChange={e => setField('lesion_location', e.target.value)} />
                          </div>
                          <div className="col-span-2">
                            <FieldLabel label="Triệu chứng chính" missing={isMissing('main_symptoms')} />
                            <div className="flex flex-wrap gap-1.5 p-2.5 border border-slate-200 rounded-xl bg-white min-h-[40px]">
                              {(fieldVal('main_symptoms') || []).map((s, i) => (
                                <span key={i} className="badge badge-blue flex items-center gap-1">
                                  {s}
                                  <X className="w-3 h-3 cursor-pointer" onClick={() => {
                                    const arr = [...(fieldVal('main_symptoms') || [])]
                                    arr.splice(i, 1)
                                    setField('main_symptoms', arr)
                                  }} />
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Section: Tiền sử & yếu tố */}
                      <div>
                        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Tiền sử &amp; Yếu tố liên quan</p>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <FieldLabel label="Tiền sử bệnh" />
                            <div className="flex flex-wrap gap-1.5 p-2.5 border border-slate-200 rounded-xl bg-white min-h-[40px]">
                              {(fieldVal('medical_history') || []).map((s, i) => (
                                <span key={i} className="badge badge-gray">{s}</span>
                              ))}
                              {!(fieldVal('medical_history') || []).length && <span className="text-xs text-slate-400 italic">Chưa có</span>}
                            </div>
                          </div>
                          <div>
                            <FieldLabel label="Yếu tố liên quan" />
                            <div className="flex flex-wrap gap-1.5 p-2.5 border border-slate-200 rounded-xl bg-white min-h-[40px]">
                              {(fieldVal('related_factors') || []).map((s, i) => (
                                <span key={i} className="badge badge-yellow">{s}</span>
                              ))}
                              {!(fieldVal('related_factors') || []).length && <span className="text-xs text-slate-400 italic">Chưa có</span>}
                            </div>
                          </div>
                          <div className="col-span-2">
                            <FieldLabel label="Điều trị trước đó" />
                            <div className="flex flex-wrap gap-1.5 p-2.5 border border-slate-200 rounded-xl bg-white min-h-[40px]">
                              {(fieldVal('previous_treatment') || []).map((s, i) => (
                                <span key={i} className="badge" style={{background:'#f3e8ff',color:'#7c3aed'}}>{s}</span>
                              ))}
                              {!(fieldVal('previous_treatment') || []).length && <span className="text-xs text-slate-400 italic">Chưa có</span>}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Field approve row */}
                      <div className="flex gap-2 justify-end pt-2 border-t border-slate-100">
                        <button className="btn-outline text-xs" onClick={() => setFieldStatus({})}>
                          <RotateCcw className="w-3.5 h-3.5" /> Đặt lại
                        </button>
                        <button className="btn-success text-xs" onClick={() => approveField('form', 'approved')}>
                          <CheckCircle className="w-3.5 h-3.5" /> Xác nhận
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Draft Note */}
                <div className="card">
                  <div className="card-header cursor-pointer" onClick={() => toggleSection('draft')}>
                    <div className="flex items-center gap-2">
                      <Edit3 className="w-4 h-4 text-blue-600" />
                      <span className="font-semibold text-slate-800 text-sm">Draft Note</span>
                      <AiTag />
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusBadge status={fieldStatus.draft || 'pending'} />
                      {expandedSection.draft ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
                    </div>
                  </div>
                  {expandedSection.draft && (
                    <div className="px-6 py-4 space-y-3">
                      <p className="text-xs text-slate-400 italic">AI đã tạo draft note bên dưới. Bác sĩ chỉnh sửa trực tiếp rồi xác nhận trước khi lưu.</p>
                      <textarea
                        className="input resize-y font-mono text-xs leading-relaxed min-h-[160px]"
                        value={draftNote}
                        onChange={e => setDraftNote(e.target.value)}
                      />
                      <div className="flex gap-2 justify-end">
                        <button className="btn-outline text-xs" onClick={() => approveField('draft', 'rejected')}>
                          <XCircle className="w-3.5 h-3.5" /> Huỷ bỏ
                        </button>
                        <button className="btn-success text-xs" onClick={() => approveField('draft', 'approved')}>
                          <CheckCircle className="w-3.5 h-3.5" /> Xác nhận draft
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex justify-between items-center">
                  <button className="btn-outline" onClick={reset}><RotateCcw className="w-4 h-4" /> Ca khám mới</button>
                  <div className="flex gap-3">
                    <button className="btn-outline" onClick={() => setStep('idle')}>Huỷ</button>
                    <button id="save-btn" className="btn-success" onClick={saveConsultation}>
                      {saved ? <><Check className="w-4 h-4" /> Đã lưu!</> : <><Save className="w-4 h-4" /> Lưu hồ sơ</>}
                    </button>
                  </div>
                </div>
              </div>

              {/* ── RIGHT 4 cols — AI Panel ── */}
              <div className="col-span-4 space-y-4">
                {/* AI disclaimer */}
                <div className="flex items-start gap-2 p-3 bg-violet-50 border border-violet-200 rounded-xl text-xs text-violet-700">
                  <Sparkles className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                  <span>Tất cả nội dung bên dưới do AI tạo ra — <strong>chỉ mang tính tham khảo</strong>. Bác sĩ quyết định cuối cùng.</span>
                </div>

                {/* Red Flags */}
                {(suggestions.red_flags || []).length > 0 && (
                  <div className={`red-flag-box animate-fade-up ${suggestions.alert_level === 'critical' ? 'border-2 border-red-600 ring-4 ring-red-100' : ''}`}>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <ShieldAlert className={`w-4 h-4 ${suggestions.alert_level === 'critical' ? 'text-red-700 animate-pulse' : 'text-red-600'}`} />
                        <span className={`font-bold text-sm ${suggestions.alert_level === 'critical' ? 'text-red-700' : 'text-red-800'}`}>
                          {suggestions.alert_level === 'critical' ? 'CẢNH BÁO NGUY HIỂM' : 'Red Flags'}
                        </span>
                      </div>
                      {suggestions.alert_level === 'critical' && (
                        <span className="bg-red-600 text-white text-[10px] px-1.5 py-0.5 rounded-full animate-pulse font-bold">KHẨN CẤP</span>
                      )}
                    </div>
                    <ul className="space-y-1.5">
                      {suggestions.red_flags.map((f, i) => (
                        <li key={i} className="text-xs text-red-700 flex items-start gap-2">
                          <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />{f}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Differential Diagnosis */}
                <div className="card">
                  <div className="card-header">
                    <div className="flex items-center gap-2">
                      <Stethoscope className="w-4 h-4 text-blue-600" />
                      <span className="font-semibold text-sm text-slate-800">Gợi ý chẩn đoán</span>
                    </div>
                    <AiTag />
                  </div>
                  <div className="px-4 py-3 space-y-2">
                    {(suggestions.differential_diagnosis || []).map((dx, i) => (
                      <div key={i} className="flex items-center justify-between py-2 border-b border-slate-50 last:border-0">
                        <span className="text-sm text-slate-700">{dx.name}</span>
                        <span className={`badge ${
                          dx.likelihood === 'Cao' ? 'badge-red' :
                          dx.likelihood === 'Trung bình' ? 'badge-yellow' :
                          dx.likelihood === 'N/A' ? 'badge-gray' : 'badge-green'
                        }`}>{dx.likelihood}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Questions to ask */}
                {(suggestions.questions_to_ask || []).length > 0 && (
                  <div className="card">
                    <div className="card-header">
                      <div className="flex items-center gap-2">
                        <MessageSquare className="w-4 h-4 text-blue-600" />
                        <span className="font-semibold text-sm text-slate-800">Câu hỏi nên hỏi thêm</span>
                      </div>
                      <AiTag />
                    </div>
                    <ul className="px-4 py-3 space-y-2">
                      {suggestions.questions_to_ask.map((q, i) => (
                        <li key={i} className="flex items-start gap-2 text-xs text-slate-600">
                          <span className="w-4 h-4 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-[10px] font-bold flex-shrink-0 mt-0.5">{i+1}</span>
                          {q}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Clinical Reminders */}
                {(suggestions.clinical_reminders || []).length > 0 && (
                  <div className="card">
                    <div className="card-header">
                      <div className="flex items-center gap-2">
                        <Heart className="w-4 h-4 text-blue-600" />
                        <span className="font-semibold text-sm text-slate-800">Lưu ý lâm sàng</span>
                      </div>
                      <AiTag />
                    </div>
                    <ul className="px-4 py-3 space-y-2">
                      {suggestions.clinical_reminders.map((r, i) => (
                        <li key={i} className="flex items-start gap-2 text-xs text-slate-600">
                          <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full mt-1.5 flex-shrink-0" />{r}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default DoctorDashboard
