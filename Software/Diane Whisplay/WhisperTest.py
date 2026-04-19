from faster_whisper import WhisperModel

model_size = "tiny.en"

# Run on GPU with FP16
# model = WhisperModel(model_size, device="cuda", compute_type="float16")

# or run on GPU with INT8
# model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
# or run on CPU with INT8
model = WhisperModel(model_size, device="cpu", compute_type="int8")

segments, info = model.transcribe("foobar.mp3", beam_size=5)

print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
segments = list(segments)  # The transcription will actually run here.


for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))