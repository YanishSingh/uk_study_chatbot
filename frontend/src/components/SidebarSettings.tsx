import React, { useState, useRef, useEffect } from "react";
import { FaUserCircle, FaSignOutAlt } from "react-icons/fa";

// Helper for avatar color (optional: pick color based on username for uniqueness)
const getColor = (name: string) => {
  const colors = [
    "#6366f1", "#10b981", "#f59e42", "#f43f5e", "#6366f1"
  ];
  return colors[name.charCodeAt(0) % colors.length];
};

const SidebarSettings: React.FC = () => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const username = localStorage.getItem("username") || "User";
  const initial = username.charAt(0).toUpperCase();

  // Close dropdown when clicking outside
  const containerRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    if (dropdownOpen) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [dropdownOpen]);

  // Handle logout logic
  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    window.location.href = "/"; // Redirect to login or landing
  };

  return (
    <div className="px-5 py-6 space-y-2 border-t border-gray-100 mt-auto">
      <button className="w-full flex items-center py-2 px-4 rounded-xl bg-[#f7f7fa] hover:bg-neutral-200 transition text-neutral-700 font-semibold mb-1">
        <span className="mr-2">
          <span style={{ fontSize: "1.25rem" }}>
            <FaUserCircle />
          </span>
        </span>
        Settings
      </button>
      <div className="relative" ref={containerRef}>
        <button
          className="w-full flex items-center py-2 px-4 rounded-xl bg-[#f7f7fa] text-neutral-700 focus:outline-none"
          onClick={() => setDropdownOpen((o) => !o)}
        >
          <span
            className="w-7 h-7 rounded-full flex items-center justify-center text-white font-bold mr-3"
            style={{
              background: getColor(username),
              fontSize: "1rem"
            }}
          >
            {initial}
          </span>
          <span className="font-medium truncate">{username}</span>
          <svg
            className={`ml-auto transition-transform ${dropdownOpen ? "rotate-180" : ""}`}
            width={18} height={18} viewBox="0 0 20 20" fill="none"
          >
            <path d="M7 8l3 3 3-3" stroke="#64748b" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
        {dropdownOpen && (
          <div className="absolute right-0 mt-2 bg-white border rounded-xl shadow-lg z-20 w-40">
            <button
              className="flex items-center w-full px-4 py-3 text-red-600 hover:bg-neutral-100 rounded-xl font-medium"
              onClick={handleLogout}
            >
              <FaSignOutAlt style={{ marginRight: 8 }} />
              Log out
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SidebarSettings;
