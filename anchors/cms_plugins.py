from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from django import forms
from django.forms.models import ModelForm
from models import Anchor, AnchorLink, TableOfContents
from cms.utils.placeholder import get_page_from_placeholder_if_exists

class AnchorPlugin(CMSPluginBase):
    model = Anchor
    name = _("Anchor")
    render_template = "cms/plugins/anchors/anchor.html"
    text_enabled = True
    
    prepopulated_fields = {"tag": ("text_content",)}

    fieldsets = [
        (None, {
            'fields': ['text_content', 'hdr_level']
        }),
        ('Advanced', {
            'fields': ['tag', 'in_contents'],
            'classes':['collapse']
        }),
    ]

    def render(self, context, instance, placeholder):
        if instance.hdr_level == 7:
            hdr_exists = False
        else:
            hdr_exists = True

        context.update({
            'placeholder':placeholder,
            'hdr_exists':hdr_exists,
            'object':instance
        })
        return context
    
    def icon_src(self, instance):
        return settings.MEDIA_URL + "anchors/img/anchor.png"



class AnchorLinkPlugin(CMSPluginBase):
    model = AnchorLink
    name = _("Anchor Link")
    render_template = "cms/plugins/anchors/anchorlink.html"
    text_enabled = True
    
    def render(self, context, instance, placeholder):
        context.update({
            'placeholder':placeholder,
            'object':instance,
            'original_page':get_page_from_placeholder_if_exists(instance.anchor.placeholder),
        })
        return context
    
    def icon_src(self, instance):
        return settings.CMS_MEDIA_URL + u"images/link.png"

    def get_form_class(self, page):
        """
        Returns the class to be used as the form
        """
        class AnchorLinkForm(ModelForm):
            anchor = forms.ModelChoiceField(label=_("Anchor"), queryset=Anchor.objects.filter(placeholder__page=page))

            class Meta:
                model = AnchorLink
        return AnchorLinkForm

    def get_form(self, request, obj=None, **kwargs):
        form = self.get_form_class(self.page)
        kwargs['form'] = form
        return super(AnchorLinkPlugin, self).get_form(request, obj, **kwargs)



class TableOfContentsPlugin(CMSPluginBase):
    model = TableOfContents
    name = _("Table of Contents")
    render_template = "cms/plugins/anchors/toc.html"

    class PluginMedia:
        js = (settings.MEDIA_URL + "anchors/js/toc.js",)
        css = {
            'all': (settings.MEDIA_URL + "anchors/css/toc.css",)
        }

    fieldsets = [
        (None, {
            'fields': ['root_page']
        }),
        ('Display', {
            'fields': ['numbered', ('show_root','link_root'), 'branch_behaviour', 'anchor_visibility'],
            'classes':['collapse']
        }),
    ]


    class TemplateMarkup:
    # Passed to template for rendering
        def __init__(self, type, text=None, link=None, anchor=None, open=None, current=None):
            self.type = type
            self.text = text
            self.link = link
            self.anchor = anchor
            self.open = open
            self.current = current

    def getPageStructure(self, tree, cur=None, show_root=True, link_root=True):
    # Returns a list to tell the template how to draw this tree
        struct = []
        if show_root:
            struct.append(TableOfContentsPlugin.TemplateMarkup("opennode", open=hasattr(tree, 'open')))
            if link_root:
                struct.append(TableOfContentsPlugin.TemplateMarkup("title", text=tree.title, link=tree.href, current=(tree==cur)))
            else:
                struct.append(TableOfContentsPlugin.TemplateMarkup("title", text=tree.title, current=(tree==cur)))
        anchors = self.getAnchorStructure(tree, tree.anchors)
        if anchors:
            struct.append(TableOfContentsPlugin.TemplateMarkup("openanchors"))
            struct.append(TableOfContentsPlugin.TemplateMarkup("openlist"))
            struct += anchors
            struct.append(TableOfContentsPlugin.TemplateMarkup("closelist"))
            struct.append(TableOfContentsPlugin.TemplateMarkup("closeanchors"))
        if tree.children:
            struct.append(TableOfContentsPlugin.TemplateMarkup("openchildren"))
            struct.append(TableOfContentsPlugin.TemplateMarkup("openlist"))
            for child in tree.children:
                struct += self.getPageStructure(child, cur)
            struct.append(TableOfContentsPlugin.TemplateMarkup("closelist"))
            struct.append(TableOfContentsPlugin.TemplateMarkup("closechildren"))
        if show_root:
            struct.append(TableOfContentsPlugin.TemplateMarkup("closenode"))
        return struct


    def getAnchorStructure(self, page_node, anchors):
    # Takes a tree of anchor nodes and returns a list for the stucture
        struct = []
        for child in anchors:
            struct.append(TableOfContentsPlugin.TemplateMarkup("opennode"))
            struct.append(TableOfContentsPlugin.TemplateMarkup("title", child.title, page_node.href, child.tag))
            children = self.getAnchorStructure(page_node, child.children)
            if children:
                struct.append(TableOfContentsPlugin.TemplateMarkup("openchildren"))
                struct.append(TableOfContentsPlugin.TemplateMarkup("openlist"))
                struct += children
                struct.append(TableOfContentsPlugin.TemplateMarkup("closelist"))
                struct.append(TableOfContentsPlugin.TemplateMarkup("closechildren"))
            struct.append(TableOfContentsPlugin.TemplateMarkup("closenode"))
        return struct

    def setOpenBranches(self, tree, page_node, behaviour):
        def openAll():            
            tree.open = True
            for child in tree.children:
                self.setOpenBranches(child, page_node, behaviour)
        def closeAll():
        # (Default so do nothing)
            pass
        def parentsOnly():
            if page_node and page_node.parent:
                page_node.parent.open = True
                self.setOpenBranches(tree, page_node.parent, behaviour)
        def parentsAndCurrent():
            if page_node:
                page_node.open = True
                if page_node.parent:
                    self.setOpenBranches(tree, page_node.parent, behaviour)
        def default():
            assert False, behaviour
        {
            0: openAll,
            1: closeAll,
            2: parentsOnly,
            3: parentsAndCurrent,
        }.get(behaviour, default)()

    def setVisibleAnchors(self, tree, page_node, visibility):
        def all(): tree.pullAnchors()
        def none(): pass
        def current(): page_node.pullAnchors(False)
        def default(): assert False, visibility
        {
            0: all,
            1: none,
            2: current,
        }.get(visibility, default)()
            

    def render(self, context, instance, placeholder):
        from utils import AnchorNode, PageNode

        # Check as root won't be checked in the other code
        if instance.root_page.published:
            tree = PageNode(instance.root_page)
            current_page_node = tree.pullChildren(context['current_page'])
            self.setOpenBranches(tree, current_page_node, instance.branch_behaviour)
            self.setVisibleAnchors(tree, current_page_node, instance.anchor_visibility)
            content = self.getPageStructure(tree, current_page_node, instance.show_root, instance.link_root)
        else:
            content = []
        context.update({
            'content':content,
            'placeholder':placeholder,
            'object':instance,
        })
        return context
    
plugin_pool.register_plugin(AnchorPlugin)
plugin_pool.register_plugin(AnchorLinkPlugin)
plugin_pool.register_plugin(TableOfContentsPlugin)
