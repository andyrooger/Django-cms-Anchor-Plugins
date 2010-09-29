from models import Anchor, AnchorLink, TableOfContents
from cms_plugins import AnchorPlugin
from cms.utils.placeholder import get_page_from_placeholder_if_exists

##################
# Helpful things
##################

class Struct:
# To allow anonymous objects
    def __init__(self, **entries):
        self.__dict__.update(entries)



##################
# Anchor Node Code
##################

def getOrderedAnchors(page, forward=True):
# Pull anchors from the page so they are ordered as they are layed out on the screen
# Make sure only anchors tagged to be included in the contents are returned
    if forward:
      return getAnchorsForward(page)
    else:
      return getAnchorsBackward(page)



def getAnchorsForward(page):

    def flattenAnchors(plugins):
    # Generates a list of anchors from a list of plugins
    # Make sure they all start on the same level
    # i.e. Kill all plugins in placeholder without position
        from cms.models import CMSPlugin
        from cms.plugins.text import utils
        from cms.plugins.text.cms_plugins import TextPlugin
        for plugin in plugins:
            if plugin.get_plugin_class() is AnchorPlugin:
                if plugin.anchor.in_contents:
                    yield plugin.anchor
            elif plugin.get_descendant_count() != 0:
                # Children won't necessarily be in the correct order so we check
                # for TextPlugin as we know how to get correct order from this
                if plugin.get_plugin_class() is TextPlugin:
                    children = [CMSPlugin.objects.get(pk=key) for key in utils.plugin_tags_to_id_list(plugin.text.body)]
                else:
                    children = plugin.get_children()
                for anchor in flattenAnchors(children):
                    # We already know these are valid :)
                    yield anchor

    # get all plugins directly on a page (in a placeholder)
    placeholders = page.placeholders.all()
    plugins = []
    for placeholder in placeholders:
        # Add plugins from this placeholder (top level only)
        plugins.extend(placeholder.get_plugins().filter(position__isnull=False).order_by('position'))
    return flattenAnchors(plugins)


    	
def getAnchorsBackward(page):
    # Original way I did this, returns wrong order (uses order they were created)
    anchors = Anchor.objects.filter(placeholder__page=page).filter(in_contents=True).order_by('cmsplugin_ptr__placeholder', 'cmsplugin_ptr__position')



class AnchorNode:
    """
    Holds anchor tree
    """

    def __init__(self, anchor=None, parent=None):
        if anchor:
            self.title = anchor.text_content
            self.tag = anchor.tag
        else:
            self.title = ""
            self.tag = ""
        self.children = []
        self.parent = parent



def makeTreeFromAnchors(page, anchor_list, recursive=False):
# Create tree of anchor nodes from a list of anchors
    if recursive:
        return makeTreeFromAnchorsR(page, anchor_list, 0, anchor_list.count(), [])
    else:
        return makeTreeFromAnchorsI(page, anchor_list)



def makeTreeFromAnchorsR(page, anchors, frm, to, alist):
# Look at anchor list between frm (inclusive) and to (exclusive)
# Returns a list of anchor nodes at the top level appended to alist

    def firstAtLevel(level, anchors, frm, to):
    # Returns the first anchor at most the given level
    # Only looks between frm and to
    # Returns to if there is no match
        pos = frm
        while pos < to:
            if anchors[pos].hdr_level <= level:
                break
            pos += 1
        return pos

    # If there are anchors left to arrange
    if frm < to:
        # Create node from first anchor
        anchor = anchors[frm]
        anode = AnchorNode(anchor, page)
        # Arrange all future lesser nodes and add them as children
        go_to = firstAtLevel(anchor.hdr_level, anchors, frm+1, to)
        anchor.children = makeTreeFromAnchorsR(page, anchors, frm+1, go_to, [])
        # Create current anchor list
        if alist:
            alist.append(anchor)
        else:
            alist = [anchor]
        # Arrange all future nodes and return
        return makeTreeFromAnchorsR(page, anchors, go_to, to, alist)
    # Or return alist as there were no nodes left
    return alist
                
def makeTreeFromAnchorsI(page, anchors):
    # This guy will be the daddy node.
    # He will be more important that any other header
    big_node = AnchorNode()
    anchor_nodes = [(Struct(hdr_level=0), big_node)]
    anchor_nodes.extend([(anchor, AnchorNode(anchor, page)) for anchor in anchors])
    # Iterate through the list of (anchor, anchor_node)
    for focus in range(len(anchor_nodes)):
        node = anchor_nodes[focus]
        # Look back through the list
        for test in range(focus-1, -1, -1):
            t_node = anchor_nodes[test]
            # If tester node's header is better, become child
            if t_node[0].hdr_level < node[0].hdr_level:
                t_node[1].children.append(node[1])
                break
    return big_node.children


##################
# Page Node Code
##################

class PageNode:
    """
    Holds page tree
    """
    
    def __init__(self, page, parent=None):
    # Take page info
        self.page = page
        self.title = page.get_page_title()
        self.href = page.get_absolute_url()
        self.anchors = []
        self.children = []
        self.parent = parent

    def pullChildren(self, cur_page, recursive=True):
    # Pulls in children for the current page as long as they are published
    # Can pull in whole published tree if recursive is true
    # Returns the node for the current page, or None
        current_node = None
        for child in self.page.children.filter(published=True):
            child_page = PageNode(child, self)
            self.children.append(child_page)
            if recursive:
                node = child_page.pullChildren(cur_page, recursive)
                if node:
                    current_node = node
        if self.page == cur_page:
            return self
        else:
            return current_node

    def pullAnchors(self, recursive=True):
    # Pulls in anchors for the current page
    # If recursive is true then pull anchors for all children
        self.anchors = makeTreeFromAnchors(self.page, getOrderedAnchors(self.page))
        if recursive:
            for child in self.children:
                child.pullAnchors(recursive)
