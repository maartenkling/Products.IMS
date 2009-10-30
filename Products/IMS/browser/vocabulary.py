from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from Products.CMFCore.utils import getToolByName
from zope.component import getSiteManager, getMultiAdapter

def members(context):
    if context is None:
        context = getSiteManager()
    mship = getToolByName(context, 'portal_membership')
    filter = getToolByName(context, 'portal_properties').site_properties.getProperty('ims_member_filter', ())
    portal_state = getMultiAdapter((context, context.REQUEST), name=u'plone_portal_state')
    member = portal_state.member()
    userid = member.getId()
    return SimpleVocabulary([SimpleTerm(m, m, mship.getMemberInfo(m).get('fullname', m).decode('UTF-8'))
                             for m in mship.listMemberIds() 
                             if not m in filter and not m == userid])