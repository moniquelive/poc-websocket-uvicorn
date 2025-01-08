# poc-websocket-superatendente

## Como rodar

```bash
uvicorn main:app --reload
```

## Como usar

```bash
curl -X POST -d '{"client_id": "id do chat", "message": "Hello World"}' http://localhost:8000/send
```

## Alguns comandos uteis no Redis

`pubsub channels` - lista quais filas estão sendo escutadas
`pubsub numsub _numero da fila_` - lista quantos subscribers estão ouvindo esta fila
`publish _nome da fila_ _mensagem_` - envia "mensagem" diretamente pra fila

### OBS

`client_id` e `fila` são a mesma coisa