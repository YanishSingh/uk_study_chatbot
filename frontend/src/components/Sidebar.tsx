import React, { useState } from "react";
import SidebarConversationList from "./SidebarConversationList";
import SidebarSettings from "./SidebarSettings";
import { FaPlus, FaSearch } from "react-icons/fa";

// Define the props the Sidebar expects:
interface SidebarProps {
  onNewChat: (firstMessage?: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ onNewChat }) => {
  const [search, setSearch] = useState("");
  const [reload, setReload] = useState(false); // For forcing sidebar reload on new chat

  // Trigger a reload in child after new chat is created
  const handleReload = () => setReload(r => !r);

  // You no longer need handleNewChat here unless you want a default message;
  // Instead, use the onNewChat prop passed from parent:
  const handleNewChatClick = () => {
  onNewChat("");  // Send an empty string (or undefined)
  handleReload();
};

  return (
    <aside className="
      w-[210px] bg-white h-[95vh] my-3 ml-3 rounded-2xl shadow-lg flex flex-col
      absolute left-0 top-0 z-30
      ">
      {/* LOGO */}
      <div className="pt-7 pb-3 px-5">
        <div className="text-[1.1rem] font-extrabold tracking-wide">BritMentor</div>
      </div>
      {/* NEW CHAT & SEARCH */}
      <div className="px-5">
        <button
          className="w-full py-2.5 mb-3 flex items-center justify-center gap-2
          bg-[#6366f1] hover:bg-[#4756e7] text-white text-base font-semibold rounded-xl shadow
          transition"
          onClick={handleNewChatClick}
        >
          <FaPlus size={16} style={{ marginRight: 4 }} /> New chat
        </button>
        <div className="relative mb-5">
          <input
            className="w-full py-2 pl-4 pr-9 bg-[#f7f7fa] rounded-full border border-gray-200 focus:outline-none text-sm"
            placeholder="Search chats"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          <FaSearch
            size={16}
            style={{ color: "#a3a3a3", position: "absolute", right: "1rem", top: "0.7rem" }}
          />
        </div>
      </div>
      <SidebarConversationList search={search} reload={reload} />
      <SidebarSettings />
    </aside>
  );
};

export default Sidebar;
