import React from 'react';
import { RefreshCw, LogIn, CreditCard, FileText } from 'lucide-react';

const RecentActivity: React.FC = () => {
  const activities = [
    {
      icon: LogIn,
      title: 'Login Successful',
      description: 'Account accessed successfully',
      time: 'Just now',
      color: 'border-green-500'
    },
    {
      icon: CreditCard,
      title: 'Payment Processed',
      description: 'Regular loan payment of ₹5000',
      time: '2 hours ago',
      color: 'border-blue-500'
    },
    {
      icon: FileText,
      title: 'Statement Generated',
      description: 'Monthly balance statement',
      time: 'Yesterday',
      color: 'border-purple-500'
    },
    {
      icon: RefreshCw,
      title: 'Account Updated',
      description: 'KYC details verified',
      time: '2 days ago',
      color: 'border-orange-500'
    }
  ];

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h2 className="text-xl font-bold text-gray-800 mb-4">Recent Activity</h2>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {activities.map((activity, idx) => {
          const Icon = activity.icon;
          return (
            <div key={idx} className={`border-l-4 ${activity.color} pl-4 py-2 hover:bg-gray-50 transition rounded-r-lg`}>
              <div className="flex items-start gap-3">
                <div className="mt-1">
                  <Icon className="w-5 h-5 text-gray-600" />
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-gray-800">{activity.title}</p>
                  <p className="text-sm text-gray-600">{activity.description}</p>
                  <p className="text-xs text-gray-500 mt-1">{activity.time}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default RecentActivity;