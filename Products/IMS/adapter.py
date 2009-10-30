from zope.interface import implements, Interface, alsoProvides
from zope.component import adapts, getMultiAdapter

from Products.CMFCore.utils import getToolByName
from Products.IMS.config import SendMessageToMany
from Products.IMS.interfaces import IIMSMessage, ISentMessage, IReceivedMessage, ISendable

from AccessControl.SecurityManagement import newSecurityManager

class IMSMessage(object):
    """ Adapter to send IMS messages
    """
    implements(IIMSMessage)
    adapts(Interface)

    def __init__(self, context):
        self.context = context

    def _getSafeId(self, container, title):
        utils = getToolByName(self.context, 'plone_utils')
        id = utils.normalizeString(title)
        objids = container.objectIds()
        if id in objids:
            i = 2
            while '%s-%s' % (id, i) in objids: i += 1;
            id = '%s-%s' % (id, i)
        return id

    def _shortenLines(self, message):
        lines = message.split("\n")
        shortened = []
        for line in lines:
            if line.startswith('>') or not line:
                shortened.append(line)
            else:
                words = line.split(' ')
                if len(words):
                    sline = words[0]
                    del words[0]
                    for word in words:
                        if len('%s %s' % (sline, word)) > 65:
                            shortened.append(sline)
                            sline = word
                        else:
                            sline = '%s %s' % (sline, word)
                    shortened.append(sline)
        return '\n'.join(shortened)


    def _createMessage(self, container, title, message, receiver, sender, replyTo=None, interface=None):
        try:
            typestool = getToolByName(self.context, 'portal_types')
            mship = getToolByName(self.context, 'portal_membership')
            id = self._getSafeId(container, title)
            current_auth = mship.getAuthenticatedMember()
            newSecurityManager(self.context.REQUEST, container.getWrappedOwner())
            typestool.constructContent(type_name='Message', container=container, id=id, title=title, message=message, receiver=receiver, replyTo=replyTo, sender=sender)
            instance = container[id]
            if interface is not None:
                alsoProvides(instance, interface)
            instance.reindexObject()
            newSecurityManager(self.context.REQUEST, current_auth)
            return instance
        except:
            return None

    def _getMessageFolder(self, userid, id, type_name):
        typestool = getToolByName(self.context, 'portal_types')
        mship = getToolByName(self.context, 'portal_membership')
        current_auth = mship.getAuthenticatedMember()
        homefolder = mship.getHomeFolder(userid)
        if homefolder is None:
            mship.createMemberarea(userid)
            homefolder = mship.getHomeFolder(userid)
        if not ISendable.providedBy(homefolder):
            alsoProvides(homefolder, ISendable)
        if not id in homefolder.objectIds():
            newSecurityManager(self.context.REQUEST, homefolder.getWrappedOwner())
            typestool.constructContent(type_name=type_name, container=homefolder, id=id)
            folder = homefolder[id]
            folder.reindexObject()
            newSecurityManager(self.context.REQUEST, current_auth)
        return homefolder[id]

    def sendMessage(self, title, message, receiver, sender=None, replyToSender=None, replyToReceiver=None):
        """Send a IMS message
        """
        if sender is None:
            portal_state = getMultiAdapter((self.context, self.context.REQUEST), name=u'plone_portal_state')
            member = portal_state.member()
            sender = member.getId()

        message = self._shortenLines(message)

        if isinstance(receiver, str):
            receiver=[receiver]
        received = []
        for r in receiver:
            received.append(self._createMessage(self._getMessageFolder(r, 'received', 'ReceivedMessageFolder'), title, message, [r], sender, replyToReceiver, IReceivedMessage))
        if received is not None and sender:
            sent = self._createMessage(self._getMessageFolder(sender, 'sent', 'SentMessageFolder'), title, message, receiver, sender, replyToSender, ISentMessage)
            if sent is not None:
                for r in received:
                    r.setCompanion(sent)
                return sent
        else:
            return None

    def replyToMessage(self, instance, title, message):
        """Reply to a IMS message
        """
        sender = instance.getReceiver()[0]
        receiver = instance.getSender()
        replyTo = instance
        reply = self.sendMessage(title, message, receiver, sender, replyTo, instance.getCompanion())
        if reply is not None:
            instance.replied = True
            instance.reindexObject()
            return reply
        return False

    def forwardMessage(self, instance, title, message, receiver):
        """Forward a IMS message to somebody
        """
        forward = self.sendMessage(title, message, receiver, None, None)
        if forward is not None:
            instance.forwarded = True
            instance.reindexObject()
            return forward
        return None

