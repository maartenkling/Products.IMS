"""Message folders (received, sent)
"""

from zope.interface import implements
from zope.i18n import translate

from Products.CMFCore.permissions import ModifyPortalContent, DeleteObjects

from Products.Archetypes.public import *

from Products.ATContentTypes.content.base import ATCTMixin

from Products.IMS.config import PROJECTNAME
from Products.IMS.interfaces import IMessageFolder, IReceivedMessageFolder, ISentMessageFolder
from Products.IMS import IMSMessageFactory as _

MessageFolderSchema = BaseFolderMixin.schema.copy()
MessageFolderSchema.delField('title')

class BaseMessageFolder(BaseFolderMixin, ATCTMixin):
    """ A folder holding messages
    """
    implements(IMessageFolder)

    _at_rename_after_creation = False
    schema = BaseFolderMixin.schema.copy()
    
class ReceivedMessageFolder(BaseMessageFolder):
    """ The folder holding received messages
    """
    implements(IReceivedMessageFolder)
    
    portal_type = meta_type = "ReceivedMessageFolder"
    
    def Title(self):
        try:
            return translate(_('title_receivedmessagefolder', default=u'Received Messages'), context=self.REQUEST)
        except:
            return u'Received Messages'
    
class SentMessageFolder(BaseMessageFolder):
    """ The folder holding sent messages
    """
    implements(ISentMessageFolder)
    
    portal_type = meta_type = "SentMessageFolder"
    
    def Title(self):
        try:
            return translate(_('title_sentmessagefolder', default=u'Sent Messages'), context=self.REQUEST)
        except:
            return u'Sent Messages'
    
registerType(ReceivedMessageFolder, PROJECTNAME)
registerType(SentMessageFolder, PROJECTNAME)
    