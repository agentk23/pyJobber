from googletrans import Translator
from typing import Dict
import re

class GoogleTranslator:
    def __init__(self):
        self.trans = Translator()

    async def detect_and_translate_text(self, text: str, target_lang: str = 'en') -> Dict[str, str]:
        """Detect language and translate text if needed"""
        try:
            # Clean text
            text = re.sub(r'\s+', ' ', text).strip()
            if not text or len(text) < 5:
                return {'original': text, 'translated': text, 'detected_lang': 'unknown'}

            # Detect language
            detection = await self.trans.detect(text)
            detected_lang = detection.lang

            # If already in English, don't translate
            if detected_lang == target_lang:
                return {
                    'original': text,
                    'translated': text,
                    'detected_lang': detected_lang
                }

            # Translate text
            translation = await self.trans.translate(text, dest=target_lang)
            return {
                'original': text,
                'translated': translation.text,
                'detected_lang': detected_lang
            }

        except Exception as e:
            print(f"Translation error: {e}")
            return {
                'original': text,
                'translated': text,
                'detected_lang': 'error'
            }