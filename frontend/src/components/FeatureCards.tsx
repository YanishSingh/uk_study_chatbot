// src/components/FeatureCards.tsx

import React from "react";

const cards = [
  {
    title: "Find My University Match",
    desc: "I want to find universities that match my GPA and English scores for Undergraduate/Postgraduate.",
  },
  {
    title: "IELTS Waiver Universities",
    desc: "I have English subject grade B+, which universities offer IELTS waiver?",
  },
  {
    title: "Scholarships for Nepalese Students",
    desc: "Show me available UK scholarships for Nepalese students.",
  },
  {
    title: "UK Student Visa Requirements",
    desc: "What are the latest document requirements for a UK study visa?",
  },
  {
    title: "Best Affordable Universities",
    desc: "List the most affordable universities in the UK for international students.",
  },
  {
    title: "Average Living Cost in London",
    desc: "What is the average monthly living cost for a student in London?",
  },
];

type Props = { onPrompt: (msg: string) => void };

const FeatureCards: React.FC<Props> = ({ onPrompt }) => (
  <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-8 mb-2">
    {cards.map((c, i) => (
      <button
        key={i}
        className="flex flex-col justify-between rounded-2xl bg-white border hover:shadow-xl transition px-5 py-4 text-left shadow
        hover:border-blue-500"
        onClick={() => onPrompt(c.desc)}
      >
        <div>
          <div className="font-semibold text-lg text-neutral-900 mb-1">{c.title}</div>
          <div className="text-[15px] text-gray-500">{c.desc}</div>
        </div>
        <div className="flex justify-end mt-4">
          <span className="text-blue-500 text-xl">🎓</span>
        </div>
      </button>
    ))}
  </div>
);

export default FeatureCards;
