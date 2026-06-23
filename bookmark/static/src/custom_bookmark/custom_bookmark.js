/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { AccordionItem } from "@web/core/dropdown/accordion_item";
import { CheckBox } from "@web/core/checkbox/checkbox";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

import { Component, useRef, useState } from "@odoo/owl";

const favoriteMenuRegistry = registry.category("favoriteMenu");

export class CustomBookmarkItem extends Component {
    setup() {
        this.notification = useService("notification");
        this.orm = useService("orm")
        this.descriptionRef = useRef("description");
        this.bookmarkService = useService("bookmarks")
        this.state = useState({
            description: this.env.config.getDisplayName(),
        });
    }

    /**
     * @param {Event} ev
     */
    async saveBookmark(ev) {
        if (!this.state.description) {
            this.notification.add(_t("A name for your bookmark is required."), {
                type: "danger",
            });
            ev.stopPropagation();
            return this.descriptionRef.el.focus();
        }

        const suggestItems = this.env.searchModel.query.map((q) => {
            let searchItem = Object.values(this.env.searchModel.searchItems).find(item => q.searchItemId == item.id);
            if (searchItem.custom) {
                if (searchItem.type == "dateGroupBy" ) {
                    searchItem["value"] = { intervalId: q.intervalId };
                } else {
                    searchItem["value"] = { domain: searchItem.domain };
                }
            } else {
                searchItem["value"] = q;
            }
            return searchItem;
        })

        const newItems = await this.orm.call(
            "search.history",
            "create_new_search",
            [this.env.searchModel.resModel, this.env.searchModel.searchViewId, suggestItems, true]
        );
        for (let i=0; i < newItems.length; i++) {
            if (Object.keys(newItems[i]).length > 0) {
                this.env.searchModel.allSuggestItems.push(Object.assign(newItems[i], suggestItems[i]))
            }
            suggestItems[i].suggestId = newItems[i].suggestId
        }
        if (newItems) {
            const bookmarkId = await this.bookmarkService.addBookmarkItem({
                name: this.state.description,
                action_id: this.env.config.actionId,
                model: this.env.searchModel.resModel,
                view_type: this.env.config.viewType,
                suggest_ids: [[6, 0, this.env.searchModel.suggestIds]]
            })
            if (bookmarkId) {
                this.notification.add(_t("Add Bookmark Success."), {
                    type: "success",
                });
                this.state.description = ""
            }
        }
    }
    /**
     * @param {KeyboardEvent} ev
     */
    onInputKeydown(ev) {
        switch (ev.key) {
            case "Enter":
                ev.preventDefault();
                this.saveBookmark();
                break;
            case "Escape":
                // Gives the focus back to the component.
                ev.preventDefault();
                ev.target.blur();
                break;
        }
    }
}

CustomBookmarkItem.template = "bookmark.CustomBookmarkItem";
CustomBookmarkItem.components = { CheckBox, AccordionItem };
CustomBookmarkItem.props = {};
favoriteMenuRegistry.add(
    "custom-bookmark-item",
    { Component: CustomBookmarkItem, groupNumber: 4 },
    { sequence: 0 }
);
