from enum import Enum


class Situacao(Enum):
    PEDIDO_RECEBIDO = 1
    PEDIDO_EM_SEPARACAO = 2
    PEDIDO_EM_TRANSPORTE = 3
    PEDIDO_ENTREGUE = 4
    PEDIDO_CANCELADO = 5
