"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Mic, Send, Plus, Camera, ChevronLeft, Edit2, Check, Trash2, LogOut } from "lucide-react";
import BottomNav from "@/components/BottomNav";
import { api } from "@/lib/api";
import { getEmployee, logout } from "@/lib/auth";
import type { Exhibition } from "@/lib/types";

interface Message {
  sender: "system" | "employee";
  text?: string;
  image?: string;
  voice?: boolean;
  extractedData?: any;
  timestamp: string;
  showBackSidePrompt?: boolean;
  showBackUploadButton?: boolean;
  // Voice confirmation UI
  voiceAnalysis?: {
    lead_id: number;
    transcript: string;
    summary: string;
    next_step?: string;
    segment: string;
    priority: string;
    interest_level?: string;
    confidence: number;
  };
}

export default function ChatPage() {
  const router = useRouter();
  const [employee, setEmployee] = useState<any>(null);

  const [exhibition, setExhibition] = useState<Exhibition | null>(null);
  const [exhibitions, setExhibitions] = useState<Exhibition[]>([]);
  const [showExhibitionPicker, setShowExhibitionPicker] = useState(false);

  const [messages, setMessages] = useState<Message[]>([]);

  const [input, setInput] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showUploadOptions, setShowUploadOptions] = useState(false);
  const [correctionMode, setCorrectionMode] = useState<{
    active: boolean;
    leadId: number | null;
    field: string | null;
  }>({ active: false, leadId: null, field: null });

  // Two-sided card upload state
  const [twoSidedMode, setTwoSidedMode] = useState<{
    active: boolean;
    frontImage: File | null;
    frontPreview: string | null;
    awaitingBackSide: boolean;
  }>({ active: false, frontImage: null, frontPreview: null, awaitingBackSide: false });

  // Voice recording state
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [audioChunks, setAudioChunks] = useState<Blob[]>([]);
  const [currentLeadId, setCurrentLeadId] = useState<number | null>(null);

  // Pending voice confirmation state
  const [pendingVoiceConfirmation, setPendingVoiceConfirmation] = useState<{
    lead_id: number;
    summary: string;
    next_step: string;
    segment: string;
    priority: string;
    interest_level: string;
  } | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const backImageInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const emp = getEmployee();
    setEmployee(emp);
    if (!emp) {
      router.push('/auth/login');
      return;
    }

    // Load messages from localStorage
    const savedMessages = localStorage.getItem('chatMessages');
    if (savedMessages) {
      try {
        const parsedMessages = JSON.parse(savedMessages);
        if (parsedMessages.length > 0) {
          setMessages(parsedMessages);
        } else {
          // If saved messages are empty, set default welcome message
          setMessages([
            {
              sender: "system",
              text: "Please upload visiting card to add a new lead.",
              timestamp: new Date().toISOString()
            }
          ]);
        }
      } catch (e) {
        console.error('Failed to parse saved messages:', e);
        // On error, set default welcome message
        setMessages([
          {
            sender: "system",
            text: "Please upload visiting card to add a new lead.",
            timestamp: new Date().toISOString()
          }
        ]);
      }
    } else {
      // No saved messages, set default welcome message
      setMessages([
        {
          sender: "system",
          text: "Please upload visiting card to add a new lead.",
          timestamp: new Date().toISOString()
        }
      ]);
    }

    loadExhibitions();
  }, [router]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Save messages to localStorage whenever they change
  // Only save last 50 messages to avoid quota exceeded errors
  // Don't save base64 images to save space
  useEffect(() => {
    if (messages.length > 0) {
      try {
        // Filter out image data and keep only last 50 messages
        const messagesToSave = messages.slice(-50).map(msg => ({
          ...msg,
          image: msg.image ? '[Image]' : undefined // Don't store base64 data
        }));
        localStorage.setItem('chatMessages', JSON.stringify(messagesToSave));
      } catch (e) {
        // If quota exceeded, clear old messages and try again
        console.warn('localStorage quota exceeded, clearing old messages');
        try {
          localStorage.removeItem('chatMessages');
          const recentMessages = messages.slice(-20).map(msg => ({
            ...msg,
            image: msg.image ? '[Image]' : undefined
          }));
          localStorage.setItem('chatMessages', JSON.stringify(recentMessages));
        } catch (e2) {
          console.error('Failed to save messages to localStorage:', e2);
        }
      }
    }
  }, [messages]);

  const loadExhibitions = async () => {
    try {
      const response = await api.getExhibitions();
      setExhibitions(response);

      // Set first active exhibition as default
      const activeExh = response.find((e) => e.IsActive);
      if (activeExh) {
        setExhibition(activeExh);
      }
    } catch (error) {
      console.error('Failed to load exhibitions:', error);
    }
  };

  const addMessage = (msg: Partial<Message>) => {
    setMessages(prev => [...prev, {
      ...msg,
      timestamp: new Date().toISOString()
    } as Message]);
  };

  const handleClearChat = () => {
    if (confirm('Are you sure you want to clear all chat messages?')) {
      localStorage.removeItem('chatMessages');
      setMessages([
        {
          sender: "system",
          text: "Please upload visiting card to add a new lead.",
          timestamp: new Date().toISOString()
        }
      ]);
    }
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onloadend = async () => {
      const imageData = reader.result as string;

      // Add employee message with image
      addMessage({
        sender: "employee",
        image: imageData,
        text: "Front Side of Visiting Card"
      });

      // Store front image and ask about back side
      setTwoSidedMode({
        active: true,
        frontImage: file,
        frontPreview: imageData,
        awaitingBackSide: true
      });

      // Ask if card has back side
      addMessage({
        sender: "system",
        text: "Does this card have a back side with additional information?",
        showBackSidePrompt: true
      });
    };
    reader.readAsDataURL(file);

    // Clear the input
    e.target.value = '';
  };

  // Handle back side upload
  const handleBackImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !twoSidedMode.frontImage) return;

    const reader = new FileReader();
    reader.onloadend = async () => {
      const imageData = reader.result as string;

      // Add back side image to chat
      addMessage({
        sender: "employee",
        image: imageData,
        text: "Back Side of Visiting Card"
      });

      // Now process both images
      await processCardExtraction(twoSidedMode.frontImage!, file);
    };
    reader.readAsDataURL(file);

    // Clear the input
    e.target.value = '';
  };

  // Handle "No Back Side" - process front only
  const handleNoBackSide = async () => {
    if (!twoSidedMode.frontImage) return;

    addMessage({
      sender: "employee",
      text: "No back side"
    });

    await processCardExtraction(twoSidedMode.frontImage, null);
  };

  // Handle "Yes, has back side" - show upload option
  const handleHasBackSide = () => {
    addMessage({
      sender: "employee",
      text: "Yes, uploading back side..."
    });

    addMessage({
      sender: "system",
      text: "Please upload the back side of the card:",
      showBackUploadButton: true
    });
  };

  // Process card extraction with front and optional back image
  const processCardExtraction = async (frontImage: File, backImage: File | null) => {
    setIsProcessing(true);
    setTwoSidedMode({ active: false, frontImage: null, frontPreview: null, awaitingBackSide: false });

    try {
      const result = await api.extractCard(
        frontImage,
        backImage,
        exhibition?.ExhibitionId || 1,
        employee?.employee_id || 1
      );

      if (result.extraction) {
        const isTwoSided = backImage !== null;

        // Check for duplicates
        const isDuplicate = result.duplicate_check?.is_duplicate || false;
        const duplicateCount = result.duplicate_check?.duplicate_count || 0;
        const topDuplicate = result.duplicate_check?.duplicates?.[0];

        let duplicateWarning = '';
        if (isDuplicate && topDuplicate) {
          duplicateWarning = `\n\n⚠️ DUPLICATE DETECTED!\nThis card details already exist in the system:\n• Lead ID: ${topDuplicate.lead_id}\n• ${topDuplicate.visitor_name || 'Unknown'} - ${topDuplicate.company_name || 'Unknown'}\n• Phone: ${topDuplicate.phone || 'N/A'}\n• Similarity: ${topDuplicate.similarity_score}%\n\n${duplicateCount > 1 ? `Found ${duplicateCount} similar leads in total.` : ''}`;
        }

        // Add system message with extracted data
        addMessage({
          sender: "system",
          text: `Extracted details ${isTwoSided ? '(2-sided card) ' : ''}(${(result.extraction.confidence * 100).toFixed(0)}% confidence):
Name: ${result.extraction.persons?.[0]?.name || 'N/A'}
Company: ${result.extraction.company_name || 'N/A'}
Phone: ${result.extraction.phones?.[0] || 'N/A'}
Email: ${result.extraction.emails?.[0] || 'N/A'}
${result.extraction.services?.length ? `Services: ${result.extraction.services.join(', ')}` : ''}${duplicateWarning}`,
          extractedData: {
            ...result.extraction,
            lead_id: result.lead_id,
            is_duplicate: isDuplicate,
            duplicate_info: topDuplicate
          }
        });
      } else {
        addMessage({
          sender: "system",
          text: "❌ Failed to extract card details. Please try again."
        });
      }

    } catch (error) {
      console.error('Extraction failed:', error);
      addMessage({
        sender: "system",
        text: "❌ Failed to extract card details. Please try again."
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSaveLead = async () => {
    // Get the lead ID from the last extracted message
    const lastExtractedMsg = messages.slice().reverse().find(m => m.extractedData?.lead_id);
    const leadId = lastExtractedMsg?.extractedData?.lead_id;

    if (!leadId) {
      addMessage({
        sender: "system",
        text: "⚠️ Error: Could not find lead ID. Please try scanning again."
      });
      return;
    }

    addMessage({
      sender: "employee",
      text: "✅ Confirmed - All details are correct"
    });

    addMessage({
      sender: "system",
      text: "💾 Lead saved successfully!\n⏳ Sending WhatsApp greeting to visitor..."
    });

    try {
      // Send greeting after employee confirms all details are correct
      const result = await api.sendGreetingAfterVerification(leadId);

      addMessage({
        sender: "system",
        text: `✅ WhatsApp greeting sent to visitor!\n\n${result.message}\n\nYou can now:\n• Record a voice note about the discussion\n• Upload another visiting card\n• View lead details in the Leads tab`
      });
    } catch (error: any) {
      console.error('Failed to send greeting:', error);
      addMessage({
        sender: "system",
        text: `⚠️ Lead saved successfully, but failed to send WhatsApp greeting.\n\nError: ${error.response?.data?.detail || error.message}\n\nYou can manually send the greeting from the Leads tab.`
      });
    }
  };

  const handleCorrectionRequest = (leadId: number) => {
    addMessage({
      sender: "employee",
      text: "✏️ Need Correction"
    });

    addMessage({
      sender: "system",
      text: "Which field is incorrect?\nPlease select:",
      extractedData: {
        _correction_menu: true,
        lead_id: leadId
      }
    });
  };

  const handleFieldCorrection = (leadId: number, field: string) => {
    setCorrectionMode({ active: true, leadId, field });

    addMessage({
      sender: "employee",
      text: `Correcting: ${field}`
    });

    const fieldPrompts: Record<string, string> = {
      'Name': 'Enter the correct name:',
      'Company': 'Enter the correct company name:',
      'Phone': 'Enter the correct phone number:',
      'Email': 'Enter the correct email address:',
      'Designation': 'Enter the correct designation:',
      'Address': 'Enter the correct address:',
      'Other': 'Please describe what needs to be corrected:'
    };

    addMessage({
      sender: "system",
      text: fieldPrompts[field] || 'Enter correction:'
    });
  };

  const handleCorrectionSubmit = async (correctionText: string) => {
    if (!correctionMode.active || !correctionMode.leadId || !correctionMode.field) return;

    // First add the employee message with the correction
    addMessage({
      sender: "employee",
      text: correctionText
    });

    try {
      // Map field names to API field names
      const fieldMap: Record<string, string> = {
        'Name': 'primary_visitor_name',
        'Company': 'company_name',
        'Phone': 'primary_visitor_phone',
        'Email': 'primary_visitor_email',
        'Designation': 'primary_visitor_designation',
        'Address': 'address',
      };

      const apiField = fieldMap[correctionMode.field];

      if (apiField) {
        // Update the lead with corrected field
        await api.updateLead(correctionMode.leadId, {
          [apiField]: correctionText
        });

        addMessage({
          sender: "system",
          text: `✅ ${correctionMode.field} updated successfully!\n\nYou can now:\n• Correct another field\n• Save the lead\n• Upload a new card`
        });
      }

      setCorrectionMode({ active: false, leadId: null, field: null });
    } catch (error) {
      console.error('Failed to update field:', error);
      addMessage({
        sender: "system",
        text: "❌ Failed to update. Please try again."
      });
    }
  };

  const handleSend = () => {
    if (!input.trim()) return;

    // If in correction mode, handle the correction
    if (correctionMode.active) {
      handleCorrectionSubmit(input);
      setInput("");
      return;
    }

    addMessage({
      sender: "employee",
      text: input
    });

    // Simple AI response simulation
    setTimeout(() => {
      addMessage({
        sender: "system",
        text: "Message received. You can continue uploading cards or recording voice notes."
      });
    }, 500);

    setInput("");
  };

  const handleMicToggle = async () => {
    if (!isRecording) {
      // Check if we have a current lead to attach voice note to
      // Get the last lead_id from messages
      const lastLeadMessage = [...messages].reverse().find(m => m.extractedData?.lead_id);
      const leadId = lastLeadMessage?.extractedData?.lead_id;

      if (!leadId) {
        addMessage({
          sender: "system",
          text: "⚠️ Please upload a visiting card first before recording a voice note."
        });
        return;
      }

      setCurrentLeadId(leadId);

      try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        const chunks: Blob[] = [];

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) {
            chunks.push(e.data);
          }
        };

        recorder.onstop = async () => {
          // Stop all tracks
          stream.getTracks().forEach(track => track.stop());

          const audioBlob = new Blob(chunks, { type: 'audio/webm' });
          setAudioChunks([]);

          addMessage({
            sender: "system",
            text: "🎤 Processing voice note..."
          });

          setIsProcessing(true);

          try {
            // Send to backend for transcription and analysis
            const result = await api.extractVoice(audioBlob, leadId, employee?.employee_id || 1);

            if (result.success && result.requires_confirmation) {
              // Show confirmation UI with extracted analysis
              addMessage({
                sender: "system",
                text: `📝 Voice Analysis (${((result.confidence || 0) * 100).toFixed(0)}% confidence):\n\n` +
                      `**Transcript:** ${result.transcript}\n\n` +
                      `**Summary:** ${result.summary}\n\n` +
                      `**Segment:** ${result.segment || 'general'}\n` +
                      `**Priority:** ${result.priority || 'medium'}\n` +
                      `**Interest:** ${result.interest_level || 'warm'}\n` +
                      `**Next Step:** ${result.next_step || 'Not identified'}\n\n` +
                      `Please confirm or modify the analysis:`,
                voiceAnalysis: {
                  lead_id: result.lead_id!,
                  transcript: result.transcript || '',
                  summary: result.summary || '',
                  next_step: result.next_step,
                  segment: result.segment || 'general',
                  priority: result.priority || 'medium',
                  interest_level: result.interest_level,
                  confidence: result.confidence || 0
                }
              });

              // Store pending confirmation data
              setPendingVoiceConfirmation({
                lead_id: result.lead_id!,
                summary: result.summary || '',
                next_step: result.next_step || '',
                segment: result.segment || 'general',
                priority: result.priority || 'medium',
                interest_level: result.interest_level || 'warm'
              });
            } else {
              addMessage({
                sender: "system",
                text: result.error || "❌ Failed to process voice note."
              });
            }
          } catch (error) {
            console.error('Voice processing error:', error);
            addMessage({
              sender: "system",
              text: "❌ Failed to process voice note. Please try again."
            });
          } finally {
            setIsProcessing(false);
          }
        };

        setMediaRecorder(recorder);
        setAudioChunks([]);
        recorder.start();
        setIsRecording(true);

        addMessage({
          sender: "employee",
          voice: true,
          text: "🎤 Recording voice note..."
        });

      } catch (error) {
        console.error('Microphone access error:', error);
        addMessage({
          sender: "system",
          text: "❌ Could not access microphone. Please check permissions."
        });
      }
    } else {
      // Stop recording
      if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
      }
      setIsRecording(false);
    }
  };

  // Handle voice analysis confirmation
  const handleConfirmVoiceAnalysis = async (confirmed: boolean, modifiedData?: {
    segment?: string;
    priority?: string;
    next_step?: string;
  }) => {
    if (!pendingVoiceConfirmation) return;

    if (!confirmed) {
      // User rejected - clear pending
      setPendingVoiceConfirmation(null);
      addMessage({
        sender: "employee",
        text: "❌ Analysis rejected"
      });
      addMessage({
        sender: "system",
        text: "Voice analysis discarded. You can record another voice note or manually update the lead."
      });
      return;
    }

    // Merge any modifications
    const finalData = {
      ...pendingVoiceConfirmation,
      ...modifiedData
    };

    setIsProcessing(true);

    try {
      await api.confirmVoiceAnalysis(finalData);

      addMessage({
        sender: "employee",
        text: "✅ Confirmed"
      });

      addMessage({
        sender: "system",
        text: `✅ Voice analysis saved!\n\nSegment: ${finalData.segment}\nPriority: ${finalData.priority}\nNext Step: ${finalData.next_step || 'None'}`
      });

      setPendingVoiceConfirmation(null);
    } catch (error) {
      console.error('Confirmation error:', error);
      addMessage({
        sender: "system",
        text: "❌ Failed to save analysis. Please try again."
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle segment/priority modification
  const handleModifyVoiceAnalysis = (field: 'segment' | 'priority', value: string) => {
    if (!pendingVoiceConfirmation) return;

    setPendingVoiceConfirmation({
      ...pendingVoiceConfirmation,
      [field]: value
    });
  };

  if (!employee) {
    return null;
  }

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* HEADER */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 shadow-lg sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <ChevronLeft className="w-5 h-5 cursor-pointer" onClick={() => router.push('/dashboard')} />
              <div>
                <h1 className="font-semibold text-lg">
                  {employee.full_name || 'Employee'}
                </h1>
                <button
                  onClick={() => setShowExhibitionPicker(!showExhibitionPicker)}
                  className="text-blue-100 text-sm flex items-center gap-1 hover:text-white transition"
                >
                  {exhibition?.Name || 'Select Exhibition'}
                  <Edit2 className="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            {/* Clear chat button */}
            <button
              onClick={handleClearChat}
              className="text-blue-100 hover:text-white hover:bg-blue-600 p-2 rounded-lg transition flex items-center gap-1"
              title="Clear Chat"
            >
              <Trash2 className="w-4 h-4" />
            </button>

            {/* Logout button */}
            <button
              onClick={() => {
                if (confirm('Are you sure you want to logout?')) {
                  logout();
                }
              }}
              className="text-blue-100 hover:text-white hover:bg-blue-600 p-2 rounded-lg transition flex items-center gap-1"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>

            <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center text-xl">
              👤
            </div>
          </div>
        </div>

        {/* Exhibition Picker */}
        {showExhibitionPicker && (
          <div className="mt-3 bg-white rounded-lg shadow-lg p-2 max-h-48 overflow-y-auto">
            {exhibitions.map((exh) => (
              <button
                key={exh.ExhibitionId}
                onClick={() => {
                  setExhibition(exh);
                  setShowExhibitionPicker(false);
                }}
                className={`w-full text-left px-3 py-2 rounded hover:bg-blue-50 transition ${
                  exhibition?.ExhibitionId === exh.ExhibitionId ? 'bg-blue-100 text-blue-700' : 'text-gray-700'
                }`}
              >
                {exh.Name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* CHAT AREA */}
      <div className="flex-1 overflow-y-auto p-4 pb-32">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`mb-4 flex animate-fadeIn ${
              msg.sender === "employee" ? "justify-end" : "justify-start"
            }`}
            style={{ animationDelay: `${i * 0.05}s` }}
          >
            <div
              className={`px-4 py-3 max-w-[85%] rounded-2xl shadow-md ${
                msg.sender === "employee"
                  ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-br-none"
                  : "bg-white text-gray-900 rounded-bl-none border border-yellow-200"
              }`}
            >
              {msg.image && msg.image !== '[Image]' && (
                <img src={msg.image} alt="Card" className="rounded-lg mb-2 max-w-full max-h-48 object-contain" />
              )}
              {msg.image === '[Image]' && (
                <div className="bg-gray-100 rounded-lg p-4 mb-2 text-center text-gray-500 text-sm">
                  📷 Image (not cached)
                </div>
              )}
              {msg.text && (
                <p className="text-sm whitespace-pre-line">{msg.text}</p>
              )}
              {msg.extractedData && !msg.extractedData._correction_menu && (
                <div className="mt-3 space-y-2">
                  <button
                    onClick={() => {
                      const leadId = msg.extractedData.lead_id;
                      if (leadId) {
                        router.push(`/leads/${leadId}`);
                      }
                    }}
                    className="w-full flex items-center justify-center gap-1 bg-blue-500 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-blue-600 transition"
                  >
                    <Edit2 className="w-4 h-4" />
                    View/Edit All Details
                  </button>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleCorrectionRequest(msg.extractedData.lead_id)}
                      className="flex-1 flex items-center justify-center gap-1 bg-orange-500 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-orange-600 transition"
                    >
                      <Edit2 className="w-4 h-4" />
                      Correct Field
                    </button>
                    <button
                      onClick={handleSaveLead}
                      className="flex-1 flex items-center justify-center gap-1 bg-green-500 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-green-600 transition"
                    >
                      <Check className="w-4 h-4" />
                      All Correct ✓
                    </button>
                  </div>
                </div>
              )}
              {msg.extractedData && msg.extractedData._correction_menu && (
                <div className="mt-3 grid grid-cols-2 gap-2">
                  {['Name', 'Company', 'Phone', 'Email', 'Designation', 'Address', 'Services', 'Other'].map((field) => (
                    <button
                      key={field}
                      onClick={() => handleFieldCorrection(msg.extractedData.lead_id, field)}
                      className="px-3 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition"
                    >
                      {field}
                    </button>
                  ))}
                </div>
              )}
              {/* Two-sided card: Yes/No prompt */}
              {msg.showBackSidePrompt && twoSidedMode.awaitingBackSide && (
                <div className="mt-3 flex gap-2">
                  <button
                    onClick={handleHasBackSide}
                    className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition"
                  >
                    Yes, has back side
                  </button>
                  <button
                    onClick={handleNoBackSide}
                    className="flex-1 px-4 py-2 bg-gray-500 text-white rounded-lg text-sm font-medium hover:bg-gray-600 transition"
                  >
                    No back side
                  </button>
                </div>
              )}
              {/* Two-sided card: Back upload button */}
              {msg.showBackUploadButton && twoSidedMode.active && (
                <div className="mt-3">
                  <button
                    onClick={() => backImageInputRef.current?.click()}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium hover:bg-blue-600 transition"
                  >
                    <Camera className="w-4 h-4" />
                    Upload Back Side
                  </button>
                </div>
              )}

              {/* Voice Analysis Confirmation UI */}
              {msg.voiceAnalysis && pendingVoiceConfirmation && msg.voiceAnalysis.lead_id === pendingVoiceConfirmation.lead_id && (
                <div className="mt-4 space-y-3">
                  {/* Segment Selection */}
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Segment:</p>
                    <div className="flex flex-wrap gap-1">
                      {['decision_maker', 'influencer', 'researcher', 'general'].map((seg) => (
                        <button
                          key={seg}
                          onClick={() => handleModifyVoiceAnalysis('segment', seg)}
                          className={`px-2 py-1 text-xs rounded-full transition ${
                            pendingVoiceConfirmation.segment === seg
                              ? 'bg-indigo-600 text-white'
                              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                          }`}
                        >
                          {seg.replace('_', ' ')}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Priority Selection */}
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Priority:</p>
                    <div className="flex gap-1">
                      {['high', 'medium', 'low'].map((pri) => (
                        <button
                          key={pri}
                          onClick={() => handleModifyVoiceAnalysis('priority', pri)}
                          className={`px-3 py-1 text-xs rounded-full transition ${
                            pendingVoiceConfirmation.priority === pri
                              ? pri === 'high' ? 'bg-red-600 text-white' :
                                pri === 'medium' ? 'bg-yellow-500 text-white' :
                                'bg-green-600 text-white'
                              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                          }`}
                        >
                          {pri}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Confirm / Reject Buttons */}
                  <div className="flex gap-2 pt-2">
                    <button
                      onClick={() => handleConfirmVoiceAnalysis(true)}
                      className="flex-1 flex items-center justify-center gap-1 bg-green-500 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-green-600 transition"
                    >
                      <Check className="w-4 h-4" />
                      Confirm
                    </button>
                    <button
                      onClick={() => handleConfirmVoiceAnalysis(false)}
                      className="flex-1 flex items-center justify-center gap-1 bg-red-500 text-white px-3 py-2 rounded-lg text-sm font-medium hover:bg-red-600 transition"
                    >
                      ✕ Reject
                    </button>
                  </div>
                </div>
              )}

              <div className={`text-xs mt-1 ${msg.sender === "employee" ? "text-blue-100" : "text-gray-400"}`}>
                {new Date(msg.timestamp).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          </div>
        ))}

        {isProcessing && (
          <div className="flex justify-start mb-4">
            <div className="bg-white px-4 py-3 rounded-2xl shadow-md border border-yellow-200">
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-sm text-gray-600">Extracting card details...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={scrollRef} />
      </div>

      {/* INPUT BAR */}
      <div className="fixed bottom-16 left-0 right-0 bg-white border-t shadow-lg z-10">
        <div className="flex items-center gap-2 p-2 px-3">
          {/* Hidden file inputs */}
          <input
            type="file"
            ref={cameraInputRef}
            className="hidden"
            accept="image/*"
            capture="environment"
            onChange={handleImageUpload}
          />
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept="image/*"
            onChange={handleImageUpload}
          />
          {/* Hidden input for back side image */}
          <input
            type="file"
            ref={backImageInputRef}
            className="hidden"
            accept="image/*"
            capture="environment"
            onChange={handleBackImageUpload}
          />

          {/* Plus button with options */}
          <div className="relative flex-shrink-0">
            <button
              onClick={() => setShowUploadOptions(!showUploadOptions)}
              className="text-gray-500 hover:text-blue-600 transition-colors active:scale-95 transform p-1"
              title="Add Card"
            >
              <Plus className="w-5 h-5" />
            </button>

            {/* Upload options popup */}
            {showUploadOptions && (
              <div className="absolute bottom-full left-0 mb-2 bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden min-w-[200px]">
                <button
                  onClick={() => {
                    cameraInputRef.current?.click();
                    setShowUploadOptions(false);
                  }}
                  className="flex items-center gap-3 px-4 py-3 hover:bg-blue-50 transition-colors w-full text-left"
                >
                  <Camera className="w-5 h-5 text-blue-600 flex-shrink-0" />
                  <span className="text-sm font-medium text-gray-700">Take Photo</span>
                </button>
                <button
                  onClick={() => {
                    fileInputRef.current?.click();
                    setShowUploadOptions(false);
                  }}
                  className="flex items-center gap-3 px-4 py-3 hover:bg-blue-50 transition-colors w-full text-left border-t border-gray-100"
                >
                  <Plus className="w-5 h-5 text-blue-600 flex-shrink-0" />
                  <span className="text-sm font-medium text-gray-700">Upload from Gallery</span>
                </button>
              </div>
            )}
          </div>

          <button
            onClick={handleMicToggle}
            className={`flex-shrink-0 transition-colors active:scale-95 transform p-1 ${
              isRecording ? 'text-red-500 animate-pulse' : 'text-gray-500 hover:text-blue-600'
            }`}
            title="Voice Note"
          >
            <Mic className="w-5 h-5" />
          </button>

          <input
            type="text"
            placeholder="Type a message..."
            className="flex-1 min-w-0 px-3 py-2 border border-gray-300 rounded-full focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-200 text-sm"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />

          <button
            className={`flex-shrink-0 p-2 rounded-full transition-all duration-200 transform active:scale-95 ${
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
      </div>

      <BottomNav />
    </div>
  );
}
