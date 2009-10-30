from zope.interface import Interface
from zope.component.interfaces import IObjectEvent

class IMessageFolder(Interface):
    """ A folder holding messages
    """

class IReceivedMessageFolder(IMessageFolder):
    """ The folder holding received messages
    """

class ISentMessageFolder(IMessageFolder):
    """ The folder holding sent messages
    """

class ISendable(Interface):
    """ A object which id is the id of a user to which a message may be sent
    """

class IMessage(Interface):
    """ A message
    """

    def reply(self, message, request):
        """ Reply to this message
        """

    def forward(self, message, receiver, request):
        """ Forward this message to somebody
        """

class ISentMessage(IMessage):
    """ A sent message
    """

class IReceivedMessage(IMessage):
    """ A received message
    """

class IIMSMessage(Interface):
    """ An adapter for the BrowserRequest to handle IMS messages.
    """

    def sendMessage(title, message, receiver, sender=None, replyTo=None):
        """ Send a IMS message.
        """

    def replyToMessage(instance, message):
        """ Reply to a IMS message
        """

    def forwardMessage(instance, message, receiver):
        """ Forward a IMS message to somebody
        """

class IMessageBeforeDelete(IObjectEvent):
    """An event signalling that a message is going to be deleted
    """
