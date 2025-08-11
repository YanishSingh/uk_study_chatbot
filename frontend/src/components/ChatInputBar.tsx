import React, { useState } from "react";
import { FaPaperPlane } from "react-icons/fa";

type Props = {
  input: string;
  setInput: (val: string) => void;
  onSend: (msg: string) => void;
  isLoading?: boolean;
};

const quickSuggestions = [
  "Show me computer science universities",
  "What are visa requirements?",
  "Living costs in London?",
  "Scholarship opportunities",
  "Application deadlines",
  "I want to study engineering"
];

const ChatInputBar: React.FC<Props> = ({ input, setInput, onSend, isLoading = false }) => {
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Handles both Enter and button click
  const handleSend = () => {
    if (input.trim() && !isLoading) {
      console.log("ChatInputBar sending:", input.trim());
      console.log("Input length:", input.trim().length);
      onSend(input.trim());
      setInput(""); // clear input after sending
      setShowSuggestions(false);
    }
  };

  // Handles Enter key
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !isLoading) {
      e.preventDefault();
      handleSend();
    } else if (e.key === "Escape") {
      setShowSuggestions(false);
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
    setShowSuggestions(false);
    onSend(suggestion);
  };

  // Show suggestions when input is focused and empty
  const handleFocus = () => {
    if (!input.trim()) {
      setShowSuggestions(true);
    }
  };

  return (
    <div className="relative">
      {/* Quick Suggestions */}
      {showSuggestions && (
        <div className="absolute bottom-full mb-2 w-full max-w-2xl bg-white rounded-2xl shadow-xl border border-gray-200 p-4">
          <div className="text-sm text-gray-600 mb-3 font-medium">💡 Quick suggestions:</div>
          <div className="flex flex-wrap gap-2">
            {quickSuggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestionClick(suggestion)}
                className="px-3 py-2 bg-gray-50 hover:bg-indigo-50 text-gray-700 hover:text-indigo-700 rounded-lg text-sm transition-colors border border-gray-200 hover:border-indigo-300"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main Input Bar */}
      <div className="w-full max-w-2xl bg-white rounded-full shadow-2xl flex items-center px-6 py-3 border border-neutral-200">
        <div className="w-7 h-7 bg-gradient-to-r from-emerald-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold text-sm mr-3">
          🎓
        </div>
        <input
          className={`flex-1 border-0 outline-none bg-transparent text-base ${isLoading ? 'text-gray-400' : 'text-gray-800'}`}
          placeholder={isLoading ? "Please wait..." : "Ask about UK universities, visas, costs, or applications..."}
          value={input}
          onChange={e => {
            if (!isLoading) {
              console.log("Input onChange:", e.target.value);
              console.log("Input value length:", e.target.value.length);
              setInput(e.target.value);
              if (e.target.value.trim()) {
                setShowSuggestions(false);
              }
            }
          }}
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)} // Delay to allow click
          disabled={isLoading}
          autoFocus
        />
        <button
          className="ml-4 p-2 bg-[#6366f1] hover:bg-[#4756e7] rounded-full text-white transition disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          tabIndex={0}
          aria-label={isLoading ? "Please wait..." : "Send message"}
        >
          {isLoading ? (
            <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full"></div>
          ) : (
            <FaPaperPlane size={20} style={{ color: "#fff" }} />
          )}
        </button>
      </div>
    </div>
  );
};

export default ChatInputBar;
