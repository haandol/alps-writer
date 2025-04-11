import json
import socketio.packet
from typing import Any
from decimal import Decimal

from src.utils.logger import logger


class DecimalEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that converts Decimal values to float.

    This encoder is needed for DynamoDB as it returns decimal.Decimal objects
    which are not JSON serializable by default.
    """

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def patch_chainlit_json():
    """
    Patch the Chainlit JSON serialization to handle Decimal values.
    This function monkey patches both the standard json.dumps function
    and the socketio.packet JSON encoder.
    """
    try:
        # patch the standard json.dumps function
        original_dumps = json.dumps

        def patched_dumps(obj: Any, *args: Any, **kwargs: Any) -> str:
            if 'cls' not in kwargs:
                kwargs['cls'] = DecimalEncoder
            return original_dumps(obj, *args, **kwargs)

        json.dumps = patched_dumps

        # 2. Patch socketio's JSON encoder
        if hasattr(socketio.packet, 'Packet'):
            # Store original JSON encoder
            original_json = socketio.packet.Packet.json

            # Create a patched JSON class that uses our DecimalEncoder
            class PatchedJSON:
                @staticmethod
                def dumps(obj, *args, **kwargs):
                    # Don't override cls if it's already set
                    if 'cls' not in kwargs:
                        kwargs['cls'] = DecimalEncoder
                    elif kwargs['cls'] is None:
                        kwargs['cls'] = DecimalEncoder
                    return original_json.dumps(obj, *args, **kwargs)

                @staticmethod
                def loads(s, *args, **kwargs):
                    return original_json.loads(s, *args, **kwargs)

            # Replace socketio's JSON encoder
            socketio.packet.Packet.json = PatchedJSON

        logger.info(
            "Successfully patched JSON serialization for both standard json and socketio")
    except Exception as e:
        logger.error("Failed to patch JSON serialization", error=e)
