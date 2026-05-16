"""
NBKR Institute AI & DS Faculty Scraper V2
Enhanced scraper with manual parsing for IRINS portal
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re

# Faculty data extracted from the page
faculty_list = [
    {
        "name": "Dr Narayana Rao Appini",
        "designation": "Head of the Department",
        "specialization": "Computer Networks, Machine Learning"
    },
    {
        "name": "Prof Nataraja Suresh Myle",
        "designation": "Professor",
        "specialization": "Computer Science"
    },
    {
        "name": "Mr Venkata Mahendra Tatiparthi",
        "designation": "Associate Professor",
        "specialization": "Computer Science"
    },
    {
        "name": "Dr Lakshmana Rao B",
        "designation": "Associate Professor",
        "specialization": "Computer Science, Software Engineering"
    },
    {
        "name": "Ms Manne Sujana",
        "designation": "Assistant Professor",
        "specialization": "AI, Deep Learning"
    },
    {
        "name": "Mr Mekala Sivapratap Reddy",
        "designation": "Assistant Professor",
        "specialization": "Machine Learning, Social Networks, Security"
    },
    {
        "name": "Mr Chiranjeevi S V",
        "designation": "Assistant Professor",
        "specialization": "Computer Organization, DBMS, DLD, CN"
    },
    {
        "name": "Mrs Chandrakala Palem",
        "designation": "Assistant Professor",
        "specialization": "Computer Science"
    },
    {
        "name": "Mr Venkateswarlu Avula",
        "designation": "Assistant Professor",
        "specialization": "Artificial Intelligence, enabling machines"
    },
    {
        "name": "Dr Mamatha Sekireddy",
        "designation": "Assistant Professor",
        "specialization": "AI and DS Department"
    },
    {
        "name": "Mrs Kalyani Bondu",
        "designation": "Assistant Professor",
        "specialization": "Software Engineering"
    },
    {
        "name": "Ms Swarnalatha V",
        "designation": "Assistant Professor",
        "specialization": "Python Programming, Digital Logic Design, Programming"
    },
    {
        "name": "Mr P PENCHALA PRASANTH",
        "designation": "Assistant Professor",
        "specialization": "Artificial Intelligence"
    },
    {
        "name": "Mrs Pitti Jyothi",
        "designation": "Assistant Professor",
        "specialization": "Teaching expert with 7+ years of experience"
    }
]

def generate_faculty_knowledge_base(faculty_data):
    """Generate knowledge base for chatbot."""
    kb = {}
    
    # Add general department info
    kb["aids faculty"] = f"The AI & DS Department at NBKR Institute has {len(faculty_data)} faculty members including 1 Head of Department, 1 Professor, 2 Associate Professors, and {len([f for f in faculty_data if 'Assistant' in f['designation']])} Assistant Professors."
    
    kb["ai ds department"] = f"The Department of AI and Data Science has {len(faculty_data)} faculty members specializing in Machine Learning, Deep Learning, Computer Networks, Software Engineering, Python Programming, and Artificial Intelligence."
    
    kb["hod aids"] = "Dr Narayana Rao Appini is the Head of the AI & DS Department. His specialization includes Computer Networks and Machine Learning."
    
    # Add individual faculty entries
    for faculty in faculty_data:
        name = faculty['name'].lower()
        name_clean = re.sub(r'\b(dr|mr|ms|mrs|prof)\b', '', name, flags=re.I).strip()
        
        info = f"{faculty['name']} is {faculty['designation']} in the AI & DS Department at NBKR Institute."
        
        if faculty.get('specialization'):
            info += f" Specialization: {faculty['specialization']}."
        
        # Add entry with full name
        kb[name] = info
        kb[name_clean] = info
        
        # Add entry for last name
        name_parts = name_clean.split()
        if len(name_parts) > 1:
            last_name = name_parts[-1]
            if len(last_name) > 3:
                kb[last_name] = info
        
        # Add entry for specialization keywords
        if faculty.get('specialization'):
            spec_lower = faculty['specialization'].lower()
            if 'machine learning' in spec_lower:
                if 'machine learning faculty' not in kb:
                    kb['machine learning faculty'] = f"Faculty specializing in Machine Learning: {faculty['name']} ({faculty['designation']})"
                else:
                    kb['machine learning faculty'] += f", {faculty['name']}"
            
            if 'deep learning' in spec_lower or 'ai' in spec_lower:
                if 'ai faculty' not in kb:
                    kb['ai faculty'] = f"Faculty specializing in AI: {faculty['name']} ({faculty['designation']})"
                else:
                    kb['ai faculty'] += f", {faculty['name']}"
    
    return kb

def save_faculty_data():
    """Save faculty data and generate knowledge base."""
    print("=" * 70)
    print("NBKR Institute AI & DS Faculty Data Processor")
    print("=" * 70)
    print()
    
    print(f"Processing {len(faculty_list)} faculty members...")
    
    # Save detailed faculty data
    with open('aids_faculty_data.json', 'w', encoding='utf-8') as f:
        json.dump(faculty_list, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved detailed data to aids_faculty_data.json")
    
    # Generate and save knowledge base
    kb = generate_faculty_knowledge_base(faculty_list)
    
    with open('aids_faculty_kb.json', 'w', encoding='utf-8') as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)
    print(f"✓ Generated knowledge base with {len(kb)} entries")
    print(f"✓ Saved knowledge base to aids_faculty_kb.json")
    
    print()
    print("=" * 70)
    print("Faculty Summary:")
    print("=" * 70)
    print(f"Total Faculty: {len(faculty_list)}")
    print(f"Head of Department: 1")
    print(f"Professors: {len([f for f in faculty_list if f['designation'] == 'Professor'])}")
    print(f"Associate Professors: {len([f for f in faculty_list if 'Associate' in f['designation']])}")
    print(f"Assistant Professors: {len([f for f in faculty_list if 'Assistant' in f['designation']])}")
    print()
    
    print("Faculty Members:")
    for i, faculty in enumerate(faculty_list, 1):
        print(f"{i:2d}. {faculty['name']:40s} - {faculty['designation']}")
    
    print()
    print("=" * 70)
    print("✓ Ready to integrate into chatbot!")
    print("=" * 70)

if __name__ == "__main__":
    save_faculty_data()
