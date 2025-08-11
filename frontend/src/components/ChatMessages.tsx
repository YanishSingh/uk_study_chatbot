import React from "react";

type Message = { role: "user" | "bot"; text: string };
type Props = { messages: Message[] };

// Enhanced markdown renderer for ChatGPT responses
const formatMessage = (text: string) => {
  if (!text) return text;
  
  // Convert **text** to bold with better styling
  let formatted = text.replace(/\*\*(.*?)\*\*/g, '<strong style="color: #4f46e5; font-weight: 600;">$1</strong>');
  
  // Handle emojis and special formatting
  formatted = formatted.replace(/🎓/g, '<span style="color: #059669;">🎓</span>');
  formatted = formatted.replace(/📋/g, '<span style="color: #0284c7;">📋</span>');
  formatted = formatted.replace(/💰/g, '<span style="color: #ca8a04;">💰</span>');
  formatted = formatted.replace(/🛂/g, '<span style="color: #dc2626;">🛂</span>');
  formatted = formatted.replace(/🌐/g, '<span style="color: #7c3aed;">🌐</span>');
  
  // Handle numbered lists (1., 2., etc.) - require space after dot to avoid decimal numbers
  formatted = formatted.replace(/^(\d+\.)\s+/gm, '<strong style="color: #4f46e5;">$1</strong> ');
  
  // Handle bullet points by wrapping them in <ul> tags
  const lines = formatted.split('\n');
  const formattedLines = [];
  let inBulletList = false;
  let inNumberedList = false;
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    // Handle bullet points
    if (line.trim().startsWith('•') || line.trim().startsWith('-')) {
      if (!inBulletList) {
        if (inNumberedList) {
          formattedLines.push('</ol>');
          inNumberedList = false;
        }
        formattedLines.push('<ul style="margin: 8px 0; padding-left: 20px; list-style-type: disc;">');
        inBulletList = true;
      }
      const content = line.replace(/^[•-]\s*/, '');
      formattedLines.push(`<li style="margin: 4px 0; line-height: 1.4;">${content}</li>`);
    }
    // Handle numbered lists (but not decimal numbers)
    else if (line.trim().match(/^\d+\.\s/)) {
      if (!inNumberedList) {
        if (inBulletList) {
          formattedLines.push('</ul>');
          inBulletList = false;
        }
        formattedLines.push('<ol style="margin: 8px 0; padding-left: 20px;">');
        inNumberedList = true;
      }
      const content = line.replace(/^\d+\.\s+/, '');
      formattedLines.push(`<li style="margin: 4px 0; line-height: 1.4;">${content}</li>`);
    }
    // Regular lines
    else {
      if (inBulletList) {
        formattedLines.push('</ul>');
        inBulletList = false;
      }
      if (inNumberedList) {
        formattedLines.push('</ol>');
        inNumberedList = false;
      }
      if (line.trim()) {
        // Handle section headers (lines ending with :)
        if (line.trim().endsWith(':') && line.trim().length > 2) {
          formattedLines.push(`<div style="font-weight: 600; color: #374151; margin: 12px 0 6px 0;">${line}</div>`);
        } else {
          formattedLines.push(`<div style="margin: 4px 0; line-height: 1.5;">${line}</div>`);
        }
      } else if (i < lines.length - 1 && lines[i + 1].trim()) {
        formattedLines.push('<div style="height: 8px;"></div>');
      }
    }
  }
  
  // Close any open lists
  if (inBulletList) {
    formattedLines.push('</ul>');
  }
  if (inNumberedList) {
    formattedLines.push('</ol>');
  }
  
  return formattedLines.join('');
};

const ChatMessages: React.FC<Props> = ({ messages }) => (
  <div className="w-full max-w-3xl mb-7">
    {messages.map((msg, idx) => (
      <div key={idx} className={`flex my-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
        <div className={`px-5 py-3 rounded-2xl max-w-xl ${msg.role === "user"
          ? "bg-[#6366f1] text-white" : "bg-white text-gray-900 border"}`}>
          <div 
            dangerouslySetInnerHTML={{ __html: formatMessage(msg.text) }}
            className="leading-relaxed"
          />
        </div>
      </div>
    ))}
  </div>
);

export default ChatMessages;
