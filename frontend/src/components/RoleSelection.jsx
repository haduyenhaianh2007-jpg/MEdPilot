import React from 'react'
import { Stethoscope, User, Activity, ShieldCheck, Zap } from 'lucide-react'

function RoleSelection({ onSelect }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-blue-950 via-blue-900 to-slate-900 relative overflow-hidden">

      {/* Background decoration */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 w-full max-w-lg px-6">

        {/* Logo */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-500/20 border border-blue-400/30 mb-4">
            <Activity className="w-9 h-9 text-blue-400" />
          </div>
          <h1 className="text-4xl font-bold text-white tracking-tight">MedPilot</h1>
          <p className="text-blue-300 mt-2 text-sm">Trợ lý AI Hỗ Trợ Da Liễu</p>
        </div>

        {/* Role Cards */}
        <div className="space-y-4 mb-8">
          {/* Doctor */}
          <button
            id="role-doctor"
            onClick={() => onSelect('doctor')}
            className="group w-full p-6 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-blue-400/50 transition-all duration-200 text-left flex items-start gap-5 hover:shadow-lg hover:shadow-blue-500/10"
          >
            <div className="w-14 h-14 rounded-xl bg-blue-500/20 border border-blue-400/30 flex items-center justify-center flex-shrink-0 group-hover:bg-blue-500/30 transition-colors">
              <Stethoscope className="w-7 h-7 text-blue-400" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-lg font-semibold text-white">Bác sĩ</h2>
                <span className="badge badge-blue text-xs">Chế độ lâm sàng</span>
              </div>
              <p className="text-blue-200/70 text-sm leading-relaxed">
                Ghi âm hội thoại, trích xuất thông tin tự động, gợi ý chẩn đoán, nhắc nhở lâm sàng, quản lý hồ sơ bệnh nhân.
              </p>
              <div className="flex gap-3 mt-3">
                {['Ghi âm & STT', 'Trích xuất AI', 'Gợi ý chẩn đoán'].map(f => (
                  <span key={f} className="text-xs text-blue-300/60 flex items-center gap-1">
                    <Zap className="w-3 h-3" />{f}
                  </span>
                ))}
              </div>
            </div>
          </button>

          {/* Patient */}
          <button
            id="role-patient"
            onClick={() => onSelect('patient')}
            className="group w-full p-6 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-emerald-400/50 transition-all duration-200 text-left flex items-start gap-5 hover:shadow-lg hover:shadow-emerald-500/10"
          >
            <div className="w-14 h-14 rounded-xl bg-emerald-500/20 border border-emerald-400/30 flex items-center justify-center flex-shrink-0 group-hover:bg-emerald-500/30 transition-colors">
              <User className="w-7 h-7 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-lg font-semibold text-white">Bệnh nhân</h2>
                <span className="badge badge-green text-xs">Chatbot tư vấn</span>
              </div>
              <p className="text-emerald-200/70 text-sm leading-relaxed">
                Hỏi đáp về triệu chứng, bệnh da liễu, chăm sóc da. Đơn giản, thân thiện và an toàn.
              </p>
              <div className="flex gap-3 mt-3">
                {['Hỏi đáp triệu chứng', 'Kiến thức da liễu', 'Hướng dẫn khám'].map(f => (
                  <span key={f} className="text-xs text-emerald-300/60 flex items-center gap-1">
                    <Zap className="w-3 h-3" />{f}
                  </span>
                ))}
              </div>
            </div>
          </button>
        </div>

        {/* Disclaimer */}
        <div className="flex items-start gap-2 p-4 rounded-xl bg-white/5 border border-white/10">
          <ShieldCheck className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
          <p className="text-xs text-slate-400 leading-relaxed">
            MedPilot chỉ đóng vai trò <strong className="text-slate-300">hỗ trợ tham khảo</strong>, không thay thế phán quyết chuyên môn của bác sĩ và không kê đơn thuốc.
          </p>
        </div>
      </div>
    </div>
  )
}

export default RoleSelection
