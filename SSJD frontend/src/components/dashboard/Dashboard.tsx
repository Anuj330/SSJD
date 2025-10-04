import React from 'react';
import StatCard from './StatCard';
import QuickActions from './QuickActions';
import RecentActivity from './RecentActivity';
import { TrendingUp, TrendingDown, Calendar, AlertCircle, CheckCircle, Clock } from 'lucide-react';

const Dashboard: React.FC = () => {
  const stats = [
    { title: 'Compulsory Deposit', balance: 4100, color: 'from-blue-500 to-blue-600' },
    { title: 'Share Money', balance: 10000, color: 'from-green-500 to-green-600' },
    { title: 'Optional Deposit', balance: 11, color: 'from-yellow-500 to-yellow-600' },
    { title: 'Regular Loan', balance: 48750, interest: 609, color: 'from-orange-500 to-orange-600' },
    { title: 'Emergent Loan', balance: 0, interest: 0, color: 'from-purple-500 to-purple-600' }
  ];

  const currentDate = new Date().toLocaleDateString('en-IN', { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  });

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-xl shadow-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Welcome Back, ANUJ MAHTO</h1>
            <p className="text-blue-100 mt-2 flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              {currentDate}
            </p>
          </div>
          <div className="hidden md:block">
            <div className="bg-white/20 backdrop-blur-sm rounded-lg p-4">
              <p className="text-sm text-blue-100">Member Since</p>
              <p className="text-2xl font-bold">2023</p>
            </div>
          </div>
        </div>
      </div>

      {/* Account Summary Cards */}
      <div>
        <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-blue-600" />
          Account Summary
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {stats.map((stat, idx) => (
            <StatCard 
              key={idx}
              title={stat.title}
              balance={stat.balance}
              interest={stat.interest}
              colorClass={stat.color}
            />
          ))}
        </div>
      </div>

      {/* Financial Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-green-100 p-3 rounded-lg">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Deposits</p>
              <p className="text-2xl font-bold text-gray-800">₹14,111</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-green-600 font-semibold">+12.5%</span>
            <span className="text-gray-600">from last month</span>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-orange-100 p-3 rounded-lg">
              <TrendingDown className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Outstanding Loan</p>
              <p className="text-2xl font-bold text-gray-800">₹48,750</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-600">Interest Due:</span>
            <span className="text-orange-600 font-semibold">₹609</span>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-purple-100 p-3 rounded-lg">
              <CheckCircle className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Credit Score</p>
              <p className="text-2xl font-bold text-gray-800">Excellent</p>
            </div>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-gradient-to-r from-green-400 to-green-600 h-2 rounded-full" style={{ width: '85%' }}></div>
          </div>
        </div>
      </div>

      {/* Important Notifications */}
      <div className="bg-yellow-50 border-l-4 border-yellow-400 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
          <div className="flex-1">
            <h3 className="font-semibold text-yellow-800">Payment Reminder</h3>
            <p className="text-sm text-yellow-700 mt-1">
              Your next EMI payment of ₹5,000 is due on 15th October 2025. 
              <button className="text-yellow-800 underline ml-1 font-medium">Pay Now</button>
            </p>
          </div>
        </div>
      </div>

      {/* Quick Actions and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <QuickActions />
        <RecentActivity />
      </div>

      {/* Upcoming Events */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-blue-600" />
          Upcoming Events & Deadlines
        </h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex flex-col items-center justify-center text-white">
                <span className="text-xs">OCT</span>
                <span className="text-lg font-bold">15</span>
              </div>
              <div>
                <p className="font-semibold text-gray-800">EMI Payment Due</p>
                <p className="text-sm text-gray-600">Regular Loan Payment</p>
              </div>
            </div>
            <span className="text-blue-600 font-semibold">₹5,000</span>
          </div>

          <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-green-600 rounded-lg flex flex-col items-center justify-center text-white">
                <span className="text-xs">OCT</span>
                <span className="text-lg font-bold">20</span>
              </div>
              <div>
                <p className="font-semibold text-gray-800">Monthly Deposit</p>
                <p className="text-sm text-gray-600">Compulsory Deposit</p>
              </div>
            </div>
            <span className="text-green-600 font-semibold">₹300</span>
          </div>

          <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-purple-600 rounded-lg flex flex-col items-center justify-center text-white">
                <span className="text-xs">OCT</span>
                <span className="text-lg font-bold">31</span>
              </div>
              <div>
                <p className="font-semibold text-gray-800">KYC Renewal</p>
                <p className="text-sm text-gray-600">Update Documents</p>
              </div>
            </div>
            <span className="text-purple-600 font-semibold text-sm">Action Required</span>
          </div>
        </div>
      </div>

      {/* Help Section */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl shadow-lg p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold mb-2">Need Help?</h3>
            <p className="text-indigo-100">Our support team is available 24/7 to assist you</p>
          </div>
          <button className="bg-white text-indigo-600 px-6 py-3 rounded-lg font-semibold hover:bg-indigo-50 transition">
            Contact Support
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;