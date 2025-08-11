import React, { useEffect, useState } from "react";
import { FaRegCommentDots } from "react-icons/fa";

type ChatSession = { id: number; name: string };

interface Props {
  search: string;
  reload: boolean;
}

const SidebarConversationList: React.FC<Props> = ({ search, reload }) => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeId, setActiveId] = useState<number | null>(
    Number(localStorage.getItem("activeSession")) || null
  );
  const [showConfirm, setShowConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // For force-reload when sessionsUpdated event fires
  const [externalReload, setExternalReload] = useState(0); // 👈

  useEffect(() => {
    const onSessionsUpdated = () => setExternalReload((r) => r + 1);
    window.addEventListener("sessionsUpdated", onSessionsUpdated); // 👈
    return () => window.removeEventListener("sessionsUpdated", onSessionsUpdated);
  }, []);

  useEffect(() => {
    const fetchSessions = async () => {
      const token = localStorage.getItem("token");
      if (!token) return;
      const res = await fetch("http://localhost:5000/api/chatbot/sessions", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSessions(data); // backend returns an array!
        // Only auto-select if there is NO active session
        if ((!activeId || !data.find((s: ChatSession) => s.id === activeId)) && data.length > 0) {
          setActiveId(data[0].id);
          localStorage.setItem("activeSession", String(data[0].id));
          window.dispatchEvent(
            new CustomEvent("sessionChange", { detail: { sessionId: data[0].id } })
          );
        }
      }
    };
    fetchSessions();
    // eslint-disable-next-line
  }, [reload, externalReload]); // 👈 Trigger reload if "sessionsUpdated" fires

  // Filtering for search
  const filtered = search
    ? sessions.filter((s) =>
        s.name.toLowerCase().includes(search.toLowerCase())
      )
    : sessions;

  // Set active session on click
  const handleSelect = (id: number) => {
    setActiveId(id);
    localStorage.setItem("activeSession", id.toString());
    window.dispatchEvent(
      new CustomEvent("sessionChange", { detail: { sessionId: id } })
    );
  };

  return (
    <div className="flex-1 overflow-auto px-2">
      <div className="flex justify-between items-center text-xs text-gray-500 mb-1 px-3">
        <span>Your conversations</span>
        <button
          className="hover:underline text-[#6366f1] font-semibold"
          onClick={() => setShowConfirm(true)}
        >
          Clear All
        </button>
      </div>
      {/* Custom Confirmation Modal */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-30">
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-xs text-center">
            <div className="font-semibold text-lg mb-3">Clear all chats?</div>
            <div className="text-gray-600 mb-5">Are you sure you want to delete all your conversations? This cannot be undone.</div>
            <div className="flex gap-3 justify-center">
              <button
                className="px-4 py-2 rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium"
                onClick={() => setShowConfirm(false)}
                disabled={deleting}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold"
                onClick={async () => {
                  setDeleting(true);
                  const token = localStorage.getItem("token");
                  if (!token) return;
                  await fetch("http://localhost:5000/api/chatbot/sessions", {
                    method: "DELETE",
                    headers: { Authorization: `Bearer ${token}` },
                  });
                  setSessions([]);
                  setActiveId(null);
                  localStorage.removeItem("activeSession");
                  window.dispatchEvent(new CustomEvent("sessionsUpdated"));
                  // Notify chat screen to create a new chat
                  window.dispatchEvent(new CustomEvent("createNewChat"));
                  setDeleting(false);
                  setShowConfirm(false);
                }}
                disabled={deleting}
              >
                {deleting ? "Deleting..." : "Yes, clear all"}
              </button>
            </div>
          </div>
        </div>
      )}
      <ul className="space-y-2 pb-2">
        {filtered.map((chat) => (
          <li
            key={chat.id}
            className={`flex items-center text-[15px] px-4 py-2 rounded-xl hover:bg-[#f6f7fb] transition cursor-pointer
            ${chat.id === activeId ? "bg-[#f0f1fa]" : ""}`}
            onClick={() => handleSelect(chat.id)}
          >
            <span
              style={{
                marginRight: "0.5rem",
                color: "#a3a3a3",
                fontSize: "1.125rem",
              }}
            >
              <FaRegCommentDots />
            </span>
            <span className="truncate font-medium text-neutral-800">
              {chat.name}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default SidebarConversationList;
