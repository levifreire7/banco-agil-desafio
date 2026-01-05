import csv
from datetime import datetime
import logging
import os
from typing import Optional

from src.data_models.models import Cliente

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Database:
    """Gerenciador dos arquivos de dados CSV."""

    def __init__(self, base_path: str = "data"):
        self.base_path = base_path
        self.clientes_file = os.path.join(base_path, "clientes.csv")
        self.score_limite_file = os.path.join(base_path, "score_limite.csv")
        self.solicitacoes_file = os.path.join(base_path, "solicitacoes_aumento_limite.csv")

    def autenticar_cliente(self, cpf: str, data_nascimento: str) -> Optional[Cliente]:
        """Autentica o cliente verificando CPF e data de nascimento."""
        try:
            if not os.path.exists(self.clientes_file):
                logger.error(f"Arquivo de clientes não encontrado: {self.clientes_file}")
                raise FileNotFoundError(f"Arquivo de dados não encontrado. Entre em contato com o suporte.")

            with open(self.clientes_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['cpf'] == cpf and row['data_nascimento'] == data_nascimento:
                        return Cliente(
                            cpf=row['cpf'],
                            nome=row['nome'],
                            data_nascimento=row['data_nascimento'],
                            limite_credito=float(row['limite_credito']),
                            score=int(row['score'])
                        )
            return None
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erro ao autenticar cliente: {str(e)}", exc_info=True)
            raise Exception(f"Erro ao acessar dados do cliente. Tente novamente.")

    def obter_cliente(self, cpf: str) -> Optional[Cliente]:
        """Obtém dados do cliente pelo CPF."""
        try:
            if not os.path.exists(self.clientes_file):
                logger.error(f"Arquivo de clientes não encontrado: {self.clientes_file}")
                raise FileNotFoundError(f"Arquivo de dados não encontrado. Entre em contato com o suporte.")

            with open(self.clientes_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['cpf'] == cpf:
                        return Cliente(
                            cpf=row['cpf'],
                            nome=row['nome'],
                            data_nascimento=row['data_nascimento'],
                            limite_credito=float(row['limite_credito']),
                            score=int(row['score'])
                        )
            return None
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erro ao obter cliente: {str(e)}", exc_info=True)
            raise Exception(f"Erro ao acessar dados do cliente. Tente novamente.")

    def atualizar_score(self, cpf: str, novo_score: int) -> bool:
        """Atualiza o score do cliente."""
        try:
            if not os.path.exists(self.clientes_file):
                logger.error(f"Arquivo de clientes não encontrado: {self.clientes_file}")
                raise FileNotFoundError(f"Arquivo de dados não encontrado. Entre em contato com o suporte.")

            clientes = []
            with open(self.clientes_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    if row['cpf'] == cpf:
                        row['score'] = str(novo_score)
                    clientes.append(row)

            with open(self.clientes_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(clientes)

            return True
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erro ao atualizar score: {str(e)}", exc_info=True)
            raise Exception(f"Erro ao atualizar dados. Tente novamente.")

    def verificar_limite_permitido(self, score: int, novo_limite: float) -> bool:
        """Verifica se o novo limite solicitado é permitido para o score."""
        try:
            if not os.path.exists(self.score_limite_file):
                logger.error(f"Arquivo de score/limite não encontrado: {self.score_limite_file}")
                raise FileNotFoundError(f"Arquivo de configuração não encontrado. Entre em contato com o suporte.")

            with open(self.score_limite_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    score_min = int(row['score_minimo'])
                    score_max = int(row['score_maximo'])
                    limite_max = float(row['limite_maximo'])

                    if score_min <= score <= score_max:
                        return novo_limite <= limite_max
            return False
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erro ao verificar limite permitido: {str(e)}", exc_info=True)
            raise Exception(f"Erro ao verificar limite permitido. Tente novamente.")

    def criar_solicitacao_aumento(self, cpf: str, limite_atual: float,
                                  novo_limite: float) -> str:
        """Cria uma solicitação de aumento de limite com status 'pendente'."""
        try:
            file_exists = os.path.exists(self.solicitacoes_file)
            data_hora = datetime.now().isoformat()

            # Garante que o diretório existe
            os.makedirs(os.path.dirname(self.solicitacoes_file), exist_ok=True)

            with open(self.solicitacoes_file, 'a', encoding='utf-8', newline='') as f:
                fieldnames = ['cpf_cliente', 'data_hora_solicitacao', 'limite_atual',
                            'novo_limite_solicitado', 'status_pedido']
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                writer.writerow({
                    'cpf_cliente': cpf,
                    'data_hora_solicitacao': data_hora,
                    'limite_atual': limite_atual,
                    'novo_limite_solicitado': novo_limite,
                    'status_pedido': 'pendente'
                })

            return data_hora
        except Exception as e:
            logger.error(f"Erro ao criar solicitação: {str(e)}", exc_info=True)
            raise Exception(f"Erro ao registrar solicitação. Tente novamente.")

    def atualizar_status_solicitacao(self, cpf: str, data_hora: str,
                                     novo_status: str, atualizar_limite: bool = False,
                                     novo_limite: float = None) -> bool:
        """Atualiza o status de uma solicitação de aumento de limite."""
        try:
            if not os.path.exists(self.solicitacoes_file):
                logger.error(f"Arquivo de solicitações não encontrado: {self.solicitacoes_file}")
                raise FileNotFoundError(f"Arquivo de solicitações não encontrado. Entre em contato com o suporte.")

            solicitacoes = []
            with open(self.solicitacoes_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    if row['cpf_cliente'] == cpf and row['data_hora_solicitacao'] == data_hora:
                        row['status_pedido'] = novo_status
                    solicitacoes.append(row)

            with open(self.solicitacoes_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(solicitacoes)

            if atualizar_limite and novo_limite is not None:
                self._atualizar_limite_cliente(cpf, novo_limite)

            return True
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erro ao atualizar status da solicitação: {str(e)}", exc_info=True)
            raise Exception(f"Erro ao atualizar solicitação. Tente novamente.")

    def _atualizar_limite_cliente(self, cpf: str, novo_limite: float) -> bool:
        """Atualiza o limite de crédito do cliente."""
        try:
            if not os.path.exists(self.clientes_file):
                logger.error(f"Arquivo de clientes não encontrado: {self.clientes_file}")
                raise FileNotFoundError(f"Arquivo de dados não encontrado. Entre em contato com o suporte.")

            clientes = []
            with open(self.clientes_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for row in reader:
                    if row['cpf'] == cpf:
                        row['limite_credito'] = str(novo_limite)
                    clientes.append(row)

            with open(self.clientes_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(clientes)

            return True
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Erro ao atualizar limite: {str(e)}", exc_info=True)
            raise Exception(f"Erro ao atualizar limite. Tente novamente.")
