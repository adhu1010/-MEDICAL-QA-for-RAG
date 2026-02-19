import React, { useState, useEffect, useCallback, useRef } from 'react';
import { initializeApp } from 'firebase/app';
import {
  getAuth, signInAnonymously, signInWithCustomToken, onAuthStateChanged
} from 'firebase/auth';
import {
  getFirestore, collection, doc, query, orderBy, onSnapshot,
  addDoc, serverTimestamp, updateDoc
} from 'firebase/firestore';
import { Menu, MessageSquare, Plus, Send, Loader, AlertCircle, TrendingUp, Cpu, Heart } from 'lucide-react';
import { apiClient } from './src/api';

// --- Configuration Variables (Sourced from Sandbox Globals) ---
const firebaseConfig = typeof __firebase_config !== 'undefined'
  ? JSON.parse(__firebase_config) : {};
const initialAuthToken = typeof __initial_auth_token !== 'undefined'
  ? __initial_auth_token : null;
const appId = typeof __app_id !== 'undefined' ? __app_id : 'default-rag-app';

// FIX 1: Sanitize the appId to ensure it is treated as a single, valid document ID, 
// preventing Firebase from interpreting internal slashes as path separators.
const sanitizeAppId = (id) => id.replace(/[^a-zA-Z0-9_-]/g, '_');
const cleanAppId = sanitizeAppId(appId);

// Note: This app uses the local Medical RAG backend API (localhost:8000)
// The old Gemini API configuration has been removed


const App = () => {
  const [db, setDb] = useState(null);
  const [userId, setUserId] = useState(null);
  const [isAuthReady, setIsAuthReady] = useState(false);
  const [chats, setChats] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const messagesEndRef = useRef(null);

  // Scroll to the latest message
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    // 1. Initialize Firebase
    if (!firebaseConfig.apiKey && Object.keys(firebaseConfig).length === 0) {
      console.error("Firebase config is missing. Check environment globals.");
      setError("Firebase not configured. Check environment setup.");
      return;
    }

    try {
      const app = initializeApp(firebaseConfig);
      const newDb = getFirestore(app);
      const newAuth = getAuth(app);
      setDb(newDb);

      // 2. Handle Authentication
      onAuthStateChanged(newAuth, async (user) => {
        if (user) {
          setUserId(user.uid);
          setIsAuthReady(true);
        } else {
          // Attempt sign-in with custom token or anonymously
          try {
            if (initialAuthToken) {
              await signInWithCustomToken(newAuth, initialAuthToken);
            } else {
              await signInAnonymously(newAuth);
            }
          } catch (e) {
            console.error("Authentication failed:", e);
            setError("Authentication failed. Check Firebase config/rules.");
          }
        }
      });
    } catch (e) {
      console.error("Firebase initialization failed:", e);
      setError("Failed to initialize Firebase services.");
    }
  }, []);

  // 3. Firestore Listeners (Run only when DB and Auth are ready)

  // Listener for Chat History (Sidebar)
  useEffect(() => {
    if (!db || !userId || !isAuthReady) return;

    // Use cleanAppId in the collection reference path
    const chatsCollectionRef = collection(db, `artifacts/${cleanAppId}/users/${userId}/chats`);
    const q = query(chatsCollectionRef, orderBy('lastUpdatedAt', 'desc'));

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const newChats = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      }));
      setChats(newChats);

      if (!currentChatId && newChats.length > 0) {
        setCurrentChatId(newChats[0].id);
      } else if (!currentChatId && newChats.length === 0) {
        handleNewChat();
      }
    }, (e) => {
      console.error("Error fetching chats:", e);
      setError("Failed to load chat history.");
    });

    return () => unsubscribe();
  }, [db, userId, isAuthReady, currentChatId]);

  // Listener for Current Chat Messages
  useEffect(() => {
    if (!db || !userId || !currentChatId) {
      setMessages([]);
      return;
    }

    // Use cleanAppId in the collection reference path
    const messagesCollectionRef = collection(db, `artifacts/${cleanAppId}/users/${userId}/chats/${currentChatId}/messages`);
    const q = query(messagesCollectionRef, orderBy('timestamp', 'asc'));

    const unsubscribe = onSnapshot(q, (snapshot) => {
      console.log('[Firebase] Message snapshot received, doc count:', snapshot.docs.length);
      const newMessages = snapshot.docs.map(doc => {
        const data = doc.data();
        console.log('[Firebase] Processing message:', { id: doc.id, role: data.role, textPreview: data.text?.substring(0, 50) });
        let parsedText = data.text;
        let metadata = null;
        if (data.role === 'model' && typeof data.text === 'string' && data.text.startsWith('{')) {
          try {
            const json = JSON.parse(data.text);
            parsedText = json.text;
            metadata = json;
            console.log('[Firebase] Parsed model response metadata:', metadata);
          } catch (e) {
            console.warn("Failed to parse JSON response, treating as plain text.");
          }
        }

        return {
          id: doc.id,
          text: parsedText,
          metadata: metadata,
          role: data.role,
          timestamp: data.timestamp?.toDate()
        };
      });
      console.log('[Firebase] Setting', newMessages.length, 'messages to state');
      setMessages(newMessages);
      scrollToBottom();
    }, (e) => {
      console.error("Error fetching messages:", e);
      setError("Failed to load messages for this chat.");
    });

    return () => unsubscribe();
  }, [db, userId, currentChatId]);

  // 4. Core Chat Functions

  const handleNewChat = useCallback(async () => {
    if (!db || !userId) return;
    setIsSidebarOpen(false);

    // Use cleanAppId in the collection reference path
    const chatsCollectionRef = collection(db, `artifacts/${cleanAppId}/users/${userId}/chats`);
    const newChatData = {
      title: "New Chat",
      createdAt: serverTimestamp(),
      lastUpdatedAt: serverTimestamp(),
    };

    try {
      const docRef = await addDoc(chatsCollectionRef, newChatData);
      setCurrentChatId(docRef.id);
    } catch (e) {
      console.error("Error creating new chat:", e);
      setError("Could not start a new chat session.");
    }
  }, [db, userId]);

  // Call the Medical RAG Backend API
  const callBackendApi = async (query) => {
    try {
      console.log('[Backend API] Calling backend with query:', query);
      const response = await apiClient.askQuestion(query, 'auto');
      console.log('[Backend API] Response received:', response);

      // Extract the retrieved mode from the backend response
      const persona = response.metadata?.detected_mode === 'patient'
        ? 'Patient/General'
        : 'Doctor/Clinical';

      // Format structured response matching the UI expectations
      const structuredResponse = {
        text: response.answer,
        confidence: Math.round(response.confidence * 100),
        persona: persona,
        mode: response.metadata?.retrieval_strategy || 'Unknown',
        citation: response.sources?.map(s => `${s.title}: ${(s.content || "").substring(0, 100)}...`).join('\n') || 'No sources found',
        safety_validated: response.safety_validated,
        entities: response.metadata?.entities_found || 0,
        evidence_count: response.metadata?.evidence_count || 0,
      };

      console.log('[Backend API] Formatted response:', structuredResponse);
      return JSON.stringify(structuredResponse);
    } catch (error) {
      console.error('[Backend API] ERROR - Failed to call backend:', error);
      return JSON.stringify({
        text: `Error: Unable to reach the backend API. Make sure the backend is running on ${apiClient.baseURL}. Error: ${error.message}`,
        confidence: 0,
        persona: 'System',
        mode: 'Error',
        citation: 'Error',
        safety_validated: false,
      });
    }
  };


  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || !db || !userId || isSending) return;

    const userMessage = input.trim();
    setInput('');
    setIsSending(true);
    setError(null);

    let chatID = currentChatId;

    if (!currentChatId || messages.length === 0) {
      const chatsCollectionRef = collection(db, `artifacts/${cleanAppId}/users/${userId}/chats`);
      const initialTitle = userMessage.substring(0, 30) + '...';
      const newChatData = {
        title: initialTitle,
        createdAt: serverTimestamp(),
        lastUpdatedAt: serverTimestamp(),
      };
      const docRef = await addDoc(chatsCollectionRef, newChatData);
      chatID = docRef.id;
      setCurrentChatId(chatID);
      setChats(prev => [{ id: chatID, title: initialTitle, createdAt: new Date(), lastUpdatedAt: new Date() }, ...prev]);
    }

    const messagesCollectionRef = collection(db, `artifacts/${cleanAppId}/users/${userId}/chats/${chatID}/messages`);

    try {
      // 1. Save User Message
      console.log('[Firebase] Saving user message:', userMessage);
      await addDoc(messagesCollectionRef, {
        text: userMessage,
        role: 'user',
        timestamp: serverTimestamp(),
      });
      console.log('[Firebase] User message saved successfully');

      // 2. Call the Medical RAG Backend API (Returns structured JSON string)
      console.log('[Backend] Calling backend API...');
      const modelResponseJSON = await callBackendApi(userMessage);
      console.log('[Backend] Got response, saving to Firebase...');

      // 3. Save Model Response (Saving the JSON string)
      await addDoc(messagesCollectionRef, {
        text: modelResponseJSON,
        role: 'model',
        timestamp: serverTimestamp(),
      });
      console.log('[Firebase] Model response saved successfully');

      // 4. Update Chat Metadata
      await updateDoc(doc(db, `artifacts/${cleanAppId}/users/${userId}/chats`, chatID), {
        lastUpdatedAt: serverTimestamp(),
      });
      console.log('[Firebase] Chat metadata updated');

    } catch (e) {
      console.error('[ERROR] Error during chat processing:', e);
      console.error('[ERROR] Error details:', e.message, e.code);
      setError("An error occurred while fetching the model response.");
    } finally {
      setIsSending(false);
    }
  };

  const ChatHistoryItem = ({ chat }) => (
    <div
      onClick={() => {
        setCurrentChatId(chat.id);
        setIsSidebarOpen(false);
      }}
      className={`p-3 rounded-xl cursor-pointer transition-colors flex items-center space-x-3 text-sm font-medium 
        ${currentChatId === chat.id ? 'bg-indigo-600 text-white shadow-lg' : 'hover:bg-gray-100 text-gray-700'}`}
    >
      <MessageSquare className="w-4 h-4" />
      <span className="truncate">{chat.title || "Untitled Chat"}</span>
    </div>
  );

  const Message = ({ message }) => {
    const isModel = message.role === 'model';
    const textContent = message.text || "Loading...";
    const metadata = message.metadata;

    // Style helper for confidence
    const getConfidenceColor = (conf) => {
      if (conf >= 90) return 'text-green-600 bg-green-100';
      if (conf >= 70) return 'text-yellow-600 bg-yellow-100';
      return 'text-red-600 bg-red-100';
    };

    return (
      <div className={`flex w-full ${isModel ? 'justify-start' : 'justify-end'}`}>
        <div className={`max-w-4xl p-4 rounded-xl shadow-md ${isModel ? 'rounded-tl-none border border-gray-200 bg-white' : 'bg-indigo-500 text-white rounded-br-none'}`}>

          {isModel && metadata && (
            <div className={`mb-3 p-3 rounded-lg border border-indigo-200 bg-indigo-50/50 text-xs font-medium text-gray-700 space-y-2`}>
              <div className="flex justify-between items-center pb-2 border-b border-indigo-200">
                <span className="flex items-center text-indigo-700">
                  <Cpu className="w-4 h-4 mr-1" /> ✨ Agent Decision Summary
                </span>
                <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${getConfidenceColor(metadata.confidence)}`}>
                  Confidence: {metadata.confidence}%
                </span>
              </div>
              <div className="flex justify-between flex-wrap text-xs">
                <p className="flex items-center">
                  <Heart className="w-3 h-3 mr-1 text-red-500" /> Persona:
                  <span className="font-semibold ml-1">{metadata.persona}</span>
                </p>
                <p className="flex items-center">
                  <TrendingUp className="w-3 h-3 mr-1 text-blue-500" /> Retrieval Mode:
                  <span className="font-semibold ml-1">{metadata.mode}</span>
                </p>
              </div>
            </div>
          )}

          <div className={`whitespace-pre-wrap ${isModel ? 'text-gray-800' : 'text-white'}`}>
            {textContent}
          </div>

          <div className="text-xs mt-3 opacity-70">
            {message.timestamp ? message.timestamp.toLocaleTimeString() : '...'}
          </div>

          {isModel && metadata?.citation && (
            <div className="text-xs mt-3 pt-3 border-t border-gray-300 text-gray-500 italic whitespace-pre-wrap">
              **Source Citation (RAG Evidence):** {metadata.citation}
            </div>
          )}
        </div>
      </div>
    );
  };

  if (!isAuthReady) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <Loader className="w-8 h-8 animate-spin text-indigo-500 mr-3" />
        <p className="text-lg text-gray-600">Initializing Authentication...</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen w-full bg-white font-sans text-gray-800">

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'} 
                      lg:relative lg:translate-x-0 transition-transform duration-300 ease-in-out z-20 
                      w-64 bg-gray-50 border-r border-gray-200 flex flex-col`}>
        <div className="p-4 text-xl font-bold flex items-center justify-between text-indigo-700">
          <span className="flex items-center">
            <AlertCircle className="w-6 h-6 mr-2 text-red-500" />
            BioGPT RAG QA
          </span>
          <button onClick={() => setIsSidebarOpen(false)} className="lg:hidden p-2 text-gray-600 hover:text-gray-900 rounded-full">
            <Menu className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 border-b border-gray-200">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center px-4 py-2 bg-indigo-500 text-white rounded-xl shadow-lg hover:bg-indigo-600 transition-colors"
          >
            <Plus className="w-5 h-5 mr-2" /> New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          <h2 className="text-xs font-semibold uppercase text-gray-500 mb-2">Chat History ({chats.length})</h2>
          {chats.map(chat => <ChatHistoryItem key={chat.id} chat={chat} />)}
          {chats.length === 0 && <p className="text-sm text-gray-500">No chats yet. Start one above!</p>}
        </div>

        <div className="p-4 text-xs text-gray-500 border-t border-gray-200 truncate">
          <p>User ID: {userId}</p>
          <p>App ID: {appId}</p>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header (Mobile menu button) */}
        <div className="lg:hidden p-4 border-b border-gray-200 flex items-center">
          <button onClick={() => setIsSidebarOpen(true)} className="p-2 mr-3 text-gray-600 hover:bg-gray-100 rounded-full">
            <Menu className="w-6 h-6" />
          </button>
          <h1 className="text-lg font-semibold truncate">{chats.find(c => c.id === currentChatId)?.title || "Welcome to BioGPT RAG"}</h1>
        </div>

        {/* Message Display Area */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-8 space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center py-20">
              <MessageSquare className="w-12 h-12 text-indigo-400 mb-4" />
              <h2 className="text-2xl font-semibold text-gray-600 mb-2">Ask BioGPT about Medical QA</h2>

              {/* FIX 2: Moved <ul> outside of <p> to fix DOM nesting error */}
              <p className="text-gray-500 max-w-md mb-2">
                This **Agentic Multi-Modal RAG** system dynamically selects the best retrieval mode (KG, Hybrid, Dense) before generating an answer.
                <br />Try asking:
              </p>
              <ul className="list-disc list-inside text-left mx-auto inline-block text-gray-500">
                <li>"What is the mechanism of aspirin?" (Triggers KG)</li>
                <li>"Tell me the side effects of aspirin simply." (Triggers Hybrid + Patient Persona)</li>
                <li>"Explain chronic inflammation." (Triggers Dense)</li>
                <li>"What is the dosage for me?" (Triggers Safety Override)</li>
              </ul>
            </div>
          )}

          {messages.map((msg) => (
            <Message key={msg.id} message={msg} />
          ))}

          <div ref={messagesEndRef} />
        </div>

        {/* Input/Footer Area */}
        <div className="p-4 sm:p-6 border-t border-gray-200 bg-white">
          {error && (
            <div className="bg-red-100 text-red-700 p-3 rounded-xl mb-4 flex items-center">
              <AlertCircle className="w-5 h-5 mr-2" />
              {error}
            </div>
          )}

          <form onSubmit={handleSendMessage} className="flex items-center space-x-3 max-w-5xl mx-auto">
            <div className="flex-1 relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage(e);
                  }
                }}
                disabled={isSending || !currentChatId}
                rows={1}
                placeholder={currentChatId ? "Ask your medical question..." : "Please start a new chat first."}
                className="w-full resize-none p-3 pr-10 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-shadow disabled:bg-gray-50"
              />
              {isSending && (
                <Loader className="w-5 h-5 animate-spin text-indigo-500 absolute right-3 top-3" />
              )}
            </div>

            <button
              type="submit"
              disabled={!input.trim() || isSending || !currentChatId}
              className="p-3 bg-indigo-500 text-white rounded-xl shadow-md hover:bg-indigo-600 transition-colors disabled:bg-indigo-300"
            >
              <Send className="w-6 h-6" />
            </button>
          </form>
        </div>
      </div>

      {/* Sidebar Overlay for Mobile */}
      {isSidebarOpen && (
        <div
          onClick={() => setIsSidebarOpen(false)}
          className="fixed inset-0 bg-black opacity-50 z-10 lg:hidden"
        />
      )}
    </div>
  );
};

export default App;