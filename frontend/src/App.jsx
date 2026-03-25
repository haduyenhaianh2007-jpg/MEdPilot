import React, { useState } from 'react'
import DoctorDashboard from './pages/DoctorDashboard'
import PatientChat from './pages/PatientChat'
import RoleSelection from './components/RoleSelection'

function App() {
  const [userRole, setUserRole] = useState(null) // null, 'doctor', 'patient'
  const [patientCode, setPatientCode] = useState('')

  const handleRoleSelect = (role) => {
    setUserRole(role)
  }

  const handleLogout = () => {
    setUserRole(null)
    setPatientCode('')
  }

  return (
    <div style={{ minHeight: '100vh' }}>
      {!userRole ? (
        <RoleSelection onSelect={handleRoleSelect} />
      ) : userRole === 'doctor' ? (
        <DoctorDashboard onLogout={handleLogout} />
      ) : (
        <PatientChat onLogout={handleLogout} />
      )}
    </div>
  )
}

export default App
