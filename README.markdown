Django-cms Anchor Plugins
=========================
###### by Andy Gurden - [as.gurden@gmail.com](mailto:as.gurden@gmail.com)


Currently there are 3 plugins:

* Anchor
* AnchorLink
* TableOfContents

Anchor
------

Lets the user anchor a point on a page, they can set the tag.

Currently the anchor tag is not unique (it should be unique for the page). This is the users job to make sure!

AnchorLink
----------

Lets the user link to an anchor.

This only lets the user link to pages on the current page. If the link is included in another page it should still link back to the original anchor on the original page.

In future it will hopefully be able to link to anchors on any page. This requires a little ajax though.

TableOfContents
---------------

Creates a table of contents including pages and optionally anchors from each page under the chosen root (and possibly including the root).

If the user has JavaScript enabled (and jQuery included) then they should be able to expand and collapse tree nodes freely.
