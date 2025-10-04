import React from 'react';
import { CreditCard, FileCheck, UserCheck } from 'lucide-react';

const QuickActions: React.FC = () => {
  const actions = [
    { 
      label: 'Make Payment', 
      icon: CreditCard, 
      color: 'bg-blue-50 hover:bg-blue-100 text-blue-700',
      onClick: () => alert('Payment feature coming soon!')
    },
    { 
      label: 'ENACH Registration', 
      icon: FileCheck, 
      color: 'bg-green-50 hover:bg-green-100 text-green-700',
      onClick: () => alert('ENACH Registration coming soon!')
    },
    { 
      label: 'Update KYC', 
      icon: UserCheck, 
      color: 'bg-purple-50 hover:bg-purple-100 text-purple-700',
      onClick: () => alert('KYC Update coming soon!')
    }
  ];

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h2 className="text-xl font-bold text-gray-800 mb-4">Quick Actions</h2>
      <div className="space-y-3">
        {actions.map((action, idx) => {
          const Icon = action.icon;
          return (
            <button
              key={idx}
              onClick={action.onClick}
              className={`w-full ${action.color} py-3 px-4 rounded-lg font-semibold transition flex items-center justify-center gap-2`}
            >
              <Icon className="w-5 h-5" />
              {action.label}
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default QuickActions;