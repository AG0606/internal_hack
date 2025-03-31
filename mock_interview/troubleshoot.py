import sounddevice as sd

print("\n🎙️ Available Audio Devices:")
print(sd.query_devices())