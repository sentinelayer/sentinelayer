import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Login } from '../pages/auth/Login'
import { OverviewPage } from '../pages/overview/OverviewPage'
import { PolicyList } from '../pages/policies/PolicyList'
import { Guards } from './guards'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={
          <Guards>
            <OverviewPage />
          </Guards>
        } />
        <Route path="/policies" element={
          <Guards>
            <PolicyList />
          </Guards>
        } />
      </Routes>
    </BrowserRouter>
  )
}

export default App
