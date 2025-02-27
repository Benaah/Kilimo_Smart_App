from flask import Flask, request, jsonify
import speech_recognition as sr
from gtts import gTTS
import os
import langdetect
from pydub import AudioSegment
from pydub.playback import play

app = Flask(__name__)

# Function to generate and play Swahili speech
def speak_text(text):
    tts = gTTS(text=text, lang='sw')  # Generate speech in Swahili
    tts.save("response.mp3")  # Save the audio
    audio = AudioSegment.from_file("response.mp3", format="mp3")
    play(audio)  # Play the audio
    os.remove("response.mp3")  # Clean up

@app.route('/voice-command', methods=['POST'])
def voice_command():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Sema amri yako kwa Kiswahili...")
        recognizer.adjust_for_ambient_noise(source)

        try:
            audio = recognizer.listen(source)
            command = recognizer.recognize_google(audio, language='sw-KE')  # Swahili recognition
            detected_lang = langdetect.detect(command)

            if detected_lang != 'sw':
                response_text = "Samahani, tafadhali ongea kwa Kiswahili."
            else:
                response_text = process_command(command)

            speak_text(response_text)
            return jsonify({'message': response_text})

        except sr.UnknownValueError:
            return jsonify({'message': "Samahani, sikuelewa. Tafadhali jaribu tena."})
        except sr.RequestError:
            return jsonify({'message': "Hitilafu ya mtandao. Tafadhali angalia muunganisho wako wa intaneti."})

# Function to process recognized Swahili command
def process_command(command):
    command = command.lower()

    if "hali ya hewa" in command:
        return "Hali ya hewa inachakatwa..."
    elif "udongo" in command:
        return "Ramani ya udongo inafunguliwa..."
    elif "shamba" in command:
        return "Inaonyesha chaguzi za upangaji wa ardhi..."
    elif "soko" in command:
        return "Soko linafunguliwa..."
    elif "ugonjwa" in command:
        return "Taarifa kuhusu magonjwa ya mimea zinapatikana..."
    else:
        return "Samahani, siwezi kutambua amri hiyo."

if __name__ == '__main__':
    app.run(debug=True)
