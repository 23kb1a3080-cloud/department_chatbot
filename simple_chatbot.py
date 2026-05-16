"""
NBKR Institute AI Chatbot - Enhanced with NLP
Uses spaCy for natural language understanding and semantic similarity matching.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List, Dict, Tuple
import json
import uvicorn
import os
import re
from difflib import SequenceMatcher

app = FastAPI(title="NBKR Institute AI Chatbot", version="2.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
chat_history: List[Dict] = []
active_connections: List[WebSocket] = []

# Load timetable data for table formatting
timetable_data = None
try:
    with open('aids_timetable_data.json', 'r', encoding='utf-8') as f:
        timetable_data = json.load(f)
        print("✓ Loaded timetable data for table formatting")
except:
    print("⚠ Timetable data not available for table formatting")

# NLP Components
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    USE_NLP = True
    print("✓ spaCy NLP model loaded successfully")
except:
    USE_NLP = False
    print("⚠ spaCy not available, using fallback matching")

def load_knowledge_base():
    """Load knowledge base from scraped data."""
    kb = {
        # Default knowledge base
        "admission": "Admissions are open from June to August. Visit the admission office or our website for more details.",
        "fees": "The fee structure varies by program. Please contact the accounts department for detailed information.",
        "courses": "We offer undergraduate and postgraduate programs in Engineering, Arts, Science, and Commerce.",
        "library": "The library is open from 8 AM to 8 PM on weekdays and 9 AM to 5 PM on weekends.",
        "hostel": "Hostel facilities are available for both boys and girls. Contact the hostel office for booking.",
        "exam": "Exam schedules are published on the notice board and website one month in advance.",
        "faculty": "Our faculty members are highly qualified with PhDs and industry experience.",
        "placement": "We have a dedicated placement cell with 85% placement record in top companies.",
        
        # NBKR Institute specific data
        "nbkr": "NBKR Institute of Science & Technology offers online attendance system, e-journals, assessment tools, timetables, and exam duties management through their intranet services.",
        "attendance": "NBKR Institute has an Online Attendance System. Faculty can enter attendance through the attendance entry portal. Students can check their attendance records online.",
        "intranet": "NBKR Institute provides comprehensive intranet services including: Online Attendance System, E-Journals publishing and reading, Assessment tools, Timetables, Website management, and Exam Duties scheduling.",
        "ejournal": "You can now publish and read E-Journals on NBKR's intranet server. Access the E-Journal link from the main menu of the intranet portal.",
        "e-journal": "You can now publish and read E-Journals on NBKR's intranet server. Access the E-Journal link from the main menu of the intranet portal.",
        "journal": "NBKR Institute provides E-Journal services where you can publish and read academic journals on the intranet server.",
        "assessment": "NBKR Institute provides online assessment tools through their intranet services for faculty and students.",
        "timetable": "Timetables are available on the NBKR Institute intranet portal. Faculty and students can access their schedules online.",
        "duties": "Exam duties and schedules are managed through the NBKR Institute intranet system.",
        "online": "NBKR Institute offers various online services including attendance entry, e-journals, assessments, and timetable management through their intranet portal.",
        "portal": "The NBKR Institute intranet portal provides access to attendance, e-journals, assessments, timetables, and exam duties.",
        "login": "To access NBKR Institute services, you need to login with your username and password through the attendance entry system.",
    }
    
    # Try to load scraped knowledge base
    if os.path.exists('nbkr_knowledge_base.json'):
        try:
            with open('nbkr_knowledge_base.json', 'r', encoding='utf-8') as f:
                scraped_kb = json.load(f)
                kb.update(scraped_kb)
                print(f"✓ Loaded {len(scraped_kb)} entries from scraped knowledge base")
        except Exception as e:
            print(f"⚠ Could not load scraped knowledge base: {e}")
    
    # Load faculty knowledge base
    if os.path.exists('aids_faculty_kb.json'):
        try:
            with open('aids_faculty_kb.json', 'r', encoding='utf-8') as f:
                faculty_kb = json.load(f)
                kb.update(faculty_kb)
                print(f"✓ Loaded {len(faculty_kb)} entries from faculty knowledge base")
        except Exception as e:
            print(f"⚠ Could not load faculty knowledge base: {e}")
    
    # Load timetable knowledge base
    if os.path.exists('aids_timetable_kb.json'):
        try:
            with open('aids_timetable_kb.json', 'r', encoding='utf-8') as f:
                timetable_kb = json.load(f)
                kb.update(timetable_kb)
                print(f"✓ Loaded {len(timetable_kb)} entries from timetable knowledge base")
        except Exception as e:
            print(f"⚠ Could not load timetable knowledge base: {e}")
    
    return kb

knowledge_base = load_knowledge_base()

def preprocess_text(text: str) -> str:
    """Preprocess text for better matching."""
    # Convert to lowercase
    text = text.lower()
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Remove special characters but keep spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    return text

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts."""
    if USE_NLP:
        try:
            doc1 = nlp(text1)
            doc2 = nlp(text2)
            return doc1.similarity(doc2)
        except:
            pass
    
    # Fallback to sequence matcher
    return SequenceMatcher(None, text1, text2).ratio()

def extract_keywords(text: str) -> List[str]:
    """Extract important keywords from text."""
    if USE_NLP:
        try:
            doc = nlp(text)
            # Extract nouns, proper nouns, and important verbs
            keywords = [token.lemma_.lower() for token in doc 
                       if token.pos_ in ['NOUN', 'PROPN', 'VERB'] and not token.is_stop]
            return keywords
        except:
            pass
    
    # Fallback: split and filter common words
    stop_words = {'the', 'is', 'are', 'was', 'were', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
    words = preprocess_text(text).split()
    return [w for w in words if w not in stop_words and len(w) > 2]

def find_best_match(user_message: str, knowledge_base: Dict[str, str], threshold: float = 0.3) -> Tuple[str, float]:
    """Find the best matching response from knowledge base using NLP."""
    user_keywords = extract_keywords(user_message)
    user_processed = preprocess_text(user_message)
    
    best_match = None
    best_score = 0.0
    
    for keyword, response in knowledge_base.items():
        if not response or response.strip() == "":
            continue
            
        # Direct keyword match (highest priority)
        if keyword in user_processed:
            score = 1.0
        else:
            # Calculate similarity score
            keyword_processed = preprocess_text(keyword)
            
            # Check if any user keyword matches the KB keyword
            keyword_match = any(uk in keyword_processed or keyword_processed in uk for uk in user_keywords)
            
            if keyword_match:
                score = 0.8
            else:
                # Use semantic similarity
                score = calculate_similarity(user_processed, keyword_processed)
        
        if score > best_score and score >= threshold:
            best_score = score
            best_match = response
    
    return best_match, best_score

def detect_intent(user_message: str) -> str:
    """Detect user intent from message."""
    message_lower = user_message.lower()
    
    # Greeting intent
    if any(word in message_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
        return "greeting"
    
    # Gratitude intent
    if any(word in message_lower for word in ["thank", "thanks", "appreciate"]):
        return "gratitude"
    
    # Help intent
    if any(word in message_lower for word in ["help", "assist", "support", "what can you"]):
        return "help"
    
    # Timetable intent - check for section timetable queries
    if any(word in message_lower for word in ["timetable", "schedule", "time table"]):
        if any(section in message_lower for section in ["section a", "section b", "section c", "section d", "sec a", "sec b", "sec c", "sec d"]):
            return "section_timetable"
    
    # Question intent
    if any(word in message_lower for word in ["who", "what", "where", "when", "why", "how", "tell me", "explain"]):
        return "question"
    
    return "general"

def format_timetable_table(section: str) -> str:
    """Format timetable as an HTML table for a specific section."""
    if not timetable_data or 'timetable' not in timetable_data:
        return None
    
    # Normalize section name
    section_key = None
    section_lower = section.lower()
    
    for key in timetable_data['timetable'].keys():
        if key.lower().replace('_', ' ') == section_lower or key.lower().replace('_', '') == section_lower.replace(' ', ''):
            section_key = key
            break
    
    if not section_key:
        return None
    
    section_data = timetable_data['timetable'][section_key]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    
    # Get all unique time slots
    all_times = set()
    for day_schedule in section_data.values():
        all_times.update(day_schedule.keys())
    
    # Sort time slots
    time_order = ["9-10", "10-11", "11-12", "9-12", "1-2", "2-3", "3-4", "1-4", "2-4", "10-12"]
    sorted_times = sorted(all_times, key=lambda x: time_order.index(x) if x in time_order else 99)
    
    # Build HTML table
    html = f"""
<div style="margin: 10px 0;">
<h3 style="color: #667eea; margin-bottom: 10px;">📅 {section_key.replace('_', ' ')} - Weekly Timetable</h3>
<table style="width: 100%; border-collapse: collapse; font-size: 12px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
<thead>
<tr style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
<th style="border: 1px solid #ddd; padding: 8px; text-align: center; font-weight: bold;">Time</th>
"""
    
    for day in days:
        html += f'<th style="border: 1px solid #ddd; padding: 8px; text-align: center; font-weight: bold;">{day}</th>'
    
    html += "</tr></thead><tbody>"
    
    # Add rows for each time slot
    for time_slot in sorted_times:
        html += f'<tr><td style="border: 1px solid #ddd; padding: 8px; text-align: center; font-weight: bold; background: #f8f9fa;">{time_slot}</td>'
        
        for day in days:
            if day in section_data and time_slot in section_data[day]:
                subject = section_data[day][time_slot]
                html += f'<td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{subject}</td>'
            else:
                html += '<td style="border: 1px solid #ddd; padding: 8px; text-align: center; color: #ccc;">-</td>'
        
        html += "</tr>"
    
    html += "</tbody></table></div>"
    
    # Add legend
    html += """
<div style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; font-size: 11px;">
<strong>📚 Subject Codes:</strong><br>
LAC = Linear Algebra & Calculus | EP = Engineering Physics | BEEE = Basic Electrical & Electronics Engineering<br>
CP LAB = Computer Programming Lab | EP-LAB = Engineering Physics Lab | EEE WS = EEE Workshop | IT WS = IT Workshop<br>
NGCS = NSS/NCC/Community Service | ENGINEERING GRAPHICS = Engineering Graphics
</div>
"""
    
    return html

def detect_section_from_query(user_message: str) -> str:
    """Extract section name from user query."""
    message_lower = user_message.lower()
    
    if "section a" in message_lower or "sec a" in message_lower or "section-a" in message_lower:
        return "Section_A"
    elif "section b" in message_lower or "sec b" in message_lower or "section-b" in message_lower:
        return "Section_B"
    elif "section c" in message_lower or "sec c" in message_lower or "section-c" in message_lower:
        return "Section_C"
    elif "section d" in message_lower or "sec d" in message_lower or "section-d" in message_lower:
        return "Section_D"
    
    return None

def get_bot_response(user_message: str) -> str:
    """Generate bot response using NLP techniques."""
    
    # Detect intent
    intent = detect_intent(user_message)
    
    # Handle specific intents
    if intent == "greeting":
        return "Hello! 👋 I'm your NBKR Institute AI assistant. I can help you with information about faculty, courses, admissions, attendance system, e-journals, and timetables. What would you like to know?"
    
    if intent == "gratitude":
        return "You're welcome! 😊 Feel free to ask if you have more questions about NBKR Institute."
    
    if intent == "help":
        return """I can help you with:
        
📚 **Academic**: Admissions, Fees, Courses, Library, Exams
👥 **Faculty**: AI & DS Department faculty information, HOD, professors
🏢 **Services**: Attendance system, E-journals, Assessments, Timetables
🎓 **Student Life**: Hostel, Placements, Campus facilities
📅 **Timetables**: AI & DS First Year timetable (Sections A, B, C, D)

Just ask me anything about NBKR Institute!"""
    
    # Handle section timetable queries
    if intent == "section_timetable":
        section = detect_section_from_query(user_message)
        if section:
            table_html = format_timetable_table(section)
            if table_html:
                return table_html
    
    # Try to find best match from knowledge base
    best_match, score = find_best_match(user_message, knowledge_base)
    
    if best_match and score > 0.3:
        return best_match
    
    # If no good match found, provide helpful fallback
    keywords = extract_keywords(user_message)
    if keywords:
        return f"I understand you're asking about {', '.join(keywords[:3])}. Could you please rephrase your question? You can ask me about faculty members, courses, admissions, attendance system, e-journals, assessments, or timetables (e.g., 'Show me Section A timetable')."
    
    return "I'm here to help with NBKR Institute information! You can ask me about faculty, courses, admissions, attendance, e-journals, assessments, timetables, or any other services. What would you like to know?"

@app.get("/")
async def get_home():
    """Serve the chat interface."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NBKR Institute AI Chatbot</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            .chat-container {
                width: 90%;
                max-width: 800px;
                height: 90vh;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            .chat-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                text-align: center;
            }
            .chat-header h1 {
                font-size: 24px;
                margin-bottom: 5px;
            }
            .chat-header p {
                font-size: 14px;
                opacity: 0.9;
            }
            .nlp-badge {
                display: inline-block;
                background: rgba(255,255,255,0.2);
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 11px;
                margin-top: 5px;
            }
            .chat-messages {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                background: #f5f5f5;
            }
            .message {
                margin-bottom: 15px;
                display: flex;
                animation: fadeIn 0.3s;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .message.user {
                justify-content: flex-end;
            }
            .message-content {
                max-width: 70%;
                padding: 12px 16px;
                border-radius: 18px;
                word-wrap: break-word;
                white-space: pre-line;
            }
            .message.bot .message-content {
                background: white;
                color: #333;
                border-bottom-left-radius: 4px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .message.user .message-content {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-bottom-right-radius: 4px;
            }
            .chat-input-container {
                padding: 20px;
                background: white;
                border-top: 1px solid #e0e0e0;
                display: flex;
                gap: 10px;
            }
            .chat-input {
                flex: 1;
                padding: 12px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 25px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.3s;
            }
            .chat-input:focus {
                border-color: #667eea;
            }
            .send-button {
                padding: 12px 24px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 25px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: transform 0.2s;
            }
            .send-button:hover {
                transform: scale(1.05);
            }
            .send-button:active {
                transform: scale(0.95);
            }
            .status {
                padding: 10px 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
                background: #f9f9f9;
            }
            .status.connected {
                color: #4caf50;
            }
            .status.disconnected {
                color: #f44336;
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div class="chat-header">
                <h1>🎓 NBKR Institute AI Chatbot</h1>
                <p>Enhanced with Natural Language Processing</p>
                <span class="nlp-badge">🧠 NLP Powered</span>
            </div>
            <div class="status" id="status">Connecting...</div>
            <div class="chat-messages" id="messages">
                <div class="message bot">
                    <div class="message-content">
                        Hello! 👋 I'm your NBKR Institute AI assistant powered by Natural Language Processing. I can understand your questions better and provide accurate information about:

📚 Faculty & Departments
🎓 Admissions & Courses  
💻 Online Services (Attendance, E-journals)
📊 Assessments & Timetables
🏢 Campus Facilities
📅 AI & DS First Year Timetable (All Sections)

Try asking me anything!
                    </div>
                </div>
            </div>
            <div class="chat-input-container">
                <input type="text" class="chat-input" id="messageInput" placeholder="Ask me anything about NBKR Institute..." />
                <button class="send-button" onclick="sendMessage()">Send</button>
            </div>
        </div>

        <script>
            let ws;
            const messagesDiv = document.getElementById('messages');
            const messageInput = document.getElementById('messageInput');
            const statusDiv = document.getElementById('status');

            function connect() {
                ws = new WebSocket('ws://localhost:8000/ws');
                
                ws.onopen = () => {
                    statusDiv.textContent = '● Connected';
                    statusDiv.className = 'status connected';
                };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    addMessage(data.message, 'bot');
                };
                
                ws.onclose = () => {
                    statusDiv.textContent = '● Disconnected';
                    statusDiv.className = 'status disconnected';
                    setTimeout(connect, 3000);
                };
                
                ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                };
            }

            function addMessage(text, sender) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}`;
                
                if (sender === 'bot' && text.includes('<table')) {
                    // Render HTML for tables
                    messageDiv.innerHTML = `<div class="message-content" style="max-width: 95%;">${text}</div>`;
                } else {
                    // Escape HTML for regular text
                    const escapedText = text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
                    messageDiv.innerHTML = `<div class="message-content">${escapedText}</div>`;
                }
                
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }

            function sendMessage() {
                const message = messageInput.value.trim();
                if (message && ws.readyState === WebSocket.OPEN) {
                    addMessage(message, 'user');
                    ws.send(JSON.stringify({ message: message }));
                    messageInput.value = '';
                }
            }

            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            connect();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for real-time chat."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("message", "")
            
            # Store in history
            chat_history.append({
                "timestamp": datetime.now().isoformat(),
                "user": user_message,
                "bot": None
            })
            
            # Generate bot response using NLP
            bot_response = get_bot_response(user_message)
            
            # Update history
            chat_history[-1]["bot"] = bot_response
            
            # Send response back to client
            await websocket.send_json({
                "message": bot_response,
                "timestamp": datetime.now().isoformat()
            })
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "NBKR Institute AI Chatbot",
        "version": "2.0.0",
        "nlp_enabled": USE_NLP,
        "active_connections": len(active_connections),
        "total_messages": len(chat_history),
        "knowledge_base_size": len(knowledge_base)
    }

@app.get("/api/history")
async def get_history():
    """Get chat history."""
    return {
        "history": chat_history[-50:],
        "total": len(chat_history)
    }

if __name__ == "__main__":
    print("=" * 70)
    print("🎓 NBKR Institute AI Chatbot v2.0 - NLP Enhanced")
    print("=" * 70)
    print(f"\n🧠 NLP Status: {'✓ Enabled (spaCy)' if USE_NLP else '⚠ Fallback mode'}")
    print(f"📚 Knowledge Base: {len(knowledge_base)} entries loaded")
    print("\n📍 Access the chatbot at: http://localhost:8000")
    print("📊 Health check at: http://localhost:8000/health")
    print("📜 Chat history at: http://localhost:8000/api/history")
    print("\n💡 Features:")
    print("   • Intent detection (greetings, questions, help)")
    print("   • Keyword extraction and matching")
    print("   • Semantic similarity scoring")
    print("   • Context-aware responses")
    print("\n Press Ctrl+C to stop the server\n")
    print("=" * 70)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
