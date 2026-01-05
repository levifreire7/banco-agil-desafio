import logging
import time
from typing import Dict, Any

from langchain_core.tools import tool
import requests

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@tool
def consultar_cotacao_moeda(moeda: str = "USD") -> Dict[str, Any]:
    """
    Consulta a cotação de uma moeda em relação ao Real (BRL).
    Implementa retry com até 3 tentativas em caso de falha.

    Args:
        moeda: Código da moeda (USD, EUR, GBP, etc.)

    Returns:
        Dict com cotação e mensagem
    """
    max_tentativas = 3
    timeout = 10

    for tentativa in range(1, max_tentativas + 1):
        try:
            moeda = moeda.upper()
            url = f"https://api.exchangerate-api.com/v4/latest/{moeda}"
            response = requests.get(url, timeout=timeout)

            if response.status_code == 200:
                data = response.json()
                if 'rates' in data and 'BRL' in data['rates']:
                    cotacao = data['rates']['BRL']
                    return {
                        "sucesso": True,
                        "moeda": moeda,
                        "cotacao": cotacao,
                        "mensagem": f"1 {moeda} = R$ {cotacao:.2f}"
                    }

            # Se status não é 200, tenta novamente
            if tentativa < max_tentativas:
                time.sleep(1)  # Aguarda 1 segundo antes de tentar novamente
                continue

            return {
                "sucesso": False,
                "mensagem": "Não foi possível obter a cotação no momento. Por favor, tente novamente mais tarde."
            }

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout na tentativa {tentativa}/{max_tentativas} para consultar {moeda}")
            if tentativa < max_tentativas:
                time.sleep(1)
                continue
            return {
                "sucesso": False,
                "mensagem": "O serviço de cotação está demorando para responder. Por favor, tente novamente em alguns instantes."
            }

        except requests.exceptions.ConnectionError:
            logger.error(f"Erro de conexão na tentativa {tentativa}/{max_tentativas} para consultar {moeda}")
            if tentativa < max_tentativas:
                time.sleep(1)
                continue
            return {
                "sucesso": False,
                "mensagem": "Não foi possível conectar ao serviço de cotação. Verifique sua conexão ou tente novamente mais tarde."
            }

        except Exception as e:
            logger.error(f"Erro ao consultar cotação na tentativa {tentativa}/{max_tentativas}: {str(e)}", exc_info=True)
            if tentativa < max_tentativas:
                time.sleep(1)
                continue
            return {
                "sucesso": False,
                "mensagem": "Erro ao consultar cotação. Por favor, tente novamente mais tarde ou entre em contato com o suporte."
            }

    # Fallback caso algo inesperado aconteça
    return {
        "sucesso": False,
        "mensagem": "Não foi possível consultar a cotação. Por favor, tente novamente."
    }
