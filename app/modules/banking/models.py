# Re-exporta el modelo ORM MovimientoBancario (definido en documents.models).
# Se mantiene aqui un alias para conservar la convencion del modulo banking.
from app.modules.documents.models import MovimientoBancario

__all__ = ["MovimientoBancario"]
