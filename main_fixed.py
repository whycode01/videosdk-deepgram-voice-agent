#!/usr/bin/env python3
"""
VideoSDK realtime AI Agent | Interviewer
"""
import os
import asyncio
import signal
import traceback
import logging
from agent.audio_stream_track import CustomAudioStreamTrack
from tts.deepgram_tts import DeepgramTTS
from intelligence.groq_intelligence import GroqIntelligence
from stt.deepgram_stt import DeepgramSTT
from agent.agent import AIInterviewer
from dotenv import load_dotenv

load_dotenv()
loop = asyncio.new_event_loop()
room_id = os.getenv("ROOM_ID")
auth_token = os.getenv("AUTH_TOKEN")
language = os.getenv("LANGUAGE", "en-US")
stt_api_key = os.getenv("DEEPGRAM_API_KEY")
tts_api_key = os.getenv("ELEVENLABS_API_KEY")
llm_api_key = os.getenv("GROQ_API_KEY")
agent: AIInterviewer = None
stopped: bool = False

class Bcolors:
    """Color class for terminal output"""
    HEADER = '\033[95m'
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'

async def run():
    """Main function"""
    global agent
    try:
        print("Loading AI Agent...")
        # audio player
        audio_track = CustomAudioStreamTrack(
            loop=loop,
            handle_interruption=True,
        )

        tts_client = DeepgramTTS(
            api_key=stt_api_key,
            output_track=audio_track,
        )
        
        # intelligence client
        intelligence_client = GroqIntelligence( 
            api_key=llm_api_key, 
            model="openai/gpt-oss-120b", 
            tts=tts_client,
            system_prompt=(
                "You are an AI Copilot in a meeting. Keep responses short and engaging. "
                "Start by introducing yourself: 'Hi, I'm your AI Copilot!'. "
                "If asked, explain how you work briefly: 'I process speech using Deepgram STT and reply using Groq LLM.' "
                "Keep the conversation interactive and avoid long responses unless explicitly requested."
            )
        )

        # stt client
        stt_client = DeepgramSTT(
            loop=loop,
            api_key=stt_api_key,
            language=language,
            intelligence=intelligence_client
        )

        agent = AIInterviewer(
            loop=loop, 
            audio_track=audio_track, 
            stt=stt_client, 
            intelligence=intelligence_client
        )
       
        await agent.join(meeting_id=room_id, token=auth_token)

    except Exception as e:
        traceback.print_exc()
        print("Error while joining:", e)
    

async def destroy():
    """Delete character peer"""
    global agent
    global stopped
    print("Destroying AI Agent...")
    if agent is not None and not stopped:
        stopped = True
        await agent.leave()
        agent = None

def sigterm_handler(signum, frame):
    """Signal term handler"""
    print("EXITING with signal:", signum)
    asyncio.create_task(destroy())
    loop.stop()
    loop.close()

def main():
    """Main entry point"""
    try:
        # Configure the logging module to capture logs from built-in modules and save to a file
        logging.basicConfig(
            filename='logfile.log',
            filemode='w', 
            level=logging.DEBUG
        )

        # Register the SIGTERM handler
        signal.signal(signal.SIGTERM, sigterm_handler)
        # Register the SIGINT handler
        signal.signal(signal.SIGINT, sigterm_handler)

        loop.run_until_complete(run())
        loop.run_forever()
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        loop.run_until_complete(destroy())

if __name__ == "__main__":
    main()
