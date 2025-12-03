import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/common/Layout'
import Dashboard from './pages/Dashboard'
import FlowsPage from './pages/FlowsPage'
import DevicesPage from './pages/DevicesPage'
import StereoToolPage from './pages/StereoToolPage'
import InfernoPage from './pages/InfernoPage'
import MonitoringPage from './pages/MonitoringPage'
import NetworkPage from './pages/NetworkPage'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/flows" element={<FlowsPage />} />
          <Route path="/devices" element={<DevicesPage />} />
          <Route path="/stereotool" element={<StereoToolPage />} />
          <Route path="/inferno" element={<InfernoPage />} />
          <Route path="/monitoring" element={<MonitoringPage />} />
          <Route path="/network" element={<NetworkPage />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
