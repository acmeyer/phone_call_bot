import os
import datetime
import openai
import argparse
from dataclasses import asdict
from models import Message
import speech_recognition as sr
import logging
logging.basicConfig(level=logging.INFO)
import dotenv
dotenv.load_dotenv('.env')
import requests

CHAT_MODEL = "gpt-3.5-turbo"
MODEL_TEMPERATURE = 0.5
AUDIO_MODEL = "whisper-1"
ELEVEN_LABS_API_KEY = os.getenv('ELEVEN_LABS_API_KEY')
ELEVEN_LABS_VOICE_ID = os.getenv('ELEVEN_LABS_VOICE_ID')

def ask_gpt3_chat(prompt: str, messages: list[Message]):
    """Returns ChatGPT-3's response to the given prompt."""
    system_message = [{"role": "system", "content": prompt}]
    message_dicts = [asdict(message) for message in messages]
    conversation_messages = system_message + message_dicts
    response = openai.ChatCompletion.create(
        model=CHAT_MODEL,
        messages=conversation_messages,
        temperature=MODEL_TEMPERATURE
    )
    return response.choices[0]['message']['content'].strip()

def setup_prompt(prompt_file: str = 'prompts/vet_prompt.md') -> str:
    """Creates a prompt for gpt-3 for generating a response."""
    with open(prompt_file) as f:
        prompt = f.read()

    return prompt

def get_transcription(file_path: str):
    audio_file= open(file_path, "rb")
    return openai.Audio.transcribe(
        model=AUDIO_MODEL, 
        file=audio_file
    )

def record():
    # load the speech recognizer with CLI settings
    r = sr.Recognizer()

    # record audio stream from multiple sources
    m = sr.Microphone()

    with m as source:
        r.adjust_for_ambient_noise(source)
        logging.info(f'Listening...')
        audio = r.listen(source)

    # write audio to a WAV file
    timestamp = datetime.datetime.now().timestamp()
    with open(f"./recordings/{timestamp}.wav", "wb") as f:
        f.write(audio.get_wav_data())
    transcript = get_transcription(f"./recordings/{timestamp}.wav")
    with open(f"./transcripts/{timestamp}.txt", "w") as f:
        f.write(transcript['text'])
    return transcript['text']

def text_to_speech(text: str):
    url = f'https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_LABS_VOICE_ID}'
    headers = {
        'accept': 'audio/mpeg',
        'xi-api-key': ELEVEN_LABS_API_KEY,
        'Content-Type': 'application/json'
    }
    data = {
        'text': text,
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.25
        }
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        timestamp = datetime.datetime.now().timestamp()
        with open(f"outputs/{timestamp}.mp3", "wb") as out:
            # Write the response to the output file.
            out.write(response.content)
        return f"outputs/{timestamp}.mp3"
    else:
        return None

def clean_up():
    logging.info('Exiting...')
    # Delete all the recordings and transcripts
    for file in os.listdir('./recordings'):
        os.remove(f"./recordings/{file}")
    for file in os.listdir('./transcripts'):
        os.remove(f"./transcripts/{file}")
    for file in os.listdir('./outputs'):
        os.remove(f"./outputs/{file}")
    # Save the conversation
    timestamp = datetime.datetime.now().timestamp()
    with open(f'logs/conversation_{timestamp}.txt', 'w') as f:
        for message in conversation_messages:
            f.write(f"{message.role}: {message.content}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-pf", "--prompt_file", help="Specify the prompt file to use.", type=str)
    args = parser.parse_args()
    prompt_file = args.prompt_file
    
    prompt = setup_prompt(prompt_file)
    conversation_messages = []
    while True:
        try:
            user_input = record()
            logging.info(f'Receiver: {user_input}')
            conversation_messages.append(Message(role="user", content=user_input))
            answer = ask_gpt3_chat(prompt, conversation_messages)
            logging.info(f'Caller: {answer}')
            logging.info('Playing audio...')
            audio_file = text_to_speech(answer)
            # Play the audio file
            os.system(f"afplay {audio_file}")
            conversation_messages.append(Message(role="assistant", content=answer))
            if 'bye' in user_input.lower():
                clean_up()
                break
        except KeyboardInterrupt:
            clean_up()
            break