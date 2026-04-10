import json
from unittest.mock import AsyncMock, MagicMock, patch

import grpc
import grpc.aio
import pytest
from grpc import StatusCode

from app.services.my_service import AsyncService
from service_pb2 import JoinRequest, CheckRequest
from service_pb2_grpc import add_ServiceServicer_to_server, ServiceStub


@pytest.fixture
def publisher_client():
    mock = MagicMock()
    mock.PublishMessage = AsyncMock()
    return mock


@pytest.fixture
def grpc_context():
    return AsyncMock()


@pytest.fixture
def service(publisher_client):
    return AsyncService(
        sdk=MagicMock(),
        logger=MagicMock(),
        publisher_client=publisher_client,
        publish_enabled=True,
    )


@pytest.fixture
def service_disabled(publisher_client):
    return AsyncService(
        sdk=MagicMock(),
        logger=MagicMock(),
        publisher_client=publisher_client,
        publish_enabled=False,
    )


# --- Join tests ---

async def test_join_publishes_correct_message(service, publisher_client, grpc_context):
    request = JoinRequest(player_id="player1")
    await service.Join(request, grpc_context)

    publisher_client.PublishMessage.assert_called_once()
    msg = publisher_client.PublishMessage.call_args[0][0]

    body = json.loads(msg.body)
    assert body["eventType"] == "PlayerJoined"
    assert body["playerId"] == "player1"
    assert "timestamp" in body

    assert msg.topic == "PlayerJoined"
    assert msg.metadata["PlayerId"] == "player1"


async def test_join_disabled_does_not_publish(service_disabled, publisher_client, grpc_context):
    request = JoinRequest(player_id="player1")
    response = await service_disabled.Join(request, grpc_context)

    publisher_client.PublishMessage.assert_not_called()
    assert response == response.__class__()  # JoinResponse()


async def test_join_publisher_error_aborts_with_internal(service, publisher_client, grpc_context):
    publisher_client.PublishMessage.side_effect = Exception("connection refused")

    request = JoinRequest(player_id="player1")
    await service.Join(request, grpc_context)

    grpc_context.abort.assert_called_once()
    code, message = grpc_context.abort.call_args[0]
    assert code == StatusCode.INTERNAL
    assert "failed to publish message" in message


async def test_join_publisher_error_raises_grpc_error():
    publisher_client = MagicMock()
    publisher_client.PublishMessage = AsyncMock(side_effect=Exception("connection refused"))

    handler = AsyncService(
        sdk=MagicMock(),
        logger=MagicMock(),
        publisher_client=publisher_client,
        publish_enabled=True,
    )

    server = grpc.aio.server()
    add_ServiceServicer_to_server(handler, server)
    port = server.add_insecure_port("[::]:0")
    await server.start()

    try:
        async with grpc.aio.insecure_channel(f"localhost:{port}") as channel:
            stub = ServiceStub(channel)
            with pytest.raises(grpc.aio.AioRpcError) as exc_info:
                await stub.Join(JoinRequest(player_id="player1"))
            assert exc_info.value.code() == grpc.StatusCode.INTERNAL
    finally:
        await server.stop(0)


# --- Check tests ---

async def test_check_returns_joined_when_record_exists(service, grpc_context):
    with patch(
        "app.services.my_service.cs_service.admin_get_game_record_handler_v1_async",
        new=AsyncMock(return_value=({"some": "data"}, None)),
    ):
        request = CheckRequest(player_id="player1", namespace="test-ns")
        response = await service.Check(request, grpc_context)

    assert response.status == "joined"


async def test_check_returns_not_found_when_record_missing(service, grpc_context):
    with patch(
        "app.services.my_service.cs_service.admin_get_game_record_handler_v1_async",
        new=AsyncMock(return_value=(None, Exception("not found"))),
    ):
        request = CheckRequest(player_id="player1", namespace="test-ns")
        response = await service.Check(request, grpc_context)

    assert response.status == "data not found"
