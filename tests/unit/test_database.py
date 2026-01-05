"""Testes unitários para operações de database."""
import os
import csv
import pytest

from src.data_models.database import Database


class TestDatabaseAutenticacao:
    """Testes para autenticação no database."""

    def test_autenticar_cliente_sucesso(self, mock_database, sample_cliente):
        """Testa autenticação bem-sucedida."""
        cliente = mock_database.autenticar_cliente(
            sample_cliente.cpf,
            sample_cliente.data_nascimento
        )

        assert cliente is not None
        assert cliente.cpf == sample_cliente.cpf
        assert cliente.nome == sample_cliente.nome
        assert cliente.limite_credito == sample_cliente.limite_credito
        assert cliente.score == sample_cliente.score

    def test_autenticar_cliente_cpf_incorreto(self, mock_database):
        """Testa autenticação com CPF incorreto."""
        cliente = mock_database.autenticar_cliente("99999999999", "1990-05-15")

        assert cliente is None

    def test_autenticar_cliente_data_incorreta(self, mock_database, sample_cliente):
        """Testa autenticação com data incorreta."""
        cliente = mock_database.autenticar_cliente(sample_cliente.cpf, "1990-12-31")

        assert cliente is None

    def test_autenticar_arquivo_inexistente(self, temp_data_dir):
        """Testa erro quando arquivo não existe."""
        db = Database(base_path=temp_data_dir)

        with pytest.raises(FileNotFoundError):
            db.autenticar_cliente("12345678901", "1990-05-15")


class TestDatabaseObterCliente:
    """Testes para obter cliente do database."""

    def test_obter_cliente_sucesso(self, mock_database, sample_cliente):
        """Testa obter cliente com sucesso."""
        cliente = mock_database.obter_cliente(sample_cliente.cpf)

        assert cliente is not None
        assert cliente.cpf == sample_cliente.cpf
        assert cliente.nome == sample_cliente.nome

    def test_obter_cliente_inexistente(self, mock_database):
        """Testa obter cliente que não existe."""
        cliente = mock_database.obter_cliente("99999999999")

        assert cliente is None

    def test_obter_cliente_arquivo_inexistente(self, temp_data_dir):
        """Testa erro quando arquivo não existe."""
        db = Database(base_path=temp_data_dir)

        with pytest.raises(FileNotFoundError):
            db.obter_cliente("12345678901")


class TestDatabaseAtualizarScore:
    """Testes para atualizar score no database."""

    def test_atualizar_score_sucesso(self, mock_database, sample_cliente):
        """Testa atualização de score com sucesso."""
        novo_score = 750
        resultado = mock_database.atualizar_score(sample_cliente.cpf, novo_score)

        assert resultado is True

        cliente = mock_database.obter_cliente(sample_cliente.cpf)
        assert cliente.score == novo_score

    def test_atualizar_score_cliente_inexistente(self, mock_database):
        """Testa atualização de score para cliente inexistente."""
        resultado = mock_database.atualizar_score("99999999999", 750)

        assert resultado is True

    def test_atualizar_score_arquivo_inexistente(self, temp_data_dir):
        """Testa erro quando arquivo não existe."""
        db = Database(base_path=temp_data_dir)

        with pytest.raises(FileNotFoundError):
            db.atualizar_score("12345678901", 750)

    def test_atualizar_score_multiplos_clientes(self, mock_database):
        """Testa que atualiza apenas o cliente correto."""
        mock_database.atualizar_score("12345678901", 800)

        cliente1 = mock_database.obter_cliente("12345678901")
        assert cliente1.score == 800

        cliente2 = mock_database.obter_cliente("98765432100")
        assert cliente2.score == 850  # Score original


class TestDatabaseVerificarLimite:
    """Testes para verificar limite permitido."""

    def test_verificar_limite_permitido(self, mock_database):
        """Testa limite dentro do permitido para o score."""
        permitido = mock_database.verificar_limite_permitido(650, 8000.0)

        assert permitido is True

    def test_verificar_limite_acima_permitido(self, mock_database):
        """Testa limite acima do permitido para o score."""
        permitido = mock_database.verificar_limite_permitido(650, 15000.0)

        assert permitido is False

    def test_verificar_limite_exato(self, mock_database):
        """Testa limite exatamente no máximo permitido."""
        permitido = mock_database.verificar_limite_permitido(650, 10000.0)

        assert permitido is True

    def test_verificar_limite_score_baixo(self, mock_database):
        """Testa limite para score baixo."""
        permitido = mock_database.verificar_limite_permitido(350, 3000.0)
        assert permitido is True

        permitido = mock_database.verificar_limite_permitido(350, 8000.0)
        assert permitido is False

    def test_verificar_limite_score_alto(self, mock_database):
        """Testa limite para score alto."""
        permitido = mock_database.verificar_limite_permitido(850, 40000.0)
        assert permitido is True

    def test_verificar_limite_arquivo_inexistente(self, temp_data_dir):
        """Testa erro quando arquivo não existe."""
        db = Database(base_path=temp_data_dir)

        with pytest.raises(FileNotFoundError):
            db.verificar_limite_permitido(650, 8000.0)


class TestDatabaseSolicitacoes:
    """Testes para solicitações de aumento."""

    def test_criar_solicitacao_sucesso(self, mock_database, sample_cliente):
        """Testa criação de solicitação com sucesso."""
        data_hora = mock_database.criar_solicitacao_aumento(
            sample_cliente.cpf,
            sample_cliente.limite_credito,
            8000.0
        )

        assert data_hora is not None
        assert isinstance(data_hora, str)

        assert os.path.exists(mock_database.solicitacoes_file)

    def test_criar_solicitacao_cria_diretorio(self, temp_data_dir):
        """Testa que cria diretório se não existir."""
        novo_dir = os.path.join(temp_data_dir, "novo_dir")
        db = Database(base_path=novo_dir)

        data_hora = db.criar_solicitacao_aumento("12345678901", 5000.0, 8000.0)

        assert data_hora is not None
        assert os.path.exists(novo_dir)

    def test_criar_solicitacao_status_pendente(self, mock_database, sample_cliente):
        """Testa que solicitação é criada com status pendente."""
        data_hora = mock_database.criar_solicitacao_aumento(
            sample_cliente.cpf,
            sample_cliente.limite_credito,
            8000.0
        )

        with open(mock_database.solicitacoes_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            solicitacoes = list(reader)
            assert len(solicitacoes) > 0
            ultima = solicitacoes[-1]
            assert ultima['status_pedido'] == 'pendente'
            assert ultima['cpf_cliente'] == sample_cliente.cpf

    def test_atualizar_status_solicitacao_aprovado(self, mock_database, sample_cliente):
        """Testa atualização de status para aprovado."""
        data_hora = mock_database.criar_solicitacao_aumento(
            sample_cliente.cpf,
            sample_cliente.limite_credito,
            8000.0
        )

        resultado = mock_database.atualizar_status_solicitacao(
            sample_cliente.cpf,
            data_hora,
            'aprovado',
            atualizar_limite=True,
            novo_limite=8000.0
        )

        assert resultado is True

        cliente = mock_database.obter_cliente(sample_cliente.cpf)
        assert cliente.limite_credito == 8000.0

    def test_atualizar_status_solicitacao_rejeitado(self, mock_database, sample_cliente):
        """Testa atualização de status para rejeitado."""
        data_hora = mock_database.criar_solicitacao_aumento(
            sample_cliente.cpf,
            sample_cliente.limite_credito,
            8000.0
        )

        limite_original = sample_cliente.limite_credito

        resultado = mock_database.atualizar_status_solicitacao(
            sample_cliente.cpf,
            data_hora,
            'rejeitado'
        )

        assert resultado is True

        cliente = mock_database.obter_cliente(sample_cliente.cpf)
        assert cliente.limite_credito == limite_original

    def test_atualizar_status_arquivo_inexistente(self, temp_data_dir, sample_cliente):
        """Testa erro quando arquivo de solicitações não existe."""
        db = Database(base_path=temp_data_dir)

        with pytest.raises(FileNotFoundError):
            db.atualizar_status_solicitacao(
                sample_cliente.cpf,
                "2024-01-01T10:00:00",
                'aprovado'
            )


class TestDatabaseIntegracao:
    """Testes de integração das operações de database."""

    def test_fluxo_completo_aumento_aprovado(self, mock_database, sample_cliente):
        """Testa fluxo completo de solicitação aprovada."""
        cliente = mock_database.autenticar_cliente(
            sample_cliente.cpf,
            sample_cliente.data_nascimento
        )
        assert cliente is not None

        novo_limite = 8000.0
        permitido = mock_database.verificar_limite_permitido(cliente.score, novo_limite)
        assert permitido is True

        data_hora = mock_database.criar_solicitacao_aumento(
            cliente.cpf,
            cliente.limite_credito,
            novo_limite
        )
        assert data_hora is not None

        resultado = mock_database.atualizar_status_solicitacao(
            cliente.cpf,
            data_hora,
            'aprovado',
            atualizar_limite=True,
            novo_limite=novo_limite
        )
        assert resultado is True

        cliente_atualizado = mock_database.obter_cliente(cliente.cpf)
        assert cliente_atualizado.limite_credito == novo_limite

    def test_fluxo_completo_aumento_rejeitado(self, mock_database, sample_cliente_baixo_score):
        """Testa fluxo completo de solicitação rejeitada."""
        cliente = mock_database.obter_cliente(sample_cliente_baixo_score.cpf)
        assert cliente is not None

        limite_original = cliente.limite_credito

        novo_limite = 10000.0
        permitido = mock_database.verificar_limite_permitido(cliente.score, novo_limite)
        assert permitido is False

        data_hora = mock_database.criar_solicitacao_aumento(
            cliente.cpf,
            cliente.limite_credito,
            novo_limite
        )

        resultado = mock_database.atualizar_status_solicitacao(
            cliente.cpf,
            data_hora,
            'rejeitado'
        )
        assert resultado is True

        cliente_final = mock_database.obter_cliente(cliente.cpf)
        assert cliente_final.limite_credito == limite_original
