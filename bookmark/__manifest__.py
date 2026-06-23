# -*- coding:utf-8 -*-
{
    "name": "Bookmark",
    "summary": "Bookmark url with default search and view",
    "version": "18.0.1.0.1",
    "category": "Extra Tools",
    "maintainer": "luuthinh2705@gmail.com",
    "author": "Lazydoo",
    "live_test_url": "https://demo.lazydoo.net",

    "depends": [
        "base",
        "web",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/search_history_views.xml",
        "views/res_bookmark_views.xml",
        "wizards/wizard_share_bookmark_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "bookmark/static/src/search_bar/**/*",
            "bookmark/static/src/systray_menu/**/*",
            "bookmark/static/src/search_history/**/*",
            "bookmark/static/src/patch_view/**/*",
            "bookmark/static/src/custom_bookmark/**/*",
        ]
    },
    "images": [
        "static/description/banner.jpg",
    ],
    "installable": True,
    "application": False,
}
