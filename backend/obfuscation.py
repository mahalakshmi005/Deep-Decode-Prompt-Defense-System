import base64
import re
import unicodedata
import urllib.parse
import codecs

class ObfuscationEngine:
    def __init__(self):
        # Homoglyphs mapping (Commonly used to bypass filters)
        self.homoglyph_map = {
            'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'zh',
            'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
            'п': 'p', 'р': 'r', 'с': 'c', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'ts',
            'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu',
            'я': 'ya',
            'ɑ': 'a', 'е': 'e', 'і': 'i', 'о': 'o', 'р': 'p', 'ѕ': 's', 'υ': 'u', 'х': 'x', 'у': 'y',
            'ԝ': 'w', 'м': 'm', 'п': 'n', 'н': 'n', 'т': 't', 'к': 'k', 'в': 'b'
        }
        
        # Leet Speak mapping
        self.leet_map = {
            '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '8': 'b', '@': 'a', '$': 's', '!': 'i'
        }

        # Zero-width spaces and other noise
        self.noise_chars = [
            '\u200b', '\u200c', '\u200d', '\u200e', '\u200f', '\ufeff',
            '\u00ad', '\u00a0', '\u180e', '\u202f', '\u205f', '\u2060'
        ]

    def normalize_unicode(self, text: str) -> str:
        """Applies NFKC normalization."""
        return unicodedata.normalize('NFKC', text)

    def remove_noise(self, text: str) -> str:
        """Removes zero-width spaces, invisible characters, and emojis."""
        for char in self.noise_chars:
            text = text.replace(char, '')
        
        # Remove combining characters (marks)
        text = "".join(ch for ch in unicodedata.normalize('NFD', text) if unicodedata.category(ch) != 'Mn')
        
        # Remove emojis and other symbols that might be used as noise
        return "".join(ch for ch in text if unicodedata.category(ch)[0] not in ['C', 'S'] or ch in '\n\r\t ')

    def replace_homoglyphs(self, text: str) -> str:
        """Replaces look-alike characters with Latin equivalents."""
        return "".join(self.homoglyph_map.get(c, c) for c in text)

    def resolve_leet(self, text: str) -> str:
        """Translates simple leet-speak back to English."""
        words = text.split()
        resolved_words = []
        for word in words:
            if any(c in self.leet_map for c in word):
                # If word is mostly letters but has leet chars, resolve it
                if sum(c.isalpha() for c in word) > sum(c.isdigit() for c in word):
                    new_word = "".join(self.leet_map.get(c, c) for c in word)
                    resolved_words.append(new_word)
                else:
                    resolved_words.append(word)
            else:
                resolved_words.append(word)
        return " ".join(resolved_words)

    def recursive_decode(self, text: str, max_depth: int = 3) -> list:
        """Attempt to decode text through multiple layers (Base64, Hex, URL, ROT13)."""
        decoded_variants = set()
        
        def _decode(current_text, depth):
            if depth > max_depth or len(current_text.strip()) < 4:
                return

            # 1. Base64
            try:
                padded = current_text
                missing_padding = len(padded) % 4
                if missing_padding: padded += '=' * (4 - missing_padding)
                b64_decoded = base64.b64decode(padded.encode('ascii'), validate=False).decode('utf-8', errors='ignore')
                if b64_decoded and b64_decoded != current_text and any(c.isalnum() for c in b64_decoded):
                    if b64_decoded not in decoded_variants:
                        decoded_variants.add(b64_decoded)
                        _decode(b64_decoded, depth + 1)
            except: pass

            # 2. Hex
            try:
                clean_hex = re.sub(r'[\s\-:x\\]+', '', current_text)
                # Handle \xNN or 0xNN formats
                if re.fullmatch(r'[0-9a-fA-F]+', clean_hex) and len(clean_hex) >= 2:
                    hex_decoded = bytes.fromhex(clean_hex).decode('utf-8', errors='ignore')
                    if hex_decoded and hex_decoded != current_text:
                        if hex_decoded not in decoded_variants:
                            decoded_variants.add(hex_decoded)
                            _decode(hex_decoded, depth + 1)
            except: pass

            # 3. URL Encoding
            try:
                if '%' in current_text:
                    url_decoded = urllib.parse.unquote(current_text)
                    if url_decoded != current_text:
                        if url_decoded not in decoded_variants:
                            decoded_variants.add(url_decoded)
                            _decode(url_decoded, depth + 1)
            except: pass

            # 4. ROT13
            try:
                rot13_decoded = codecs.encode(current_text, 'rot_13')
                if rot13_decoded != current_text and any(c.isalpha() for c in rot13_decoded):
                    # Only add if it seems like it might be English (very basic check)
                    if ' ' in rot13_decoded or any(common in rot13_decoded.lower() for common in ['the', 'and', 'ing']):
                        if rot13_decoded not in decoded_variants:
                            decoded_variants.add(rot13_decoded)
                            _decode(rot13_decoded, depth + 1)
            except: pass

        _decode(text, 0)
        return list(decoded_variants)

    def extract_and_decode_all(self, text: str) -> list:
        """Finds potential encoded blocks and decodes them."""
        # Find B64 and Hex patterns
        patterns = [
            r'(?:[A-Za-z0-9+/]{4}){2,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?', # B64
            r'\b(?:[0-9a-fA-F]{2}[\s\-:]?){4,}\b', # Hex
            r'0x[0-9a-fA-F]+', # Hex with 0x
            r'(?:\\x[0-9a-fA-F]{2})+' # Hex with \x
        ]
        
        potential_blocks = []
        for p in patterns:
            potential_blocks.extend(re.findall(p, text))
            
        all_decoded = []
        for block in set(potential_blocks):
            all_decoded.extend(self.recursive_decode(block.strip()))
            
        # Also try decoding the whole text
        all_decoded.extend(self.recursive_decode(text))
        
        # Add variants that are cleaned up
        cleaned_variants = []
        for d in all_decoded:
            cleaned = self.get_clean_text(d)
            if cleaned != d:
                cleaned_variants.append(cleaned)
        all_decoded.extend(cleaned_variants)
        
        # Add leet-resolved variants
        all_decoded.append(self.resolve_leet(text))
        
        valid_decoded = []
        for d in set(all_decoded):
            d_strip = d.strip()
            if len(d_strip) > 5 and any(c.isalnum() for c in d_strip):
                valid_decoded.append(d_strip)
                
        return valid_decoded

    def get_clean_text(self, text: str) -> str:
        """Returns a normalized, noise-free, homoglyph-replaced version of the text."""
        # 1. Remove noise (including zero-width and invisible) BEFORE normalization
        text = self.remove_noise(text)
        
        # 2. Normalize Unicode (NFKC)
        text = self.normalize_unicode(text)
        
        # 3. Replace homoglyphs
        text = self.replace_homoglyphs(text)
        
        # 4. Resolve leet-speak
        text = self.resolve_leet(text)
        
        # 5. Handle spaced-out text (e.g., "i n j e c t i o n")
        # If the text has a lot of single characters separated by spaces, join them
        words = text.split()
        if len(words) > 3:
            single_char_words = sum(1 for w in words if len(w) == 1)
            if single_char_words / len(words) > 0.5:
                text = "".join(words)
        
        return text

