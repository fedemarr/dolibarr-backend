# Servicio de negocio para el modulo bancario
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.banking import repository
from app.modules.banking.parsers.csv_parser import CSVParser
from app.modules.banking.parsers.ofx_parser import OFXParser
from app.core.exceptions import ErrorApp


async def importar_archivo(
    contenido: bytes,
    formato: str,
    cuenta: str,
    org_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """
    Parsea un extracto bancario y guarda los movimientos en la DB.
    Retorna {"importados": N, "duplicados": M, "errores": K, "detalle_errores": [...]}
    """
    formato = (formato or "").lower().strip()
    if formato == "csv":
        parser = CSVParser()
    elif formato in ("ofx", "qfx"):
        parser = OFXParser()
    else:
        raise ErrorApp(
            status_code=400,
            code="FORMATO_INVALIDO",
            message=f"Formato no soportado: {formato}. Use 'csv' u 'ofx'",
        )

    movimientos_parseados, errores_parseo = parser.parsear(contenido)

    importados = 0
    duplicados = 0

    for mov in movimientos_parseados:
        try:
            datos = {
                "cuenta_bancaria": cuenta,
                "fecha_movimiento": mov.fecha,
                "fecha_valor": mov.fecha_valor,
                "monto": Decimal(str(mov.monto)),
                "descripcion": mov.descripcion,
                "referencia": mov.referencia,
                "tipo_movimiento": mov.tipo,
                "datos_raw": mov.datos_raw,
                "conciliado": False,
            }
            _, es_nuevo = await repository.crear_movimiento(datos, org_id, db)
            if es_nuevo:
                importados += 1
            else:
                duplicados += 1
        except Exception as e:
            errores_parseo.append(f"Error al guardar movimiento: {e}")

    return {
        "importados": importados,
        "duplicados": duplicados,
        "errores": len(errores_parseo),
        "detalle_errores": errores_parseo[:20],
    }
