from Acquisition import aq_parent
from Products.CMFCore.utils import getToolByName
from Products.IMS.interfaces import IReceivedMessageFolder, IMessage, IIMSMessage
from Products.IMS import IMSMessageFactory as _

from zope.i18n import translate
from zope.component import getSiteManager

def createMessageFolders(event):
    """ creates message-folders for the user
    """
    try:
        inst = getToolByName(event.principal, 'portal_quickinstaller')
    except:
        return
    if inst.isProductInstalled('IMS'):
        userid = event.principal.getId()
        ims = IIMSMessage(event.principal)
        ims._getMessageFolder(userid, 'received', 'ReceivedMessageFolder')
        ims._getMessageFolder(userid, 'sent', 'SentMessageFolder')

def newMessageNotify(object, event):
    """ Notifies the appropriate User if he received a new message
    """
    if IReceivedMessageFolder.providedBy(aq_parent(object)):
        try:
            mailhost = getToolByName(object, 'MailHost')
            mship = getToolByName(object, 'portal_membership')
            sender = object.getSender()
            receiver = object.getReceiver()
            portal = getSiteManager(object)
            body = object.new_message_notification(name=mship.getMemberInfo(receiver).get('fullname', object.getReceiver()),
                                                   sender=mship.getMemberInfo(sender).get('fullname', object.getSender()),
                                                   site=portal.getProperty('title', ''),
                                                   siteurl=getToolByName(object, 'portal_url')(),
                                                   url=object.absolute_url(),
                                                   emailfrom=portal.getProperty('email_from_name', ''),
                                                   message=object)
            mailhost.secureSend(body,
                                mto=mship.getMemberById(receiver).getProperty('email'),
                                mfrom='%s <%s>' % (portal.getProperty('email_from_name', ''), portal.getProperty('email_from_address', '')),
                                subject=translate(_(u'mail_subject', default=u'You have received a new message'), context=object.REQUEST),
                                charset='utf-8')
        except:
            # no mailserver
            pass

def handleMessageDelete(event):
    """ Set reference between possible reply and replyTo of message to be deleted
    """
    if IMessage.providedBy(event.object):
        replyTo = event.object.getReplyTo()
        if replyTo is not None:
            reply = event.object.getBackReferences(relationship='replyTo')
            if len(reply) > 0:
                reply[0].setReplyTo(replyTo)