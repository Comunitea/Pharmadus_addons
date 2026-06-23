# -*- coding: utf-8 -*-

import json

from odoo import api, fields, models


class SearchHistory(models.Model):
    _name = "search.history"
    _description = "Search History"
    _order = "create_date DESC"
    _rec_name = "description"

    user_ids = fields.Many2many("res.users", string="Users")
    model_id = fields.Many2one("ir.model", string="Model", ondelete="CASCADE")
    model = fields.Char(related="model_id.model", store=True)
    search_view_id = fields.Many2one(
        "ir.ui.view", string="Search View", ondelete="CASCADE"
    )

    name = fields.Char(string="Name", readonly=True)
    favorite_id = fields.Many2one(
        "ir.filters", string="Favorite Id", readonly=True, ondelete="CASCADE"
    )
    description = fields.Char(string="Description", readonly=True)
    value = fields.Char(string="Value")
    custom = fields.Boolean(string="Custom", readonly=True)
    type = fields.Selection(
        [
            ("field", "Field"),
            ("filter", "Filter"),
            ("groupBy", "GroupBy"),
            ("favorite", "Favorite"),
            ("dateFilter", "Date Filter"),
            ("dateGroupBy", "Date Group"),
        ],
        string="Type",
    )
    use_in_bookmark = fields.Boolean(string="Use In Bookmark", default=False)
    active = fields.Boolean(default=True)
    options_params = fields.Char(string="Options Params")

    @api.model
    def create_new_search(self, model, search_view_id, datas, use_in_bookmark=False):
        if not len(datas):
            return []
        res = []
        model_id = self.env["ir.model"].sudo().search([("model", "=", model)], limit=1)
        for data in datas:
            type = data.get("type")
            custom = data.get("custom")
            name = (
                data.get("name")
                if type in ["filter", "dateFilter"]
                else data.get("fieldName")
            )
            favorite_id = data.get("serverSideId")
            value = data.get("value", {})
            if "searchItemId" in value:
                value.pop("searchItemId")
            value = json.dumps(value)
            options_params = json.dumps(data.get("optionsParams"))
            domain = [
                ("model", "=", model),
                ("search_view_id", "=", search_view_id),
                ("type", "=", type),
                ("value", "=", value),
            ]

            if type in ["field", "filter", "groupBy"]:
                domain.append(("name", "=", name))
            if type == "favorite":
                domain.append(("favorite_id", "=", favorite_id))

            exist_suggest = self.search(domain, limit=1)
            if exist_suggest:
                use_in_bookmark = exist_suggest.use_in_bookmark
                vals = {}

                if use_in_bookmark:
                    vals["use_in_bookmark"] = False

                if len(vals.keys()):
                    exist_suggest.write(vals)

                if use_in_bookmark:
                    res.append(exist_suggest.get_value(show=True))
                else:
                    res.append({})
            else:
                vals = self.create(
                    {
                        "model_id": model_id and model_id.id or False,
                        "search_view_id": search_view_id,
                        "type": type,
                        "name": name,
                        "custom": custom,
                        "favorite_id": favorite_id,
                        "description": data.get("description"),
                        "value": value,
                        "user_ids": [(4, self.env.uid)],
                        "use_in_bookmark": use_in_bookmark,
                        "options_params": options_params,
                    }
                ).get_value(show=True)
                res += vals
        return res

    def share_suggest(self, user_ids):
        self.write({"user_ids": [(4, user) for user in user_ids]})

    def remove_or_unlink(self):
        bookmarks = self.env["res.bookmark"].search(
            [("user_ids", "in", [self.env.uid]), ("suggest_ids", "in", self.ids)]
        )
        suggests_not_in_bookmark = self.filtered(
            lambda s: s.id not in bookmarks.mapped("suggest_ids").ids
        )
        suggests_in_bookmark = self - suggests_not_in_bookmark

        cond1 = suggests_not_in_bookmark.filtered(
            lambda s: len(s.user_ids) == 1
        ).unlink()
        cond2 = suggests_not_in_bookmark.filtered(lambda s: len(s.user_ids) > 1).write(
            {"user_ids": [(3, self.env.uid)]}
        )
        cond3 = suggests_in_bookmark.write({"use_in_bookmark": True})
        return all([cond1, cond2, cond3])

    @api.model
    def get_suggest(self, model, search_view_id):
        domain = [
            ("search_view_id", "=", search_view_id),
            ("model", "=", model),
            ("user_ids", "in", [self.env.uid]),
        ]

        suggests = self.env["search.history"].search(domain, order="create_date DESC")
        return suggests and suggests.get_value(show=True) or []

    def get_value(self, show):
        return [
            {
                "type": suggest.type,
                "name": suggest.name or None,
                "fieldName": suggest.name or None,
                "serverSideId": suggest.favorite_id.id or None,
                "custom": suggest.custom,
                "value": json.loads(suggest.value),
                "description": suggest.description,
                "suggestId": suggest.id,
                "show": show,
                "use_in_bookmark": suggest.use_in_bookmark,
                "options_params": suggest.options_params and json.loads(suggest.options_params) or {},
            }
            for suggest in self
        ]
