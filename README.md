# Alice & Bob ACP Agents

## Run agents

```sh
pixi run alice-test
pixi run bob-test
```

## Register in BeeAI

```sh
beeai add src/agentic_protocols/alice_acp/alice.py
```

## Check agents

```sh
curl http://localhost:8000/agents
```

## Run ACP Client

```sh
pixi run client
```

or...

```sh
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{
        "agent_name": "cv",
        "input": [
          {
            "role": "user",
            "parts": [
            ]
          }
        ]
      }'
```


## TODO The below commands with docker do not publish the Bob agent for whatever reason

### Create Docker Images and Run them

```sh
pixi install
pixi run build-wheel
pixi run install-wheel

docker --debug build --progress=plain -t alice-agentic-protocols -f Dockerfile.alice .
docker run --rm -it -p 8000:8000 alice-agentic-protocols
```

```sh
docker --debug build --build-arg AGENT_NAME="alice" --build-arg AGENT_PORT="8000" --progress=plain -t alice-agentic-protocols .
docker --debug build --build-arg AGENT_NAME="bob" --build-arg AGENT_PORT="8001" --progress=plain -t bob-agentic-protocols .
docker run --rm -it -p 8000:8000 alice-agentic-protocols
docker run --rm -it -p 8001:8001 bob-agentic-protocols
```
