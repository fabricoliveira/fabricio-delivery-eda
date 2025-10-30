# Serviço de Eventos e Pedidos

## Visão geral
Projeto que implementa:
- Um consumidor assíncrono de eventos (RabbitMQ via `aio_pika`) responsável por processar eventos relacionados a pedidos (salvar evento, atualizar status do pedido).
- Uma API HTTP leve (FastAPI + Uvicorn) que fornece operações de leitura de pedidos (`obter_pedido`) e endpoint(s) complementares conforme implementação.
Objetivo: processar eventos de forma confiável, com baixa latência, e expor estado de pedidos via HTTP.

## Principais responsabilidades
- Consumir mensagens do broker (RabbitMQ), parsear payloads JSON ou raw, aplicar validações e chamar handlers (`salvar_evento`, `atualizar_status_pedido`).
- Expor endpoint HTTP para consulta de pedidos (ex.: `GET /pedidos/{pedido_id}`).
- Ser executável via Docker Compose (com RabbitMQ e banco de dados).
- Ter tratamento robusto de erros, retries com backoff exponencial e logging estruturado.
- Ser testável localmente (suite de testes em `app/tests/...`).

---

## Requisitos (softwares)
- Sistema operacional: Windows / Linux / macOS (desenvolvimento no Windows suportado).
- Python: 3.11 (recomendado). Verifique com `python --version`.
- Pip: `pip` (ou use `python -m pip`).
- Docker & Docker Compose (opcional, recomendado para execução com infra como RabbitMQ).
- Git (opcional).

Recomendações:
- Criar ambiente virtual: `python -m venv .venv` e ativar (`.venv\Scripts\activate` no Windows ou `source .venv/bin/activate` no Linux/macOS).

---

## Execução com Docker (recomendada)

Este projeto já contém um ambiente adequado para execução com Docker \+ Docker Compose. Use esta opção para reproduzir facilmente a aplicação e dependências (RabbitMQ, banco, etc).

Pré-requisitos:
- Docker instalado
- Docker Compose integrado (`docker compose` disponível)
- (Opcional) Git

1. Clone o repositório:
   - `git clone <https://github.com/fabricoliveira/fabricio-delivery-eda>`
   - `cd <fabricio-delivery-eda>`
   
2. Build e subida dos serviços
   - Na raiz do projeto execute no terminal:
     ```
     docker compose up --build
     ```
   - O comando irá:
     - construir a imagem da aplicação,
     - iniciar RabbitMQ (imagem `rabbitmq:3-management`)
     - iniciar PostgreSQL (imagem `postgres:15`)
     - iniciar a API (Uvicorn) e o consumer.

3. Ver logs e status
   - Para acompanhar logs do app:
     ```
     docker compose logs -f app
     ```
   - Para listar containers em execução:
     ```
     docker compose ps
     ```

4. Parar e remover containers
   - Parar:
     ```
     docker compose stop
     ```
   - Parar e remover (volumes opcionais):
     ```
     docker compose down
     ```
   - Remover volumes (quando necessário):
     ```
     docker compose down -v
     ```

5. Rodar comandos dentro do container da aplicação
   - Abra um shell:
     ```
     docker compose exec app sh
     ```
   - Executar testes dentro do container:
     ```
     docker compose exec app python -m unittest discover -v
     ```
     ou, se usar pytest:
     ```
     docker compose exec app pytest -q
     ```

6. Acessando serviços
   - API (por padrão): `http://localhost:8081`
   - Swagger: `http://localhost:8081/docs`
   - RabbitMQ management UI: `http://localhost:15672` (usuário `rabbitmq`/`1234`)
   - PostgreSQL: `localhost:5432` (usuário `postgres`/`1234`)


---

## Arquitetura (resumo)
- Camadas:
  - API HTTP (FastAPI)
  - Worker/Consumer (async) que consome RabbitMQ
  - Handlers de domínio: `salvar_evento`, `atualizar_status_pedido`
  - Persistência (abstraída; ex.: repositório para PostgreSQL/SQLite/Redis)
- Fluxo (consumer):
  - Conexão com RabbitMQ (robusta com `aio_pika.connect_robust`)
  - Declaração de exchange/queue e binding
  - Iterador assíncrono sobre mensagens (`queue.iterator()`)
  - Para cada mensagem: processar (possível JSON ou raw), chamar `to_thread` apenas para operações síncronas custosas, confirmar/nack conforme resultado.

---

## Estratégias para consistência e baixa latência

- Consistência:
  - Idempotência: eventos devem ser salvos com `id` único; evitar dupla aplicação.
  - Confirmação explícita de mensagens (ack/nack) somente após persistência bem-sucedida.
  - Tratamento de exceções e retries controlados (backoff exponencial configurável).
  - Utilizar transações na camada de persistência (quando aplicável).
  - Outbox Pattern:
    - Garantia de atomicidade entre a alteração de estado no banco e o registro do evento em uma tabela `outbox`.
    - Na mesma transação que altera o pedido, inserir também um registro na tabela `outbox` (event_id, aggregate_id, payload, created_at).
    - Após commit, um worker separado faz publish das entradas pendentes para RabbitMQ e marca `published_at` (ou remove).
    - Worker com retries, backoff, incrementos de `attempts` e descarte da mensagem após N falhas.
    - Idempotência no publish: usar `event_id` (UUID) para evitar publishes duplicados.
    - Benefícios: evita perda de eventos, mantém consistência entre DB e mensagens e permite auditoria.
- Baixa latência:
  - Processamento assíncrono com `asyncio` e `aio_pika`.
  - Evitar bloqueios na event loop: usar `asyncio.to_thread` só quando necessário; priorizar handlers assíncronos.
  - Batch ou flush controlado quando salvar múltiplos eventos (se aplicável).
  - Desacoplamento: produtor -> broker -> consumidor, permitindo escalabilidade horizontal do consumer.
  - Timeouts curtos e limites configuráveis para evitar tarefas presas no event loop.
- Observabilidade:
  - Logs estruturados (nível configurável).
  - Métricas básicas (contagem de eventos processados, falhas, latência de publicação do outbox — `created_at` → `published_at`).


---

## Tecnologias utilizadas e justificativa
- Python 3.11: estabilidade, suporte de typing e performance.
- FastAPI: criação rápida de APIs assíncronas, documentação automática (Swagger).
- Uvicorn: servidor ASGI performático.
- aio-pika: client AMQP assíncrono (bom para integração com RabbitMQ).
- anyio: abstração de I/O assíncrono usada por frameworks.
- Docker / Docker Compose: reproduzibilidade do ambiente e dependências (RabbitMQ, DB).
- PostgreSQL: banco relacional robusto, amplamente usado em produção, suporte a transações e integridade referencial — escolhido como camada de persistência principal para garantir consistência dos eventos e consultas de pedidos.
- unittest / pytest (tests): facilitar testes unitários e mocks.
Justificativa: stack focada em I/O assíncrono para baixa latência e escalabilidade, com ferramentas populares na comunidade Python.

---

## Endpoints (descrição)

1. `POST /fabricio-delivery/pedidos`:
   - Payload:
     ```json
     {
        "destinatario": "teste",
        "endereco": "teste",
        "itens": [{ "produto": 1 }]
     }
     ```
   - Response 201: criado.
2. `GET /fabricio-delivery/pedidos/{pedido_id}`
   - Descrição: retorna representação do pedido com `pedido_id`.
   - Path parameter:
     - `pedido_id` (int) — identificador do pedido.
   - Response 200 (JSON):
     ```json
      {
            "id": 1,
            "destinatario": "string", 
            "endereco": "string",
            "itens": [{ "item": 1 }],
            "status": "entregue",
            "criado_em": "2025-10-30T10:10:29.209036Z"
      }
     ```
   - Response 404:
     ```json
     { "detail": "Pedido não encontrado" }
     ```
3. `GET /fabricio-delivery/pedidos/{pedido_id}/eventos`
   - Descrição: retorna representação dos eventos de um pedido com `pedido_id`.
   - Path parameter:
     - `pedido_id` (int) — identificador do pedido.
   - Response 200 (JSON):
     ```json
     [
         {
            "id": "1-1761819032139",
            "pedido_id": 1,
            "tipo_evento": "entregue",
            "payload": "{\"pedido_id\": 1, \"status\": \"entregue\", \"timestamp\": \"2025-10-30T10:10:31.433317\"}",
            "criado_em": "2025-10-30T10:10:32.139355Z"
         }
     ]
     ```
   - Response 404:
     ```json
     []
     ```

---