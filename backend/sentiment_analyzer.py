import os
import logging
from typing import Optional, Dict, Any
from textblob import TextBlob
import openai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.openai_client = None
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            try:
                openai.api_key = openai_api_key
                self.openai_client = openai
                logger.info("OpenAI client initialized for advanced sentiment analysis")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        else:
            logger.info("OpenAI API key not found, using TextBlob for sentiment analysis")
    
    def analyze_sentiment(self, text: str, title: str = "") -> Dict[str, Any]:
        """
        分析新聞的情緒分數
        返回包含情緒分數、信心度和分析方法的字典
        """
        if not text and not title:
            return {
                "score": 0.0,
                "confidence": 0.0,
                "method": "no_text",
                "sentiment": "neutral"
            }
        
        # 組合標題和內容進行分析
        combined_text = f"{title} {text}".strip()
        
        # 首先使用 TextBlob 進行基本分析
        textblob_score = self._analyze_with_textblob(combined_text)
        
        # 如果有 OpenAI，進行進階分析
        openai_score = None
        if self.openai_client:
            try:
                openai_score = self._analyze_with_openai(combined_text, title)
            except Exception as e:
                logger.warning(f"OpenAI analysis failed: {e}")
        
        # 決定最終分數
        final_score, method, confidence = self._combine_scores(textblob_score, openai_score)
        
        return {
            "score": final_score,
            "confidence": confidence,
            "method": method,
            "sentiment": self._get_sentiment_label(final_score),
            "textblob_score": textblob_score.get("score", 0.0),
            "openai_score": openai_score.get("score", 0.0) if openai_score else None
        }
    
    def _analyze_with_textblob(self, text: str) -> Dict[str, Any]:
        """使用 TextBlob 進行基本情緒分析"""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 到 1
            subjectivity = blob.sentiment.subjectivity  # 0 到 1
            
            # 將極性轉換為 0-100 分數
            score = (polarity + 1) * 50  # 0-100 分數
            
            return {
                "score": round(score, 2),
                "polarity": round(polarity, 3),
                "subjectivity": round(subjectivity, 3),
                "confidence": max(0.3, 1 - subjectivity)  # 主觀性越低，信心度越高
            }
        except Exception as e:
            logger.error(f"TextBlob analysis failed: {e}")
            return {"score": 50.0, "polarity": 0.0, "subjectivity": 0.5, "confidence": 0.3}
    
    def _analyze_with_openai(self, text: str, title: str) -> Dict[str, Any]:
        """使用 OpenAI 進行進階情緒分析"""
        try:
            prompt = f"""
            請分析以下股票新聞的情緒，並給出 0-100 的分數：
            
            標題：{title}
            內容：{text[:500]}...
            
            請考慮以下因素：
            1. 對股價的影響（正面/負面）
            2. 市場情緒
            3. 公司基本面影響
            4. 行業趨勢影響
            
            請以 JSON 格式回覆：
            {{
                "score": 分數 (0-100),
                "reasoning": "分析理由",
                "confidence": 信心度 (0-1)
            }}
            """
            
            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一個專業的股票新聞情緒分析師。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            # 解析回應
            content = response.choices[0].message.content
            # 簡單的 JSON 解析（實際使用中可能需要更robust的解析）
            import json
            try:
                result = json.loads(content)
                return {
                    "score": float(result.get("score", 50)),
                    "reasoning": result.get("reasoning", ""),
                    "confidence": float(result.get("confidence", 0.7))
                }
            except:
                # 如果 JSON 解析失敗，嘗試提取數字
                import re
                score_match = re.search(r'"score":\s*(\d+)', content)
                score = int(score_match.group(1)) if score_match else 50
                return {
                    "score": score,
                    "reasoning": content,
                    "confidence": 0.6
                }
                
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            return {"score": 50.0, "reasoning": "Analysis failed", "confidence": 0.3}
    
    def _combine_scores(self, textblob_result: Dict, openai_result: Optional[Dict]) -> tuple:
        """結合兩種分析方法的結果"""
        textblob_score = textblob_result.get("score", 50.0)
        textblob_confidence = textblob_result.get("confidence", 0.5)
        
        if openai_result:
            openai_score = openai_result.get("score", 50.0)
            openai_confidence = openai_result.get("confidence", 0.5)
            
            # 加權平均
            total_confidence = textblob_confidence + openai_confidence
            if total_confidence > 0:
                final_score = (textblob_score * textblob_confidence + openai_score * openai_confidence) / total_confidence
                method = "combined"
                confidence = (textblob_confidence + openai_confidence) / 2
            else:
                final_score = textblob_score
                method = "textblob"
                confidence = textblob_confidence
        else:
            final_score = textblob_score
            method = "textblob"
            confidence = textblob_confidence
        
        return round(final_score, 2), method, round(confidence, 2)
    
    def _get_sentiment_label(self, score: float) -> str:
        """根據分數返回情緒標籤"""
        if score >= 70:
            return "very_positive"
        elif score >= 60:
            return "positive"
        elif score >= 45:
            return "slightly_positive"
        elif score >= 40:
            return "neutral"
        elif score >= 30:
            return "slightly_negative"
        elif score >= 20:
            return "negative"
        else:
            return "very_negative"

# 全域實例
sentiment_analyzer = SentimentAnalyzer() 