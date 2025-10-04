import React from 'react';

interface StatCardProps {
  title: string;
  balance: number;
  interest?: number;
  colorClass: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, balance, interest, colorClass }) => {
  return (
    <div className={`bg-gradient-to-br ${colorClass} rounded-xl shadow-lg p-6 text-white transform hover:scale-105 transition duration-200`}>
      <h3 className="text-lg font-semibold opacity-90">{title}</h3>
      <p className="text-3xl font-bold mt-3">₹{balance.toLocaleString()}</p>
      {interest !== undefined && (
        <p className="text-sm mt-2 opacity-90">Interest: ₹{interest}</p>
      )}
    </div>
  );
};

export default StatCard;