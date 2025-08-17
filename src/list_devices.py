import sounddevice as sd

def main():
    print("Available audio devices:")
    devices = sd.query_devices()
    for i, dev in enumerate(devices):
        print(f"{i}: {dev['name']} (input channels: {dev['max_input_channels']})")

if __name__ == "__main__":
    main()
