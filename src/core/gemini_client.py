"""
Gemini API Client Wrapper.
Files API, Caching, Chat ve Structured Output yönetimi.
"""

import os
import time
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Type, Generator
from datetime import datetime, timedelta

from google import genai
from google.genai import types
from pydantic import BaseModel

from ..models.project import CacheInfo, TokenUsage, ThinkingLevel


class GeminiClient:
    """
    Gemini API istemcisi.
    Files API, Context Caching ve Chat fonksiyonlarını yönetir.
    """
    
    # Model sabitleri
    GEMINI_3_PRO = "gemini-3-pro-preview"
    GEMINI_3_FLASH = "gemini-3-flash-preview"
    NANO_BANANA_PRO = "nano-banana-pro"
    
    # Limit sabitleri
    MAX_CONTEXT_TOKENS = 1_000_000
    MAX_OUTPUT_TOKENS = 8_000
    
    def __init__(self, api_key: Optional[str] = None):
        """
        GeminiClient başlat.
        
        Args:
            api_key: Gemini API key. None ise GEMINI_API_KEY env var kullanılır.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY bulunamadı. "
                "Lütfen api_key parametresi verin veya GEMINI_API_KEY env var ayarlayın."
            )
        
        # Client oluştur
        self._client = genai.Client(api_key=self.api_key)
        
        # Aktif cache'ler, chat oturumları ve yüklenen dosyalar
        self._caches: Dict[str, CacheInfo] = {}
        self._chats: Dict[str, Any] = {}  # chat_id -> Chat instance
        self._uploaded_files: Dict[str, Any] = {}  # file_path -> File object
        
    # ==================== FILES API ====================
    
    def upload_file(
        self,
        file_path: str,
        display_name: Optional[str] = None,
        wait_for_processing: bool = True
    ) -> Any:
        """
        Dosya yükle (Files API).
        
        Args:
            file_path: Yerel dosya yolu
            display_name: Görüntülenen ad (opsiyonel)
            wait_for_processing: İşlenene kadar bekle
            
        Returns:
            File objesi (cache'e geçilebilir)
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Dosya bulunamadı: {file_path}")
        
        # Dosyayı yükle
        uploaded_file = self._client.files.upload(
            file=path,
            config={"display_name": display_name or path.name}
        )
        
        # İşlenene kadar bekle
        if wait_for_processing:
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_file = self._client.files.get(name=uploaded_file.name)
            
            if uploaded_file.state.name == "FAILED":
                raise RuntimeError(f"Dosya işleme başarısız: {file_path}")
        
        # File objesini sakla (cache için)
        self._uploaded_files[file_path] = uploaded_file
        
        return uploaded_file
    
    def get_file_info(self, file_name: str) -> Dict[str, Any]:
        """Dosya bilgisi al"""
        file_info = self._client.files.get(name=file_name)
        return {
            "name": file_info.name,
            "display_name": file_info.display_name,
            "uri": file_info.uri,
            "state": file_info.state.name,
            "size_bytes": getattr(file_info, "size_bytes", None),
            "mime_type": getattr(file_info, "mime_type", None),
        }
    
    def list_files(self) -> List[Dict[str, Any]]:
        """Tüm yüklü dosyaları listele"""
        files = self._client.files.list()
        return [
            {
                "name": f.name,
                "display_name": f.display_name,
                "uri": f.uri,
                "state": f.state.name,
            }
            for f in files
        ]
    
    def delete_file(self, file_name: str) -> bool:
        """Dosya sil"""
        try:
            self._client.files.delete(name=file_name)
            return True
        except Exception:
            return False
    
    # ==================== CONTEXT CACHING ====================
    
    def create_cache(
        self,
        cache_id: str,
        model: str,
        system_instruction: str,
        contents: List[Any] = None,
        ttl_seconds: int = 3600,
        display_name: Optional[str] = None
    ) -> CacheInfo:
        """
        Context cache oluştur.
        
        Args:
            cache_id: Benzersiz cache ID (bizim tarafımızdan)
            model: Model adı
            system_instruction: System prompt
            contents: Cache'lenecek içerikler (File objeleri veya metin)
            ttl_seconds: Cache süresi (saniye)
            display_name: Görüntülenen ad
            
        Returns:
            CacheInfo objesi
        """
        # İçerikleri hazırla
        # Google dokümantasyonuna göre File objesi direkt geçilebilir
        prepared_contents = contents if contents else []
        
        # Cache oluştur config
        cache_config = types.CreateCachedContentConfig(
            display_name=display_name or cache_id,
            system_instruction=system_instruction,
            ttl=f"{ttl_seconds}s"
        )
        
        # Contents varsa ekle
        if prepared_contents:
            cache_config.contents = prepared_contents
        
        # Cache oluştur
        cache = self._client.caches.create(
            model=model,
            config=cache_config
        )
        
        # Token sayısını al - usage_metadata bir obje, dict değil
        usage_meta = getattr(cache, "usage_metadata", None)
        token_count = getattr(usage_meta, "total_token_count", 0) if usage_meta else 0
        
        # Cache bilgisini kaydet
        cache_info = CacheInfo(
            cache_name=cache.name,
            model=model,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=ttl_seconds),
            token_count=token_count
        )
        self._caches[cache_id] = cache_info
        
        return cache_info
    
    def get_cache(self, cache_id: str) -> Optional[CacheInfo]:
        """Cache bilgisi al"""
        return self._caches.get(cache_id)
    
    def update_cache_ttl(self, cache_id: str, new_ttl_seconds: int) -> bool:
        """Cache TTL güncelle"""
        cache_info = self._caches.get(cache_id)
        if not cache_info:
            return False
        
        try:
            self._client.caches.update(
                name=cache_info.cache_name,
                config={"ttl": f"{new_ttl_seconds}s"}
            )
            cache_info.expires_at = datetime.now() + timedelta(seconds=new_ttl_seconds)
            return True
        except Exception:
            return False
    
    def delete_cache(self, cache_id: str) -> bool:
        """Cache sil"""
        cache_info = self._caches.get(cache_id)
        if not cache_info:
            return False
        
        try:
            self._client.caches.delete(name=cache_info.cache_name)
            del self._caches[cache_id]
            return True
        except Exception:
            return False
    
    def list_caches(self) -> List[CacheInfo]:
        """Tüm cache'leri listele"""
        return list(self._caches.values())
    
    # ==================== CHAT API ====================
    
    def create_chat(
        self,
        chat_id: str,
        model: str,
        cache_id: Optional[str] = None,
        thinking_level: ThinkingLevel = ThinkingLevel.HIGH,
        system_instruction: Optional[str] = None
    ) -> str:
        """
        Chat oturumu oluştur.
        
        Args:
            chat_id: Benzersiz chat ID
            model: Model adı
            cache_id: Kullanılacak cache ID (opsiyonel)
            thinking_level: Düşünme seviyesi
            system_instruction: System prompt (cache yoksa)
            
        Returns:
            chat_id
        """
        config = {}
        
        # Cache varsa referans ekle
        if cache_id:
            cache_info = self._caches.get(cache_id)
            if cache_info:
                config["cached_content"] = cache_info.cache_name
        
        # Thinking level
        config["thinking_config"] = types.ThinkingConfig(
            thinking_level=thinking_level.value
        )
        
        # Chat oluştur
        chat = self._client.chats.create(
            model=model,
            config=types.GenerateContentConfig(**config)
        )
        
        self._chats[chat_id] = {
            "chat": chat,
            "model": model,
            "cache_id": cache_id,
            "message_count": 0
        }
        
        return chat_id
    
    def send_message(
        self,
        chat_id: str,
        message: str,
        stream: bool = False
    ) -> tuple[str, TokenUsage]:
        """
        Chat'e mesaj gönder.
        
        Args:
            chat_id: Chat ID
            message: Mesaj
            stream: Streaming yanıt mı
            
        Returns:
            (yanıt metni, token kullanımı) tuple
        """
        chat_data = self._chats.get(chat_id)
        if not chat_data:
            raise ValueError(f"Chat bulunamadı: {chat_id}")
        
        chat = chat_data["chat"]
        
        if stream:
            # Streaming yanıt
            full_response = ""
            usage = TokenUsage()
            
            for chunk in chat.send_message_stream(message):
                if chunk.text:
                    full_response += chunk.text
                # Son chunk'ta usage bilgisi var
                if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                    usage = self._parse_usage(chunk.usage_metadata)
            
            chat_data["message_count"] += 1
            return full_response, usage
        else:
            # Normal yanıt
            response = chat.send_message(message)
            usage = self._parse_usage(response.usage_metadata)
            chat_data["message_count"] += 1
            return response.text, usage
    
    def send_message_stream(
        self,
        chat_id: str,
        message: str
    ) -> Generator[str, None, TokenUsage]:
        """
        Streaming mesaj gönder (generator).
        
        Yields:
            Her chunk'taki metin
            
        Returns:
            TokenUsage (generator bitince)
        """
        chat_data = self._chats.get(chat_id)
        if not chat_data:
            raise ValueError(f"Chat bulunamadı: {chat_id}")
        
        chat = chat_data["chat"]
        usage = TokenUsage()
        
        for chunk in chat.send_message_stream(message):
            if chunk.text:
                yield chunk.text
            if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                usage = self._parse_usage(chunk.usage_metadata)
        
        chat_data["message_count"] += 1
        return usage
    
    def get_chat_history(self, chat_id: str) -> List[Dict[str, str]]:
        """Chat geçmişini al"""
        chat_data = self._chats.get(chat_id)
        if not chat_data:
            raise ValueError(f"Chat bulunamadı: {chat_id}")
        
        history = []
        for message in chat_data["chat"].get_history():
            history.append({
                "role": message.role,
                "text": message.parts[0].text if message.parts else ""
            })
        
        return history
    
    def delete_chat(self, chat_id: str) -> bool:
        """Chat oturumunu sil"""
        if chat_id in self._chats:
            del self._chats[chat_id]
            return True
        return False
    
    def send_message_structured(
        self,
        chat_id: str,
        message: str,
        response_schema: Type[BaseModel]
    ) -> tuple[BaseModel, TokenUsage]:
        """
        Chat oturumu üzerinden structured output al.
        
        Bu metod chat history'yi koruyarak mesaj gönderir ve
        JSON schema'ya uygun yapılandırılmış yanıt alır.
        
        Args:
            chat_id: Chat ID
            message: Prompt/mesaj
            response_schema: Pydantic model sınıfı
            
        Returns:
            (Pydantic model instance, TokenUsage)
        """
        chat_data = self._chats.get(chat_id)
        if not chat_data:
            raise ValueError(f"Chat bulunamadı: {chat_id}")
        
        chat = chat_data["chat"]
        model = chat_data["model"]
        
        text_response = None
        
        # Config oluştur
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=response_schema.model_json_schema()
        )
        
        # Cache varsa config'e ekle (Chat config'ini override ediyoruz, bu yüzden tekrar belirtmek gerekebilir)
        cache_id = chat_data.get("cache_id")
        if cache_id and cache_id in self._caches:
             config.cached_content = self._caches[cache_id].cache_name
             
        # Chat üzerinden gönder - History otomatik yönetilir
        response = chat.send_message(
            message=message,
            config=config
        )
        
        text_response = response.text
        
        # JSON parse ve Pydantic model oluştur
        result = response_schema.model_validate_json(text_response)
        usage = self._parse_usage(response.usage_metadata)
        
        chat_data["message_count"] += 1
        
        return result, usage
    
    # ==================== STRUCTURED OUTPUT ====================
    
    def generate_structured(
        self,
        model: str,
        prompt: str,
        response_schema: Type[BaseModel],
        cache_id: Optional[str] = None,
        thinking_level: ThinkingLevel = ThinkingLevel.HIGH
    ) -> tuple[BaseModel, TokenUsage]:
        """
        Yapılandırılmış yanıt üret (Pydantic modeli).
        
        Args:
            model: Model adı
            prompt: Prompt
            response_schema: Pydantic model sınıfı
            cache_id: Kullanılacak cache ID
            thinking_level: Düşünme seviyesi
            
        Returns:
            (Pydantic model instance, token kullanımı)
        """
        # Resmi dokümantasyona uygun config
        config = {
            "response_mime_type": "application/json",
            "response_json_schema": response_schema.model_json_schema(),
            "thinking_config": types.ThinkingConfig(
                thinking_level=thinking_level.value
            )
        }
        
        # Cache varsa ekle
        if cache_id:
            cache_info = self._caches.get(cache_id)
            if cache_info:
                config["cached_content"] = cache_info.cache_name
        
        response = self._client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(**config)
        )
        
        # JSON parse et ve Pydantic modeline dönüştür
        result = response_schema.model_validate_json(response.text)
        usage = self._parse_usage(response.usage_metadata)
        
        return result, usage
    
    # ==================== YARDIMCI METODLAR ====================
    
    def count_tokens(self, model: str, text: str) -> int:
        """Token sayısını hesapla"""
        result = self._client.models.count_tokens(
            model=model,
            contents=text
        )
        return result.total_tokens
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Model bilgisi al"""
        info = self._client.models.get(model=model)
        return {
            "name": info.name,
            "input_token_limit": info.input_token_limit,
            "output_token_limit": info.output_token_limit,
        }
    
    def _parse_usage(self, usage_metadata) -> TokenUsage:
        """usage_metadata'yı TokenUsage'a dönüştür"""
        if not usage_metadata:
            return TokenUsage()
        
        # None değerleri 0'a çevir
        return TokenUsage(
            prompt_tokens=getattr(usage_metadata, "prompt_token_count", 0) or 0,
            cached_tokens=getattr(usage_metadata, "cached_content_token_count", 0) or 0,
            output_tokens=getattr(usage_metadata, "candidates_token_count", 0) or 0,
            total_tokens=getattr(usage_metadata, "total_token_count", 0) or 0
        )
    
    def estimate_tokens(self, text: str) -> int:
        """Yaklaşık token sayısı (4 karakter ≈ 1 token)"""
        return len(text) // 4
