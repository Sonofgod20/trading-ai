import re
import json
from typing import Dict, Optional, Tuple

class AnalysisParser:
    @staticmethod
    def parse_analysis_response(response: str) -> Tuple[Dict, Dict]:
        """
        Parse the AI's analysis response to extract trade signals and visual elements
        Returns:
            Tuple containing trade signals and visual elements
        """
        try:
            if not response:
                return {}, {}

            # Extract trade signals
            trade_signals = {
                'direction': AnalysisParser._extract_direction(response),
                'confidence': AnalysisParser._extract_confidence(response),
                'entry': AnalysisParser._extract_multiple_prices('entry_points', response),
                'tp': AnalysisParser._extract_multiple_prices('exit_points', response),
                'sl': AnalysisParser._extract_stop_loss(response)
            }

            # Extract visual elements
            visual_elements = {
                'trend_lines': AnalysisParser._extract_json_array('trend_lines', response),
                'patterns': AnalysisParser._extract_json_array('patterns', response),
                'zones': AnalysisParser._extract_json_array('zones', response)
            }

            return trade_signals, visual_elements
        except Exception as e:
            print(f"Error parsing analysis response: {str(e)}")
            return {}, {}

    @staticmethod
    def _extract_multiple_prices(key: str, response: str) -> list:
        """Extract multiple price points from response"""
        try:
            prices = []
            if key == 'entry_points':
                # Buscar precios en el formato "Entrada escalonada: 33% en $94,000"
                pattern = r'entrada.*?\$\s*(\d{2,3}(?:,\d{3})*(?:\.\d+)?)'
            else:  # exit_points
                # Buscar precios en el formato "Toma de beneficios parcial en $95,000"
                pattern = r'(?:toma|salida).*?\$\s*(\d{2,3}(?:,\d{3})*(?:\.\d+)?)'
            
            matches = re.finditer(pattern, response.lower(), re.IGNORECASE)
            for match in matches:
                try:
                    price = float(match.group(1).replace(',', ''))
                    prices.append(price)
                except:
                    continue
            
            return sorted(prices) if prices else None
        except Exception as e:
            print(f"Error extracting multiple prices: {str(e)}")
            return None

    @staticmethod
    def _extract_stop_loss(response: str) -> Optional[float]:
        """Extract stop loss price from response"""
        try:
            # Buscar stop loss en el formato "stop_loss: "$92,000""
            pattern = r'stop.*?\$\s*(\d{2,3}(?:,\d{3})*(?:\.\d+)?)'
            match = re.search(pattern, response.lower(), re.IGNORECASE)
            if match:
                return float(match.group(1).replace(',', ''))
            return None
        except Exception:
            return None

    @staticmethod
    def _extract_direction(response: str) -> str:
        """Extract trade direction from response"""
        try:
            # Look for direction in a more flexible way
            direction_patterns = [
                r'Direction:\s*(LONG|SHORT|NO TRADE)',
                r'Direction\s*-\s*(LONG|SHORT|NO TRADE)',
                r'Direction\s*=\s*(LONG|SHORT|NO TRADE)',
                r'Direction\s*:\s*(LONG|SHORT|NO TRADE)',
            ]
            
            for pattern in direction_patterns:
                direction_match = re.search(pattern, response, re.IGNORECASE)
                if direction_match:
                    return direction_match.group(1).upper()
            
            # Inferir dirección basado en los niveles
            if 'stop_loss' in response.lower():
                sl = AnalysisParser._extract_stop_loss(response)
                entries = AnalysisParser._extract_multiple_prices('entry_points', response)
                if sl and entries:
                    return 'LONG' if entries[0] > sl else 'SHORT'
            
            return 'NO TRADE'
        except Exception:
            return 'NO TRADE'

    @staticmethod
    def _extract_confidence(response: str) -> float:
        """Extract confidence level from response"""
        try:
            # Look for confidence in a more flexible way
            confidence_patterns = [
                r'confidence_level["\']?\s*:\s*(\d+(?:\.\d+)?)',
                r'Confidence Level:\s*(\d+(?:\.\d+)?)%?',
                r'probability:\s*["\']?(\d+(?:\.\d+)?)%?',
                r'probabilidad.*?(\d+(?:\.\d+)?)%?'
            ]
            
            for pattern in confidence_patterns:
                confidence_match = re.search(pattern, response, re.IGNORECASE)
                if confidence_match:
                    return float(confidence_match.group(1))
            
            return 0.0
        except Exception:
            return 0.0

    @staticmethod
    def _extract_json_array(element_type: str, response: str) -> list:
        """Extract JSON array from response"""
        try:
            # Define patterns for different visual elements
            patterns = {
                'trend_lines': [
                    r'Trend Lines:.*?\[(.*?)\]',
                    r'trend_lines\s*=\s*\[(.*?)\]',
                    r'trend_lines:\s*\[(.*?)\]'
                ],
                'patterns': [
                    r'Patterns:.*?\[(.*?)\]',
                    r'patterns\s*=\s*\[(.*?)\]',
                    r'patterns:\s*\[(.*?)\]'
                ],
                'zones': [
                    r'Zones:.*?\[(.*?)\]',
                    r'zones\s*=\s*\[(.*?)\]',
                    r'zones:\s*\[(.*?)\]'
                ]
            }

            # Try each pattern
            for pattern in patterns.get(element_type, []):
                section_match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                if section_match:
                    try:
                        # Clean up the JSON string
                        json_str = section_match.group(1).strip()
                        if not json_str:
                            continue
                            
                        # Handle single objects (not in array)
                        if not json_str.startswith('['):
                            json_str = f"[{json_str}]"
                            
                        # Parse JSON
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        continue

            return []
        except Exception as e:
            print(f"Error extracting {element_type}: {str(e)}")
            return []
