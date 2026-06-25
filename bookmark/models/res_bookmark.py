# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResBookmark(models.Model):
    _name = "res.bookmark"
    _description = "Bookmark"
    _rec_name = "name"

    name = fields.Char(string="Name", required=True)
    suggest_ids = fields.Many2many("search.history", string="Search History")
    user_ids = fields.Many2many("res.users", string="User", required=True)
    action_id = fields.Many2one(
        "ir.actions.actions", required=True, string="Action", ondelete="CASCADE"
    )
    menu_id = fields.Many2one("ir.ui.menu", string="Menu", ondelete="CASCADE")
    model = fields.Char(string="Model", required=True)
    view_type = fields.Char(string="View Type", required=True)

    def get_values(self):
        res = []
        for bookmark in self:
            action = (
                self.env["ir.actions.act_window"]
                .sudo()
                .browse(bookmark.action_id.id)
                .read()[0]
            )
            action["display_name"] = bookmark.name
            res.append(
                {
                    "id": bookmark.id,
                    "name": bookmark.name,
                    "suggestIds": bookmark.suggest_ids.ids,
                    "menu_id": bookmark.menu_id and bookmark.menu_id.id or None,
                    "action_id": bookmark.action_id and bookmark.action_id.id or None,
                    "action": action,
                    "view_type": bookmark.view_type or None,
                }
            )
        return res

    @api.model
    def get_bookmarks(self):
        bookmarks = self.search([("user_ids", "in", [self.env.uid])])
        return bookmarks.get_values()

    @api.model
    def create_bookmark(self, vals_list):
        bookmarks = self.create(vals_list)
        return bookmarks.get_values()

    def share_bookmark(self, user_ids):
        self.mapped("suggest_ids").write({"user_ids": [(4, user) for user in user_ids]})
        self.write({"user_ids": [(4, user) for user in user_ids]})

    def remove_or_unlink(self):
        cond1 = self.filtered(lambda s: len(s.user_ids) == 1).unlink()
        cond2 = self.filtered(lambda s: len(s.user_ids) > 1).write(
            {"user_ids": [(3, self.env.uid)]}
        )
        return all([cond1, cond2])

    def unlink(self):
        self.mapped("suggest_ids").filtered(lambda s: s.use_in_bookmark).unlink()
        return super(ResBookmark, self).unlink()
