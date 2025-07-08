# Alice & Bob ACP Agents

Retrieves Francisco's CV from an MCP server throught Alice and Bob ACP agents deployed on BeeAI

## Requirements

- pixi
- uv

## TL;DR

```sh
# Install agents
make alice bob
# Trigger Francisco's CV retrieval from Bob through Alice as proxy
make client ARGS="--msg 'Hello, Francisco!'"
```


## Run agents in dev mode

```sh
pixi run alice-test
pixi run bob-test
```

## Register in BeeAI in dev mode

```sh
beeai add alice/src/agentic_protocols/alice_acp/alice.py
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

### Adding Agents to BeeAI through Dockerfiles

Local:

```sh
make alice
make bob
```

If they are in Github:

```sh
beeai add -v https://github.com/francisco-perez-sorrosal/agentic_protocols.git\#main:alice # Point to alice dir specifically
beeai add -v https://github.com/francisco-perez-sorrosal/agentic_protocols.git\#main:bob # Point to bob dir specifically
```

### Running the Client

```sh
make client
```

## Reference/Old Stuff

### Create Python Wheels with Pixi (Used in Dockerfile)

```sh
pixi install
pixi run build-wheel
pixi run install-wheel
```

### Manual creation (NOT USEFUL as this process goes through the BeeAI platform. This is just for illustration purposes)

```sh
docker --debug build --progress=plain -t alice-agentic-protocols -f Dockerfile.alice .
docker run --rm -it -p 8000:8000 alice-agentic-protocols
docker --debug build --build-arg AGENT_NAME="alice" --build-arg AGENT_PORT="8000" --progress=plain -t alice-agentic-protocols .
docker --debug build --build-arg AGENT_NAME="bob" --build-arg AGENT_PORT="8001" --progress=plain -t bob-agentic-protocols .
docker run --rm -it -p 8000:8000 alice-agentic-protocols
docker run --rm -it -p 8001:8001 bob-agentic-protocols
```
