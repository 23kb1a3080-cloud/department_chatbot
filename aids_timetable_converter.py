"""
Convert AI&DS First Year Timetable to Knowledge Base Format
"""
import json

# Original timetable data
timetable = {
    "Section_A": {
        "Monday": {
            "9-10": "LAC (VHKR)",
            "10-11": "BEEE (SDS)",
            "11-12": "EP (BRK)",
            "1-4": "ENGINEERING GRAPHICS (PNK, AKYN, YSR)"
        },
        "Tuesday": {
            "9-10": "EP (BRK)",
            "10-11": "BEEE (SDS)",
            "11-12": "LAC (VHKR)",
            "1-4": "ENGINEERING GRAPHICS (RMB, AKYN, YSR)"
        },
        "Wednesday": {
            "9-12": "INTRODUCTION TO PROGRAMMING (VSRA)",
            "1-2": "EP (BRK)",
            "2-3": "BEEE (SDS)"
        },
        "Thursday": {
            "9-12": "CP LAB (VSRA)",
            "1-2": "LAC (VHKR)",
            "2-4": "EEE WS (TMS, NUSA, SDS)"
        },
        "Friday": {
            "9-12": "EP-LAB (BRK, MDHB)",
            "1-4": "INTRODUCTION TO PROGRAMMING (VSRA)"
        },
        "Saturday": {
            "9-10": "EP (BRK)",
            "10-11": "BEEE (SDS)",
            "11-12": "LAC (VHKR)",
            "1-2": "NGCS (GM)",
            "2-4": "IT WS (SSB, USJ, CVVR)"
        }
    },
    "Section_B": {
        "Monday": {
            "9-10": "BEEE (RRP)",
            "10-11": "LAC (CHMR)",
            "11-12": "EP (YMK)",
            "1-2": "BEEE (RRP)",
            "2-4": "EEE WS (MODS, JCMA, RRP)"
        },
        "Tuesday": {
            "9-12": "ENGINEERING GRAPHICS (KNP, MSR, BSK)",
            "1-2": "BEEE (RRP)",
            "2-3": "EP (YMK)",
            "3-4": "LAC (CHMR)"
        },
        "Wednesday": {
            "9-12": "INTRODUCTION TO PROGRAMMING (VSRA)",
            "1-2": "EP (YMK)",
            "2-3": "BEEE (RRP)",
            "3-4": "LAC (CHMR)"
        },
        "Thursday": {
            "9-12": "EP-LAB (YMK, DSRY)",
            "1-4": "CP LAB (VSRA)"
        },
        "Friday": {
            "9-10": "EP (YMK)",
            "10-11": "NGCS (DAVI)",
            "11-12": "LAC (CHMR)",
            "1-4": "INTRODUCTION TO PROGRAMMING (VSRA)"
        },
        "Saturday": {
            "9-10": "LAC (CHMR)",
            "10-12": "IT WS (PN, USJ, DSR)"
        }
    },
    "Section_C": {
        "Monday": {
            "9-12": "EP-LAB (MDHB, HKK)",
            "1-4": "ENGINEERING GRAPHICS (CHRK, SCS, SKRB)"
        },
        "Tuesday": {
            "9-12": "CP LAB (MSMA, SMAM)",
            "1-2": "LAC (SKA)",
            "2-3": "BEEE (KVTR)",
            "3-4": "EP (HKK)"
        },
        "Wednesday": {
            "9-10": "EP (HKK)",
            "10-12": "EEE WS (KVTR, MRJ, VANJ)",
            "1-2": "LAC (SKA)",
            "2-3": "BEEE (KVTR)",
            "3-4": "EP (HKK)"
        },
        "Thursday": {
            "9-10": "EP (HKK)",
            "10-11": "BEEE (KVTR)",
            "11-12": "LAC (SKA)",
            "1-2": "BEEE (KVTR)",
            "2-3": "LAC (SKA)",
            "3-4": "NGCS (DAVI)"
        },
        "Friday": {
            "9-12": "INTRODUCTION TO PROGRAMMING (MSMA)",
            "1-4": "INTRODUCTION TO PROGRAMMING (MSMA)"
        },
        "Saturday": {
            "9-12": "ENGINEERING GRAPHICS (BSK, TPK, SKRB)",
            "1-2": "LAC (SKA)",
            "2-4": "IT WS (SUNP, CSKA, MSMA)"
        }
    },
    "Section_D": {
        "Monday": {
            "9-12": "ENGINEERING GRAPHICS (MCS, CHRK, MSR)",
            "1-2": "LAC (SRK)",
            "2-3": "BEEE (GSR)",
            "3-4": "EP (KVK)"
        },
        "Tuesday": {
            "9-10": "NGCS (DAVI)",
            "10-11": "BEEE (GSR)",
            "11-12": "EP (KVK)",
            "1-4": "CP LAB (MSMA)"
        },
        "Wednesday": {
            "9-10": "EP (KVK)",
            "10-11": "BEEE (GSR)",
            "11-12": "LAC (SRK)",
            "1-2": "LAC (SRK)",
            "2-4": "EEE WS (IPR, MRJ, GSR)"
        },
        "Thursday": {
            "9-10": "LAC (SRK)",
            "10-11": "BEEE (GSR)",
            "11-12": "EP (KVK)",
            "1-4": "ENGINEERING GRAPHICS (SKRB, MSR)"
        },
        "Friday": {
            "9-12": "INTRODUCTION TO PROGRAMMING (MSMA)",
            "1-4": "INTRODUCTION TO PROGRAMMING (MSMA)"
        },
        "Saturday": {
            "9-12": "EP-LAB (KVK, YMK)",
            "1-2": "LAC (SRK)",
            "2-4": "IT WS (VSRA, BKOT)"
        }
    }
}

subjects = {
    "LAC": "Linear Algebra & Calculus",
    "EP": "Engineering Physics",
    "BEEE": "Basic Electrical and Electronics Engineering",
    "I_P": "Introduction to Programming",
    "NGCS": "NSS/NCC/Scouts and Guides/Community Service",
    "CP LAB": "Computer Programming Lab",
    "EP-LAB": "Engineering Physics Lab",
    "EEE WS": "EEE Workshop",
    "IT WS": "IT Workshop",
    "ENGINEERING GRAPHICS": "Engineering Graphics"
}

faculty = {
    "VHKR": "Harikrishna Reddy V",
    "BRK": "Radha Krishna B",
    "SDS": "Bhagyamma S D S",
    "VSRA": "Mahendra TV",
    "GM": "Madhavaiah G",
    "CHMR": "Madhava Reddy Ch",
    "YMK": "Madhava Kumar Y",
    "DAVI": "Avinash Damarapu",
    "RRP": "Ram Prasad R",
    "HKK": "Hari Krishna Koduru",
    "SKA": "Abzal SK",
    "KVTR": "Thulasi Ram KV",
    "SRK": "Ravi Kumar S",
    "GSR": "Subba Reddy Gade",
    "KVK": "Vasanth Kumar K"
}

def generate_knowledge_base():
    """Generate knowledge base entries for timetable queries."""
    kb = {}
    
    # General timetable info
    kb["timetable"] = "AI & DS First Year First Semester timetable is available for Sections A, B, C, and D. You can ask about specific sections, days, or subjects."
    kb["first year timetable"] = "AI & DS First Year First Semester has 4 sections (A, B, C, D) with classes from Monday to Saturday. Subjects include LAC, EP, BEEE, Introduction to Programming, Engineering Graphics, and various labs."
    kb["aids timetable"] = "AI & DS First Year First Semester timetable includes theory classes, labs (CP Lab, EP Lab), and workshops (EEE Workshop, IT Workshop) across 4 sections."
    kb["1st year timetable"] = "First year AI & DS students have classes in 4 sections with subjects like Linear Algebra & Calculus, Engineering Physics, BEEE, Programming, and Engineering Graphics."
    
    # Section-specific queries
    for section, days in timetable.items():
        section_name = section.replace("_", " ")
        
        # Section overview
        schedule_summary = []
        for day, periods in days.items():
            subjects_today = list(periods.values())
            schedule_summary.append(f"{day}: {', '.join(subjects_today[:2])}")
        
        kb[f"{section_name.lower()}"] = f"{section_name} timetable for AI & DS First Year includes classes from Monday to Saturday. Key subjects: LAC, EP, BEEE, Introduction to Programming, Engineering Graphics, and labs."
        kb[f"{section_name.lower()} timetable"] = f"{section_name} schedule: " + "; ".join(schedule_summary[:3]) + "... (Full week schedule available)"
        
        # Day-specific queries for each section
        for day, periods in days.items():
            key = f"{section_name.lower()} {day.lower()}"
            schedule = []
            for time, subject in periods.items():
                schedule.append(f"{time}: {subject}")
            kb[key] = f"{section_name} on {day}: " + ", ".join(schedule)
    
    # Day-specific queries (all sections)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    for day in days:
        day_schedule = []
        for section in timetable.keys():
            if day in timetable[section]:
                section_name = section.replace("_", " ")
                first_class = list(timetable[section][day].values())[0]
                day_schedule.append(f"{section_name}: {first_class}")
        kb[f"{day.lower()} timetable"] = f"AI & DS First Year {day} schedule varies by section. " + "; ".join(day_schedule[:2])
        kb[f"{day.lower()} schedule"] = f"On {day}, AI & DS First Year sections have different schedules. Ask about a specific section for details."
    
    # Subject-specific queries
    for subject_code, subject_name in subjects.items():
        kb[subject_name.lower()] = f"{subject_name} ({subject_code}) is taught in AI & DS First Year First Semester across all sections."
        kb[subject_code.lower()] = f"{subject_code} stands for {subject_name}. It's part of the AI & DS First Year curriculum."
    
    # Lab queries
    kb["cp lab"] = "Computer Programming Lab (CP LAB) is conducted for all AI & DS First Year sections. Different sections have it on different days."
    kb["programming lab"] = "Computer Programming Lab is available for all sections. Section A: Thursday 9-12, Section B: Thursday 1-4, Section C: Tuesday 9-12, Section D: Tuesday 1-4."
    kb["ep lab"] = "Engineering Physics Lab (EP-LAB) is conducted for all sections on different days with practical experiments."
    kb["physics lab"] = "Engineering Physics Lab: Section A (Friday 9-12), Section B (Thursday 9-12), Section C (Monday 9-12), Section D (Saturday 9-12)."
    kb["eee workshop"] = "EEE Workshop is conducted for all sections: Section A (Thursday 2-4), Section B (Monday 2-4), Section C (Wednesday 10-12), Section D (Wednesday 2-4)."
    kb["it workshop"] = "IT Workshop is scheduled for all sections: Section A (Saturday 2-4), Section B (Saturday 1-2), Section C (Saturday 2-4), Section D (Saturday 2-4)."
    
    # Time-based queries
    kb["morning classes"] = "Morning classes (9-12) in AI & DS First Year include theory subjects like LAC, EP, BEEE, and labs like CP Lab, EP Lab, and Engineering Graphics."
    kb["afternoon classes"] = "Afternoon classes (1-4) include labs, workshops, and continuation of theory subjects across all sections."
    
    return kb

def save_timetable_data():
    """Save complete timetable data and knowledge base."""
    
    # Save complete timetable
    with open('aids_timetable_data.json', 'w', encoding='utf-8') as f:
        json.dump({
            'timetable': timetable,
            'subjects': subjects,
            'faculty': faculty
        }, f, indent=2, ensure_ascii=False)
    
    # Save knowledge base
    kb = generate_knowledge_base()
    with open('aids_timetable_kb.json', 'w', encoding='utf-8') as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved complete timetable data to aids_timetable_data.json")
    print(f"✓ Generated {len(kb)} knowledge base entries in aids_timetable_kb.json")
    
    return kb

if __name__ == "__main__":
    print("=" * 60)
    print("AI & DS First Year Timetable Converter")
    print("=" * 60)
    kb = save_timetable_data()
    print(f"\n✓ Conversion complete!")
    print(f"✓ Total KB entries: {len(kb)}")
    print("\nSample entries:")
    for i, (key, value) in enumerate(list(kb.items())[:5], 1):
        print(f"{i}. {key}: {value[:80]}...")
