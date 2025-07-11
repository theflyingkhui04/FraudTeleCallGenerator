#!/usr/bin/env python3
"""
Quick TTS Library Test
"""

print("=== TTS Library Availability Test ===")

# Test 1: gTTS (Google Text-to-Speech)
try:
    from gtts import gTTS
    print("✓ gTTS (Google TTS): AVAILABLE")
    gtts_available = True
except ImportError as e:
    print(f"✗ gTTS: NOT AVAILABLE - {e}")
    gtts_available = False

# Test 2: pyttsx3 (Offline TTS)
try:
    import pyttsx3
    print("✓ pyttsx3 (Offline TTS): AVAILABLE")
    pyttsx3_available = True
except ImportError as e:
    print(f"✗ pyttsx3: NOT AVAILABLE - {e}")
    pyttsx3_available = False

print("\n=== Installation Commands ===")
if not gtts_available:
    print("Install gTTS: pip install gtts")
if not pyttsx3_available:
    print("Install pyttsx3: pip install pyttsx3")

print("\n=== Current Status ===")
if gtts_available or pyttsx3_available:
    print("✓ At least one TTS engine is available")
    preferred = "gTTS" if gtts_available else "pyttsx3"
    print(f"✓ Preferred engine: {preferred}")
else:
    print("✗ No TTS engines available - will use mock audio")
    print("⚠️  Audio files will contain sine wave, not speech")

# Test 3: Quick TTS generation if available
if gtts_available:
    print("\n=== Quick gTTS Test ===")
    try:
        import io
        tts = gTTS(text="Xin chào", lang='vi')
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_size = len(audio_buffer.getvalue())
        print(f"✓ gTTS test successful - Generated {audio_size} bytes of audio")
    except Exception as e:
        print(f"✗ gTTS test failed: {e}")

if pyttsx3_available:
    print("\n=== Quick pyttsx3 Test ===")
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        print(f"✓ pyttsx3 test successful - Found {len(voices) if voices else 0} voices")
        if voices:
            for i, voice in enumerate(voices[:3]):  # Show first 3 voices
                print(f"  Voice {i}: {voice.name} ({voice.id})")
    except Exception as e:
        print(f"✗ pyttsx3 test failed: {e}")

print("\n" + "="*50)
