// Copyright © 2025 Lazydoo
// See LICENSE file for full copyright and licensing details.

import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { router } from "@web/core/browser/router";
import { browser } from "@web/core/browser/browser";

export const bookmarkService = {
    dependencies: ["orm", "menu", "action"],
    start(env, { menu, orm, action }) {
        let bookmarkItems = [];
        const _refreshBookmark = async () => {
            return await orm.call("res.bookmark", "get_bookmarks", []);
        };
        return {
            bookmarkItems,
            get currentBookmark() {
                return user.context.bookmark || [];
            },

            selectBookmark(bookmark) {
                user.updateContext({bookmark: bookmark.suggestIds});
                if (bookmark.menu_id) {
                    menu.setCurrentMenu(bookmark.menu_id)
                }
                action.doAction(bookmark.action, {
                    clearBreadcrumbs: true,
                    viewType: bookmark.view_type
                });
            },

            async addBookmarkItem(val) {
                let menuId = Number(router.current.menu_id || 0);
                const storedMenuId = Number(browser.sessionStorage.getItem("menu_id"));
                const firstAction = router.current.actionStack?.[0]?.action;
                if (!menuId && firstAction) {
                    // Find all menus that match this action
                    const matchingMenus = menu
                        .getAll()
                        .filter((m) => m.actionID === firstAction || m.actionPath === firstAction);

                    if (matchingMenus.length > 0) {
                        // Use sessionStorage context to determine the correct menu
                        menuId = matchingMenus.find(m =>
                            m.appID === storedMenuId
                        )?.appID;
                        if (!menuId) {
                            menuId = matchingMenus[0]?.appID;
                        }
                    }
                }
                val.menu_id = menuId;
                val.user_ids = [[4, user.userId]];
                const newBookmark = await orm.call("res.bookmark", "create_bookmark", [val]);
                this.bookmarkItems = this.bookmarkItems.concat(newBookmark);
                return newBookmark;
            },

            async refreshBookmark() {
                this.bookmarkItems = await _refreshBookmark();
            },

            async removeBookmarkItem(items) {
                const bookmarkIds = items.map(i => i.id);
                const result = await orm.call("res.bookmark", "remove_or_unlink", [bookmarkIds]);
                if (result) {
                    this.bookmarkItems = this.bookmarkItems.filter(i => !bookmarkIds.includes(i.id));
                }
            },

            async shareBookmarkItem(items) {
                let actionShare = await action.loadAction("bookmark.wizard_share_bookmark_action");
                actionShare.context = {"bookmark_ids": items.map(i => i.id)};
                action.doAction(actionShare);
            }
        };
    }
};

registry.category("services").add("bookmarks", bookmarkService);
