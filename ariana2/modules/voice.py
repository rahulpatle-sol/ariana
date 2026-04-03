"""
voice.py — edge-tts (Microsoft Neural) Indian girl voice
         + sounddevice STT (no PyAudio needed)
"""
import asyncio
import threading
import subprocess
import tempfile
import os

# Best Indian female voices (edge-tts)
VOICES = {
    "neerja":  "en-IN-NeerjaNeural",      # Natural Indian girl ✅
    "prabhat": "hi-IN-SwaraNeural",        # Hindi female
    "aria":    "en-IN-NeerjaExpressiveNeural",  # Expressive
}
CURRENT_VOICE = "neerja"
_speaking_proc = None

def speak(text, voice=None, blocking=False):
    """Speak using Microsoft Neural TTS — very natural"""
    global _speaking_proc

    # Stop current
    stop()

    # Clean text
    clean = text.replace("```", "").replace("**","").replace("*","").replace("#","")
    clean = clean[:500]

    voice_name = VOICES.get(voice or CURRENT_VOICE, VOICES["neerja"])

    def _do():
        global _speaking_proc
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            tmp_path = tmp.name
            tmp.close()

            # Generate speech with edge-tts
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def _gen():
                import edge_tts
                tts = edge_tts.Communicate(clean, voice_name, rate="+8%", pitch="+2Hz")
                await tts.save(tmp_path)

            loop.run_until_complete(_gen())
            loop.close()

            # Play with mpg123 or mpv
            for player in ["mpg123", "mpv", "ffplay"]:
                if _which(player):
                    if player == "mpg123":
                        _speaking_proc = subprocess.Popen(
                            [player, "-q", tmp_path],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                        )
                    elif player == "mpv":
                        _speaking_proc = subprocess.Popen(
                            [player, "--no-video", "--really-quiet", tmp_path],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                        )
                    else:
                        _speaking_proc = subprocess.Popen(
                            [player, "-nodisp", "-autoexit", "-loglevel", "quiet", tmp_path],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                        )
                    _speaking_proc.wait()
                    break
            else:
                # Fallback espeak-ng Indian
                subprocess.run(["espeak-ng", "-v", "en-in+f3", "-s", "155", "-p", "62", clean],
                               capture_output=True)

            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        except Exception as e:
            # Fallback
            try:
                subprocess.run(["espeak-ng", "-v", "en-in+f3", "-s", "150", clean],
                               capture_output=True)
            except Exception:
                pass

    if blocking:
        _do()
    else:
        t = threading.Thread(target=_do, daemon=True)
        t.start()
        return t

def stop():
    """Stop current speech immediately"""
    global _speaking_proc
    if _speaking_proc:
        try:
            _speaking_proc.terminate()
            _speaking_proc = None
        except Exception:
            pass
    subprocess.run(["pkill", "-f", "mpg123"], capture_output=True)
    subprocess.run(["pkill", "-f", "mpv.*mp3"], capture_output=True)
    subprocess.run(["pkill", "espeak-ng"], capture_output=True)

def listen_once(timeout=6):
    """Listen from mic — uses sounddevice (no PyAudio needed)"""
    try:
        import speech_recognition as sr
        import sounddevice  # just to verify it works

        r = sr.Recognizer()
        r.energy_threshold = 200
        r.dynamic_energy_threshold = True
        r.pause_threshold = 0.8

        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.3)
            audio = r.listen(source, timeout=timeout, phrase_time_limit=10)

        # Try Google (needs internet)
        try:
            return r.recognize_google(audio, language="hi-IN")
        except Exception:
            try:
                return r.recognize_google(audio, language="en-IN")
            except Exception:
                return ""
    except OSError as e:
        # Mic not available
        return f"MIC_ERROR:{e}"
    except Exception as e:
        return f"ERROR:{e}"

def _which(cmd):
    return subprocess.run(["which", cmd], capture_output=True).returncode == 0
