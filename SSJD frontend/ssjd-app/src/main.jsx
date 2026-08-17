import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          className: '!bg-white !text-gray-900 dark:!bg-gray-800 dark:!text-gray-100 !shadow-lg',
        }}
      />
    </BrowserRouter>
  </StrictMode>,
)
