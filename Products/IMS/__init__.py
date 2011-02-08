from Products.IMS import config

from Products.Archetypes import atapi
from Products.CMFCore import utils as cmfutils

from zope.i18nmessageid import MessageFactory
IMSMessageFactory = MessageFactory('IMS')

from Products.PlacelessTranslationService.utility import PTSTranslationDomain
imsdomain = PTSTranslationDomain('IMS')

def initialize(context):

    from content import message, message_folder

    content_types, constructors, ftis = atapi.process_types(
        atapi.listTypes(config.PROJECTNAME),
        config.PROJECTNAME)

    for atype, constructor in zip(content_types, constructors):
        cmfutils.ContentInit("%s: %s" % (config.PROJECTNAME, atype.portal_type),
            content_types      = (atype,),
            permission         = config.SendMessage,
            extra_constructors = (constructor,),
            ).initialize(context)