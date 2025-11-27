'use client';

import { useState, useRef } from 'react';
import toast from 'react-hot-toast';
import { Camera, Mic, Send, StopCircle } from 'lucide-react';

interface ChatInputProps {
  leadId?: number;
  onSendMessage: (message: string) => Promise<void>;
  onCameraClick: () => void;
  onVoiceRecording: (audioBlob: Blob) => Promise<void>;
}

export default function ChatInput({
  leadId,
  onSendMessage,
  onCameraClick,
  onVoiceRecording,
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const handleSend = async () => {
    if (!message.trim()) return;

    await onSendMessage(message);
    setMessage('');
  };

  const startRecording = async () => {
    console.log('🎤 Mic button clicked - startRecording called');

    try {
      // Check if mediaDevices is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error('❌ MediaDevices not supported');
        toast.error('Your browser does not support audio recording');
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

        await onVoiceRecording(audioBlob);

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
    } catch (error) {
      console.error('❌ Failed to start recording:', error);
      toast.error('Microphone access denied or not available');

      // Reset state on error
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const stopRecording = () => {
    console.log('🛑 Stop button clicked');

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

  // Debug log to show current state
  console.log(`🎨 Component render - isRecording: ${isRecording}, recordingTime: ${recordingTime}`);

  return (
    <div className="bg-white border-t border-gray-200 px-4 py-3">
      {isRecording ? (
        <div className="relative flex items-center bg-gradient-to-r from-blue-50 to-blue-100 rounded-full px-6 py-3 shadow-lg">
          {/* Blue microphone icon */}
          <div className="bg-blue-500 rounded-full p-3 mr-3 shadow-md flex-shrink-0">
            <Mic className="w-5 h-5 text-white" />
          </div>

          {/* Animated waveform bars */}
          <div className="flex items-center justify-center gap-1 flex-1 h-10">
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
        <div className="flex items-center space-x-2">
          {/* Camera Button */}
          <button
            onClick={onCameraClick}
            className="p-3 text-gray-600 hover:bg-gray-100 rounded-full transition flex-shrink-0"
            title="Capture card"
          >
            <Camera className="w-5 h-5" />
          </button>

          {/* Mic Button */}
          <button
            onClick={() => {
              console.log('🔴 MIC BUTTON CLICKED!');
              startRecording();
            }}
            className="p-3 text-gray-600 hover:bg-gray-100 rounded-full transition flex-shrink-0"
            title="Record voice note"
          >
            <Mic className="w-5 h-5" />
          </button>

          {/* Text Input */}
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type a message..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500"
          />

          {/* Send Button */}
          <button
            onClick={handleSend}
            disabled={!message.trim()}
            className={`p-3 rounded-full transition flex-shrink-0 ${
              message.trim()
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            }`}
            title="Send message"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      )}
    </div>
  );
}
