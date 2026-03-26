#!/usr/bin/env python3

import ssl
import xmlrpc.client


class OdooXmlRpcClient:
    def __init__(self, url, db, username, password, verify_ssl=True):
        self.url = url.rstrip("/")
        self.db = db
        self.username = username
        self.password = password
        transport = None
        if self.url.startswith("https://") and not verify_ssl:
            ssl_context = ssl._create_unverified_context()
            transport = xmlrpc.client.SafeTransport(context=ssl_context)
        self.common = xmlrpc.client.ServerProxy(
            "{}/xmlrpc/2/common".format(self.url),
            transport=transport,
        )
        self.models = xmlrpc.client.ServerProxy(
            "{}/xmlrpc/2/object".format(self.url),
            transport=transport,
        )
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})
        if not self.uid:
            raise RuntimeError(
                "Authentication failed for {} on database {}".format(
                    self.username, self.db
                )
            )

    def execute(self, model, method, *args, **kwargs):
        return self.models.execute_kw(
            self.db,
            self.uid,
            self.password,
            model,
            method,
            list(args),
            kwargs,
        )

    def search(self, model, domain, **kwargs):
        return self.execute(model, "search", domain, **kwargs)

    def read(self, model, ids, fields=None, **kwargs):
        read_kwargs = dict(kwargs)
        if fields is not None:
            read_kwargs["fields"] = fields
        return self.execute(model, "read", ids, **read_kwargs)

    def search_read(self, model, domain, fields=None, **kwargs):
        read_kwargs = dict(kwargs)
        if fields is not None:
            read_kwargs["fields"] = fields
        return self.execute(model, "search_read", domain, **read_kwargs)

    def write(self, model, ids, values):
        return self.execute(model, "write", ids, values)
