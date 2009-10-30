"""Common configuration constants
"""

from AccessControl import ModuleSecurityInfo
from Products.CMFCore.permissions import setDefaultRoles

security = ModuleSecurityInfo('Products.IMS.config')

PROJECTNAME = "IMS"

security.declarePublic('UseSystem')
UseSystem = 'IMS: Use System'
setDefaultRoles(UseSystem, ('Member',))

security.declarePublic('SendMessage')
SendMessage = 'IMS: Send Message'
setDefaultRoles(SendMessage, ('Member',))

security.declarePublic('SendMessageToAny')
SendMessageToAny = 'IMS: Send Message to Any'
setDefaultRoles(SendMessageToAny, ('Manager',))

security.declarePublic('SendMessageToMany')
SendMessageToMany = 'IMS: Send Message to Many'
setDefaultRoles(SendMessageToMany, ('Manager',))

product_globals = globals()