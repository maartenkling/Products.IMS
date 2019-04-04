"""Message content type
"""

from AccessControl import ClassSecurityInfo
from Acquisition import aq_base

from zope.interface import implements
from zope.i18n import translate
from zope.event import notify
from Products.CMFCore.utils import getToolByName

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

    def _catalogs(self):
        # return [getToolByName(self, 'email_catalog')]
        return [getToolByName(self, 'portal_catalog')]

    def indexObject(self):
        for c in self._catalogs:
            c.catalog_object(self)

    def unindexObject(self):
        """remove an object from all registered catalogs"""
        path = '/'.join(self.getPhysicalPath())
        for c in self._catalogs():
            c.uncatalog_object(path)

    def reindexObjectSecurity(self, skip_self=False):
        path = '/'.join(self.getPhysicalPath())
        for c in self._catalogs():
            for brain in c.unrestrictedSearchResults(path=path):
                brain_path = brain.getPath()
                if brain_path == path and skip_self:
                    continue
            # Get the object
            ob = brain._unrestrictedGetObject()

            # Recatalog with the same catalog uid.
            # _cmf_security_indexes in CMFCatalogAware
            c.reindexObject(ob,
                            idxs=self._cmf_security_indexes,
                            update_metadata=0,
                            uid=brain_path
                            )

    def reindexObject(self, idxs=[]):
        """reindex object"""
        if idxs == []:
            # Update the modification date.
            if hasattr(aq_base(self), 'notifyModified'):
               self.notifyModified()
        for c in self._catalogs():
            if c is not None:
                c.reindexObject(self,
                                idxs=idxs
                                )

registerType(Message, PROJECTNAME)