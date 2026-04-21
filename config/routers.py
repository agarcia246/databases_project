class VectorRouter:
    """Route the `search` app to the `vectors` (Postgres/pgvector) DB.

    All other apps stay on `default` (MySQL). Cross-DB FKs are forbidden,
    so the ProductEmbedding model must reference products by ID only.
    """

    VECTOR_APP = 'search'

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.VECTOR_APP:
            return 'vectors'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.VECTOR_APP:
            return 'vectors'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        labels = {obj1._meta.app_label, obj2._meta.app_label}
        if self.VECTOR_APP in labels and len(labels) > 1:
            return False
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.VECTOR_APP:
            return db == 'vectors'
        return db == 'default'
