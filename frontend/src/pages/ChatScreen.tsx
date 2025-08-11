/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useState, useCallback } from "react";
import Sidebar from "../components/Sidebar";
import MainChat from "../components/MainChat";

type ChatMessage = { role: "user" | "bot"; text: string };

const ChatScreen: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch chat messages for current session
  const fetchMessages = async (sid: number) => {
    const token = localStorage.getItem("token");
    if (!token || !sid) return;
    const res = await fetch(`http://localhost:5000/api/chatbot/sessions/${sid}/messages`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (res.ok) {
      const data = await res.json(); // [{message, response, ...}]
      // Flatten to [{role, text}]
      const msgs: ChatMessage[] = data.flatMap((m: any) => [
        { role: "user", text: m.message },
        m.response && { role: "bot", text: m.response }
      ]).filter(Boolean);
      setMessages(msgs);
    }
  };

  // New chat handler (called from Sidebar button)
  const handleNewChat = useCallback(async (firstMessage?: string) => {
    const token = localStorage.getItem("token");
    const body = firstMessage ? { message: firstMessage } : {};
    const res = await fetch(`http://localhost:5000/api/chatbot/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(body)
    });
    if (res.ok) {
      const data = await res.json();
      setSessionId(data.id);
      localStorage.setItem("activeSession", String(data.id));
      setMessages([]); // clear messages
      // 👇 THIS triggers sidebar to reload immediately after new chat
      window.dispatchEvent(new CustomEvent("sessionsUpdated"));
    }
  }, []);

  // Load session from localStorage or first session
  useEffect(() => {
    const active = localStorage.getItem("activeSession");
    if (active) {
      setSessionId(Number(active));
      fetchMessages(Number(active));
    }
    // Listen to session changes triggered by Sidebar
    const handleSessionChange = (e: any) => {
      const id = Number(e.detail?.sessionId || localStorage.getItem("activeSession"));
      setSessionId(id);
      fetchMessages(id);
    };
    // Listen to create new chat event (when all chats are cleared)
    const handleCreateNewChat = () => {
      setMessages([]); // Clear current messages
      setSessionId(null); // Clear current session
      handleNewChat(); // Create a new chat
    };
    window.addEventListener("sessionChange", handleSessionChange as any);
    window.addEventListener("createNewChat", handleCreateNewChat);
    return () => {
      window.removeEventListener("sessionChange", handleSessionChange as any);
      window.removeEventListener("createNewChat", handleCreateNewChat);
    };
    // eslint-disable-next-line
  }, [handleNewChat]);

  // Send a message to backend and update chat
  const handleSend = async (msg: string) => {
    console.log("handleSend called with:", msg);
    console.log("Message length:", msg.length);
    console.log("Message characters:", msg.split('').map(char => `'${char}'`));
    console.log("Current sessionId:", sessionId);
    
    if (!msg.trim()) {
      console.log("Message is empty");
      return;
    }
    
    setIsLoading(true); // Start loading
    
    // If no sessionId, create a new chat session first
    let currentSessionId = sessionId;
    if (!currentSessionId) {
      console.log("No sessionId, creating new chat session");
      const token = localStorage.getItem("token");
      const res = await fetch(`http://localhost:5000/api/chatbot/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ message: msg })
      });
      if (res.ok) {
        const data = await res.json();
        currentSessionId = data.id;
        setSessionId(data.id);
        localStorage.setItem("activeSession", String(data.id));
        console.log("Created new session:", data.id);
        // Trigger sidebar update
        window.dispatchEvent(new CustomEvent("sessionsUpdated"));
      } else {
        console.error("Failed to create new session");
        setIsLoading(false);
        return;
      }
    }
    
    setInput("");
    const userMessage = msg.trim();
    console.log("Adding user message to state:", userMessage);
    console.log("User message length:", userMessage.length);
    setMessages(prev => [...prev, { role: "user", text: userMessage }]);
    console.log("Added user message to state");
    
    // Send to backend (POST /sessions/<id>/message)
    const token = localStorage.getItem("token");
    console.log("Making API call to:", `http://localhost:5000/api/chatbot/sessions/${currentSessionId}/message`);
    
    try {
      const res = await fetch(`http://localhost:5000/api/chatbot/sessions/${currentSessionId}/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ message: msg })
      });
      
      console.log("API response status:", res.status);
      
      if (res.ok) {
        const data = await res.json();
        console.log("API response data:", data);
        setMessages(prev => [...prev, { role: "bot", text: data.answer }]);
        console.log("Added bot response to state");
        // 👇 THIS triggers sidebar to reload session names in real time!
        window.dispatchEvent(new CustomEvent("sessionsUpdated"));
      } else {
        console.error("API call failed:", res.status, res.statusText);
        const errorData = await res.text();
        console.error("Error response:", errorData);
        // Add error message to chat
        setMessages(prev => [...prev, { 
          role: "bot", 
          text: "I'm having trouble connecting right now. Please try again in a moment." 
        }]);
      }
    } catch (error) {
      console.error("Network error:", error);
      // Add error message to chat
      setMessages(prev => [...prev, { 
        role: "bot", 
        text: "Sorry, there seems to be a connection issue. Please check your internet and try again." 
      }]);
    } finally {
      setIsLoading(false); // End loading
    }
  };

  return (
    <div className="min-h-screen bg-[#f7f8fa] flex font-inter">
      <Sidebar onNewChat={handleNewChat} />
      <MainChat
        messages={messages}
        onSend={handleSend}
        input={input}
        setInput={setInput}
        isLoading={isLoading}
      />
    </div>
  );
};

export default ChatScreen;
