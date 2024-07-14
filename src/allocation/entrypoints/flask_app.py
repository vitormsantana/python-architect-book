from datetime import datetime
from flask import Flask, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from allocation.service_layer import unit_of_work, messagebus as messageBus
from allocation.service_layer import handlers
from allocation.domain import model, events
from allocation.adapters import orm
from allocation.service_layer import unit_of_work

app = Flask(__name__)
orm.start_mappers()


@app.route("/add_batch", methods=["POST"])
def add_batch():
    eta = request.json["eta"]
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()
    handlers.add_batch(
        request.json["ref"],
        request.json["sku"],
        request.json["qty"],
        eta,
        unit_of_work.SqlAlchemyUnitOfWork(),
    )
    return "OK", 201


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        event = events.AllocationRequired(request.json['orderid'], request.json['sku'], request.json['qty'],)
        results = messageBus.handle(event, unit_of_work.SqlAlchemyUnitOfWork())
        batchref = results.pop(0)

    except (model.OutOfStock, handlers.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201
