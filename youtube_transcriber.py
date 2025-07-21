#!/usr/bin/env python3
"""
YouTube Transcriber
A command-line tool to extract transcripts from YouTube videos with timestamps.
Falls back to local transcription when YouTube transcripts aren't available.
"""

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import subprocess
import json

try:
    import yt_dlp
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled, 
        NoTranscriptFound, 
        VideoUnavailable
    )
    import whisper
    from tqdm import tqdm
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install dependencies with: pip install -r requirements.txt")
    sys.exit(1)


class YouTubeTranscriber:
    def __init__(self):
        self.temp_dir = None
        
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL."""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def is_valid_youtube_url(self, url: str) -> bool:
        """Check if URL is a valid YouTube URL."""
        return self.extract_video_id(url) is not None
    
    def format_timestamp(self, seconds: float) -> str:
        """Format timestamp from seconds to HH:MM:SS or MM:SS format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
    
    def get_youtube_transcript(self, video_id: str) -> List[Dict]:
        """Fetch transcript directly from YouTube."""
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to get English transcript first
            try:
                transcript = transcript_list.find_transcript(['en'])
            except:
                # If no English, get the first available
                available_transcripts = list(transcript_list._transcript_data.keys())
                if available_transcripts:
                    transcript = transcript_list.find_transcript([available_transcripts[0]])
                else:
                    raise Exception("No transcripts available")
            
            # Fetch the transcript data
            transcript_data = transcript.fetch()
            
            # Convert to our expected format
            formatted_transcript = []
            for item in transcript_data:
                formatted_transcript.append({
                    'text': item['text'],
                    'start': item['start'],
                    'duration': item.get('duration', 0)
                })
            
            return formatted_transcript
            
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
            raise Exception(f"No YouTube transcript available: {str(e)}")
        except Exception as e:
            raise Exception(f"Error fetching transcript: {str(e)}")
    
    def download_audio(self, url: str, output_path: str) -> str:
        """Download audio from YouTube video."""
        print("📥 Downloading audio...")
        
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio',
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
        }
        
        class ProgressHook:
            def __init__(self):
                self.pbar = None
                
            def __call__(self, d):
                if d['status'] == 'downloading':
                    if self.pbar is None:
                        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                        if total > 0:
                            self.pbar = tqdm(total=total, unit='B', unit_scale=True, desc="Download")
                    
                    if self.pbar:
                        downloaded = d.get('downloaded_bytes', 0)
                        self.pbar.update(downloaded - self.pbar.n)
                        
                elif d['status'] == 'finished':
                    if self.pbar:
                        self.pbar.close()
                    print("✅ Download completed")
        
        progress_hook = ProgressHook()
        ydl_opts['progress_hooks'] = [progress_hook]
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Find the downloaded file
            base_path = output_path.replace('.%(ext)s', '')
            for ext in ['.m4a', '.webm', '.mp4', '.mp3']:
                potential_path = base_path + ext
                if os.path.exists(potential_path):
                    return potential_path
            
            raise Exception("Downloaded file not found")
            
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")
    
    def transcribe_audio_local(self, audio_path: str, model_size: str = "small") -> List[Dict]:
        """Transcribe audio using OpenAI Whisper."""
        print("🎙️  Initializing Whisper model...")
        
        try:
            # Load Whisper model
            print(f"🔄 Loading Whisper '{model_size}' model (this may take a while on first run)...")
            model = whisper.load_model(model_size)
            
            print("📝 Transcribing audio...")
            result = model.transcribe(audio_path, verbose=False)
            
            # Show detected language
            if 'language' in result:
                print(f"🌍 Detected language: {result['language'].title()}")
            
            # Convert to our format with timestamps
            segments = []
            for segment in result['segments']:
                segments.append({
                    'text': segment['text'].strip(),
                    'start': segment['start'],
                    'duration': segment['end'] - segment['start']
                })
            
            return segments
            
        except Exception as e:
            raise Exception(f"Local transcription failed: {str(e)}")
    
    def local_transcription(self, url: str, options: Dict) -> List[Dict]:
        """Perform local transcription of YouTube video."""
        self.temp_dir = tempfile.mkdtemp()
        video_id = self.extract_video_id(url)
        audio_path = os.path.join(self.temp_dir, f"{video_id}.%(ext)s")
        
        try:
            # Download audio
            downloaded_path = self.download_audio(url, audio_path)
            
            # Transcribe
            segments = self.transcribe_audio_local(downloaded_path, options.get('model', 'small'))
            
            return segments
            
        except Exception as e:
            raise e
        finally:
            # Cleanup
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def print_transcript(self, segments: List[Dict], show_timestamps: bool = True, source: str = ""):
        """Print formatted transcript."""
        if source:
            print(f"\nTranscript (Source: {source})\n")
        else:
            print(f"\nTranscript\n")
        
        print("=" * 60)
        
        for segment in segments:
            if 'start' in segment:
                # Local transcription format
                timestamp = self.format_timestamp(segment['start'])
                text = segment['text']
            else:
                # YouTube transcript format
                timestamp = self.format_timestamp(segment.get('start', 0))
                text = segment.get('text', '')
            
            if show_timestamps:
                print(f"[{timestamp}] {text}")
            else:
                print(text)
        
        print("\n" + "=" * 60)
        print(f"Total segments: {len(segments)}")
    
    def get_transcript(self, url: str, options: Dict):
        """Main function to get transcript with fallback."""
        if not self.is_valid_youtube_url(url):
            raise Exception("Invalid YouTube URL provided")
        
        video_id = self.extract_video_id(url)
        print(f"Processing video: {video_id}")
        
        # Try YouTube transcript first (unless local-only)
        if not options.get('local_only', False):
            try:
                print("🔍 Checking for YouTube transcript...")
                segments = self.get_youtube_transcript(video_id)
                
                self.print_transcript(segments, options.get('timestamps', True), "YouTube")
                return
                
            except Exception as e:
                if options.get('no_local', False):
                    raise Exception(f"No transcript available: {str(e)}")
                
                print(f"⚠️  {str(e)}")
                print("🔄 Falling back to local transcription...")
        
        # Local transcription
        try:
            segments = self.local_transcription(url, options)
            self.print_transcript(segments, options.get('timestamps', True), "Local AI")
            
        except Exception as e:
            raise Exception(f"Local transcription failed: {str(e)}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract transcripts from YouTube videos with timestamps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  %(prog)s "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --no-timestamps
  %(prog)s "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --local-only
  %(prog)s "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --model base
        """
    )
    
    parser.add_argument('url', help='YouTube video URL')
    parser.add_argument('-t', '--timestamps', action='store_true', default=True,
                       help='Include timestamps in output (default: true)')
    parser.add_argument('--no-timestamps', action='store_true',
                       help='Exclude timestamps from output')
    parser.add_argument('-l', '--local-only', action='store_true',
                       help='Skip YouTube transcript and use local transcription only')
    parser.add_argument('--no-local', action='store_true',
                       help='Disable local transcription fallback')
    parser.add_argument('--model', choices=['tiny', 'base', 'small', 'medium', 'large'],
                       default='small', help='Whisper model size for local transcription (default: small)')
    
    args = parser.parse_args()
    
    # Handle timestamp options
    if args.no_timestamps:
        args.timestamps = False
    
    options = {
        'timestamps': args.timestamps,
        'local_only': args.local_only,
        'no_local': args.no_local,
        'model': args.model
    }
    
    transcriber = YouTubeTranscriber()
    
    try:
        transcriber.get_transcript(args.url, options)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()