import React, { useRef, useEffect } from "react";
import ChatMessages from "./ChatMessages";
import ChatInputBar from "./ChatInputBar";
import FeatureCards from "./FeatureCards";

type Message = { role: "user" | "bot"; text: string };

interface Props {
  messages: Message[];
  input: string;
  setInput: (val: string) => void;
  onSend: (msg: string) => void;
  isLoading?: boolean;
}

const MainChat: React.FC<Props> = ({ messages, input, setInput, onSend, isLoading = false }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  return (
    <main className="flex-1 flex flex-col items-center px-4 pt-16 pb-2" style={{ marginLeft: 220, minHeight: "100vh" }}>
      <div className="w-full flex-1 flex flex-col items-center overflow-y-auto max-h-[calc(100vh-120px)] mb-3">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center w-full h-[60vh]">
            <div className="text-3xl font-bold mb-2 text-neutral-900">Good day! How may I assist you today?</div>
            <FeatureCards onPrompt={onSend} />
          </div>
        ) : (
          <>
            <ChatMessages messages={messages} />
            {isLoading && (
              <div className="flex gap-4 justify-start my-2 w-full max-w-3xl">
                <div className="w-8 h-8 bg-gradient-to-r from-emerald-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                  🎓
                </div>
                <div className="bg-white text-gray-800 border border-gray-200 px-5 py-4 rounded-2xl shadow-sm">
                  <div className="flex items-center space-x-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                    </div>
                    <span className="text-sm text-gray-600 ml-2">Thinking with AI...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef}></div>
          </>
        )}
      </div>
      <div className="sticky bottom-8 w-full flex justify-center z-50">
        <ChatInputBar input={input} setInput={setInput} onSend={onSend} isLoading={isLoading} />
      </div>
    </main>
  );
};

export default MainChat;
