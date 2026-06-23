// Copyright © 2025 Lazydoo
// See LICENSE file for full copyright and licensing details.

import { Component, onWillStart, markup } from "@odoo/owl";
import { useService, useBus } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { escape } from "@web/core/utils/strings";
import { _t } from "@web/core/l10n/translation";
import { getPeriodOptions } from "@web/search/utils/dates";

const suggestIcon = {
    field: "fa fa-fw fa-search",
    filter: "fa fa-fw fa-filter",
    groupBy: "fa-fw oi oi-group",
    favorite: "fa-fw fa fa-star",
    dateFilter: "fa fa-fw fa-filter",
    dateGroupBy: "fa-fw oi oi-group",
};

export class SearchHistory extends Component {
    static template = "bookmark.SearchHistory";
    static props = {}
    setup() {
        this.currentQuery = []
        this.orm = useService("orm");
        this.bookmarkService = useService("bookmarks")
        this.dialogService = useService("dialog");

        onWillStart(async () => {
            const searchItemIds = this.currentQuery.map(q => q.searchItemId)
            this.getAllSuggestItems().forEach(item => {
                if (searchItemIds.includes(item.id)) {
                    item.show = false
                }
            })
        });
    }

    get intervalOptions() {
        return this.env.searchModel.intervalOptions
    }

    get optionGenerators() {
        return this.env.searchModel.optionGenerators
    }

    get searchItems() {
        return this.env.searchModel.searchItems;
    }

    get model() {
        return this.env.searchModel.resModel;
    }

    get searchViewId() {
        return this.env.searchModel.searchViewId;
    }

    getAllSuggestItems() {
        return this.env.searchModel?.allSuggestItems || [];
    }

    get displaySuggestItems() {
        return this.getAllSuggestItems().filter(item => item.show && !item.use_in_bookmark)
    }

    async onSuggestRemoveAll(items) {
        const confirmMessage = _t("Are you sure you can delete the all suggestion?");
        this.dialogService.add(ConfirmationDialog, {
            body: markup(
                `<h4>${escape(confirmMessage)}</h4>`
            ),
            confirm: async () => {
                await this.env.searchModel.removeSuggest(items);
            },
            cancel: () => { },
        });
    }

    async onSuggestRemove(item) {
        const confirmMessage = _t("Are you sure you can delete the suggestion?");
        this.dialogService.add(ConfirmationDialog, {
            body: markup(
                `<h4>${escape(confirmMessage)}</h4>`
            ),
            confirm: async () => {
                await this.env.searchModel.removeSuggest([item]);
            },
            cancel: () => { },
        });
    }

    getIcon(item) {
        return suggestIcon[item.type];
    }

    getValueItem(item) {
        if (item.type == "field") {
            return ": " + item.value.autocompleteValue.label
        } else if (item.type == "dateGroupBy") {
            const label = this.intervalOptions?.find(interval => interval.id == item.value.intervalId)
            return label !== undefined ? ": " + label.description : ""
        } else if (item.type == "dateFilter") {
            if ("options_params" in item) {
                const label = getPeriodOptions(this.env.searchModel.referenceMoment, item.options_params).find((o) => o.id === item.value.generatorId)
                return label !== undefined ? ": " + label.description : "";
            } else {
                return "";
            }
        }
        else {
            return "";
        }
    }
}
