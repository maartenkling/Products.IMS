"""Message content type
"""

from AccessControl import ClassSecurityInfo

from zope.interface import implements
from zope.i18n import translate
from zope.event import notify

from Products.CMFCore.permissions import ModifyPortalContent, View

from Products.Archetypes.public import *

from Products.ATContentTypes.content.base import ATCTMixin

from Products.IMS.config import PROJECTNAME
from Products.IMS.interfaces import IMessage, IIMSMessage, ISentMessage, IReceivedMessage
from Products.IMS import IMSMessageFactory as _
from Products.IMS.events import MessageBeforeDelete

MessageSchema = BaseContent.schema.copy() + Schema((
                                                        
    StringField(
        name='sender',
        required=1,
        widget=StringWidget(
            label=_('label_sender', default=u'Sent by'),
            visible=0,
        ),
    ),
                                                        
    LinesField(
        name='receiver',
        required=1,
        widget=TextAreaWidget(
            label=_('label_receiver', default=u'Received by'),
            visible=0,
        ),
    ),
    
    TextField(
        name='message',
        required=1,
        widget=TextAreaWidget(
            label=_('label_message', default=u'Message'),
            visible=0,
        ),
    ),
    
    ReferenceField(
        name='replyTo',
        required=0,
        allowed_types=('Message',),
        relationship='replyTo',
        widget=ReferenceWidget(
            label=_('label_replyTo', default=u'Reply to'),
            visible=0,
        ),
    ),
    
    ReferenceField(
        name='companion',
        required=0,
        allowed_types=('Message',),
        relationship='companion',
        widget=ReferenceWidget(
            label=_('label_companion', default=u'Companio'),
            visible=0,
        ),
    ),
    
))

for field in ('creators','allowDiscussion','contributors','location','subject','language','rights','effectiveDate','expirationDate',):
    if MessageSchema.has_key(field):
        MessageSchema[field].widget.visible = {'edit': 'invisible', 'view': 'invisible'}

class Message(BaseContent):
    """ A message
    """
    implements(IMessage)

    portal_type = meta_type = "Message"
    _at_rename_after_creation = False
    schema = MessageSchema
    forwarded = False
    replied = False
    read = False

    security = ClassSecurityInfo()

    security.declareProtected(View, 'title_or_id')
    def title_or_id(self):
        """Returns the title if it is not blank and the id otherwise.
        """
        return self.getId()
    
    def replyToMessage(self, title, message):
        """ Reply to this message
        """
        adapter = IIMSMessage(self)
        return adapter.replyToMessage(self, title, message)
    
    def forwardMessage(self, title, message, receiver):
        """ Forward this message to somebody
        """
        adapter = IIMSMessage(self)
        return adapter.forwardMessage(self, title, message, receiver)
    
    @property
    def isSent(self):
        return ISentMessage.providedBy(self)
    
    @property
    def isReceived(self):
        return IReceivedMessage.providedBy(self)
    
    @property
    def isRead(self):
        return self.read

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        notify(MessageBeforeDelete(item))
        BaseContentMixin.manage_beforeDelete(self, item, container)
    
registerType(Message, PROJECTNAME)