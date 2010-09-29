from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin, Page

HEADER_LEVELS = (
    (1, _("H1")),
    (2, _("H2")),
    (3, _("H3")),
    (4, _("H4")),
    (5, _("H5")),
    (6, _("H6")),
    (7, _("None")),
)

class Anchor(CMSPlugin):
    """
    An anchor inside a webpage that can be linked to
    """
    
    text_content = models.CharField(_("text content"), max_length=256)
    tag = models.SlugField(_("tag"))
    hdr_level = models.PositiveSmallIntegerField(_("header level"), choices=HEADER_LEVELS, default=7)
    in_contents = models.BooleanField(_("in table of contents"), default=True)
    
    def __unicode__(self):
        return self.text_content + " (" + self.tag + ")"



class AnchorLink(CMSPlugin):
    """
    A link to an anchor
    """
    
    text_content = models.CharField(_("text content"), max_length=256)
    anchor = models.ForeignKey(Anchor, verbose_name=_("anchor"))
    
    def __unicode__(self):
        return self.text_content



BRANCH_STATES = (
    (0, _("All open")),
    (1, _("All closed")),
    (2, _("Parents open")),
    (3, _("Current and parents open")),
)

ANCHOR_STATES = (
    (0, _("All")),
    (1, _("None")),
    (2, _("Current page")),
)


class TableOfContents(CMSPlugin):
    """
    Info to display a table of contents for a page
    """
    
    root_page = models.ForeignKey(Page, verbose_name=_("root page"))
    numbered = models.BooleanField(_("is numbered"), default=True)
    show_root = models.BooleanField(_("show root page"), default=False)
    link_root = models.BooleanField(_("link root page"), default=False)
    branch_behaviour = models.PositiveSmallIntegerField(_("initially open branches"), choices=BRANCH_STATES, default=3)
    anchor_visibility = models.PositiveSmallIntegerField(_("visible anchors"), choices=ANCHOR_STATES, default=2)
    
    def __unicode__(self):
        return self.root_page.__unicode__()
