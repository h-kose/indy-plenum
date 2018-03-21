from abc import ABCMeta
from typing import List, Generic, TypeVar

from plenum.common.constants import MSG_SER, MSG_FROM, MSG_PAYLOAD_PROTOCOL_VERSION, MSG_PAYLOAD_DATA, \
    MSG_PAYLOAD_METADATA, MSG_SIGNATURE_TYPE, \
    SIGNATURE_ED25519, SIGNATURE_ED25519_MULTI, MSG_SIGNATURE_VALUES, MSG_SIGNATURE_VALUES_FROM, SERIALIZATION_MSG_PACK, \
    MSG_SIGNATURE_THRESHOLD, MSG_SIGNATURE, MSG_DATA, MSG_DATA_SERIALIZED, MSG_PAYLOAD_PLUGIN_DATA, \
    MSG_SIGNATURE_VALUES_VALUE
from plenum.common.messages.fields import NonEmptyStringField, NonNegativeNumberField, AnyMapField, \
    EnumField, IterableField, LimitedLengthStringField, SerializedValueField
from plenum.common.messages.message_base import MessageBase, MessageField
from plenum.config import SIGNATURE_FIELD_LIMIT


class SignatureValue(MessageBase):
    schema = (
        ("frm", MSG_SIGNATURE_VALUES_FROM, NonEmptyStringField()),
        ("value", MSG_SIGNATURE_VALUES_VALUE, LimitedLengthStringField(max_length=SIGNATURE_FIELD_LIMIT))
    )

    def __init__(self, frm: str = None, value: str = None):
        self.frm = frm
        self.value = value


class Signature(MessageBase):
    schema = (
        ("type", MSG_SIGNATURE_TYPE,
         EnumField(expected_values=[SIGNATURE_ED25519, SIGNATURE_ED25519_MULTI])),
        ("values", MSG_SIGNATURE_VALUES,
         IterableField(MessageField(cls=SignatureValue))),
        ("threshold", MSG_SIGNATURE_THRESHOLD, NonNegativeNumberField(optional=True))
    )

    def __init__(self, type: str = None, values: List[SignatureValue] = None, threshold: int = None):
        self.type = type
        self.values = values
        self.threshold = threshold


class MessageMetadata(MessageBase):
    pass


class MessageData(MessageBase, metaclass=ABCMeta):
    pass


D = TypeVar('D')
MD = TypeVar('MD')


class Message(MessageBase, Generic[D, MD]):
    typename = None
    version = 0
    dataCls = MessageData
    metadataCls = MessageMetadata

    def __init__(self, protocol_version: int = None, frm: str = None, data: D = None, metadata: MD = None,
                 plugin_data=None):
        self.schema = (
            ("frm", MSG_FROM, NonEmptyStringField()),
            ("protocol_version", MSG_PAYLOAD_PROTOCOL_VERSION, NonNegativeNumberField(optional=True)),
            ("data", MSG_PAYLOAD_DATA, MessageField(cls=self.dataCls)),
            ("metadata", MSG_PAYLOAD_METADATA, MessageField(cls=self.metadataCls)),
            ("plugin_data", MSG_PAYLOAD_PLUGIN_DATA, AnyMapField(optional=True))
        )

        self.frm = frm
        self.protocol_version = protocol_version
        self.data = data
        self.metadata = metadata
        self.plugin_data = plugin_data


M = TypeVar('M')


class SignedMessage(MessageBase, Generic[M]):
    typename = None
    version = 0

    msgCls = Message

    def __init__(self, serialization: str = None, msg_serialized: bytes = None, msg: M = None,
                 signature: Signature = None):
        self.schema = (
            # assume MsgPack by default
            ("serialization", MSG_SER, EnumField(expected_values=[SERIALIZATION_MSG_PACK], optional=True)),
            ("msg_serialized", MSG_DATA_SERIALIZED, SerializedValueField()),
            ("signature", MSG_SIGNATURE, MessageField(cls=Signature)),
            ("msg", MSG_DATA, MessageField(cls=self.msgCls, optional=True)),
        )

        self.serialization = serialization
        self.msg_serialized = msg_serialized
        self.msg = msg
        self.signature = signature