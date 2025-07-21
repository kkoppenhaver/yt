# YouTube Transcriberrrr

A Python command-line tool that extracts transcripts from YouTube videos with timestamps. When YouTube transcripts aren't available, it automatically falls back to local AI transcription using OpenAI's Whisper.

## Features

- ✅ Extract existing YouTube transcripts (fast)
- 🎙️ Local AI transcription fallback using Whisper
- ⏱️ Timestamps support
- 📊 Progress bars for downloads and processing
- 🧹 Automatic cleanup of temporary files
- 🎯 Multiple Whisper model sizes (tiny to large)
- 🌍 Multi-language support

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup
1. Clone or download this project
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage (with fallback)
```bash
python youtube_transcriber.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Force local transcription only
```bash
python youtube_transcriber.py "https://www.youtube.com/watch?v=VIDEO_ID" --local-only
```

### Disable local fallback (YouTube only)
```bash
python youtube_transcriber.py "https://www.youtube.com/watch?v=VIDEO_ID" --no-local
```

### Without timestamps
```bash
python youtube_transcriber.py "https://www.youtube.com/watch?v=VIDEO_ID" --no-timestamps
```

### Use different Whisper model
```bash
python youtube_transcriber.py "https://www.youtube.com/watch?v=VIDEO_ID" --model base
```

### Make it globally accessible
```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
alias yt-transcript="python /path/to/youtube_transcriber.py"

# Then use anywhere:
yt-transcript "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Options

- `url`: YouTube video URL (required)
- `-t, --timestamps`: Include timestamps in output (default: true)
- `--no-timestamps`: Exclude timestamps from output
- `-l, --local-only`: Skip YouTube transcript and use local transcription only
- `--no-local`: Disable local transcription fallback
- `--model`: Whisper model size: tiny, base, small, medium, large (default: small)
- `-h, --help`: Show help

## How it works

1. **First attempt**: Tries to fetch existing YouTube transcripts (fast)
2. **Fallback**: If no transcript exists, downloads video and transcribes locally using Whisper AI
3. **Progress indication**: Shows download and transcription progress
4. **Cleanup**: Automatically removes temporary files

## Supported URL formats

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`

## Whisper Model Sizes

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| tiny  | ~39 MB | Fastest | Good | Quick transcription |
| base  | ~74 MB | Fast | Better | Balanced |
| small | ~244 MB | Medium | Good | **Default - Good balance** |
| medium| ~769 MB | Slow | Very Good | Professional use |
| large | ~1550 MB | Slowest | Best | Maximum accuracy |

## Requirements

- Python 3.8+
- Internet connection
- ~500MB disk space (for Whisper models)

## Performance Notes

- **YouTube transcripts**: Nearly instant
- **Local transcription**: 
  - tiny model: 2-5 minutes for 10-minute video
  - base model: 3-8 minutes for 10-minute video
  - small model (default): 4-10 minutes for 10-minute video
  - larger models: proportionally slower but more accurate
- **First run**: Downloads Whisper model (one-time setup)
- **Subsequent runs**: Uses cached model (much faster)

## Dependencies

- `yt-dlp`: YouTube video downloading
- `youtube-transcript-api`: YouTube transcript extraction
- `openai-whisper`: Local AI transcription
- `tqdm`: Progress bars

## Troubleshooting

### Installation Issues

**"No module named 'torch'"**
```bash
pip install torch
```

**"Microsoft Visual C++ 14.0 is required" (Windows)**
Install Microsoft C++ Build Tools or Visual Studio.

### Runtime Issues

**"No YouTube transcript available"**
- Video has no captions/subtitles
- Will automatically fall back to local transcription

**"Video unavailable"**
- Video is private, deleted, or region-restricted
- Try a different video

**"Download failed"**
- Check internet connection
- Video might have download restrictions
- Try with `--local-only` flag

**Local transcription is slow**
- Use smaller model: `--model tiny` or `--model base`
- Default `small` model balances speed and accuracy
- Larger models are more accurate but slower

**Out of memory errors**
- Use smaller Whisper model
- Close other applications
- For very long videos, consider using cloud transcription services

## Examples

```bash
# Quick transcription with timestamps
python youtube_transcriber.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# High accuracy transcription
python youtube_transcriber.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --model large

# Only text, no timestamps
python youtube_transcriber.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --no-timestamps

# Force local transcription (skip YouTube transcript check)
python youtube_transcriber.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --local-only

# YouTube transcript only (no AI fallback)
python youtube_transcriber.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --no-local
```
