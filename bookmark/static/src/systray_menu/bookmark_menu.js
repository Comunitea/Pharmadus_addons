// Copyright © 2025 Lazydoo
// See LICENSE file for full copyright and licensing details.

import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";

import { Component, onWillStart, useState, markup } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { escape } from "@web/core/utils/strings";
import { _t } from "@web/core/l10n/translation";


export class BookmarkMenu extends Component {
    static template = "bookmark.BookmarkMenu"
    static components = { Dropdown, DropdownItem }
    static props = {}

    setup() {
        this.actionService = useService("action")
        this.bookmarkService = useState(useService("bookmarks"))
        this.dialogService = useService("dialog");
        onWillStart(async() => {
            await this.bookmarkService.refreshBookmark()
        })

    }

    onBookmarkChoose(item) {
        this.bookmarkService.selectBookmark(item)
    }

    onBookmarkRemove(item) {
        const confirmMessage = _t("Are you sure you can delete the bookmark?");
        this.dialogService.add(ConfirmationDialog, {
            body: markup(
                `<h4>${escape(confirmMessage)}</h4>`
            ),
            confirm: async () => {
                await this._onRemoveItem([item])
            },
            cancel: () => { },
        });
    }

    onBookmarkRemoveAll() {
        const confirmMessage = _t("Are you sure you can delete all the bookmark?");
        this.dialogService.add(ConfirmationDialog, {
            body: markup(
                `<h4>${escape(confirmMessage)}</h4>`
            ),
            confirm: async () => {
                await this._onRemoveItem(this.bookmarkService.bookmarkItems)
            },
            cancel: () => { },
        });
    }

    async _onRemoveItem(items) {
        await this.bookmarkService.removeBookmarkItem(items)
    }

    async onBookmarkShare(item) {
        await this.bookmarkService.shareBookmarkItem([item])
    }

    async onBookmarkShareAll() {
        await this.bookmarkService.shareBookmarkItem(this.bookmarkService.bookmarkItems)
    }

}

export const systrayItem ={
    Component: BookmarkMenu,
    isDisplayed(env) {
        return true
    }
}

registry.category("systray").add("BookmarkMenu", systrayItem, { sequence: 1000 })
