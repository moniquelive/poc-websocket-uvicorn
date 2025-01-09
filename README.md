# poc-websocket-uvicorn

Projeto de demonstração de como usar o websocket com o Uvicorn com comunicação entre processos através de Redis.

## Projetos utilizados

- [FastAPI+Websocket](https://fastapi.tiangolo.com/advanced/websockets/?h=webs#handling-disconnections-and-multiple-clients)
- [Redis](https://redis.io/)
- [Uvicorn](https://www.uvicorn.org/)
- [Pydantic](https://pydantic-docs.helpmanual.io/)
- [Broadcaster](https://github.com/encode/broadcaster)
- [AnyIO](https://anyio.readthedocs.io/en/stable/)

## Como rodar

```bash
uvicorn main:app --workers 2 --port 8000 (ou 9000)
```

## Como usar

```bash
curl -X POST -d '{"client_id": "id do chat", "message": "Hello World"}' http://localhost:8000/send (ou :9000)
```

## Alguns comandos uteis no Redis

- `pubsub channels` - lista quais filas estão sendo escutadas
- `pubsub numsub _numero da fila_` - lista quantos subscribers estão ouvindo esta fila
- `publish _nome da fila_ _mensagem_` - envia "mensagem" diretamente pra fila

### Nota

`client_id` e `fila` são a mesma coisa
