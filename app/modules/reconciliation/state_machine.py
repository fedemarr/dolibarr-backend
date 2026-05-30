# Controla el ciclo de vida de cada documento impositivo
from enum import Enum
from app.core.exceptions import ErrorApp


class EstadoDocumento(str, Enum):
    SUBIDO = "UPLOADED"
    PROCESANDO = "PROCESSING"
    CLASIFICADO = "CLASSIFIED"
    REQUIERE_REVISION = "PENDING_REVIEW"
    APROBADO = "APPROVED"
    SINCRONIZADO = "SYNCED"
    PAGADO = "PAID"
    CONCILIADO = "RECONCILED"
    ERROR = "ERROR"


# Transiciones permitidas entre estados
TRANSICIONES: dict[EstadoDocumento, list[EstadoDocumento]] = {
    EstadoDocumento.SUBIDO: [EstadoDocumento.PROCESANDO, EstadoDocumento.ERROR],
    EstadoDocumento.PROCESANDO: [
        EstadoDocumento.CLASIFICADO,
        EstadoDocumento.REQUIERE_REVISION,
        EstadoDocumento.ERROR,
    ],
    EstadoDocumento.CLASIFICADO: [
        EstadoDocumento.APROBADO,
        EstadoDocumento.REQUIERE_REVISION,
    ],
    EstadoDocumento.REQUIERE_REVISION: [
        EstadoDocumento.APROBADO,
        EstadoDocumento.ERROR,
    ],
    EstadoDocumento.APROBADO: [EstadoDocumento.SINCRONIZADO, EstadoDocumento.ERROR],
    EstadoDocumento.SINCRONIZADO: [EstadoDocumento.PAGADO, EstadoDocumento.CONCILIADO],
    EstadoDocumento.PAGADO: [EstadoDocumento.CONCILIADO],
    EstadoDocumento.CONCILIADO: [],
    EstadoDocumento.ERROR: [EstadoDocumento.SUBIDO],
}


class ErrorMaquinaEstados(ErrorApp):
    def __init__(self, mensaje: str):
        super().__init__(status_code=409, code="TRANSICION_INVALIDA", message=mensaje)


def transicionar(actual: EstadoDocumento, destino: EstadoDocumento) -> EstadoDocumento:
    """
    Valida y ejecuta una transicion de estado.
    Lanza ErrorMaquinaEstados si la transicion no esta permitida.
    """
    permitidas = TRANSICIONES.get(actual, [])
    if destino not in permitidas:
        raise ErrorMaquinaEstados(
            f"Transicion no permitida: {actual.value} -> {destino.value}. "
            f"Desde {actual.value} se puede ir a: {[e.value for e in permitidas]}"
        )
    return destino


async def transicionar_y_registrar(
    documento,
    destino: EstadoDocumento,
    actor_id,
    tipo_actor: str,
    db,
    detalle: str = "",
):
    """
    Transiciona el estado del documento Y registra el cambio en log_auditoria.
    Siempre usar esta funcion en vez de transicionar() directamente.
    """
    from datetime import datetime, timezone
    from app.modules.reconciliation.events import registrar_auditoria

    estado_anterior = documento.estado
    nuevo_estado = transicionar(EstadoDocumento(documento.estado), destino)
    documento.estado = nuevo_estado.value
    documento.actualizado_en = datetime.now(timezone.utc)

    await registrar_auditoria(
        db=db,
        org_id=str(documento.org_id),
        tipo_entidad="documento_impositivo",
        id_entidad=str(documento.id),
        accion=f"CAMBIO_ESTADO_{destino.value}",
        estado_anterior={"estado": estado_anterior},
        estado_nuevo={"estado": nuevo_estado.value, "detalle": detalle},
        actor_id=actor_id,
        tipo_actor=tipo_actor,
    )
    return documento
