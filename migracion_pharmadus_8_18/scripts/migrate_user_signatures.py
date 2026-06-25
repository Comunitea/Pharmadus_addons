import argparse


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Migra firmas locales desde res_users.signature_moved1 al campo "
            "res.users.pharmadus_signature_image. Debe ejecutarse dentro de odoo shell."
        )
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Límite opcional de usuarios a procesar.",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Desplazamiento para la búsqueda de usuarios.",
    )
    parser.add_argument(
        "--user-ids",
        default="",
        help="IDs de res.users, separados por comas, para migrar solo esos usuarios.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Escribe cambios. Sin este parámetro, se ejecuta en modo simulación.",
    )
    return parser.parse_args(argv)


def parse_id_list(raw_value):
    if not raw_value:
        return []
    return [int(part.strip()) for part in raw_value.split(",") if part.strip()]


def log(message):
    print(message)


def _legacy_rows(env, user_ids=None, limit=0, offset=0):
    params = []
    where = ["signature_moved1 IS NOT NULL"]
    if user_ids:
        where.append("id = ANY(%s)")
        params.append(user_ids)

    query = """
        SELECT id, encode(signature_moved1, 'escape')
          FROM res_users
         WHERE {where}
         ORDER BY id
    """.format(where=" AND ".join(where))
    if limit:
        query += " LIMIT %s"
        params.append(limit)
    if offset:
        query += " OFFSET %s"
        params.append(offset)

    env.cr.execute(query, params)
    return env.cr.fetchall()


def migrate(env, user_ids=None, limit=0, offset=0, write=False):
    counters = {
        "updated": 0,
        "would_update": 0,
        "target_already_has_signature": 0,
        "missing_user": 0,
        "missing_source_signature": 0,
    }
    rows = _legacy_rows(env, user_ids=user_ids, limit=limit, offset=offset)

    log("Modo: {}".format("ESCRITURA" if write else "SIMULACION"))
    log("Usuarios con firma heredada: {}".format(len(rows)))

    Users = env["res.users"].with_context(active_test=False)
    for user_id, legacy_signature in rows:
        user = Users.browse(user_id).exists()
        if not user:
            counters["missing_user"] += 1
            log("OMITIDO {} -> missing_user".format(user_id))
            continue
        if not legacy_signature:
            counters["missing_source_signature"] += 1
            log("OMITIDO {} -> missing_source_signature".format(user.login))
            continue
        if user.pharmadus_signature_image:
            counters["target_already_has_signature"] += 1
            log("OMITIDO {} -> target_already_has_signature".format(user.login))
            continue

        if write:
            user.pharmadus_signature_image = legacy_signature
            counters["updated"] += 1
            log("UPDATED {}".format(user.login))
        else:
            counters["would_update"] += 1
            log("WOULD_UPDATE {}".format(user.login))

    log("Resumen:")
    for key, value in counters.items():
        log("  {}: {}".format(key, value))
    return counters


def main(env, argv=None):
    args = parse_args(argv)
    return migrate(
        env,
        user_ids=parse_id_list(args.user_ids),
        limit=args.limit,
        offset=args.offset,
        write=args.write,
    )
