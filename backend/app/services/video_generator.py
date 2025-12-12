import os
import logging
from typing import Dict, Optional
from datetime import datetime
import textwrap

logger = logging.getLogger(__name__)

try:
    from moviepy.editor import (
        AudioFileClip, ImageClip
    )
    from PIL import Image, ImageDraw, ImageFont
    from gtts import gTTS
    MOVIEPY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Video dependencies missing: {e}")
    MOVIEPY_AVAILABLE = False

class VideoGenerator:
    """Generate videos from articles using MoviePy and gTTS"""
    
    def __init__(self, output_dir: str = "app/static/videos"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
    def is_available(self) -> bool:
        return MOVIEPY_AVAILABLE

    async def generate_video_from_article(
        self,
        article: Dict,
        platform: str = "youtube"  # "youtube" or "tiktok"
    ) -> Optional[str]:
        """Generate video from blog article
        
        Args:
            article: Blog article dictionary with title, content, excerpt, slug
            platform: "youtube" or "tiktok"
            
        Returns:
            Path to generated video file, or None if generation fails
        """
        if not self.is_available():
            logger.warning("Video generation unavailable: Missing dependencies")
            return None
            
        try:
            title = article.get('title', 'Reporte FactCheckr')
            # Use excerpt or summary for audio script
            text = article.get('excerpt') or article.get('content', '')[:500]
            
            # 1. Generate Audio
            audio_path = self._generate_audio(text, lang='es')
            if not audio_path:
                return None
                
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            # 2. Create Video visuals
            # YouTube: 1280x720 (16:9)
            # TikTok: 720x1280 (9:16)
            
            if platform == "tiktok":
                w, h = 720, 1280
            else:
                w, h = 1280, 720
                
            # Create a slide image using PIL (safer than TextClip which needs ImageMagick)
            img_path = self._create_slide_image(title, text[:200] + "...", w, h)
            
            # Create video clip from image
            video_clip = ImageClip(img_path).set_duration(duration).set_fps(24)
            
            # Set audio
            final_clip = video_clip.set_audio(audio_clip)
            
            # Output filename
            slug = article.get('slug', 'video')
            filename = f"{slug}_{platform}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
            output_path = os.path.join(self.output_dir, filename)
            
            # Write video file
            # using 'fast' preset for speed
            final_clip.write_videofile(
                output_path, 
                fps=24, 
                codec='libx264', 
                audio_codec='aac',
                preset='ultrafast',
                logger=None # Silence standard logger
            )
            
            # Cleanup temp files
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                if os.path.exists(img_path):
                    os.remove(img_path)
            except Exception as e:
                logger.warning(f"Error cleaning up temp files: {e}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Video generation error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _generate_audio(self, text: str, lang: str = 'es') -> Optional[str]:
        try:
            # Use gTTS
            tts = gTTS(text=text, lang=lang, slow=False)
            filename = f"temp_audio_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
            path = os.path.join(self.output_dir, filename)
            tts.save(path)
            return path
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None

    def _create_slide_image(self, title: str, body: str, w: int, h: int) -> str:
        # Use PIL
        # Background: Dark Blue
        img = Image.new('RGB', (w, h), color=(13, 27, 42)) # #0d1b2a
        draw = ImageDraw.Draw(img)
        
        # Load fonts
        try:
            # Try efficient defaults if available
            font_title = ImageFont.truetype("Arial", int(h/10))
            font_body = ImageFont.truetype("Arial", int(h/20))
        except IOError:
            font_title = ImageFont.load_default()
            font_body = ImageFont.load_default()
            
        # Draw Title (Centered top)
        # Using simple layout
        margin = int(w * 0.1)
        
        # Title wrap
        chars_per_line_title = int(w / (int(h/10) * 0.6))
        title_lines = textwrap.wrap(title, width=chars_per_line_title)
        
        y = int(h * 0.1)
        for line in title_lines:
            # Naive centering
            draw.text((margin, y), line, font=font_title, fill="#E0E1DD")
            y += int(h/8)
            
        # Draw Body
        y += int(h/20)
        chars_per_line_body = int((w - 2*margin) / (int(h/20) * 0.5))
        body_lines = textwrap.wrap(body, width=chars_per_line_body)
        
        for line in body_lines[:10]: # Limit lines
            draw.text((margin, y), line, font=font_body, fill="#778DA9")
            y += int(h/15)
            
        # Add branding
        draw.text((margin, h - int(h/10)), "FactCheckr MX", font=font_body, fill="#415A77")
            
        filename = f"temp_slide_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        path = os.path.join(self.output_dir, filename)
        img.save(path)
        return path
