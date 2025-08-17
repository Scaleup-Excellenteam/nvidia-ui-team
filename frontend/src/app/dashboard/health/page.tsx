"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface SystemComponent {
  name: string;
  status: 'healthy' | 'warning' | 'error';
  uptime: string;
  responseTime: number;
}

interface BIMetrics {
  totalRevenue: number;
  totalCustomers: number;
  activeImages: number;
  totalContainers: number;
  averageLoad: number;
}

export default function HealthPage() {
  const router = useRouter();
  const [isAdmin, setIsAdmin] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [systemComponents, setSystemComponents] = useState<SystemComponent[]>([]);
  const [biMetrics, setBiMetrics] = useState<BIMetrics | null>(null);

  useEffect(() => {
    // Check if user is logged in and is admin
    const token = localStorage.getItem('authToken');
    if (!token) {
      router.push('/signin');
      return;
    }

    const checkAdminStatus = async () => {
      try {
        const response = await fetch('/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const userData = await response.json();
          const isAdminUser = userData.email?.toLowerCase() === 'admin@gmail.com' || 
                             userData.email?.toLowerCase() === 'admin';
          
          if (!isAdminUser) {
            router.push('/dashboard');
            return;
          }
          
          setIsAdmin(true);
          fetchHealthData();
        }
      } catch (error) {
        console.error('Error checking admin status:', error);
        router.push('/dashboard');
      } finally {
        setIsLoading(false);
      }
    };

    checkAdminStatus();
  }, [router]);

  const fetchHealthData = async () => {
    try {
      // Fetch system health data
      const healthResponse = await fetch('/api/health/system', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      
      if (healthResponse.ok) {
        const healthData = await healthResponse.json();
        setSystemComponents(healthData.components);
      }

      // Fetch BI metrics
      const biResponse = await fetch('/api/health/bi', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });
      
      if (biResponse.ok) {
        const biData = await biResponse.json();
        setBiMetrics(biData);
      }
    } catch (error) {
      console.error('Error fetching health data:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-100 text-green-800';
      case 'warning': return 'bg-yellow-100 text-yellow-800';
      case 'error': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAdmin) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <Link
                href="/dashboard"
                className="text-blue-600 hover:text-blue-500"
              >
                ← Back to Dashboard
              </Link>
              <h1 className="text-3xl font-bold text-gray-900">System Health</h1>
            </div>
            <div className="text-sm text-gray-600">
              Admin Dashboard
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* BI Metrics */}
        {biMetrics && (
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Business Intelligence</h2>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-5">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm font-medium text-gray-500">Total Revenue</div>
                <div className="text-2xl font-bold text-green-600">${biMetrics.totalRevenue.toFixed(2)}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm font-medium text-gray-500">Total Customers</div>
                <div className="text-2xl font-bold text-blue-600">{biMetrics.totalCustomers}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm font-medium text-gray-500">Active Images</div>
                <div className="text-2xl font-bold text-purple-600">{biMetrics.activeImages}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm font-medium text-gray-500">Total Containers</div>
                <div className="text-2xl font-bold text-indigo-600">{biMetrics.totalContainers}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm font-medium text-gray-500">Average Load</div>
                <div className="text-2xl font-bold text-orange-600">{biMetrics.averageLoad.toFixed(1)}%</div>
              </div>
            </div>
          </div>
        )}

        {/* System Components */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900">System Components Status</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Component
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Uptime
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Response Time
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {systemComponents.map((component) => (
                  <tr key={component.name}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {component.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(component.status)}`}>
                        {component.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {component.uptime}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {component.responseTime}ms
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
