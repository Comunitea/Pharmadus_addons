// Copyright © 2025 Lazydoo
// See LICENSE file for full copyright and licensing details.

import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { SearchBar } from "@web/search/search_bar/search_bar";

patch(SearchBar.prototype, {
    setup() {
        super.setup()
        this.notification = useService("notification");
    },

    async addSearchHistory(facet) {
        const searchItems = Object.values(this.env.searchModel.searchItems).filter(
            (queryElem) => queryElem.groupId === facet.groupId && facet.searchItemIds.includes(queryElem.id));
        const suggestItems = searchItems.map((item) => {
            const query = this.env.searchModel.query.find(q => q.searchItemId == item.id);
            if (item.custom) {
                if (item.type == "dateGroupBy" ) {
                    item["value"] = { intervalId: query.intervalId };
                } else {
                    item["value"] = { domain: item.domain };
                }
            } else {
                item["value"] = query;
            }
            return item;
        })
        if (suggestItems.length > 0) {
            const newItems = await this.orm.call(
                "search.history",
                "create_new_search",
                [this.env.searchModel.resModel, this.env.searchModel.searchViewId, suggestItems]
            );
            for (let i=0; i < newItems.length; i++) {
                if (Object.keys(newItems[i]).length > 0) {
                    this.env.searchModel.allSuggestItems.push(Object.assign(newItems[i], suggestItems[i]))
                }
                suggestItems[i].suggestId = newItems[i].suggestId
            }
            if (newItems) {
                return this.notification.add(_t("Add Search History Success."), {
                    type: "success",
                });
            }
        }
    },

    onFacetLabelClick(ev, facet) {
        if (ev.ctrlKey || ev.metaKey) {
            this.addSearchHistory(facet)
        } else {
            super.onFacetLabelClick(ev.target, facet)
        }
    }
});
