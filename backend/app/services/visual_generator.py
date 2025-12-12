import os
import textwrap
import logging
from datetime import datetime
from typing import Optional, Dict

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import io
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

logger = logging.getLogger(__name__)

class VisualGenerator:
    """Service to generate visual assets for social media"""
    
    def __init__(self, output_dir: str = "app/static/generated"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        # Design configuration
        self.colors = {
            "Verified": "#2E7D32",   # Green
            "Debunked": "#C62828",   # Red
            "Misleading": "#EF6C00", # Orange
            "Unverified": "#616161", # Grey
            "background": "#FFFFFF",
            "text": "#000000"
        }
        
    def generate_verdict_card(self, claim_text: str, verdict: str, explanation: Optional[str] = None, sources: Optional[list] = None) -> Optional[str]:
        """Generate a social media card with the fact-check verdict"""
        if not PIL_AVAILABLE:
            logger.warning("Pillow not available. Cannot generate images.")
            return None
            
        try:
            # Create base image (Twitter post size: 1080x1080 or 1200x675)
            # Using 1200x675 for standard landscape
            width, height = 1200, 675
            img = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Map verdict to proper Spanish if needed, or keep English but styled
            verdict_map = {
                "Verified": "VERDADERO",
                "Debunked": "FALSO",
                "Misleading": "ENGAÑOSO",
                "Unverified": "NO VERIFICADO"
            }
            display_verdict = verdict_map.get(verdict, verdict.upper())
            
            # Draw header bar
            header_height = 80
            header_color = self.colors.get(verdict, "#000000")
            draw.rectangle([(0, 0), (width, header_height)], fill=header_color)
            
            # Draw Logo/Brand in header (Placeholder text)
            try:
                # Try to load a font, fall back to default
                font_header = ImageFont.truetype("Arial", 40)
            except IOError:
                font_header = ImageFont.load_default()
                
            draw.text((30, 20), "FactCheckr MX", fill="white", font=font_header)
            draw.text((width - 250, 20), datetime.now().strftime("%d/%m/%Y"), fill="white", font=font_header)
            
            # Draw Verdict Title
            try:
                font_verdict = ImageFont.truetype("Arial", 80)
            except IOError:
                font_verdict = ImageFont.load_default()
            
            # Center verdict text relative to image, below header
            # Using textbbox to get dimensions (left, top, right, bottom)
            bbox = draw.textbbox((0, 0), display_verdict, font=font_verdict)
            text_w = bbox[2] - bbox[0]
            draw.text(((width - text_w) / 2, 130), display_verdict, fill=header_color, font=font_verdict)
            
            # Draw Claim Text
            try:
                font_claim = ImageFont.truetype("Arial", 36)
            except IOError:
                font_claim = ImageFont.load_default()
                
            # Wrap text
            claim_lines = textwrap.wrap(f"\"{claim_text}\"", width=50) # Approx chars
            y_text = 250
            for line in claim_lines:
                bbox = draw.textbbox((0, 0), line, font=font_claim)
                text_w = bbox[2] - bbox[0]
                draw.text(((width - text_w) / 2, y_text), line, font=font_claim, fill="black")
                y_text += 45
                
            # Draw Explanation if exists
            if explanation:
                y_text += 40
                try:
                    font_expl = ImageFont.truetype("Arial", 28)
                except IOError:
                    font_expl = ImageFont.load_default()
                    
                expl_lines = textwrap.wrap(explanation, width=70)
                for line in expl_lines[:4]: # Limit lines
                    bbox = draw.textbbox((0, 0), line, font=font_expl)
                    text_w = bbox[2] - bbox[0]
                    draw.text(((width - text_w) / 2, y_text), line, font=font_expl, fill="#555555")
                    y_text += 35

            # Draw Sources if provided (Transparency Footer)
            if sources:
                y_text = height - 60  # Position near bottom
                try:
                    font_source = ImageFont.truetype("Arial", 20)
                except IOError:
                    font_source = ImageFont.load_default()
                
                source_text = "Fuentes: " + ", ".join(sources[:3])  # Top 3 sources
                if len(sources) > 3:
                     source_text += ", ..."
                     
                bbox = draw.textbbox((0, 0), source_text, font=font_source)
                text_w = bbox[2] - bbox[0]
                draw.text(((width - text_w) / 2, y_text), source_text, fill="#888888", font=font_source)

            # Save image
            filename = f"verdict_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            path = os.path.join(self.output_dir, filename)
            img.save(path)
            
            return path
            
        except Exception as e:
            logger.error(f"Error generating verdict card: {e}")
            return None

    def generate_chart(self, title: str, data: Dict[str, float], chart_type: str = "bar") -> Optional[str]:
        """Generate a chart using matplotlib/seaborn"""
        if not MATPLOTLIB_AVAILABLE:
            logger.warning("Matplotlib not available. Cannot generate charts.")
            return None
            
        try:
            plt.figure(figsize=(10, 6))
            sns.set_theme(style="whitegrid")
            
            labels = list(data.keys())
            values = list(data.values())
            
            if chart_type == "bar":
                sns.barplot(x=labels, y=values, palette="viridis")
            elif chart_type == "pie":
                plt.pie(values, labels=labels, autopct='%1.1f%%', colors=sns.color_palette("pastel"))
                
            plt.title(title)
            plt.tight_layout()
            
            filename = f"chart_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            path = os.path.join(self.output_dir, filename)
            plt.savefig(path)
            plt.close()
            
            return path
            
        except Exception as e:
            logger.error(f"Error generating chart: {e}")
            return None
