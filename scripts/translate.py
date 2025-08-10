import argparse
import os
import re
from openai import OpenAI


def parse_srt(srt_content):
    """Parse SRT content into a list of subtitle entries."""
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\d+\n|\n*$)"
    matches = re.findall(pattern, srt_content, re.DOTALL)

    subtitles = []
    for match in matches:
        subtitles.append(
            {
                "index": int(match[0]),
                "start": match[1],
                "end": match[2],
                "text": match[3].strip(),
            }
        )
    return subtitles


def format_srt(subtitles):
    """Format subtitle entries back to SRT format."""
    srt_content = ""
    for sub in subtitles:
        srt_content += f"{sub['index']}\n"
        srt_content += f"{sub['start']} --> {sub['end']}\n"
        srt_content += f"{sub['text']}\n\n"
    return srt_content


def translate_text(client, text, target_language):
    """Translate text using OpenAI GPT."""
    language_names = {
        "fr": "French",
        "es": "Spanish",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "ar": "Arabic",
    }

    target_lang_name = language_names.get(target_language, target_language)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": f"You are a professional translator. Translate the following text to {target_lang_name}. Maintain the original meaning and tone. Only return the translated text, nothing else.",
            },
            {"role": "user", "content": text},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Generate and translate audio subtitles using OpenAI Whisper and GPT."
    )
    parser.add_argument("audio_path", help="Path to input audio file (e.g., audio.wav)")
    parser.add_argument("srt_output", help="Path to output SRT file")
    parser.add_argument(
        "--target-language",
        "-t",
        default="en",
        help="Target language code (en, fr, es, de, it, pt, ru, ja, ko, zh, ar). Default: en (English transcription)",
    )
    parser.add_argument(
        "--mode",
        "-m",
        choices=["transcribe", "translate"],
        default="transcribe",
        help="Mode: 'transcribe' for original language transcription, 'translate' for English translation via Whisper",
    )

    args = parser.parse_args()

    # Initialize OpenAI client with API key from environment or hardcoded fallback
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    # Step 1: Get transcription or translation from Whisper
    with open(args.audio_path, "rb") as audio_file:
        if args.mode == "translate":
            print("Sending audio to Whisper for translation to English...")
            transcript = client.audio.translations.create(
                model="whisper-1", file=audio_file, response_format="srt"
            )
        else:
            print("Sending audio to Whisper for transcription...")
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file, response_format="srt"
            )

    # Step 2: If target language is not English, translate the text
    if args.target_language != "en":
        print(f"Translating subtitles to {args.target_language}...")

        # Parse the SRT content
        subtitles = parse_srt(transcript)

        # Translate each subtitle text
        for i, subtitle in enumerate(subtitles):
            print(f"Translating subtitle {i+1}/{len(subtitles)}...")
            subtitle["text"] = translate_text(
                client, subtitle["text"], args.target_language
            )

        # Format back to SRT
        transcript = format_srt(subtitles)

    # Step 3: Save the final result
    with open(args.srt_output, "w", encoding="utf-8") as f:
        f.write(transcript)

    language_desc = args.target_language if args.target_language != "en" else "English"
    print(f"✅ Subtitle saved to {args.srt_output} in {language_desc}")


if __name__ == "__main__":
    main()
