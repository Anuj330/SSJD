import React from 'react';

interface HeaderProps {
  userName: string;
  memberId: string;
}

const Header: React.FC<HeaderProps> = ({ userName, memberId }) => {
  const initials = userName.split(' ').map(n => n[0]).join('');
  
  return (
    <div className="bg-white shadow-md p-4 flex items-center justify-between">
      <h1 className="text-xl font-bold text-gray-800">Jan Dhan Sanchay Coop. Society</h1>
      <div className="flex items-center space-x-4">
        <div className="text-right">
          <p className="text-sm font-semibold text-gray-800">{userName}</p>
          <p className="text-xs text-gray-600">Member ID: {memberId}</p>
        </div>
        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold">
          {initials}
        </div>
      </div>
    </div>
  );
};

export default Header;