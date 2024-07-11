import abc

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.allocation import config
from src.allocation.adapters import repository


class AbstractUnitOfWork(abc.ABC):
    products: repository.AbstractProductsRepository

    def __enter__(self):
        return self

    def __exit__(self, exn_type, exn_value, traceback):
        if exn_type is None:
            self.commit()
        else:
            self.rollback()


DEFAULT_SESSION_FACTORY = sessionmaker(
    bind=create_engine(config.get_postgres_uri(), isolation_level="REPEATABLE READ")
)


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()
        self.batches = repository.SqlAlchemyRepositoy(self.session)
        return super().__enter__()

        def __exit__(self, *args):
            super().__exit__(*args)
            self.session.close()

        def commit(self):
            self.session.commit()

        def rollback(self):
            self.session.rollback()
