import json
import os
from typing import Dict, Any

class I18nService:
    def __init__(self):
        self.locales_dir = os.path.join(os.path.dirname(__file__), 'locales')
        self.default_locale = os.getenv('DEFAULT_LOCALE', 'zh_tw')
        self.fallback_locale = os.getenv('FALLBACK_LOCALE', 'en')
        self._translations = {}
        self._load_translations()
    
    def _load_translations(self):
        """Load all translation files"""
        for filename in os.listdir(self.locales_dir):
            if filename.endswith('.json'):
                locale = filename.replace('.json', '')
                filepath = os.path.join(self.locales_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self._translations[locale] = json.load(f)
                except Exception as e:
                    print(f"Error loading translations for {locale}: {e}")
    
    def t(self, key: str, locale: str = None, **kwargs) -> str:
        """
        Get translation for a key
        
        Args:
            key: Translation key (e.g., 'ai.welcome')
            locale: Target locale (defaults to default_locale)
            **kwargs: Variables to interpolate in the translation
        
        Returns:
            Translated string
        """
        if locale is None:
            locale = self.default_locale
        
        # Try to get translation from specified locale
        translation = self._get_nested_value(self._translations.get(locale, {}), key)
        
        # Fallback to fallback locale if not found
        if translation is None and locale != self.fallback_locale:
            translation = self._get_nested_value(self._translations.get(self.fallback_locale, {}), key)
        
        # Fallback to key itself if still not found
        if translation is None:
            translation = key
        
        # Interpolate variables if any
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except (KeyError, ValueError):
                pass  # Return as-is if interpolation fails
        
        return translation
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        keys = key.split('.')
        value = data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return None
        
        return value
    
    def get_available_locales(self) -> list:
        """Get list of available locales"""
        return list(self._translations.keys())
    
    def is_locale_available(self, locale: str) -> bool:
        """Check if locale is available"""
        return locale in self._translations

# Global instance
i18n_service = I18nService()
