# NBKR Institute AI Chatbot - NLP Enhanced Version 2.0

## 🎯 Overview
The chatbot has been upgraded with **Natural Language Processing (NLP)** capabilities using spaCy, providing intelligent understanding and better response accuracy.

## 🚀 Key Improvements

### 1. **Intent Detection**
The chatbot now understands user intent:
- **Greeting Intent**: Recognizes "hello", "hi", "hey", "good morning", etc.
- **Question Intent**: Detects "who", "what", "where", "when", "why", "how", "tell me", "explain"
- **Help Intent**: Understands requests for assistance
- **Gratitude Intent**: Recognizes "thank you", "thanks", "appreciate"

### 2. **Keyword Extraction**
- Automatically extracts important keywords from user queries
- Uses spaCy's Part-of-Speech (POS) tagging to identify nouns, proper nouns, and verbs
- Filters out stop words for better matching

### 3. **Semantic Similarity Matching**
- Uses spaCy's word vectors for semantic similarity
- Calculates similarity scores between user queries and knowledge base entries
- Fallback to sequence matching when spaCy is unavailable
- Threshold-based matching (minimum 30% similarity)

### 4. **Text Preprocessing**
- Converts text to lowercase for case-insensitive matching
- Removes extra whitespace and special characters
- Normalizes text for better comparison

### 5. **Context-Aware Responses**
- Provides relevant responses based on detected intent
- Offers helpful suggestions when no exact match is found
- Mentions extracted keywords in fallback responses

## 📚 Knowledge Base

### Total Entries: 70+
1. **NBKR Institute Services** (11 entries)
   - Online Attendance System
   - E-Journals
   - Assessments
   - Timetables
   - Exam Duties
   - Intranet Portal

2. **AI & DS Faculty** (44 entries)
   - 14 Faculty members
   - Department information
   - Specializations
   - Contact details

3. **General College Info** (15+ entries)
   - Admissions
   - Fees
   - Courses
   - Library
   - Hostel
   - Placements

## 🧠 NLP Technologies Used

### spaCy (v3.8.13)
- **Model**: en_core_web_sm (English language model)
- **Features**:
  - Tokenization
  - Part-of-Speech tagging
  - Named Entity Recognition
  - Word vectors for similarity
  - Lemmatization

### Python Libraries
- **FastAPI**: Web framework
- **WebSocket**: Real-time communication
- **spaCy**: NLP processing
- **difflib**: Fallback similarity matching

## 💡 How It Works

### Query Processing Flow:
```
User Query
    ↓
1. Intent Detection
    ↓
2. Text Preprocessing
    ↓
3. Keyword Extraction
    ↓
4. Similarity Matching
    ↓
5. Response Generation
    ↓
Bot Response
```

### Matching Algorithm:
1. **Direct Match** (Score: 1.0)
   - Exact keyword found in query
   
2. **Keyword Match** (Score: 0.8)
   - Extracted keywords match KB keywords
   
3. **Semantic Match** (Score: 0.0-1.0)
   - spaCy similarity calculation
   - Threshold: 0.3 (30%)

## 🎨 User Interface Features

- **Modern Gradient Design**: Purple gradient theme
- **Real-time Chat**: WebSocket-based instant messaging
- **NLP Badge**: Shows NLP is enabled
- **Responsive Layout**: Works on all screen sizes
- **Smooth Animations**: Fade-in effects for messages
- **Connection Status**: Shows online/offline status

## 📊 API Endpoints

### 1. Main Interface
```
GET http://localhost:8000/
```
Returns the chat interface HTML

### 2. WebSocket Connection
```
WS ws://localhost:8000/ws
```
Real-time chat communication

### 3. Health Check
```
GET http://localhost:8000/health
```
Returns:
```json
{
  "status": "healthy",
  "service": "NBKR Institute AI Chatbot",
  "version": "2.0.0",
  "nlp_enabled": true,
  "active_connections": 2,
  "total_messages": 15,
  "knowledge_base_size": 70
}
```

### 4. Chat History
```
GET http://localhost:8000/api/history
```
Returns last 50 chat messages

## 🧪 Testing the Chatbot

### Sample Queries to Try:

#### Faculty Queries:
- "Who is the HOD of AI & DS department?"
- "Tell me about Dr Narayana Rao Appini"
- "Which faculty teaches Machine Learning?"
- "Who are the professors?"
- "Tell me about Prof Nataraja Suresh Myle"

#### Services Queries:
- "How do I check my attendance?"
- "What is the e-journal system?"
- "Tell me about assessments"
- "Where can I find timetables?"
- "How to access the intranet portal?"

#### General Queries:
- "What courses are available?"
- "Tell me about admissions"
- "What are the fees?"
- "Is there a hostel?"
- "How is the placement record?"

#### Natural Language Queries:
- "I want to know about the head of department"
- "Can you help me with attendance?"
- "Who teaches AI subjects?"
- "What facilities are available?"

## 🔧 Technical Specifications

### Requirements:
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
spacy==3.7.2
websockets==12.0
python-multipart==0.0.6
```

### System Requirements:
- Python 3.8+
- 2GB RAM minimum
- Internet connection (for initial spaCy model download)

### Performance:
- Response time: < 100ms (average)
- Concurrent connections: Unlimited
- Knowledge base lookup: O(n) where n = KB size

## 🎯 Advantages Over Previous Version

| Feature | Old Version | New Version |
|---------|-------------|-------------|
| Matching | Simple keyword | NLP + Semantic similarity |
| Intent | None | 4 intent types |
| Keyword Extraction | Manual | Automatic (spaCy) |
| Similarity | Exact match only | Fuzzy + Semantic |
| Response Quality | Basic | Context-aware |
| Understanding | Limited | Natural language |

## 🚀 Future Enhancements

1. **Conversation Memory**: Remember previous messages in conversation
2. **Multi-turn Dialogue**: Handle follow-up questions
3. **Entity Recognition**: Extract names, dates, locations automatically
4. **Sentiment Analysis**: Detect user emotions
5. **Multi-language Support**: Add support for regional languages
6. **Voice Input**: Speech-to-text integration
7. **Advanced RAG**: Vector database for better retrieval
8. **Fine-tuned Model**: Custom trained model for NBKR Institute

## 📝 Usage Instructions

### Starting the Chatbot:
```bash
python simple_chatbot.py
```

### Accessing the Interface:
1. Open browser
2. Navigate to: http://localhost:8000
3. Start chatting!

### Stopping the Chatbot:
Press `Ctrl+C` in the terminal

## 🐛 Troubleshooting

### Issue: spaCy model not found
**Solution**: 
```bash
python -m spacy download en_core_web_sm
```

### Issue: Port 8000 already in use
**Solution**: 
```bash
# Kill the process using port 8000
netstat -ano | findstr :8000
taskkill /PID <process_id> /F
```

### Issue: WebSocket connection failed
**Solution**: 
- Check if chatbot is running
- Verify firewall settings
- Try refreshing the browser

## 📞 Support

For issues or questions:
1. Check the health endpoint: http://localhost:8000/health
2. Review chat history: http://localhost:8000/api/history
3. Check console logs for errors

## 🎓 Credits

- **Framework**: FastAPI
- **NLP**: spaCy
- **Data Sources**: 
  - NBKR Institute website
  - AI & DS Faculty directory
  - Manual knowledge base entries

---

**Version**: 2.0.0  
**Last Updated**: May 16, 2026  
**Status**: ✅ Production Ready
