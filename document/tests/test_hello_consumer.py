import pytest
import json
from channels.testing import WebsocketCommunicator
from iransanad.consumer import HelloWorldConsumer
from iransanad.asgi import application
from django.test import override_settings

@pytest.mark.asyncio
async def test_hello_world_consumer():
    communicator = WebsocketCommunicator(application, "/ws/helloworld/")
    connected, _ = await communicator.connect()
    assert connected
    # Initial message assertion
    initial_response = await communicator.receive_json_from()
    assert initial_response == {"message": "Hello World from WebSocket!"}

    # Echo test
    await communicator.send_json_to({"message": "Test Message"})
    response = await communicator.receive_json_from()
    assert response == {"message": "You said: Test Message"}

    await communicator.disconnect()
