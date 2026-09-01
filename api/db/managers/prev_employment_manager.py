from sqlmodel import Session

from api.db.schema.prev_employment import PrevEmployment

class PrevEmploymentManager:

    def __init__(self, session: Session):
        self.session = session
        self.schema = PrevEmployment

    def get(self, **schema_fields) -> PrevEmployment:
        results = self.session.query(self.schema).filter_by(**schema_fields).all()
        if not results:
            raise Exception(f"{self.schema.__name__} matching {schema_fields} does not exist.")
        if len(results) > 1:
            raise Exception(
                f"{len(results)} {self.schema.__name__} objects match {schema_fields}, expected exactly one."
            )
        return results[0]

    def filter(self, **schema_fields):
        return self.session.query(self.schema).filter_by(**schema_fields).all()

    def create(self, **data):
        instance = self.schema(**data)
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def update(self, instances, data):
        for instance in instances:
            for key, value in data.items():
                setattr(instance, key, value)
        self.session.commit()
        for instance in instances:
            self.session.refresh(instance)
        return instances

    def delete(self, instance):
        self.session.delete(instance)
        self.session.commit()