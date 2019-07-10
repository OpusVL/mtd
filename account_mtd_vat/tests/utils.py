def arbitrary(iterable):
    try:
        return next(iter(iterable))
    except StopIteration:
        raise IndexError("Iterable is empty")


def all_records_in_model(odoo_model):
    return odoo_model.search([])
