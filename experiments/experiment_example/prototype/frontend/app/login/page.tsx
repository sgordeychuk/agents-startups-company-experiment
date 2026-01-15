'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        throw new Error('Invalid credentials')
      }

      const data = await response.json()
      
      // Store token and user info
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify({
        id: data.user_id,
        email: data.email,
        role: data.role,
      }))

      // Redirect based on role
      if (data.role === 'fisher') {
        router.push('/fisher/dashboard')
      } else if (data.role === 'buyer_admin' || data.role === 'buyer_viewer') {
        router.push('/buyer/dashboard')
      } else {
        router.push('/dashboard')
      }
    } catch (err) {
      setError('Invalid email or password')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-primary mb-2">🌊 SeaChain</h1>
          <p className="text-gray-600">Sign in to your account</p>
        </div>

        <Card>
          <Card.Content className="pt-6">
            <form onSubmit={handleLogin} className="space-y-4">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                  {error}
                </div>
              )}

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                  Email Address
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder="you@example.com"
                  required
                />
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder="••••••••"
                  required
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                className="w-full"
                disabled={isLoading}
              >
                {isLoading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>

            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm font-semibold text-gray-700 mb-2">Demo Credentials:</p>
              <p className="text-sm text-gray-600">Fisher: fisher@seachain.com / password123</p>
              <p className="text-sm text-gray-600">Buyer: buyer@seachain.com / password123</p>
            </div>
          </Card.Content>
        </Card>

        <div className="text-center mt-6">
          <button
            onClick={() => router.push('/')}
            className="text-sm text-gray-600 hover:text-primary"
          >
            ← Back to home
          </button>
        </div>
      </div>
    </div>
  )
}
