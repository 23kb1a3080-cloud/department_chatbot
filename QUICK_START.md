# 🚀 NBKR Institute AI Chatbot - Quick Start Guide

## ✅ Current Status: RUNNING

The NLP-enhanced chatbot is **currently active** and ready to use!

---

## 🌐 Access the Chatbot

### **Main Interface:**
```
http://localhost:8000
```
👉 **Open this URL in your web browser to start chatting!**

---

## 📊 System Status

✅ **Server**: Running on port 8000  
✅ **NLP**: Enabled (spaCy loaded)  
✅ **Knowledge Base**: 70 entries loaded  
✅ **Active Connections**: Multiple users can connect  
✅ **Version**: 2.0.0 (NLP Enhanced)

---

## 🧪 Try These Sample Queries

### Faculty Questions:
```
1. "Who is the HOD of AI & DS department?"
2. "Tell me about Dr Narayana Rao Appini"
3. "Which faculty teaches Machine Learning?"
4. "Who are the professors in AI department?"
5. "Tell me about Prof Nataraja Suresh Myle"
```

### Services Questions:
```
6. "How do I check my attendance?"
7. "What is the e-journal system?"
8. "Tell me about assessments"
9. "Where can I find timetables?"
10. "How to access the intranet portal?"
```

### General Questions:
```
11. "What courses are available?"
12. "Tell me about admissions"
13. "What are the fees?"
14. "Is there a hostel?"
15. "How is the placement record?"
```

### Natural Language Questions:
```
16. "I want to know about the head of department"
17. "Can you help me with attendance?"
18. "Who teaches AI subjects?"
19. "What facilities are available?"
20. "Hello, what can you help me with?"
```

---

## 🎯 Key Features

### 🧠 NLP Powered
- Understands natural language
- Extracts keywords automatically
- Semantic similarity matching
- Intent detection

### 💬 Smart Responses
- Context-aware answers
- Helpful suggestions
- Multiple matching strategies
- Fallback responses

### 📚 Comprehensive Knowledge
- 70+ knowledge base entries
- AI & DS faculty information
- NBKR Institute services
- General college information

---

## 🔗 API Endpoints

### 1. **Chat Interface**
```
http://localhost:8000
```
Main web interface for chatting

### 2. **Health Check**
```
http://localhost:8000/health
```
Returns system status and statistics

### 3. **Chat History**
```
http://localhost:8000/api/history
```
View last 50 chat messages

### 4. **WebSocket**
```
ws://localhost:8000/ws
```
Real-time chat connection

---

## 📱 How to Use

### Step 1: Open Browser
Open any modern web browser (Chrome, Firefox, Edge, Safari)

### Step 2: Navigate to Chatbot
Go to: **http://localhost:8000**

### Step 3: Start Chatting
- Type your question in the input box
- Press Enter or click "Send"
- Get instant AI-powered responses!

---

## 🎨 User Interface

### Features:
- 🎨 Modern purple gradient design
- 💬 Real-time messaging
- 🏷️ "NLP Powered" badge
- ✨ Smooth animations
- 📱 Mobile responsive
- 🟢 Connection status indicator

---

## 🛠️ Management Commands

### Check if Running:
```bash
curl http://localhost:8000/health
```

### View Logs:
The chatbot displays logs in the terminal where it's running

### Stop the Chatbot:
Press `Ctrl+C` in the terminal (if needed)

### Restart the Chatbot:
```bash
python simple_chatbot.py
```

---

## 📊 Current Statistics

**From Health Check:**
```json
{
  "status": "healthy",
  "service": "NBKR Institute AI Chatbot",
  "version": "2.0.0",
  "nlp_enabled": true,
  "active_connections": 2,
  "total_messages": 0,
  "knowledge_base_size": 70
}
```

---

## 💡 Tips for Best Results

### 1. **Ask Natural Questions**
❌ Bad: "hod"  
✅ Good: "Who is the head of AI department?"

### 2. **Be Specific**
❌ Bad: "faculty"  
✅ Good: "Tell me about Machine Learning faculty"

### 3. **Use Complete Sentences**
❌ Bad: "attendance"  
✅ Good: "How do I check my attendance?"

### 4. **Try Different Phrasings**
If you don't get the answer, try rephrasing:
- "Who is the HOD?"
- "Tell me about the head of department"
- "Who leads the AI & DS department?"

---

## 🎓 Knowledge Base Coverage

### ✅ Available Information:

**Faculty (44 entries):**
- Dr Narayana Rao Appini (HOD)
- Prof Nataraja Suresh Myle
- Mr Venkata Mahendra Tatiparthi
- Dr Lakshmana Rao B
- Ms Manne Sujana
- Mr Mekala Sivapratap Reddy
- Mr Chiranjeevi S V
- Mrs Chandrakala Palem
- Mr Venkateswarlu Avula
- Dr Mamatha Sekireddy
- Mrs Kalyani Bondu
- Ms Swarnalatha V
- Mr P Penchala Prasanth
- Mrs Pitti Jyothi

**Services (11 entries):**
- Online Attendance System
- E-Journals
- Assessments
- Timetables
- Exam Duties
- Intranet Portal
- Website Management

**General (15+ entries):**
- Admissions
- Fees
- Courses
- Library
- Hostel
- Exams
- Placements

---

## 🔍 Troubleshooting

### Issue: Can't access http://localhost:8000
**Solution**: 
- Check if chatbot is running
- Try http://127.0.0.1:8000 instead
- Check firewall settings

### Issue: No response from chatbot
**Solution**:
- Check WebSocket connection status
- Refresh the browser page
- Check browser console for errors

### Issue: Slow responses
**Solution**:
- Normal response time is < 100ms
- Check your internet connection
- Restart the chatbot if needed

---

## 📞 Quick Reference

| What | Where |
|------|-------|
| **Chat Interface** | http://localhost:8000 |
| **Health Check** | http://localhost:8000/health |
| **Chat History** | http://localhost:8000/api/history |
| **Documentation** | CHATBOT_NLP_FEATURES.md |
| **Summary** | CHATBOT_UPGRADE_SUMMARY.md |
| **Test Script** | test_chatbot.py |

---

## 🎉 You're All Set!

The chatbot is **running and ready** to answer your questions!

### 👉 **Next Step:**
**Open http://localhost:8000 in your browser and start chatting!**

---

**Status**: ✅ **ACTIVE**  
**Version**: 2.0.0  
**NLP**: Enabled  
**Knowledge Base**: 70 entries

**Happy Chatting! 🎓💬**
