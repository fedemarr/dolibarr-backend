# Parser CSV flexible para extractos bancarios argentinos
import csv
import io
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from typing import Optional
from app.modules.banking.parsers.base import ParserBancarioBase, MovimientoBancarioParsado

NOMBRES_FECHA = {"fecha", "date", "fecha operacion", "fecha mov", "fecha_movimiento", "fecha_operacion"}
NOMBRES_MONTO = {"importe", "monto", "amount"}
NOMBRES_DEBITO = {"debito", "debe", "importe_debito", "debito_credito"}
NOMBRES_CREDITO = {"credito", "haber", "importe_credito"}
NOMBRES_DESCRIPCION = {"descripcion", "concepto", "detalle", "description", "descripcion"}
NOMBRES_REFERENCIA = {"referencia", "nro", "numero", "ref", "comprobante", "numero", "nro_comprobante"}


def _parsear_monto_argentino(valor: str) -> Decimal:
    """Convierte formato argentino (1.234,56) a Decimal"""
    limpio = valor.strip().replace("$", "").replace(" ", "")
    # Si tiene coma: puede ser decimal argentino
    if "," in limpio and "." in limpio:
        # 1.234,56 -> 1234.56
        limpio = limpio.replace(".", "").replace(",", ".")
    elif "," in limpio:
        # puede ser separador decimal o miles
        partes = limpio.split(",")
        if len(partes) == 2 and len(partes[1]) <= 2:
            limpio = limpio.replace(",", ".")
        else:
            limpio = limpio.replace(",", "")
    return Decimal(limpio)


def _parsear_fecha_argentina(valor: str) -> date:
    """Parsea DD/MM/YYYY o DD-MM-YYYY"""
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(valor.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Formato de fecha no reconocido: {valor}")


class CSVParser(ParserBancarioBase):
    """Parser para extractos CSV de bancos argentinos"""

    def parsear(self, contenido: bytes) -> tuple[list[MovimientoBancarioParsado], list[str]]:
        # Detectar encoding
        texto = None
        for encoding in ("utf-8-sig", "latin-1", "utf-8"):
            try:
                texto = contenido.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if texto is None:
            return [], ["No se pudo decodificar el archivo CSV"]

        # Detectar separador
        muestra = texto[:2000]
        sep = ";" if muestra.count(";") > muestra.count(",") else ","

        movimientos = []
        errores = []
        lector = csv.DictReader(io.StringIO(texto), delimiter=sep)

        # Mapear columnas a roles
        columnas = {(c or "").lower().strip(): c for c in (lector.fieldnames or [])}
        col_fecha = next((columnas[k] for k in NOMBRES_FECHA if k in columnas), None)
        col_monto = next((columnas[k] for k in NOMBRES_MONTO if k in columnas), None)
        col_debito = next((columnas[k] for k in NOMBRES_DEBITO if k in columnas), None)
        col_credito = next((columnas[k] for k in NOMBRES_CREDITO if k in columnas), None)
        col_desc = next((columnas[k] for k in NOMBRES_DESCRIPCION if k in columnas), None)
        col_ref = next((columnas[k] for k in NOMBRES_REFERENCIA if k in columnas), None)

        if not col_fecha:
            return [], ["No se encontro columna de fecha en el CSV"]

        for i, fila in enumerate(lector, start=2):
            try:
                fecha = _parsear_fecha_argentina(fila.get(col_fecha, ""))

                # Calcular monto
                if col_monto:
                    val = (fila.get(col_monto) or "").strip()
                    monto = _parsear_monto_argentino(val) if val else Decimal("0")
                elif col_debito and col_credito:
                    val_deb = (fila.get(col_debito) or "").strip()
                    val_cred = (fila.get(col_credito) or "").strip()
                    deb = _parsear_monto_argentino(val_deb) if val_deb else Decimal("0")
                    cred = _parsear_monto_argentino(val_cred) if val_cred else Decimal("0")
                    monto = cred - deb
                else:
                    errores.append(f"Fila {i}: no se encontro columna de monto")
                    continue

                tipo = "CREDITO" if monto >= 0 else "DEBITO"
                descripcion = fila.get(col_desc, "") if col_desc else str(fila)
                referencia = fila.get(col_ref, "") if col_ref else None

                movimientos.append(MovimientoBancarioParsado(
                    fecha=fecha,
                    fecha_valor=None,
                    monto=monto,
                    descripcion=(descripcion or "").strip() or "Sin descripcion",
                    referencia=referencia.strip() if referencia else None,
                    tipo=tipo,
                    datos_raw=dict(fila),
                ))
            except Exception as e:
                errores.append(f"Fila {i}: {str(e)}")

        return movimientos, errores
