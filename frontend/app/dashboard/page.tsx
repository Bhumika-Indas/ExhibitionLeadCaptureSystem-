'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { isAuthenticated } from '@/lib/auth';
import BottomNav from '@/components/BottomNav';
import { api } from '@/lib/api';
import type { AnalyticsSummary } from '@/lib/types';
import {
  Users,
  Building2,
  CheckCircle,
  Clock,
  TrendingUp,
  Calendar,
  MessageSquare,
} from 'lucide-react';

interface EmployeePerformance {
  employee_name: string;
  leads_captured: number;
  confirmed_count: number;
  conversion_rate: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [performance, setPerformance] = useState<EmployeePerformance[]>([]);
  const [followupStats, setFollowupStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/auth/login');
      return;
    }

    loadDashboardData();
  }, [router]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Load analytics summary
      const summaryData = await api.getAnalyticsSummary();
      setSummary(summaryData);

      // Load employee performance
      const performanceData = await api.getEmployeePerformance();
      setPerformance(performanceData || []);

      // Load follow-up stats
      const followupData = await api.getFollowupStats();
      setFollowupStats(followupData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated()) {
    return null;
  }

  if (loading) {
    return (
      <div className="flex flex-col h-screen bg-gradient-to-b from-blue-50 to-white">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center animate-fadeIn">
            <div className="relative mx-auto mb-6 w-12 h-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <div className="absolute top-0 left-0 animate-ping rounded-full h-12 w-12 border-2 border-blue-300 opacity-20"></div>
            </div>
            <p className="text-gray-600">Loading dashboard...</p>
          </div>
        </div>
        <BottomNav />
      </div>
    );
  }

  const conversionRate = summary
    ? summary.total_leads > 0
      ? ((summary.confirmed_leads / summary.total_leads) * 100).toFixed(1)
      : '0.0'
    : '0.0';

  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-b from-blue-50 to-white pb-20">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-6 shadow-lg sticky top-0 z-10">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-blue-100 text-sm mt-1">Analytics & Performance</p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white rounded-xl shadow-md p-4 transform transition-all duration-300 hover:scale-105 hover:shadow-xl animate-fadeIn">
            <div className="flex items-center justify-between mb-2">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Users className="w-5 h-5 text-blue-600" />
              </div>
              <span className="text-2xl font-bold text-gray-900">
                {summary?.total_leads || 0}
              </span>
            </div>
            <p className="text-sm text-gray-600">Total Leads</p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-4 transform transition-all duration-300 hover:scale-105 hover:shadow-xl animate-fadeIn" style={{ animationDelay: '0.1s' }}>
            <div className="flex items-center justify-between mb-2">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
              <span className="text-2xl font-bold text-gray-900">
                {summary?.confirmed_leads || 0}
              </span>
            </div>
            <p className="text-sm text-gray-600">Confirmed</p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-4 transform transition-all duration-300 hover:scale-105 hover:shadow-xl animate-fadeIn" style={{ animationDelay: '0.2s' }}>
            <div className="flex items-center justify-between mb-2">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Clock className="w-5 h-5 text-yellow-600" />
              </div>
              <span className="text-2xl font-bold text-gray-900">
                {summary?.pending_leads || 0}
              </span>
            </div>
            <p className="text-sm text-gray-600">Pending</p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-4 transform transition-all duration-300 hover:scale-105 hover:shadow-xl animate-fadeIn" style={{ animationDelay: '0.3s' }}>
            <div className="flex items-center justify-between mb-2">
              <div className="p-2 bg-purple-100 rounded-lg">
                <TrendingUp className="w-5 h-5 text-purple-600" />
              </div>
              <span className="text-2xl font-bold text-gray-900">{conversionRate}%</span>
            </div>
            <p className="text-sm text-gray-600">Conversion</p>
          </div>
        </div>

        {/* Lead Sources */}
        <div className="bg-white rounded-xl shadow-md p-5 transform transition-all duration-300 hover:shadow-xl animate-fadeIn" style={{ animationDelay: '0.4s' }}>
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg mr-2">
              <MessageSquare className="w-5 h-5 text-blue-600" />
            </div>
            Lead Sources
          </h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Employee Captured</span>
              <span className="font-semibold text-gray-900">
                {summary?.leads_by_source?.find((s) => s.source === 'employee')?.count || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">QR Code</span>
              <span className="font-semibold text-gray-900">
                {summary?.leads_by_source?.find((s) => s.source === 'qr')?.count || 0}
              </span>
            </div>
          </div>
        </div>

        {/* Follow-up Stats */}
        {followupStats && (
          <div className="bg-white rounded-xl shadow-md p-5 transform transition-all duration-300 hover:shadow-xl animate-fadeIn" style={{ animationDelay: '0.5s' }}>
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg mr-2">
                <Calendar className="w-5 h-5 text-blue-600" />
              </div>
              Follow-ups
            </h2>
            <div className="grid grid-cols-2 gap-3">
              <div className="flex flex-col p-3 bg-yellow-50 rounded-lg">
                <span className="text-2xl font-bold text-gray-900">
                  {followupStats.pending || 0}
                </span>
                <span className="text-sm text-gray-600">Pending</span>
              </div>
              <div className="flex flex-col p-3 bg-green-50 rounded-lg">
                <span className="text-2xl font-bold text-green-600">
                  {followupStats.completed || 0}
                </span>
                <span className="text-sm text-gray-600">Completed</span>
              </div>
            </div>
          </div>
        )}

        {/* Employee Performance */}
        {performance.length > 0 && (
          <div className="bg-white rounded-xl shadow-md p-5 transform transition-all duration-300 hover:shadow-xl animate-fadeIn" style={{ animationDelay: '0.6s' }}>
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg mr-2">
                <Users className="w-5 h-5 text-blue-600" />
              </div>
              Employee Performance
            </h2>
            <div className="space-y-3">
              {performance.slice(0, 5).map((emp, index) => (
                <div key={index} className="flex items-center justify-between py-3 px-3 rounded-lg border border-gray-100 hover:border-blue-200 hover:bg-blue-50 transition-all duration-200 transform hover:scale-[1.02]">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{emp.employee_name}</p>
                    <p className="text-xs text-gray-500">
                      {emp.leads_captured} leads • {emp.confirmed_count} confirmed
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-semibold text-blue-600 bg-blue-100 px-3 py-1 rounded-full">
                      {(emp.conversion_rate || 0).toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Exhibitions */}
        <div className="bg-white rounded-xl shadow-md p-5 transform transition-all duration-300 hover:shadow-xl animate-fadeIn" style={{ animationDelay: '0.7s' }}>
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg mr-2">
              <Building2 className="w-5 h-5 text-blue-600" />
            </div>
            Exhibitions
          </h2>
          <div className="flex items-center justify-between">
            <span className="text-gray-700">Total Exhibitions</span>
            <span className="text-2xl font-bold text-gray-900">
              {summary?.total_exhibitions || 0}
            </span>
          </div>
          <button
            onClick={() => router.push('/exhibitions')}
            className="mt-4 w-full bg-blue-50 text-blue-600 py-2 rounded-lg font-medium hover:bg-blue-100 transition"
          >
            View All Exhibitions
          </button>
        </div>
      </div>

      {/* Bottom Navigation */}
      <BottomNav />
    </div>
  );
}
