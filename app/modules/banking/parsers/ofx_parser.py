# Parser para archivos OFX/QFX (formato estandar bancario)
import re
from decimal import Decimal
from datetime import date, datetime
from typing import Optional
from app.modules.banking.parsers.base import ParserBancarioBase, MovimientoBancarioParsado


class OFXParser(ParserBancarioBase):
    """Parser para extractos OFX/QFX"""

    def parsear(self, contenido: bytes) -> tuple[list[MovimientoBancarioParsado], list[str]]:
        # Intentar usar ofxparse primero; fallback a regex manual
        try:
            return self._parsear_con_libreria(contenido)
        except Exception:
            return self._parsear_con_regex(contenido)

    def _parsear_con_libreria(self, contenido: bytes):
        from ofxparse import OfxParser as OfxParseLib
        import io
        movimientos = []
        errores = []
        ofx = OfxParseLib.parse(io.BytesIO(contenido))
        cuentas = []
        if hasattr(ofx, 'accounts') and ofx.accounts:
            cuentas = ofx.accounts
        elif hasattr(ofx, 'account') and ofx.account:
            cuentas = [ofx.account]

        for cuenta in cuentas:
            statement = getattr(cuenta, 'statement', None)
            if statement is None:
                continue
            for txn in getattr(statement, 'transactions', []):
                try:
                    monto = Decimal(str(txn.amount))
                    tipo = "CREDITO" if monto >= 0 else "DEBITO"
                    fecha_val = txn.date.date() if hasattr(txn.date, 'date') else txn.date
                    movimientos.append(MovimientoBancarioParsado(
                        fecha=fecha_val,
                        fecha_valor=None,
                        monto=monto,
                        descripcion=str(txn.memo or txn.payee or "Sin descripcion"),
                        referencia=str(txn.id) if txn.id else None,
                        tipo=tipo,
                        datos_raw={"id": str(txn.id), "type": str(txn.type)},
                    ))
                except Exception as e:
                    errores.append(f"Transaccion OFX invalida: {e}")
        return movimientos, errores

    def _parsear_con_regex(self, contenido: bytes):
        """Fallback manual si ofxparse no esta disponible o falla"""
        texto = None
        for enc in ("utf-8", "latin-1"):
            try:
                texto = contenido.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        if texto is None:
            return [], ["No se pudo decodificar el archivo OFX"]

        movimientos = []
        errores = []
        bloques = re.findall(r'<STMTTRN>(.*?)</STMTTRN>', texto, re.DOTALL | re.IGNORECASE)

        for bloque in bloques:
            try:
                def extraer(tag):
                    m = re.search(rf'<{tag}>(.*?)(?:<|$)', bloque, re.IGNORECASE)
                    return m.group(1).strip() if m else None

                fecha_str = extraer("DTPOSTED") or extraer("DTUSER") or ""
                monto_str = extraer("TRNAMT") or "0"
                descripcion = extraer("NAME") or extraer("MEMO") or "Sin descripcion"
                referencia = extraer("FITID")

                # Parsear fecha OFX: YYYYMMDDHHMMSS o YYYYMMDD
                fecha_limpia = fecha_str[:8]
                fecha = datetime.strptime(fecha_limpia, "%Y%m%d").date()

                monto = Decimal(monto_str.replace(",", "."))
                tipo = "CREDITO" if monto >= 0 else "DEBITO"

                movimientos.append(MovimientoBancarioParsado(
                    fecha=fecha,
                    fecha_valor=None,
                    monto=monto,
                    descripcion=descripcion,
                    referencia=referencia,
                    tipo=tipo,
                    datos_raw={"bloque": bloque[:200]},
                ))
            except Exception as e:
                errores.append(f"Bloque OFX invalido: {e}")

        return movimientos, errores
