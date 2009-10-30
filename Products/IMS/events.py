from zope.interface import implements
from zope.component.interfaces import ObjectEvent

from Products.IMS import interfaces

class MessageBeforeDelete(ObjectEvent):
    """An event signalling that a message is going to be deleted
    """
    implements(interfaces.IMessageBeforeDelete)