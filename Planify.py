"""
Planify - AI-Powered Smart Student Planner
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from fpdf import FPDF
import io
import time
import random
from docx import Document
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from dotenv import load_dotenv
import requests
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="Planify - AI Student Planner",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    :root {
        --primary-black: #000000;
        --primary-white: #ffffff;
        --dark-blue: #1e3a5f;
        --accent-blue: #2c5282;
        --light-gray: #f5f5f5;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
    }
    
    .chat-message {
        padding: 1.2rem;
        margin: 1rem 0;
        border-radius: 15px;
        animation: slideIn 0.4s ease;
        max-width: 80%;
    }
    
    .bot-message {
        background: white;
        border: 2px solid var(--dark-blue);
        margin-right: auto;
        border-bottom-left-radius: 5px;
    }
    
    .user-message {
        background: var(--dark-blue);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 5px;
        text-align: right;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .stButton > button {
        background-color: white;
        color: var(--dark-blue);
        border: 2px solid var(--dark-blue);
        border-radius: 25px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: var(--dark-blue);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(30, 58, 95, 0.3);
    }
    
    .planner-header {
        background: linear-gradient(135deg, var(--dark-blue), var(--accent-blue));
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        text-align: center;
    }
    
    .step-indicator {
        display: flex;
        justify-content: space-between;
        margin: 2rem 0;
        padding: 1rem;
        background: white;
        border-radius: 10px;
    }
    
    .step {
        flex: 1;
        text-align: center;
        padding: 0.5rem;
        border-radius: 10px;
        margin: 0 0.25rem;
    }
    
    .step.active {
        background: var(--dark-blue);
        color: white;
    }
    
    .step.completed {
        background: var(--accent-blue);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1
if 'project_data' not in st.session_state:
    st.session_state.project_data = {
        'folder_name': '',
        'plan_type': '',
        'problem': '',
        'schedule': {},
        'subjects': [],
        'template': '',
        'generated_plan': None,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
if 'step_completed' not in st.session_state:
    st.session_state.step_completed = {i: False for i in range(1, 8)}

# Motivational quotes
MOTIVATIONAL_QUOTES = [
    "💪 Every expert was once a beginner. Keep pushing forward!",
    "🌟 Your potential is endless. Go do what you were created to do!",
    "🎯 Focus on your goal. Don't look in any direction but ahead.",
    "🚀 Success doesn't come from what you do occasionally, but what you do consistently.",
    "✨ Believe in yourself. You are braver than you think, more talented than you know.",
    "🏆 The difference between ordinary and extraordinary is that little extra.",
    "📚 Education is the most powerful weapon which you can use to change the world.",
    "⭐ Your limitation—it's only your imagination.",
    "🎓 The expert in anything was once a beginner.",
    "💡 Don't wait for opportunity. Create it."
]

# Study tips database
STUDY_TIPS = {
    'daily': [
        "Start your day with the most challenging subject when your mind is fresh",
        "Use the Pomodoro Technique: 25 minutes focus, 5 minutes break",
        "Review today's notes before sleeping for better retention",
        "Keep a water bottle nearby to stay hydrated",
        "Set specific goals for each study session"
    ],
    'weekly': [
        "Dedicate Sundays for weekly review and planning",
        "Alternate between different subjects to avoid burnout",
        "Schedule mock tests every Friday",
        "Keep Wednesday light for catching up on pending work",
        "Reward yourself after completing weekly goals"
    ],
    'monthly': [
        "Break down syllabus into weekly milestones",
        "Schedule comprehensive revision in the last week",
        "Track progress with monthly self-assessments",
        "Adjust study hours based on difficulty level",
        "Plan buffer days for unexpected events"
    ]
}

class LLMProvider:
    """Unified LLM provider for multiple APIs"""
    
    def __init__(self):
        self.provider = self._detect_provider()
        self.client = self._initialize_client()
        self.model_name = self._select_model()
    
    def _detect_provider(self) -> str:
        """Detect which API provider to use"""
        if os.getenv('GROQ_API_KEY'):
            return 'groq'
    
    def _initialize_client(self):
        """Initialize the appropriate client"""
        if self.provider == 'groq':
            from groq import Groq
            return Groq(api_key=os.getenv('GROQ_API_KEY'))
    
    def _select_model(self) -> str:
        """Select the best available model"""
        if self.provider == 'groq':
            # Use Llama 3.3 70B for best results
            return "llama-3.3-70b-versatile"
        elif self.provider == 'together':
            # Use openai/gpt
            return "openai/gpt-oss-120b"
        else:
            return "default"
    
    def get_response(self, prompt: str, context: List[Dict] = None) -> str:
        """Get response from the LLM"""
        try:
            if self.provider == 'groq':
                return self._groq_response(prompt, context)
            
            
        except Exception as e:
            st.error(f"AI Error: {str(e)}")
            return self._fallback_response(prompt)
    
    def _groq_response(self, prompt: str, context: List[Dict] = None) -> str:
        """Get response from Groq API"""
        messages = [
            {
                "role": "system",
                "content": """You are Mind Mapella, an expert AI study planner assistant. 
                You help students create personalized study schedules, solve time management issues, 
                and provide motivational support. Be friendly, encouraging, and specific in your advice.
                Always structure your responses clearly and provide actionable suggestions."""
            }
        ]
        
        if context:
            messages.extend(context)
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9,
                stream=False
            )
            return completion.choices[0].message.content
        except Exception as e:
            return self._fallback_response(prompt)
    
    def _together_response(self, prompt: str, context: List[Dict] = None) -> str:
        """Get response from Together AI"""
        import together
        
        full_prompt = """<|system|>
        You are Mind Mapella, an expert AI study planner assistant. Help students create personalized schedules.
        <|user|>
        """
        
        if context:
            for msg in context[-3:]:  # Use last 3 messages for context
                full_prompt += f"{msg['role']}: {msg['content']}\n"
        
        full_prompt += f"User: {prompt}\n<|assistant|>"
        
        try:
            response = together.Complete.create(
                model=self.model_name,
                prompt=full_prompt,
                max_tokens=1000,
                temperature=0.7,
                top_p=0.9
            )
            return response['choices'][0]['text'].strip()
        except Exception as e:
            return self._fallback_response(prompt)
    
    def _custom_response(self, prompt: str, context: List[Dict] = None) -> str:
        """Get response from custom API endpoint"""
        api_url = os.getenv('CUSTOM_API_URL')
        api_key = os.getenv('CUSTOM_API_KEY')
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'llama-3.3-70b-versatile',
            'messages': [
                {"role": "system", "content": "You are Mind Mapella, an AI study planner assistant."},
                {"role": "user", "content": prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 1000
        }
        
        try:
            response = requests.post(api_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return self._fallback_response(prompt)
    
    def _fallback_response(self, prompt: str) -> str:
        """Rule-based fallback responses"""
        prompt_lower = prompt.lower()
        
        # Step-specific responses
        if 'folder' in prompt_lower or 'name' in prompt_lower:
            return "Great choice! A well-organized folder structure is the first step to successful planning. Your project folder has been created."
        
        elif 'daily' in prompt_lower:
            return """Excellent! A daily planner will help you:
            • Manage time hour by hour
            • Build consistent study habits
            • Track daily progress
            • Balance study with breaks
            Let's customize it for your needs."""
        
        elif 'weekly' in prompt_lower:
            return """Perfect! A weekly planner will help you:
            • See the bigger picture
            • Plan for tests and assignments
            • Balance multiple subjects
            • Include review sessions
            Let's create your ideal weekly schedule."""
        
        elif 'monthly' in prompt_lower:
            return """Great choice! A monthly planner will help you:
            • Track long-term goals
            • Prepare for major exams
            • Monitor overall progress
            • Plan ahead effectively
            Let's design your monthly roadmap."""
        
        elif any(word in prompt_lower for word in ['problem', 'challenge', 'struggle', 'difficult']):
            return """I understand. Common challenges students face include:
            • Procrastination and lack of motivation
            • Difficulty balancing multiple subjects
            • Poor time management
            • Exam anxiety
            
            I'll create a plan that addresses these issues with:
            • Structured time blocks
            • Regular breaks to prevent burnout
            • Priority-based subject allocation
            • Built-in review sessions
            
            Let's continue building your personalized solution."""
        
        elif any(word in prompt_lower for word in ['subject', 'course', 'class']):
            return """I'll organize your subjects by:
            • Difficulty level (harder subjects when you're fresh)
            • Time requirements (more time for challenging topics)
            • Exam dates (priority to upcoming tests)
            • Personal interest (mixing enjoyable and difficult subjects)
            
            This balanced approach will maximize your learning efficiency."""
        
        else:
            return """I'm here to help you create the perfect study plan! Let's continue with the next step to build your personalized schedule."""

class SmartPlannerGenerator:
    """Generate intelligent study planners"""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
    
    def generate_schedule(self, project_data: Dict) -> pd.DataFrame:
        """Generate AI-optimized schedule"""
        plan_type = project_data.get('plan_type', 'daily')
        
        if plan_type == 'daily':
            return self._generate_daily_schedule(project_data)
        elif plan_type == 'weekly':
            return self._generate_weekly_schedule(project_data)
        else:
            return self._generate_monthly_schedule(project_data)
    
    def _generate_daily_schedule(self, project_data: Dict) -> pd.DataFrame:
        """Generate daily schedule with AI optimization"""
        subjects = project_data.get('subjects', ['Math', 'Science', 'English'])
        problem = project_data.get('problem', '')
        
        # AI prompt for schedule optimization
        prompt = f"""Create a daily study schedule with these requirements:
        Subjects: {', '.join(subjects)}
        Student's challenge: {problem}
        
        Provide a balanced schedule with study sessions, breaks, and meals.
        Format: Time | Activity | Subject/Details | Duration | Tips"""
        
        # Get AI suggestions
        ai_suggestions = self.llm.get_response(prompt)
        
        # Create structured schedule
        schedule_data = {
            'Time': [
                '6:30 AM', '7:00 AM', '8:00 AM', 
                '9:00 AM - 11:00 AM', '11:00 AM - 11:15 AM',
                '11:15 AM - 1:15 PM', '1:15 PM - 2:30 PM',
                '2:30 PM - 4:30 PM', '4:30 PM - 5:00 PM',
                '5:00 PM - 6:30 PM', '6:30 PM - 8:00 PM',
                '8:00 PM - 10:00 PM', '10:00 PM - 10:30 PM'
            ],
            'Activity': [
                'Wake Up & Exercise', 'Morning Routine', 'Breakfast',
                'Study Session 1', 'Short Break',
                'Study Session 2', 'Lunch & Rest',
                'Study Session 3', 'Tea Break',
                'Recreation/Hobbies', 'Dinner & Family Time',
                'Study Session 4', 'Wind Down'
            ],
            'Subject/Details': [
                'Yoga/Walk/Gym', 'Shower & Planning', 'Nutritious meal',
                subjects[0] if subjects else 'Priority Subject',
                'Stretch & Hydrate',
                subjects[1] if len(subjects) > 1 else 'Secondary Subject',
                'Meal & Power Nap',
                subjects[2] if len(subjects) > 2 else 'Practice/Revision',
                'Healthy Snack',
                'Sports/Music/Art',
                'Family Bonding',
                'Review & Homework',
                'Prepare for tomorrow'
            ],
            'Duration': [
                '30 min', '30 min', '30 min',
                '2 hours', '15 min',
                '2 hours', '1 hr 15 min',
                '2 hours', '30 min',
                '1.5 hours', '1.5 hours',
                '2 hours', '30 min'
            ],
            'Tips': [
                '🌅 Start fresh!', '📝 Plan your day', '🥗 Fuel up',
                '🎯 Peak focus time', '💆 Recharge',
                '📚 Deep learning', '😴 Rest well',
                '✍️ Practice time', '☕ Stay energized',
                '🎮 Enjoy yourself', '👨‍👩‍👧‍👦 Connect',
                '🔄 Review & reinforce', '🛏️ Sleep prep'
            ]
        }
        
        # Add problem-specific adjustments
        if 'procrastination' in problem.lower():
            schedule_data['Tips'][3] = '🎯 Start with easiest task first!'
        if 'focus' in problem.lower() or 'concentration' in problem.lower():
            schedule_data['Tips'][5] = '📚 Use Pomodoro: 25min work, 5min break'
        
        return pd.DataFrame(schedule_data)
    
    def _generate_weekly_schedule(self, project_data: Dict) -> pd.DataFrame:
        """Generate weekly schedule"""
        subjects = project_data.get('subjects', ['Math', 'Science', 'English'])
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        schedule_data = {
            'Day': days,
            'Morning (7-12)': [],
            'Afternoon (12-5)': [],
            'Evening (5-10)': [],
            'Focus Subject': [],
            'Daily Goal': [],
            'Motivation': []
        }
        
        for i, day in enumerate(days):
            subject_index = i % len(subjects) if subjects else 0
            focus_subject = subjects[subject_index] if subjects else f'Subject {i+1}'
            
            schedule_data['Morning (7-12)'].append(f'Deep Study: {focus_subject}')
            schedule_data['Afternoon (12-5)'].append('Practice & Assignments')
            schedule_data['Evening (5-10)'].append('Review & Light Study')
            schedule_data['Focus Subject'].append(focus_subject)
            
            if day == 'Sunday':
                schedule_data['Daily Goal'].append('Weekly Review & Planning')
                schedule_data['Morning (7-12)'][-1] = 'Weekly Assessment'
                schedule_data['Afternoon (12-5)'][-1] = 'Catch-up & Revision'
            else:
                schedule_data['Daily Goal'].append(f'Master {focus_subject} concepts')
            
            schedule_data['Motivation'].append(random.choice(MOTIVATIONAL_QUOTES))
        
        return pd.DataFrame(schedule_data)
    
    def _generate_monthly_schedule(self, project_data: Dict) -> pd.DataFrame:
        """Generate monthly schedule"""
        subjects = project_data.get('subjects', ['Math', 'Science', 'English'])
        
        schedule_data = {
            'Week': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            'Phase': ['Foundation', 'Development', 'Advanced', 'Mastery'],
            'Focus Areas': [],
            'Subjects': [],
            'Targets': ['25% Complete', '50% Complete', '75% Complete', '100% & Review'],
            'Assessment': ['Diagnostic Test', 'Mid-Month Quiz', 'Practice Test', 'Final Assessment'],
            'Study Hours/Day': ['4-5 hours', '5-6 hours', '6-7 hours', '5-6 hours'],
            'Key Strategy': [
                '📖 Build strong basics',
                '🔨 Practice problem-solving',
                '🚀 Tackle complex topics',
                '🔄 Revise and perfect'
            ]
        }
        
        for i in range(4):
            if subjects:
                schedule_data['Subjects'].append(', '.join(subjects))
                if i == 0:
                    schedule_data['Focus Areas'].append('Fundamentals & Basics')
                elif i == 1:
                    schedule_data['Focus Areas'].append('Core Concepts')
                elif i == 2:
                    schedule_data['Focus Areas'].append('Advanced Topics')
                else:
                    schedule_data['Focus Areas'].append('Complete Revision')
            else:
                schedule_data['Subjects'].append('All Subjects')
                schedule_data['Focus Areas'].append(f'Phase {i+1} Topics')
        
        return pd.DataFrame(schedule_data)

class ExportManager:
    """Handle all export operations"""
    
    @staticmethod
    def export_to_pdf(df: pd.DataFrame, project_data: Dict) -> bytes:
        """Export to PDF with styling"""
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("Arial", 'B', 24)
        pdf.set_text_color(30, 58, 95)  # Dark blue
        pdf.cell(0, 15, "Mind Mapella", 0, 1, 'C')
        
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, f"{project_data['plan_type'].title()} Study Planner", 0, 1, 'C')
        
        # Project info
        pdf.set_font("Arial", '', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)
        pdf.cell(0, 8, f"Project: {project_data['folder_name']}", 0, 1, 'L')
        pdf.cell(0, 8, f"Created: {project_data['created_at']}", 0, 1, 'L')
        
        if project_data.get('problem'):
            pdf.multi_cell(0, 8, f"Challenge: {project_data['problem']}", 0, 'L')
        
        if project_data.get('subjects'):
            pdf.cell(0, 8, f"Subjects: {', '.join(project_data['subjects'])}", 0, 1, 'L')
        
        pdf.ln(10)
        
        # Calculate column widths
        col_count = len(df.columns)
        page_width = pdf.w - 20  # Margins
        col_width = page_width / col_count
        
        # Table header
        pdf.set_font("Arial", 'B', 10)
        pdf.set_fill_color(30, 58, 95)  # Dark blue
        pdf.set_text_color(255, 255, 255)  # White
        
        for col in df.columns:
            pdf.cell(col_width, 10, str(col)[:15], 1, 0, 'C', True)
        pdf.ln()
        
        # Table data
        pdf.set_font("Arial", '', 9)
        pdf.set_text_color(0, 0, 0)
        
        for _, row in df.iterrows():
            for col in df.columns:
                text = str(row[col])[:20]
                pdf.cell(col_width, 8, text, 1, 0, 'C')
            pdf.ln()
        
        # Add tips section
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(30, 58, 95)
        pdf.cell(0, 10, "Study Tips", 0, 1, 'L')
        
        pdf.set_font("Arial", '', 11)
        pdf.set_text_color(0, 0, 0)
        tips = STUDY_TIPS.get(project_data['plan_type'], STUDY_TIPS['daily'])
        for tip in tips[:3]:
            pdf.cell(10, 8, "•", 0, 0, 'L')
            pdf.multi_cell(0, 8, tip, 0, 'L')
        
        # Add motivational quote
        pdf.ln(10)
        pdf.set_font("Arial", 'I', 12)
        pdf.set_text_color(100, 100, 100)
        quote = random.choice(MOTIVATIONAL_QUOTES)
        pdf.multi_cell(0, 10, quote, 0, 'C')
        
        return pdf.output(dest='S').encode('latin-1')
    
    @staticmethod
    def export_to_excel(df: pd.DataFrame, project_data: Dict) -> bytes:
        """Export to Excel with multiple sheets"""
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Main schedule
            df.to_excel(writer, sheet_name='Schedule', index=False)
            
            # Project information
            info_data = {
                'Property': ['Project Name', 'Plan Type', 'Created Date', 'Problem Statement', 'Template'],
                'Value': [
                    project_data.get('folder_name', 'Untitled'),
                    project_data.get('plan_type', 'daily'),
                    project_data.get('created_at', ''),
                    project_data.get('problem', 'General planning'),
                    project_data.get('template', 'simple')
                ]
            }
            info_df = pd.DataFrame(info_data)
            info_df.to_excel(writer, sheet_name='Project Info', index=False)
            
            # Subjects
            if project_data.get('subjects'):
                subjects_df = pd.DataFrame({
                    'Subject': project_data['subjects'],
                    'Priority': ['High'] * len(project_data['subjects']),
                    'Status': ['In Progress'] * len(project_data['subjects'])
                })
                subjects_df.to_excel(writer, sheet_name='Subjects', index=False)
            
            # Study tips
            tips_data = {
                'Category': [],
                'Tip': []
            }
            for category, tips in STUDY_TIPS.items():
                for tip in tips:
                    tips_data['Category'].append(category.title())
                    tips_data['Tip'].append(tip)
            tips_df = pd.DataFrame(tips_data)
            tips_df.to_excel(writer, sheet_name='Study Tips', index=False)
            
            # Format the workbook
            workbook = writer.book
            
            for sheet_name in workbook.sheetnames:
                worksheet = workbook[sheet_name]
                
                # Adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # Style header row
                for cell in worksheet[1]:
                    cell.font = Font(bold=True, color='FFFFFF')
                    cell.fill = PatternFill(start_color='1e3a5f', end_color='1e3a5f', fill_type='solid')
                    cell.alignment = Alignment(horizontal='center', vertical='center')
        
        output.seek(0)
        return output.getvalue()
    
    @staticmethod
    def export_to_word(df: pd.DataFrame, project_data: Dict) -> bytes:
        """Export to Word document"""
        doc = Document()
        
        # Add title
        title = doc.add_heading('Mind Mapella Study Planner', 0)
        title.alignment = 1  # Center
        
        # Add subtitle
        subtitle = doc.add_heading(f"{project_data['plan_type'].title()} Schedule", 1)
        subtitle.alignment = 1
        
        # Project information
        doc.add_heading('Project Information', 2)
        doc.add_paragraph(f"**Folder Name:** {project_data.get('folder_name', 'Untitled')}")
        doc.add_paragraph(f"**Created:** {project_data.get('created_at', '')}")
        doc.add_paragraph(f"**Challenge:** {project_data.get('problem', 'General planning')}")
        
        if project_data.get('subjects'):
            doc.add_paragraph(f"**Subjects:** {', '.join(project_data['subjects'])}")
        
        # Add schedule table
        doc.add_heading('Your Schedule', 2)
        table = doc.add_table(rows=1, cols=len(df.columns))
        table.style = 'Light Grid Accent 1'
        
        # Header row
        header_cells = table.rows[0].cells
        for i, col in enumerate(df.columns):
            header_cells[i].text = str(col)
            header_cells[i].paragraphs[0].runs[0].font.bold = True
        
        # Data rows
        for _, row in df.iterrows():
            row_cells = table.add_row().cells
            for i, col in enumerate(df.columns):
                row_cells[i].text = str(row[col])
        
        # Add study tips
        doc.add_page_break()
        doc.add_heading('Personalized Study Tips', 1)
        
        tips = STUDY_TIPS.get(project_data['plan_type'], STUDY_TIPS['daily'])
        for i, tip in enumerate(tips, 1):
            doc.add_paragraph(f"{i}. {tip}", style='List Number')
        
        # Add motivation section
        doc.add_heading('Daily Motivation', 2)
        doc.add_paragraph(random.choice(MOTIVATIONAL_QUOTES))
        
        # Save to bytes
        doc_buffer = io.BytesIO()
        doc.save(doc_buffer)
        doc_buffer.seek(0)
        
        return doc_buffer.getvalue()

def display_step_indicator():
    """Display progress steps"""
    steps = [
        "📁 Folder",
        "📅 Type",
        "❓ Challenge",
        "⏰ Schedule",
        "📚 Subjects",
        "🎨 Template",
        "✅ Generate"
    ]
    
    cols = st.columns(len(steps))
    for i, (col, step) in enumerate(zip(cols, steps)):
        step_num = i + 1
        with col:
            if step_num < st.session_state.current_step:
                st.success(step, icon="✅")
            elif step_num == st.session_state.current_step:
                st.info(step, icon="👉")
            else:
                st.text(step)

def chat_interface():
    """Main chat interface"""
    
    # Initialize LLM provider
    if 'llm_provider' not in st.session_state:
        st.session_state.llm_provider = LLMProvider()
    
    # Display messages
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            st.markdown(f"""
            <div class="chat-message bot-message">
                🤖 {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message user-message">
                {message["content"]} 👤
            </div>
            """, unsafe_allow_html=True)
    
    # Step-based interaction
    if st.session_state.current_step == 1:
        # Folder name
        if not st.session_state.messages:
            welcome = "👋 Welcome to Mind Mapella! I'm your AI study planning assistant. Let's create the perfect study plan for you. First, what would you like to name your project folder?"
            st.session_state.messages.append({"role": "assistant", "content": welcome})
            st.rerun()
        
        folder_name = st.text_input("Enter folder name:", key="folder_input")
        if st.button("Continue →", key="folder_btn") and folder_name:
            st.session_state.project_data['folder_name'] = folder_name
            st.session_state.messages.append({"role": "user", "content": folder_name})
            
            response = f"Great! I've created a folder called '{folder_name}'. Now, what type of planner would you like to create?"
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.current_step = 2
            st.rerun()
    
    elif st.session_state.current_step == 2:
        # Plan type selection
        st.markdown("### Choose your planner type:")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📅 Daily Planner", use_container_width=True):
                st.session_state.project_data['plan_type'] = 'daily'
                st.session_state.messages.append({"role": "user", "content": "Daily planner"})
                
                response = """Perfect! A daily planner will help you manage your time hour by hour. 
                
Now, tell me about any specific challenges you face with studying or time management. For example:
- Do you struggle with procrastination?
- Find it hard to focus for long periods?
- Need help balancing multiple subjects?"""
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.current_step = 3
                st.rerun()
        
        with col2:
            if st.button("📆 Weekly Planner", use_container_width=True):
                st.session_state.project_data['plan_type'] = 'weekly'
                st.session_state.messages.append({"role": "user", "content": "Weekly planner"})
                
                response = """Excellent choice! A weekly planner gives you a broader view of your study goals.
                
What challenges do you face in managing your weekly schedule? Share any specific issues like:
- Difficulty maintaining consistency
- Balancing study with other activities
- Preparing for weekly tests"""
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.current_step = 3
                st.rerun()
        
        with col3:
            if st.button("🗓️ Monthly Planner", use_container_width=True):
                st.session_state.project_data['plan_type'] = 'monthly'
                st.session_state.messages.append({"role": "user", "content": "Monthly planner"})
                
                response = """Great! A monthly planner helps you track long-term goals and prepare for major exams.
                
What are your main challenges with long-term planning? For instance:
- Completing syllabus on time
- Maintaining motivation over weeks
- Tracking overall progress"""
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.current_step = 3
                st.rerun()
    
    elif st.session_state.current_step == 3:
        # Problem/challenge input
        problem = st.text_area("Describe your challenges:", height=100, key="problem_input")
        if st.button("Continue →", key="problem_btn") and problem:
            st.session_state.project_data['problem'] = problem
            st.session_state.messages.append({"role": "user", "content": problem})
            
            # Get AI response
            llm = st.session_state.llm_provider
            ai_response = llm.get_response(
                f"The student faces this challenge: {problem}. Provide empathetic understanding and ask about their daily schedule.",
                st.session_state.messages
            )
            
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            st.session_state.current_step = 4
            st.rerun()
    
    elif st.session_state.current_step == 4:
        # Schedule input
        st.markdown("### Tell me about your typical day:")
        
        col1, col2 = st.columns(2)
        with col1:
            wake_time = st.time_input("⏰ Wake up time:", value=datetime.strptime("07:00", "%H:%M").time())
            breakfast = st.time_input("🍳 Breakfast time:", value=datetime.strptime("08:00", "%H:%M").time())
            lunch = st.time_input("🍽️ Lunch time:", value=datetime.strptime("12:30", "%H:%M").time())
        
        with col2:
            dinner = st.time_input("🍝 Dinner time:", value=datetime.strptime("19:00", "%H:%M").time())
            sleep_time = st.time_input("😴 Sleep time:", value=datetime.strptime("22:30", "%H:%M").time())
            study_hours = st.slider("📚 Preferred study hours per day:", 1, 12, 6)
        
        if st.button("Continue →", key="schedule_btn"):
            schedule = f"Wake: {wake_time}, Breakfast: {breakfast}, Lunch: {lunch}, Dinner: {dinner}, Sleep: {sleep_time}, Study hours: {study_hours}"
            st.session_state.project_data['schedule'] = {
                'wake': str(wake_time),
                'breakfast': str(breakfast),
                'lunch': str(lunch),
                'dinner': str(dinner),
                'sleep': str(sleep_time),
                'study_hours': study_hours
            }
            st.session_state.messages.append({"role": "user", "content": schedule})
            
            response = "Perfect! I've analyzed your daily routine. Now, please list your subjects and any specific topics you need to focus on."
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.current_step = 5
            st.rerun()
    
    elif st.session_state.current_step == 5:
        # Subjects input
        subjects = st.text_area(
            "Enter your subjects (comma-separated):",
            placeholder="e.g., Mathematics, Physics, Chemistry, Biology, English",
            height=80,
            key="subjects_input"
        )
        
        # File upload
        uploaded_file = st.file_uploader(
            "📎 Upload syllabus (optional)",
            type=['pdf', 'doc', 'docx', 'txt'],
            help="Upload your syllabus for automatic subject extraction"
        )
        
        if uploaded_file:
            st.success(f"✅ {uploaded_file.name} uploaded successfully!")
        
        if st.button("Continue →", key="subjects_btn") and subjects:
            subjects_list = [s.strip() for s in subjects.split(',')]
            st.session_state.project_data['subjects'] = subjects_list
            st.session_state.messages.append({"role": "user", "content": subjects})
            
            response = f"""Excellent! I'll create a plan for these {len(subjects_list)} subjects: {', '.join(subjects_list)}.
            
Now, let's choose a template style for your planner. This will determine how your schedule looks."""
            
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.current_step = 6
            st.rerun()
    
    elif st.session_state.current_step == 6:
        # Template selection
        st.markdown("### Select your preferred template style:")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **⬜ Simple & Plain**
            - Clean and minimalist
            - Focus on functionality
            - Easy to read
            """)
            if st.button("Choose Simple", use_container_width=True):
                st.session_state.project_data['template'] = 'simple'
                st.session_state.messages.append({"role": "user", "content": "Simple template"})
                st.session_state.current_step = 7
                st.rerun()
        
        with col2:
            st.markdown("""
            **💼 Professional**
            - Business-like design
            - Structured layout
            - Formal appearance
            """)
            if st.button("Choose Professional", use_container_width=True):
                st.session_state.project_data['template'] = 'professional'
                st.session_state.messages.append({"role": "user", "content": "Professional template"})
                st.session_state.current_step = 7
                st.rerun()
        
        with col3:
            st.markdown("""
            **🎨 Aesthetic**
            - Creative design
            - Colorful elements
            - Motivating visuals
            """)
            if st.button("Choose Aesthetic", use_container_width=True):
                st.session_state.project_data['template'] = 'aesthetic'
                st.session_state.messages.append({"role": "user", "content": "Aesthetic template"})
                st.session_state.current_step = 7
                st.rerun()
    
    elif st.session_state.current_step == 7:
        # Generate planner
        with st.spinner("✨ Creating your personalized planner..."):
            time.sleep(2)
            
            # Generate the schedule
            generator = SmartPlannerGenerator(st.session_state.llm_provider)
            schedule_df = generator.generate_schedule(st.session_state.project_data)
            st.session_state.project_data['generated_plan'] = schedule_df
            
            response = """🎉 **Your personalized planner is ready!**
            
I've created an optimized schedule based on:
- Your specific challenges
- Your daily routine
- Your subjects and priorities
- Scientific study patterns for maximum retention
            
Your planner includes built-in breaks, varied study sessions, and time for recreation to maintain a healthy balance."""
            
            st.session_state.messages.append({"role": "assistant", "content": response})

def display_generated_planner():
    """Display the generated planner"""
    if st.session_state.project_data.get('generated_plan') is not None:
        df = st.session_state.project_data['generated_plan']
        
        # Planner header
        st.markdown(f"""
        <div class="planner-header">
            <h2>📚 Your {st.session_state.project_data['plan_type'].title()} Study Planner</h2>
            <p>Personalized for: {st.session_state.project_data['folder_name']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display the schedule
        st.dataframe(df, use_container_width=True, height=400)
        
        # AI Insights
        with st.expander("🤖 AI Insights & Recommendations", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 Schedule Analysis")
                st.markdown(f"""
                - **Total Study Time:** {st.session_state.project_data['schedule'].get('study_hours', 6)} hours/day
                - **Subjects Covered:** {len(st.session_state.project_data['subjects'])}
                - **Break Frequency:** Every 2 hours
                - **Peak Study Time:** Morning (9-11 AM)
                """)
                
                st.markdown("### 🎯 Focus Areas")
                problem = st.session_state.project_data.get('problem', '')
                if 'procrastination' in problem.lower():
                    st.info("💡 Added shorter initial tasks to build momentum")
                if 'focus' in problem.lower():
                    st.info("💡 Incorporated Pomodoro technique")
                if 'balance' in problem.lower():
                    st.info("💡 Equal time distribution across subjects")
            
            with col2:
                st.markdown("### 💪 Success Tips")
                tips = STUDY_TIPS.get(st.session_state.project_data['plan_type'], STUDY_TIPS['daily'])
                for tip in tips[:4]:
                    st.markdown(f"• {tip}")
                
                st.markdown("### 🏆 Motivation")
                st.success(random.choice(MOTIVATIONAL_QUOTES))
        
        # Export section
        st.markdown("### 💾 Export Your Planner")
        
        export_manager = ExportManager()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            pdf_data = export_manager.export_to_pdf(df, st.session_state.project_data)
            st.download_button(
                label="📄 Download PDF",
                data=pdf_data,
                file_name=f"{st.session_state.project_data['folder_name']}_planner.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        
        with col2:
            excel_data = export_manager.export_to_excel(df, st.session_state.project_data)
            st.download_button(
                label="📊 Download Excel",
                data=excel_data,
                file_name=f"{st.session_state.project_data['folder_name']}_planner.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col3:
            word_data = export_manager.export_to_word(df, st.session_state.project_data)
            st.download_button(
                label="📝 Download Word",
                data=word_data,
                file_name=f"{st.session_state.project_data['folder_name']}_planner.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        
        # Reminder settings
        st.markdown("### 🔔 Smart Reminders")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            enable_reminders = st.checkbox(
                "Enable AI-powered study reminders",
                help="Get timely notifications with motivational messages"
            )
        
        with col2:
            if enable_reminders:
                st.success("✅ Active")
        
        if enable_reminders:
            reminder_time = st.time_input(
                "Daily reminder time:",
                value=datetime.strptime("08:00", "%H:%M").time()
            )
            
            st.info(f"""
            📱 **Sample Reminder:**
            
            Time to study {st.session_state.project_data['subjects'][0] if st.session_state.project_data['subjects'] else 'your subject'}!
            
            {random.choice(MOTIVATIONAL_QUOTES)}
            
            Remember: Consistency is key to success! 🎯
            """)
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📝 Modify Planner", use_container_width=True):
                st.session_state.current_step = 1
                st.rerun()
        
        with col2:
            if st.button("🆕 Create New", use_container_width=True):
                # Reset everything
                st.session_state.messages = []
                st.session_state.current_step = 1
                st.session_state.project_data = {
                    'folder_name': '',
                    'plan_type': '',
                    'problem': '',
                    'schedule': {},
                    'subjects': [],
                    'template': '',
                    'generated_plan': None,
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.rerun()
        
        with col3:
            if st.button("💬 Ask AI", use_container_width=True):
                st.info("Chat with AI about your planner - Feature coming soon!")

def main():
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 2rem; background: white; border-radius: 15px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 2rem;'>
        <h1 style='color: #1e3a5f; margin: 0; font-size: 3rem;'>🧠 Mind Mapella</h1>
        <p style='color: #666; margin: 0.5rem 0 0 0; font-size: 1.2rem;'>
            AI-Powered Study Planning Assistant
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # API Status
    llm_provider = LLMProvider()
    if llm_provider.provider == 'groq':
        st.success("✅ Connected to Groq AI (Llama 3.3 70B)")
    elif llm_provider.provider == 'together':
        st.success("✅ Connected to Together AI")
    elif llm_provider.provider == 'custom':
        st.success("✅ Connected to Custom AI Endpoint")
    else:
        st.warning("⚠️ Running in offline mode (rule-based responses)")
    
    # Progress indicator
    display_step_indicator()
    
    # Main chat interface
    chat_interface()
    
    # Display planner if generated
    if st.session_state.current_step == 7:
        display_generated_planner()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎯 Quick Stats")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Progress", f"{st.session_state.current_step}/7")
        with col2:
            st.metric("Messages", len(st.session_state.messages))
        
        st.markdown("---")
        
        # Current project info
        if st.session_state.project_data['folder_name']:
            st.markdown("### 📁 Current Project")
            st.info(st.session_state.project_data['folder_name'])
        
        # Help section
        with st.expander("❓ How It Works"):
            st.markdown("""
            **7 Simple Steps:**
            1. **Name** your project
            2. **Choose** plan type
            3. **Describe** your challenges
            4. **Share** your schedule
            5. **List** your subjects
            6. **Select** a template
            7. **Generate** & export!
            
            The AI analyzes your inputs to create a personalized study plan optimized for your needs.
            """)
        
        # Tips of the day
        st.markdown("---")
        st.markdown("### 💡 Study Tip of the Day")
        st.info(random.choice(STUDY_TIPS['daily']))
        
        # About
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; padding: 1rem;'>
            <small>
                Mind Mapella v1.0<br>
                Powered by AI 🤖<br>
                Made for Students 📚
            </small>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()