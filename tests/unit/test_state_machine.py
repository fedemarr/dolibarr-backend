# Tests de la maquina de estados
import pytest

from app.modules.reconciliation.state_machine import (
    EstadoDocumento,
    transicionar,
    ErrorMaquinaEstados,
)


def test_transicion_valida_subido_a_procesando():
    nuevo = transicionar(EstadoDocumento.SUBIDO, EstadoDocumento.PROCESANDO)
    assert nuevo == EstadoDocumento.PROCESANDO


def test_transicion_invalida_conciliado_a_subido_lanza():
    with pytest.raises(ErrorMaquinaEstados):
        transicionar(EstadoDocumento.CONCILIADO, EstadoDocumento.SUBIDO)


def test_transicion_error_a_subido_es_valida():
    nuevo = transicionar(EstadoDocumento.ERROR, EstadoDocumento.SUBIDO)
    assert nuevo == EstadoDocumento.SUBIDO


def test_transicion_procesando_a_clasificado():
    nuevo = transicionar(EstadoDocumento.PROCESANDO, EstadoDocumento.CLASIFICADO)
    assert nuevo == EstadoDocumento.CLASIFICADO


def test_transicion_aprobado_a_sincronizado():
    nuevo = transicionar(EstadoDocumento.APROBADO, EstadoDocumento.SINCRONIZADO)
    assert nuevo == EstadoDocumento.SINCRONIZADO


def test_transicion_aprobado_a_subido_invalida():
    with pytest.raises(ErrorMaquinaEstados):
        transicionar(EstadoDocumento.APROBADO, EstadoDocumento.SUBIDO)
