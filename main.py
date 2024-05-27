import os
import datetime
from openai import OpenAI
from elevenlabs.client import ElevenLabs, Voice
from elevenlabs import stream
import argparse
from dataclasses import asdict
from models import Message
import speech_recognition as sr
import logging
from pathlib import Path
logging.basicConfig(level=logging.INFO)
import dotenv
dotenv.load_dotenv('.env')

oai_client = OpenAI()
elevenlabs_client = ElevenLabs()

CHAT_MODEL = "gpt-4o"
TTS_MODEL = "tts-1"
MODEL_TEMPERATURE = 0.5
AUDIO_MODEL = "whisper-1"
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

def ask_gpt_chat(prompt: str, messages: list[Message]):
    """Returns ChatGPT's response to the given prompt."""
    system_message = [{"role": "system", "content": prompt}]
    message_dicts = [asdict(message) for message in messages]
    conversation_messages = system_message + message_dicts
    response = oai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=conversation_messages,
        temperature=MODEL_TEMPERATURE
    )
    return response.choices[0].message.content

def setup_prompt(prompt_file: str = 'prompts/vet_prompt.md') -> str:
    """Creates a prompt for gpt for generating a response."""
    with open(prompt_file) as f:
        prompt = f.read()

    return prompt

def get_transcription(file_path: str):
    audio_file= open(file_path, "rb")
    transcription = oai_client.audio.transcriptions.create(
        model=AUDIO_MODEL, 
        file=audio_file
    )
    return transcription.text

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
        f.write(transcript)
    return transcript

def oai_text_to_speech(text: str):
    timestamp = datetime.datetime.now().timestamp()
    speech_file_path = Path(__file__).parent / f"outputs/{timestamp}.mp3"
    response = oai_client.audio.speech.create(
        model=TTS_MODEL,
        voice="nova",
        input=text
    )
    response.write_to_file(speech_file_path)
    return speech_file_path

def elevenlabs_text_to_speech(text: str):
    audio_stream = elevenlabs_client.generate(
        text=text,
        voice=Voice(
            voice_id=VOICE_ID
        ),
        stream=True
    )
    stream(audio_stream)

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
    parser.add_argument("-tts", "--tts_type", help="Specify the TTS type to use.", type=str, default="openai", choices=["openai", "elevenlabs"])
    args = parser.parse_args()
    prompt_file = args.prompt_file
    tts_type = args.tts_type or "openai"

    prompt = setup_prompt(prompt_file)
    conversation_messages = []
    while True:
        try:
            user_input = record()
            logging.info(f'Receiver: {user_input}')
            conversation_messages.append(Message(role="user", content=user_input))
            answer = ask_gpt_chat(prompt, conversation_messages)
            logging.info(f'Caller: {answer}')
            logging.info('Playing audio...')
            if tts_type == "elevenlabs":
                elevenlabs_text_to_speech(answer)
            else:
                audio_file = oai_text_to_speech(answer)
                # Play the audio file
                os.system(f"afplay {audio_file}")
            conversation_messages.append(Message(role="assistant", content=answer))
            if 'bye' in user_input.lower():
                clean_up()
                break
        except KeyboardInterrupt:
            clean_up()
            break