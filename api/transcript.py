from http.server import BaseHTTPRequestHandler
from youtube_transcript_api import YouTubeTranscriptApi
import json
import re

ytt_api = YouTubeTranscriptApi()


def parse_youtube_id(url):
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/shorts/)([\w-]{11})',
        r'youtube\.com/v/([\w-]{11})',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    if re.match(r'^[\w-]{11}$', url):
        return url
    return None


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        data = json.loads(body) if body else {}
        url = data.get('url', '')

        video_id = parse_youtube_id(url)
        if not video_id:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Could not parse YouTube URL'}).encode())
            return

        try:
            transcript = ytt_api.fetch(video_id)
            full_text = ' '.join([entry.text for entry in transcript])
            result = {
                'video_id': video_id,
                'transcript': full_text,
                'segments': [{'text': e.text, 'start': e.start, 'duration': e.duration} for e in transcript],
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
