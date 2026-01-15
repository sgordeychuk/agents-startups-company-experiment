'use client'

import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'

interface Catch {
  id: string
  vessel_id: string
  species: string
  quantity: number
  catch_method: string
  location: {
    latitude: number
    longitude: number
  }
  catch_timestamp: string
  fisher_id: string
  is_verified: boolean
  compliance_status: string
}

export default function BuyerDashboard() {
  const router = useRouter()
  const [catches, setCatches] = useState<Catch[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('token')
    const userData = localStorage.getItem('user')
    
    if (!token || !userData) {
      router.push('/login')
      return
    }

    setUser(JSON.parse(userData))
    fetchCatches()
  }, [])

  const fetchCatches = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const token = localStorage.getItem('token')
      
      const response = await fetch(`${apiUrl}/api/v1/catches`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        setCatches(data.catches || [])
      }
    } catch (error) {
      console.error('Error fetching catches:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }

  const totalQuantity = catches.reduce((sum, c) => sum + c.quantity, 0)
  const verifiedCatches = catches.filter(c => c.is_verified).length
  const compliantCatches = catches.filter(c => c.compliance_status === 'compliant').length

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <span className="text-2xl font-bold text-primary">🌊 SeaChain</span>
              <span className="ml-4 text-gray-600">Buyer Dashboard</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-600">{user?.email}</span>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <Card.Content>
              <div className="text-sm font-medium text-gray-600">Total Catches</div>
              <div className="text-3xl font-bold text-primary mt-2">{catches.length}</div>
            </Card.Content>
          </Card>
          <Card>
            <Card.Content>
              <div className="text-sm font-medium text-gray-600">Total Quantity</div>
              <div className="text-3xl font-bold text-secondary mt-2">{totalQuantity.toFixed(1)} kg</div>
            </Card.Content>
          </Card>
          <Card>
            <Card.Content>
              <div className="text-sm font-medium text-gray-600">Verified</div>
              <div className="text-3xl font-bold text-green-600 mt-2">{verifiedCatches}</div>
            </Card.Content>
          </Card>
          <Card>
            <Card.Content>
              <div className="text-sm font-medium text-gray-600">Compliant</div>
              <div className="text-3xl font-bold text-blue-600 mt-2">{compliantCatches}</div>
            </Card.Content>
          </Card>
        </div>

        {/* Catches Table */}
        <Card>
          <Card.Header>
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold text-gray-900">Recent Catches</h2>
              <Button variant="primary" size="sm">
                Generate SIMP Report
              </Button>
            </div>
          </Card.Header>
          <Card.Content>
            {isLoading ? (
              <div className="text-center py-8 text-gray-500">Loading catches...</div>
            ) : catches.length === 0 ? (
              <div className="text-center py-8 text-gray-500">No catches found</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vessel</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Species</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Method</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {catches.map((catchItem) => (
                      <tr key={catchItem.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">{catchItem.vessel_id}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">{catchItem.species}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">{catchItem.quantity} kg</td>
                        <td className="px-4 py-3 text-sm text-gray-600">{catchItem.catch_method}</td>
                        <td className="px-4 py-3 text-sm text-gray-600">
                          {catchItem.location.latitude.toFixed(4)}, {catchItem.location.longitude.toFixed(4)}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            catchItem.compliance_status === 'compliant'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {catchItem.compliance_status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card.Content>
        </Card>
      </div>
    </div>
  )
}
