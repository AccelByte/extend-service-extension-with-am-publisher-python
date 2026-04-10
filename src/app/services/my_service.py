# Copyright (c) 2023 AccelByte Inc. All Rights Reserved.
# This is licensed software from AccelByte Inc, for limitations
# and restrictions contact your company contract manager.

import json

from datetime import datetime, timezone
from logging import Logger
from typing import Any

from grpc import StatusCode

from accelbyte_py_sdk import AccelByteSDK
from accelbyte_py_sdk.api import cloudsave as cs_service

from service_pb2 import (
    JoinRequest,
    JoinResponse,
    CheckRequest,
    CheckResponse,
    DESCRIPTOR,
)

from service_pb2_grpc import ServiceServicer

from async_messaging.publisher_service_pb2 import PublishMessageRequest
from async_messaging.publisher_service_pb2_grpc import AsyncMessagingPublisherServiceStub


class AsyncService(ServiceServicer):
    full_name: str = DESCRIPTOR.services_by_name["Service"].full_name

    def __init__(
        self,
        sdk: AccelByteSDK,
        logger: Logger,
        publisher_client: AsyncMessagingPublisherServiceStub,
        publish_enabled: bool,
    ) -> None:
        self.sdk = sdk
        self.logger = logger
        self.publisher_client = publisher_client
        self.publish_enabled = publish_enabled

    async def Join(self, request: JoinRequest, context: Any) -> JoinResponse:
        topic = "PlayerJoined"
        event = {
            "eventType": "PlayerJoined",
            "playerId": request.player_id,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        msg = PublishMessageRequest(
            body=json.dumps(event),
            topic=topic,
            metadata={"PlayerId": request.player_id},
        )
        if not self.publish_enabled:
            self.logger.info(f"Publishing disabled - message would be published: {msg}")
        else:
            await self.publisher_client.PublishMessage(msg)
        return JoinResponse()

    async def Check(self, request: CheckRequest, context: Any) -> CheckResponse:
        key = f"player_joined_event_{request.player_id}"
        _, error = await cs_service.admin_get_game_record_handler_v1_async(
            key=key,
            namespace=request.namespace,
            sdk=self.sdk,
        )
        if error:
            return CheckResponse(status="data not found")
        return CheckResponse(status="joined")
