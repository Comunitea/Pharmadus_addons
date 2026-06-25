# -*-coding:utf-8 -*-

from odoo import api, fields, models


class WizardShareBookmark(models.Model):
    _name = "wizard.share.bookmark"
    _description = "Share Bookmark"

    @api.model
    def default_get(self, fields):
        res = super(WizardShareBookmark, self).default_get(fields)
        bookmark_records = self.env.context.get("bookmark_ids", [])
        res.update({"bookmark_ids": [(6, 0, bookmark_records)]})
        return res

    user_ids = fields.Many2many("res.users", string="Share Users", required=True)
    bookmark_ids = fields.Many2many("res.bookmark", string="Bookmark", required=True)

    def action_share(self):
        self.bookmark_ids.share_bookmark(self.user_ids.ids)
