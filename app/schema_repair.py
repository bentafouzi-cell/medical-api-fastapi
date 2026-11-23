"""Reparation additive du schema.

`Base.metadata.create_all()` cree les tables manquantes mais ne modifie jamais
une table existante : ajouter un champ au modele apres coup provoque donc une
erreur "column does not exist" en production.

Ce module ajoute les colonnes manquantes, uniquement. Il ne supprime rien, ne
renomme rien, ne change aucun type. Il est idempotent : sans ecart, il ne fait
rien.

Ce n'est pas un remplacement d'Alembic : les changements destructifs ou les
colonnes NOT NULL restent a traiter par une vraie migration.
"""
from sqlalchemy import inspect, text

from .database import Base, engine


def reparer_schema() -> list[str]:
    inspecteur = inspect(engine)
    tables_existantes = set(inspecteur.get_table_names())
    ajouts: list[str] = []

    for table in Base.metadata.sorted_tables:
        if table.name not in tables_existantes:
            continue  # create_all vient de la creer, elle est complete

        presentes = {c["name"] for c in inspecteur.get_columns(table.name)}
        for colonne in table.columns:
            if colonne.name in presentes:
                continue

            nom = f"{table.name}.{colonne.name}"
            if not colonne.nullable and colonne.default is None and colonne.server_default is None:
                print(f"[schema] IGNORE {nom} : NOT NULL sans defaut, migration manuelle requise")
                continue

            type_sql = colonne.type.compile(engine.dialect)
            ddl = f'ALTER TABLE "{table.name}" ADD COLUMN "{colonne.name}" {type_sql}'
            with engine.begin() as connexion:
                connexion.execute(text(ddl))
            print(f"[schema] colonne ajoutee : {nom} ({type_sql})")
            ajouts.append(nom)

    if not ajouts:
        print("[schema] aucun ecart detecte")
    return ajouts
