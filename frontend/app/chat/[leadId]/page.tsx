"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Camera, Mic, Send, StopCircle } from "lucide-react";
import BottomNav from "@/components/BottomNav";
import { api } from "@/lib/api";

interface Message {
  sender: "me" | "lead" | "system";
  text: string;
  timestamp?: string;
}

export default function ChatScreen({ params }: { params: { leadId: string } }) {
  const router = useRouter();
  const leadId = parseInt(params.leadId);

  const [lead, setLead] = useState<any>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);

  const scrollRef = useRef<HTMLDivElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    loadLead();
  }, [leadId]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadLead = async () => {
    try {
      setLoading(true);
      const response = await api.getLead(leadId);
      setLead(response);

      // Load messages
      const messagesData = await api.getLeadMessages(leadId);
      if (messagesData && messagesData.length > 0) {
        const formattedMessages = messagesData.map((msg: any): Message => ({
          sender: (msg.SenderType === 'employee' ? 'me' : msg.SenderType === 'system' ? 'system' : 'lead') as "me" | "lead" | "system",
          text: msg.MessageText,
          timestamp: msg.CreatedAt
        }));
        setMessages(formattedMessages);
      }
    } catch (error) {
      console.error('Failed to load lead:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = () => {
    if (!input.trim()) return;

    const newMessage: Message = {
      sender: "me",
      text: input,
      timestamp: new Date().toISOString()
    };

    setMessages([...messages, newMessage]);
    setInput("");

    // TODO: Send message to API
    // api.sendMessage(leadId, input);
  };

  const startRecording = async () => {
    console.log('🎤 [CHAT PAGE] Mic button clicked - startRecording called');

    try {
      // Check if mediaDevices is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error('❌ MediaDevices not supported');
        alert('Your browser does not support audio recording');
        return;
      }

      console.log('✅ Requesting microphone access...');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      console.log('✅ Microphone access granted');

      // Set recording state BEFORE creating MediaRecorder
      console.log('🔵 Setting isRecording to TRUE');
      setIsRecording(true);
      setRecordingTime(0);
      console.log('🔵 State updated, starting timer');

      // Start timer immediately
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => {
          console.log(`⏰ Timer tick: ${prev + 1}s`);
          return prev + 1;
        });
      }, 1000);

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      const chunks: Blob[] = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
          console.log(`📦 Audio chunk received: ${e.data.size} bytes`);
        }
      };

      mediaRecorder.onstop = async () => {
        console.log('🛑 Recording stopped, processing audio...');
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        console.log(`🎵 Audio blob created: ${audioBlob.size} bytes`);

        try {
          // Add voice note to messages immediately
          const newMessage: Message = {
            sender: "me",
            text: "🎤 Sending voice note...",
            timestamp: new Date().toISOString()
          };
          setMessages(prev => [...prev, newMessage]);

          // Upload voice note to API and extract
          const audioFile = new File([audioBlob], 'voice_note.webm', { type: 'audio/webm' });
          const result = await api.extractVoice(audioFile, leadId, undefined);

          // Update message with transcription
          if (result.transcript) {
            setMessages(prev => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                sender: "me",
                text: `🎤 Voice note: "${result.transcript}"`,
                timestamp: new Date().toISOString()
              };
              return updated;
            });
          }
        } catch (error) {
          console.error('Failed to upload voice note:', error);
          alert('Failed to send voice note');
        }

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());
        console.log('✅ All tracks stopped');
      };

      mediaRecorder.start();
      console.log('🎙️ MediaRecorder started successfully');

      // Force a small delay to ensure state propagates
      setTimeout(() => {
        console.log('🔍 Checking state after 100ms - isRecording should be true');
      }, 100);
    } catch (error: any) {
      console.error('❌ Failed to start recording:', error);

      // Reset state on error
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }

      // More specific error messages
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        alert('Microphone permission denied. Please allow microphone access in your browser settings.');
      } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
        alert('No microphone found. Please connect a microphone and try again.');
      } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
        alert('Microphone is already in use by another application.');
      } else {
        alert(`Failed to start recording: ${error.message || 'Unknown error'}`);
      }
    }
  };

  const stopRecording = () => {
    console.log('🛑 [CHAT PAGE] Stop button clicked');

    if (mediaRecorderRef.current && isRecording) {
      console.log('🛑 Stopping MediaRecorder...');
      mediaRecorderRef.current.stop();

      console.log('🔴 Setting isRecording to FALSE');
      setIsRecording(false);

      if (timerRef.current) {
        console.log('⏹️ Clearing timer interval');
        clearInterval(timerRef.current);
        timerRef.current = null;
      }

      console.log('✅ Recording stopped successfully');
    } else {
      console.warn('⚠️ Cannot stop recording - not currently recording or no MediaRecorder');
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="flex flex-col h-screen bg-gradient-to-b from-blue-50 to-white">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center animate-fadeIn">
            <div className="relative mx-auto mb-6 w-12 h-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <div className="absolute top-0 left-0 animate-ping rounded-full h-12 w-12 border-2 border-blue-300 opacity-20"></div>
            </div>
            <p className="text-gray-600">Loading chat...</p>
          </div>
        </div>
        <BottomNav />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* HEADER */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 shadow-lg sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push('/leads')}
            className="text-white hover:bg-white/20 p-2 rounded-full transition-all duration-200 active:scale-95"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>

          <div className="flex-1">
            <h1 className="font-semibold text-lg">
              {lead?.PrimaryVisitorName || `Lead #${leadId}`}
            </h1>
            {lead?.CompanyName && (
              <p className="text-blue-100 text-sm">{lead.CompanyName}</p>
            )}
          </div>

          <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center text-xl">
            👤
          </div>
        </div>
      </div>

      {/* CHAT AREA */}
      <div className="flex-1 overflow-y-auto p-4 pb-24">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-500 animate-fadeIn">
              <div className="text-4xl mb-2">💬</div>
              <p className="text-sm">No messages yet</p>
              <p className="text-xs">Start the conversation!</p>
            </div>
          </div>
        ) : (
          messages.map((m, i) => (
            <div
              key={i}
              className={`mb-3 flex animate-fadeIn ${
                m.sender === "me" ? "justify-end" : "justify-start"
              }`}
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              <div
                className={`px-4 py-2 max-w-[75%] rounded-2xl text-sm shadow-md transition-all duration-200 hover:shadow-lg ${
                  m.sender === "me"
                    ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-br-none"
                    : m.sender === "system"
                    ? "bg-yellow-50 text-gray-700 border border-yellow-200 rounded-lg"
                    : "bg-white text-gray-900 rounded-bl-none"
                }`}
              >
                {m.text}
                {m.timestamp && (
                  <div className={`text-xs mt-1 ${m.sender === "me" ? "text-blue-100" : "text-gray-400"}`}>
                    {new Date(m.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        <div ref={scrollRef} />
      </div>

      {/* INPUT BAR */}
      <div className="fixed bottom-16 left-0 right-0 bg-white border-t shadow-lg">
        {isRecording ? (
          <div className="flex items-center justify-center bg-gradient-to-r from-blue-50 to-blue-100 rounded-full px-6 py-3 mx-4 my-2 shadow-lg">
            {/* Blue microphone icon */}
            <div className="bg-blue-500 rounded-full p-3 mr-3 shadow-md flex-shrink-0">
              <Mic className="w-5 h-5 text-white" />
            </div>

            {/* Animated waveform bars */}
            <div className="flex items-center justify-center gap-1 flex-1 h-10 max-w-md">
              {[...Array(30)].map((_, i) => {
                const randomHeight = 10 + Math.floor(Math.random() * 25);
                return (
                  <div
                    key={i}
                    className="bg-blue-500 rounded-full waveform-bar"
                    style={{
                      width: '2.5px',
                      height: `${randomHeight}px`,
                      animationDelay: `${i * 0.05}s`,
                    }}
                  />
                );
              })}
            </div>

            {/* Stop button */}
            <button
              onClick={stopRecording}
              className="ml-3 bg-red-500 hover:bg-red-600 text-white rounded-full p-2 transition-colors flex-shrink-0"
              title="Stop recording"
            >
              <StopCircle className="w-5 h-5" />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-3 p-3 max-w-4xl mx-auto">
            <button
              className="text-gray-500 hover:text-blue-600 transition-colors active:scale-95 transform p-2"
              title="Capture card"
            >
              <Camera className="w-6 h-6" />
            </button>
            <button
              onClick={() => {
                console.log('🔴 [CHAT PAGE] MIC BUTTON CLICKED!');
                startRecording();
              }}
              className="text-gray-500 hover:text-blue-600 transition-colors active:scale-95 transform p-2"
              title="Record voice note"
            >
              <Mic className="w-6 h-6" />
            </button>

            <input
              type="text"
              placeholder="Type a message..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            />

            <button
              className={`px-4 py-2 rounded-full transition-all duration-200 transform active:scale-95 ${
                input.trim()
                  ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-md hover:shadow-lg'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
              onClick={handleSend}
              disabled={!input.trim()}
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        )}
      </div>

      <BottomNav />
    </div>
  );
}
