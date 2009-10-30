from Products.CMFCore.utils import getToolByName

def setupIMS(context):

    # XXX: Since this is run an as extension profile, this shouldn't be
    # needed IMHO, but GS will run this step again if RD has been inspected
    # for an import_steps.xml again.
    if context.readDataFile('ims_various.txt') is None:
        return

    portal = context.getSite()

    mship = getToolByName(portal, 'portal_membership')
    mship.memberareaCreationFlag = True