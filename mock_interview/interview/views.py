from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import cv2
import threading
import os
import time
import wave
import sounddevice as sd
import numpy as np
import subprocess
import google.generativeai as genai
from gtts import gTTS
import PyPDF2

# Global Variables
recording = False
current_question_index = 0
questions = []
video_writer = None
cap = None
output_file = None
audio_file = None
fourcc = cv2.VideoWriter_fourcc(*'XVID')
frame_size = (640, 480)
fps = 30

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyBwtC8oC6R8hGrMroiTIbHoQquN_Kr2tzI"  
genai.configure(api_key=GEMINI_API_KEY)


def extract_text_from_pdf(pdf_path):
    """Extract text content from a PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""  # Ensure non-None string
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""
    

# Function to generate questions using Gemini API
def generate_questions(resume_text, job_description):
    """Generate interview questions using Gemini API."""
    prompt = f"""
    Based on the following resume and job description, generate 10 interview questions:
    - 5 general questions related to the candidate's background and experience.
    - 5 technical/skill-based questions relevant to the job description.

    Resume:
    {resume_text}

    Job Description:
    {job_description}

    Format the response as:
    1. Question one
    2. Question two
    ...
    """
    
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content(prompt)
    
    if response and response.text:
        return response.text.strip().split("\n")
    return []


# Function to convert questions to MP3
def save_questions_as_mp3(questions):
    """Save generated questions as MP3 files in media/questions folder."""
    questions_folder = os.path.join(settings.MEDIA_ROOT, 'questions')
    os.makedirs(questions_folder, exist_ok=True)

    for i, question in enumerate(questions):
        question_text = question.strip().split('. ', 1)[-1]  # Remove numbering
        mp3_path = os.path.join(questions_folder, f"question_{i + 1}.mp3")
        
        # Convert text to speech and save as MP3
        try:
            tts = gTTS(text=question_text, lang='en')
            tts.save(mp3_path)
            print(f"✅ Saved: {mp3_path}")
        except Exception as e:
            print(f"⚠️ Error saving question {i + 1}: {e}")



def load_questions():
    global questions
    questions_folder = os.path.join(settings.MEDIA_ROOT, 'questions')
    os.makedirs(questions_folder, exist_ok=True)
    questions = sorted([os.path.join(questions_folder, f) for f in os.listdir(questions_folder) if f.endswith('.mp3')])

 
def record_audio():
    """Records audio in parallel with video."""
    global audio_file, recording

    # Ensure media folder exists
    audio_folder = os.path.join(settings.MEDIA_ROOT, 'audio')
    os.makedirs(audio_folder, exist_ok=True)

    audio_file = os.path.join(audio_folder, f"interview_{int(time.time())}.wav")

    # Set audio parameters
    sample_rate = 44100  # CD-quality audio
    channels = 2          # Stereo
    duration = 5          # Will record in chunks of 5 seconds

    # Open WAV file
    with wave.open(audio_file, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        # Audio recording loop
        print("🎙️ Audio recording started...")
        while recording:
            audio_data = sd.rec(int(sample_rate * duration), samplerate=sample_rate, channels=channels, dtype='int16')
            sd.wait()
            wf.writeframes(audio_data.tobytes())

        print("🎙️ Audio recording stopped.")

# Video streaming generator
def generate_frames():
    """Generates frames for the live video feed."""
    global recording, output_file
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Could not open webcam.")
        return

    video_writer = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Display timestamp on the video
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, f"{timestamp}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Start recording if enabled
        if recording:
            if video_writer is None:
                # Ensure media folder exists
                video_folder = os.path.join(settings.MEDIA_ROOT, 'videos')
                os.makedirs(video_folder, exist_ok=True)

                output_file = os.path.join(video_folder, f"interview_{int(time.time())}.avi")
                video_writer = cv2.VideoWriter(output_file, fourcc, fps, frame_size)

            video_writer.write(frame)

        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()
    if video_writer:
        video_writer.release()

def stop_recording():
    global recording, video_writer
    recording = False
    if video_writer:
        video_writer.release()
        video_writer = None

def start_new_recording():
    global recording, output_file, video_writer, cap
    stop_recording()
    recording = True
    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(0)
    video_folder = os.path.join(settings.MEDIA_ROOT, 'videos')
    os.makedirs(video_folder, exist_ok=True)
    output_file = os.path.join(video_folder, f"answer_{current_question_index + 1}.avi")
    if video_writer:
        video_writer.release()
    video_writer = cv2.VideoWriter(output_file, fourcc, fps, frame_size)
    threading.Thread(target=record_audio, daemon=True).start()

def play_mp3_non_blocking(mp3_path):
    try:
        if os.name == 'nt':
            subprocess.Popen(["start", mp3_path], shell=True)
        else:
            subprocess.Popen(["afplay", mp3_path] if os.name == 'posix' else ["mpg123", mp3_path])
    except Exception as e:
        print(f"⚠️ Error playing MP3: {e}")

@csrf_exempt
def toggle_recording(request):
    global recording, current_question_index, cap
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == "ask_question":
            current_question_index = 0
            load_questions()
            if questions:
                play_mp3_non_blocking(questions[current_question_index])
                start_new_recording()
                return JsonResponse({"status": f"Playing question {current_question_index + 1}"})
            return JsonResponse({"status": "No questions available"})
        elif action == "next_question":
            if recording:
                recording = False
            current_question_index += 1
            if cap:
                cap.release()
                cap = None
            if current_question_index < len(questions):
                start_new_recording()
                play_mp3_non_blocking(questions[current_question_index])
                return JsonResponse({"status": f"Playing question {current_question_index + 1}", "video_file": output_file, "audio_file": audio_file})
            return JsonResponse({"status": "End Interview"})
        elif action == "end_interview":
            if recording:
                recording = False
            if cap:
                cap.release()
                cap = None
            return JsonResponse({"status": "Interview ended", "video_file": output_file, "audio_file": audio_file})
    return JsonResponse({"error": "Invalid request"}, status=400)

def video_feed(request):
    return StreamingHttpResponse(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')

def live_stream(request):
    load_questions()
    return render(request, 'interview/live_stream.html')

# View for uploading resume and generating questions
def resume_upload(request):
    if request.method == 'POST':
        resume = request.FILES.get('resume')
        job_description = request.POST.get('job_description')

        # Save resume as 'resume.pdf'
        if resume:
            resume_folder = os.path.join(settings.MEDIA_ROOT, 'resume')
            os.makedirs(resume_folder, exist_ok=True)
            resume_path = os.path.join(resume_folder, 'resume.pdf')
            
            # Save the uploaded resume
            with open(resume_path, 'wb+') as destination:
                for chunk in resume.chunks():
                    destination.write(chunk)

            # Extract resume text
            resume_text = extract_text_from_pdf(resume_path)
        
        # Save job description as 'personality.txt'
        if job_description:
            personality_folder = os.path.join(settings.MEDIA_ROOT, 'personality')
            os.makedirs(personality_folder, exist_ok=True)
            job_file = os.path.join(personality_folder, 'personality.txt')
            
            # Save the job description
            with open(job_file, 'w') as f:
                f.write(job_description)

        # ✅ Generate and save questions immediately
        print("🎯 Generating questions...")
        questions = generate_questions(resume_text, job_description)

        if questions:
            save_questions_as_mp3(questions)
            print("✅ Questions saved successfully!")

        return redirect('live_stream')

    return render(request, 'interview/resume_upload.html')

def home(request):
    return render(request, 'interview/home.html')
