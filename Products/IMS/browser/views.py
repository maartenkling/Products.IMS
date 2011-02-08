from Acquisition import aq_inner, aq_parent
from AccessControl import Unauthorized
from OFS.interfaces import IApplication

from zope.component import getMultiAdapter

from zope.interface import Interface
from zope import schema
from zope.formlib import form

from Products.statusmessages.interfaces import IStatusMessage

from Products.Five.formlib import formbase
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.CMFCore.utils import getToolByName

from plone.memoize.instance import memoize

from Products.IMS.config import UseSystem, SendMessageToAny
from Products.IMS.interfaces import IIMSMessage, IMessage, IReceivedMessageFolder, ISentMessageFolder, IReceivedMessage, ISentMessage
from Products.IMS import IMSMessageFactory as _

def checkOwnership(context):
    owner = context.getWrappedOwner()
    mship = getToolByName(context, 'portal_membership')
    auth = mship.getAuthenticatedMember()
    if not owner.getId() == auth.getId():
        raise Unauthorized

class MessageFolderView(BrowserView):
    """view of a message-folder
    """

    template = ViewPageTemplateFile('templates/message_folder.pt')

    def __call__(self):
        self.request.set('disable_border', True)

        checkOwnership(self.context)

        return self.template()

    @property
    @memoize
    def sent(self):
        return ISentMessageFolder.providedBy(self.context)

    @property
    @memoize
    def received(self):
        return IReceivedMessageFolder.providedBy(self.context)

    @property
    @memoize
    def hasAnyPerm(self):
        mship = getToolByName(self.context, 'portal_membership')
        return mship.checkPermission(SendMessageToAny, self.context)

    @memoize
    def getMessages(self):
        ploneview = getMultiAdapter((self.context, self.request), name='plone')
        catalog = getToolByName(self.context, 'portal_catalog')
        mship = getToolByName(self.context, 'portal_membership')
        acl_users = self.context.acl_users
        results = catalog(object_provides=IMessage.__identifier__, path={'query': '/'.join(self.context.getPhysicalPath())}, sort_on='created', sort_order='reverse')
        return [{'title': message.Title,
                 'message': message.getMessage,
                 'sender': message.getSender and mship.getMemberInfo(message.getSender) or {'username': message.getSender},
                 'receiver': [mship.getMemberInfo(receiver) or {'username': receiver} for receiver in message.getReceiver],
                 'read': message.read,
                 'replied': message.replied,
                 'forwarded': message.forwarded,
                 'created': ploneview.toLocalizedTime(message.created, 1),
                 'uid': message.UID,
                 'url': {'base': message.getURL(),
                         'forward': self.hasAnyPerm and '%s/%s' % (message.getURL(), 'forward') or '',
                         'reply': self.received and '%s/%s' % (message.getURL(), 'reply') or ''}} for message in results]

class MessageMarkReadView(BrowserView):
    """view to mark messages as read
    """

    def __call__(self):
        self.request.set('disable_border', True)

        checkOwnership(self.context)

        catalog = getToolByName(self.context, 'portal_catalog')
        results = catalog(object_provides=IMessage.__identifier__, path={'query': '/'.join(self.context.getPhysicalPath())}, UID=self.request.get('uids', []))
        for message in results:
            message = message.getObject()
            message.read = True
            message.reindexObject()

        return self.request.RESPONSE.redirect(self.context.absolute_url())

class MessageDeleteView(MessageFolderView):
    """view to delete messages (after confirmation)
    """

    template = ViewPageTemplateFile('templates/messages_delete.pt')

    def __call__(self):
        self.request.set('disable_border', True)

        checkOwnership(self.context)

        if self.request.get('delete_confirm', None) is not None and self.request.get('paths', None) is not None:
            return self.context.restrictedTraverse('%s/folder_delete' % '/'.join(self.context.getPhysicalPath()))()
        if not self.request.get('uids', []):
            return self.request.RESPONSE.redirect(self.context.absolute_url())

        return self.template()

    @memoize
    def getMessages(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        mship = getToolByName(self.context, 'portal_membership')
        base = '/'.join(self.context.getPhysicalPath())
        results = catalog(object_provides=IMessage.__identifier__, path={'query': base}, UID=self.request.get('uids', []), sort_on='Date', sort_order='reverse')
        return [{'title': message.Title,
                 'message': message.getMessage,
                 'sender': message.getSender and mship.getMemberInfo(message.getSender) or {'username': message.getSender},
                 'receiver': [mship.getMemberInfo(receiver) or {'username': receiver} for receiver in message.getReceiver],
                 'url': '%s/%s' % (base, message.getId)} for message in results]

class MessageView(BrowserView):
    """view of a message
    """

    template = ViewPageTemplateFile('templates/message.pt')

    def __call__(self):
        self.request.set('disable_border', True)

        checkOwnership(self.context)

        if not self.context.read:
            self.context.read = True
            self.context.reindexObject()

        context_state = getMultiAdapter((self.context, self.request),
                                        name=u'plone_context_state')

        try: # Plone 4+
            self.message_actions = context_state.actions(category="message")
        except TypeError: # Plone 3
            self.message_actions = context_state.actions().get('message', ())

        plone_utils = getToolByName(self.context, 'plone_utils')
        self.getIconFor = plone_utils.getIconFor

        return self.template()

    @property
    @memoize
    def receiver(self):
        mship = getToolByName(self.context, 'portal_membership')
        return [mship.getMemberInfo(receiver) or {'username': receiver} for receiver in self.context.getReceiver()]

    @property
    @memoize
    def sender(self):
        mship = getToolByName(self.context, 'portal_membership')
        return self.context.getSender() and mship.getMemberInfo(self.context.getSender()) or {'username': self.context.getSender()}

    @property
    @memoize
    def date(self):
        ploneview = getMultiAdapter((self.context, self.request), name='plone')
        return ploneview.toLocalizedTime(self.context.CreationDate(), 1)

    def _getMessageValues(self, message):
        ploneview = getMultiAdapter((self.context, self.request), name='plone')
        mship = getToolByName(self.context, 'portal_membership')
        return {'title': message.Title(),
                'message': message.getMessage(),
                'sender': message.getSender() and mship.getMemberInfo(message.getSender()) or message.getSender(),
                'receiver': [mship.getMemberInfo(receiver) or receiver for receiver in message.getReceiver()],
                'created': ploneview.toLocalizedTime(message.CreationDate(), 1),
                'received': IReceivedMessage.providedBy(message),
                'sent': ISentMessage.providedBy(message)}

    @memoize
    def getMessageThread(self):
        replyTo = self.context.getReplyTo()
        thread = []
        while replyTo is not None:
            thread.append(self._getMessageValues(replyTo))
            replyTo = replyTo.getReplyTo()
        return thread

class INewMessageForm(Interface):
    """Define the fields of our form
    """

    receiver = schema.Choice(title=_(u"To"),
                             required=True,
                             source='ims.members')

    subject = schema.TextLine(title=_(u"Subject"),
                              required=True)

    message = schema.Text(title=_(u"Message"),
                          required=True)

class NewMessageForm(formbase.PageForm):
    form_fields = form.FormFields(INewMessageForm)
    label = _(u"New Message")

    def __call__(self):
        mship = getToolByName(self.context, 'portal_membership')
        current_auth = mship.getAuthenticatedMember()
        if IApplication.providedBy(aq_parent(aq_parent(current_auth.getUser()))):
            IStatusMessage(self.request).addStatusMessage(_(u"Unfortunately it is not possible to send messages using your user account. Please use a Plone user rather than a Zope user."), type='error')
            return self.request.response.redirect(self.context.absolute_url())
        
        self.request.set('disable_border', True)

        self.form_fields.get('receiver').field.default = None
        self.form_fields.get('receiver').field.readonly = False
        self.form_fields.get('subject').field.default = None
        self.form_fields.get('message').field.default = None

        if self.request.get('receiver', None) is not None:
            self.form_fields.get('receiver').field.default = self.request.get('receiver', None)

        if self.request.get('subject', None) is not None:
            self.form_fields.get('subject').field.default = self.request.get('subject', None).decode('utf-8')

        return super(NewMessageForm, self).__call__()

    @form.action(_(u"send"))
    def action_send(self, action, data):
        """Send the message
        """
        return self._sendMessage(action, data)

    def _sendMessage(self, action, data):
        imsmessage = IIMSMessage(self.context)

        message = imsmessage.sendMessage(data['subject'], data['message'], data['receiver'])
        if message:
            IStatusMessage(self.request).addStatusMessage(_(u"Your message has been sent successfully"), type='info')
            return self.request.response.redirect(message.absolute_url())
        else:
            IStatusMessage(self.request).addStatusMessage(_(u"Sending your message failed"), type='error')
            return self.request.response.redirect(self.context.absolute_url())

    @form.action(_(u"cancel"),validator=lambda *args, **kwargs: {})
    def action_cancel(self, action, data):
        """Cancel message-creation
        """
        return self.request.response.redirect(self.context.absolute_url())

class NewContextMessageForm(NewMessageForm):
    form_fields = form.FormFields(INewMessageForm)

    def __call__(self):
        self.request.set('disable_border', True)

        self.form_fields.get('receiver').field.default = self.context.getId()
        self.form_fields.get('receiver').field.readonly = True
        self.form_fields.get('subject').field.default = None
        self.form_fields.get('message').field.default = None

        if self.request.get('subject', None) is not None:
            self.form_fields.get('subject').field.default = self.request.get('subject', None).decode('utf-8')

        return super(NewMessageForm, self).__call__()

    @form.action(_(u"send"))
    def action_send(self, action, data):
        """Send the message
        """
        data['receiver'] = self.context.getId()
        return self._sendMessage(action, data)

class ReplyMessageForm(formbase.PageForm):
    form_fields = form.FormFields(INewMessageForm)
    label = _(u"Reply to Message")

    template = ViewPageTemplateFile('templates/message_form.pt')

    def __call__(self):
        self.request.set('disable_border', True)

        checkOwnership(self.context)

        self.form_fields.get('subject').field.default = ('Re: %s' % self.context.Title().decode('utf-8'))
        self.form_fields.get('receiver').field.default = self.context.getSender()
        self.form_fields.get('receiver').field.readonly = True
        self.form_fields.get('message').field.default = None

        return super(ReplyMessageForm, self).__call__()

    @form.action(_(u"reply"))
    def action_reply(self, action, data):
        """Reply to Message
        """
        message = self.context.replyToMessage(self.request.form.get('subject', data['subject']), data['message'])
        if message:
            IStatusMessage(self.request).addStatusMessage(_(u"Your message has been sent successfully"), type='info')
            return self.request.response.redirect(message.absolute_url())
        else:
            IStatusMessage(self.request).addStatusMessage(_(u"Sending your message failed"), type='error')
            return self.request.response.redirect(self.context.absolute_url())

    @form.action(_(u"cancel"),validator=lambda *args, **kwargs: {})
    def action_cancel(self, action, data):
        """Cancel message-creation
        """
        return self.request.response.redirect(self.context.absolute_url())

    @memoize
    def getMessageThread(self):
        messageview = getMultiAdapter((self.context, self.request), name='view')
        thread = messageview.getMessageThread()
        thread.insert(0, messageview._getMessageValues(self.context))
        return thread

class ForwardMessageForm(formbase.PageForm):
    form_fields = form.FormFields(INewMessageForm)
    label = _(u"Forward Message")

    template = ViewPageTemplateFile('templates/message_form.pt')

    def __call__(self):
        self.request.set('disable_border', True)

        checkOwnership(self.context)

        self.form_fields.get('receiver').field.default = None
        self.form_fields.get('receiver').field.readonly = False

        self.form_fields.get('subject').field.default = ('Fw: %s' % self.context.Title().decode('utf-8'))
        if self.request.get('receiver', None) is not None:
            self.form_fields.get('receiver').field.default = self.request.get('receiver', None)
        self.form_fields.get('message').field.default = self.context.getMessage().decode('utf-8')

        return super(ForwardMessageForm, self).__call__()

    @form.action(_(u"forward"))
    def action_forward(self, action, data):
        """Forward Message
        """
        message = self.context.forwardMessage(self.request.form.get('subject', data['subject']), data['message'], data['receiver'])
        if message:
            IStatusMessage(self.request).addStatusMessage(_(u"Your message has been sent successfully"), type='info')
            return self.request.response.redirect(message.absolute_url())
        else:
            IStatusMessage(self.request).addStatusMessage(_(u"Sending your message failed"), type='error')
            return self.request.response.redirect(self.context.absolute_url())

    @form.action(_(u"cancel"),validator=lambda *args, **kwargs: {})
    def action_cancel(self, action, data):
        """Cancel message-creation
        """
        return self.request.response.redirect(self.context.absolute_url())
