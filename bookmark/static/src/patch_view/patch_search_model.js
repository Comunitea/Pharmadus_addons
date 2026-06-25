/** @odoo-module */

import { SearchModel } from "@web/search/search_model";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { FACET_ICONS, FACET_COLORS } from "@web/search/utils/misc";
import { Domain } from "@web/core/domain";

const shallowEqual = (object1, object2) => {
    const keys1 = Object.keys(object1);
    const keys2 = Object.keys(object2);

    if (keys1.length !== keys2.length) {
      return false;
    }

    for (let key of keys1) {
      if (object1[key] !== object2[key]) {
        return false;
      }
    }

    return true;
}

patch(SearchModel.prototype, {

    setup(services) {
        super.setup(services);
        this.bookmarkService = useService("bookmarks");
        this.allSuggestItems = [];
    },

    deactivateGroup(groupId) {
        const removeQuery = this.query.filter((queryElem) => {
            const searchItem = this.searchItems[queryElem.searchItemId];
            return searchItem.groupId === groupId;
        }).map(q => q.searchItemId);
        this.allSuggestItems.forEach((item) => {
            if (removeQuery.includes(item.id)) {
                item.show = true
            }
        });

        super.deactivateGroup(...arguments)
    },

    mappingSearchItem (item) {
        const searchItems = Object.values(this.searchItems).reverse()
        const searchItem = searchItems.find(
            (searchItem) => {
                if (!searchItem.custom) {
                    if (item.type == "field") {
                        return (
                            searchItem.type == "field" &&
                            searchItem.fieldName == item.name
                        );
                    } else if (["groupBy", "dateGroupBy"].includes(item.type)) {
                        return (
                            ["groupBy", "dateGroupBy"].includes(searchItem.type) &&
                            searchItem.fieldName == item.name
                        );
                    } else if (["filter", "dateFilter"].includes(item.type)) {
                        return (
                            ["filter", "dateFilter"].includes(searchItem.type) &&
                            searchItem.name == item.name
                        );
                    } else if (item.type == "favorite") {
                        return (
                            searchItem.type == "favorite" &&
                            searchItem.serverSideId == item.serverSideId
                        );
                    } else {
                        return false;
                    }
                } else {
                    return searchItem.suggestId == item.suggestId
                }
            }
        )
        return searchItem == undefined ? item : Object.assign(item, searchItem)
    },

    async load(config) {
        const { resModel } = config;
        if (!resModel) {
            throw Error(`SearchPanel config should have a "resModel" key`);
        }
        this.allSuggestItems = await this.orm.call("search.history", "get_suggest", [
            resModel,
            config.searchViewId,
        ]);
        return super.load(config);
    },

    createNewFilters(prefilters) {
        prefilters.forEach(prefilter => {
            prefilter.custom = true
        });
        super.createNewFilters(prefilters)
    },

    onSuggestChoose(item) {
        if (item.type == "favorite" && !Object.values(this.searchItems).find(i => i.id == item.id)) {
            this.allSuggestItems = this.allSuggestItems.filter(i => i.id !== item.id)
            this.trigger("remove_suggest")
            return
        }
        if (item.id) {
            if (item.type == "field") {
                this.addAutoCompletionValues(
                    item.id,
                    item.value.autocompleteValue
                );
            } else if (["groupBy", "filter", "favorite"].includes(item.type)) {
                this.toggleSearchItem(item.id);
            } else if(item.type == "dateGroupBy") {
                this.toggleDateGroupBy(item.id, item.value.intervalId);
            } else if(item.type == "dateFilter") {
                this.toggleDateFilter(item.id, item.value.generatorId);
            }
        } else if (item.custom) {
            if (["groupBy","dateGroupBy"].includes(item.type)) {
                const searchItem = Object.values(this.searchItems).find(i => i.fieldName == item.fieldName)
                if (searchItem) {
                    item.type == "groupBy" ? this.toggleSearchItem(searchItem.id) : this.toggleDateGroupBy(searchItem.id, item.value.intervalId);
                }  else {
                    this.createNewGroupBy(item.fieldName);
                }
            } else if (item.type == "filter") {
                this.createNewFilters([
                    {
                        custom: true,
                        description: item.description,
                        domain: item.value.domain,
                        suggestId: item.suggestId
                    },
                ]);
            }
            item = this.mappingSearchItem(item)
        }
        item.show = false
    },

    _activateDefaultSearchItems(defaultFavoriteId) {
        const bookmark = this.bookmarkService.currentBookmark
        this.allSuggestItems = this.allSuggestItems.map((item) => {
            return !item.custom ? this.mappingSearchItem(item) : item
        });
        if (bookmark.length > 0) {
            const defaultItems = this.allSuggestItems.filter(item => bookmark.includes(item.suggestId))
            defaultItems.forEach((item) => this.onSuggestChoose(item))
        } else {
            super._activateDefaultSearchItems(defaultFavoriteId)
        }
    },

    _getFacets() {
        const facets = [];
        const groups = this._getGroups();
        for (const group of groups) {
            const groupActiveItemDomains = [];
            const values = [];
            const searchItemIds = [];
            let title;
            let type;
            for (const activeItem of group.activeItems) {
                const domain = this._getSearchItemDomain(activeItem, {
                    withDateFilterDomain: true,
                });
                if (domain) {
                    groupActiveItemDomains.push(domain);
                }
                const searchItem = this.searchItems[activeItem.searchItemId];
                searchItemIds.push(activeItem.searchItemId)
                switch (searchItem.type) {
                    case "field_property":
                    case "field": {
                        type = "field";
                        title = searchItem.description;
                        for (const autocompleteValue of activeItem.autocompletValues) {
                            values.push(autocompleteValue.label);
                        }
                        break;
                    }
                    case "groupBy": {
                        type = "groupBy";
                        values.push(searchItem.description);
                        break;
                    }
                    case "dateGroupBy": {
                        type = "groupBy";
                        for (const intervalId of activeItem.intervalIds) {
                            const option = this.intervalOptions.find((o) => o.id === intervalId);
                            values.push(`${searchItem.description}: ${option.description}`);
                        }
                        break;
                    }
                    case "dateFilter": {
                        type = "filter";
                        const periodDescription = this._getDateFilterDomain(
                            searchItem,
                            activeItem.generatorIds,
                            "description"
                        );
                        values.push(`${searchItem.description}: ${periodDescription}`);
                        break;
                    }
                    default: {
                        type = searchItem.type;
                        values.push(searchItem.description);
                    }
                }
            }
            const facet = {
                groupId: group.id,
                type,
                values,
                searchItemIds,
                separator: type === "groupBy" ? ">" : _t("or"),
            };
            if (type === "field") {
                facet.title = title;
            } else {
                facet.icon = FACET_ICONS[type];
                facet.color = FACET_COLORS[type];
            }
            if (groupActiveItemDomains.length) {
                facet.domain = Domain.or(groupActiveItemDomains).toString();
            }
            facets.push(facet);
        }

        return facets;
    },

    get suggestIds() {
        let res = []
        this.query.forEach(q => {
            let suggestItem = this.allSuggestItems.find(
                i => {
                    if (i.custom) {
                        return shallowEqual(q, Object.assign({searchItemId: i.id}))
                    } else {
                        return shallowEqual(q, Object.assign({searchItemId: i.id}, i.value))
                    }
                    })
            if (suggestItem) {
                res.push(suggestItem)
            }
        })
        return res.map(r => r.suggestId)
    },

    async removeSuggest(items) {
        const suggestIds = items.map(item => item.suggestId)
        const result = this.orm.call("search.history", "remove_or_unlink", [suggestIds,]);
        if (result) {
            this.allSuggestItems = this.allSuggestItems.filter(
                (item) => !suggestIds.includes(item.suggestId)
            );
        }
        this.trigger("remove_suggest")
    }
});
