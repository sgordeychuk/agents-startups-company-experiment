'use client'

import React from 'react'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()

  const features = [
    {
      title: 'Fisher Mobile App',
      description: 'Offline-first catch data capture with GPS verification, photo documentation, and automatic sync when online.',
      icon: '📱',
    },
    {
      title: 'Supply Chain Visibility',
      description: 'Real-time traceability from catch to consumer with interactive maps and timeline views.',
      icon: '🗺️',
    },
    {
      title: 'Automated Compliance',
      description: 'Generate SIMP/IUU compliance reports instantly. Reduce compliance labor costs by 40-60%.',
      icon: '📊',
    },
    {
      title: 'Fraud Prevention',
      description: 'Immutable audit trails with GPS validation and blockchain-backed data integrity.',
      icon: '🔒',
    },
    {
      title: 'Chain of Custody',
      description: 'Track seafood through entire supply chain with cryptographic proof of transfers.',
      icon: '🔗',
    },
    {
      title: 'Risk Alerts',
      description: 'Automated alerts for incomplete data, suspicious patterns, and compliance violations.',
      icon: '⚠️',
    },
  ]

  const stats = [
    { value: '40-60%', label: 'Reduction in compliance costs' },
    { value: '$500K', label: 'Average penalty per violation' },
    { value: '20%', label: 'Global seafood illegally sourced' },
  ]

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <span className="text-2xl font-bold text-primary">🌊 SeaChain</span>
            </div>
            <div className="flex items-center gap-4">
              <Button variant="outline" onClick={() => router.push('/login')}>
                Sign In
              </Button>
              <Button variant="primary" onClick={() => router.push('/login')}>
                Get Started
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-50 to-green-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <h1 className="text-5xl font-bold text-gray-900 mb-6">
              Enterprise Seafood Traceability
              <span className="block text-primary mt-2">Made Simple</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              Automate SIMP/IUU compliance, prevent fraud, and gain end-to-end supply chain visibility.
              Reduce compliance costs by 40-60% while protecting your brand reputation.
            </p>
            <div className="flex justify-center gap-4">
              <Button variant="primary" size="lg" onClick={() => router.push('/login')}>
                Start Free Trial
              </Button>
              <Button variant="outline" size="lg">
                Schedule Demo
              </Button>
            </div>
          </div>

          {/* Stats */}
          <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="bg-white rounded-lg shadow-md p-6 text-center">
                <div className="text-4xl font-bold text-primary mb-2">{stat.value}</div>
                <div className="text-gray-600">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Complete Traceability Solution
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need to achieve SIMP compliance and protect your supply chain
              from IUU fishing risks.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index}>
                <Card.Header>
                  <div className="text-4xl mb-3">{feature.icon}</div>
                  <h3 className="text-xl font-semibold text-gray-900">{feature.title}</h3>
                </Card.Header>
                <Card.Content>
                  <p className="text-gray-600">{feature.description}</p>
                </Card.Content>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Transform Your Seafood Supply Chain?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join leading seafood buyers achieving automated compliance and fraud prevention.
          </p>
          <Button variant="secondary" size="lg" onClick={() => router.push('/login')}>
            Get Started Today
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="text-2xl font-bold mb-4">🌊 SeaChain</div>
              <p className="text-gray-400">
                Enterprise traceability platform for seafood compliance.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400">
                <li>Features</li>
                <li>Pricing</li>
                <li>Security</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Company</h4>
              <ul className="space-y-2 text-gray-400">
                <li>About</li>
                <li>Contact</li>
                <li>Careers</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Resources</h4>
              <ul className="space-y-2 text-gray-400">
                <li>Documentation</li>
                <li>API Reference</li>
                <li>Support</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
            <p>&copy; 2024 SeaChain. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
