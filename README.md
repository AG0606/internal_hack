# Lumen : Your AI-Powered Interview Coach

## Overview
The AI-Powered Interview Coach is a comprehensive tool designed to help individuals improve their interview skills through real-time analysis. It leverages machine learning models for facial emotion recognition, speech-to-text transcription, sentiment analysis, and response evaluation to provide actionable feedback for interview preparation.
![LUMEN](https://github.com/user-attachments/assets/f6907aed-3b1c-4a36-b9e5-623bce900793)

## Features
- **Live Facial Emotion Recognition**: Analyzes facial expressions in real-time to detect emotions during the interview.
 ![image](https://github.com/user-attachments/assets/c8d56500-c311-466e-98b0-11273bec6d9e)
- **Live Tone detection**
- <img src="https://github.com/user-attachments/assets/0bf7d20a-a5e4-479f-a370-6618344cac07" width="400" height="400">
- **Speech-to-Text Conversion**: Uses advanced transcription models to convert spoken responses into text.
- **Sentiment Analysis**: Evaluates the tone of the response to determine positivity or negativity.
- **Filler Word Detection**: Identifies unnecessary filler words that impact communication clarity.
- **Response Quality Scoring**: Compares user responses against an ideal response using a natural language processing model.





## Installation
Ensure that Python and Anaconda are installed before proceeding.

```sh
# Clone the repository
git clone https://github.com/your-repo/interview-coach.git
cd interview-coach

# Create and activate a virtual environment
conda create --name interview-coach python=3.9 -y
conda activate interview-coach

# Install dependencies
pip install -r requirements.txt
```

## Usage
Run the following command to start the AI-powered interview analysis:

```sh
python main.py
```

## Dependencies
The project requires the following libraries:
- `opencv-python`
- `fer`
- `whisper`
- `numpy`
- `spacy`
- `transformers`
- `vaderSentiment`
- `pyaudio`
- `ffmpeg`

Install them manually if necessary:
```sh
pip install opencv-python fer openai-whisper numpy spacy transformers vaderSentiment pyaudio ffmpeg
```

## Contribution
Contributions are welcome. Please follow these steps:
1. Fork the repository.
2. Create a new branch for your feature.
3. Commit your changes.
4. Push to your branch and create a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
