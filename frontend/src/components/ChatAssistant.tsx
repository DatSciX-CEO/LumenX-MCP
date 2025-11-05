import { useState, useRef, useEffect } from 'react';
import { GraphNode } from '../types/graph';
import { graphApi } from '../services/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatAssistantProps {
  node: GraphNode;
}

export default function ChatAssistant({ node }: ChatAssistantProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [useOllama, setUseOllama] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Reset messages when node changes
    setMessages([{
      role: 'assistant',
      content: `Hello! I'm Agent X. I can help you analyze "${node.label}". Ask me anything about this entity.`,
      timestamp: new Date(),
    }]);
  }, [node.id]);

  useEffect(() => {
    // Scroll to bottom when messages change
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await graphApi.chat(input, node.id, useOllama);
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestedQuestions = [
    'What are the main risks associated with this entity?',
    'Who has accessed this recently?',
    'What connections should I investigate?',
    'Summarize the key insights',
  ];

  return (
    <div className="flex flex-col h-full">
      {/* Provider Toggle */}
      <div className="p-3 border-b border-slate-700 bg-slate-750">
        <label className="flex items-center gap-2 text-xs text-gray-400">
          <input
            type="checkbox"
            checked={useOllama}
            onChange={(e) => setUseOllama(e.target.checked)}
            className="w-3 h-3 accent-blue-500"
          />
          <span>Use Local Ollama (faster, offline)</span>
        </label>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-lg p-3 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-gray-100'
              }`}
            >
              <div className="text-sm whitespace-pre-wrap">{message.content}</div>
              <div className="text-xs opacity-60 mt-1">
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-700 rounded-lg p-3">
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <div className="animate-pulse">Agent X is thinking...</div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions */}
      {messages.length === 1 && (
        <div className="px-4 pb-3">
          <div className="text-xs text-gray-400 mb-2">Suggested questions:</div>
          <div className="space-y-2">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => setInput(question)}
                className="w-full text-left text-xs bg-slate-700 hover:bg-slate-600 rounded p-2 transition"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-slate-700">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask Agent X anything..."
            className="flex-1 bg-slate-700 text-white rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={2}
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:text-gray-500 rounded-lg transition"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
