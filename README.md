# Alice ACP Agent

## Run agent

```sh
pixi run alice
```

## Register in BeeAI

```sh
beeai add src/acp_agent/alice.py
```

## Check agents

```sh
curl http://localhost:8000/agents
```

## Run Client

```sh
pixi run client --agent_name c
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
