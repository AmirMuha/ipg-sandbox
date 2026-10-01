"""T008 guards: illegal state transitions raise; numeric constraints reject bad input.

Numeric rules are DB CHECK constraints, so these tests execute real SQL against a real
SQLite database rather than asserting on ORM behaviour. Postgres-only details that SQLite
cannot express are asserted against the compiled Postgres DDL instead — see
`test_partial_unique_index_on_enabled_provider` and the module docstring of `conftest.py`.

`_persisted` is used wherever a test needs real column defaults: SQLAlchemy applies
`default=`/`server_default=` at INSERT, so a freshly constructed row still has `None`.
"""

import uuid

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import CreateIndex

from src.models import (
    AdapterConfig,
    IllegalTransitionError,
    Project,
    Provider,
    Transaction,
    TransactionStatus,
)


def _project(**overrides) -> Project:
    fields = {"id": uuid.uuid4(), "name": "default"}
    fields.update(overrides)
    return Project(**fields)


def _persisted(session, **overrides) -> Transaction:
    """Flush project + adapter + transaction, returning the transaction with DB defaults set."""
    project = _project()
    session.add(project)
    adapter = AdapterConfig(
        id=uuid.uuid4(),
        project_id=project.id,
        provider=Provider.zarinpal,
        endpoint_path_prefix="/pg/v4/payment",
    )
    session.add(adapter)
    session.flush()

    fields = {
        "id": uuid.uuid4(),
        "project_id": project.id,
        "adapter_id": adapter.id,
        "amount_rial": 50_000,
    }
    fields.update(overrides)
    tx = Transaction(**fields)
    session.add(tx)
    session.flush()
    return tx


def _set_status(session, tx: Transaction, status: TransactionStatus) -> None:
    """Write `status` straight to the DB, bypassing the guard that is under test."""
    tx.status = status
    session.flush()


# --- illegal state transition raises (data-model.md state machine) ------------


def test_illegal_transition_settled_to_initiated_raises(session):
    """`settled` is terminal — moving back to `initiated` must raise, not mutate."""
    tx = _persisted(session)
    _set_status(session, tx, TransactionStatus.settled)

    with pytest.raises(IllegalTransitionError):
        tx.transition_to(TransactionStatus.initiated)

    assert tx.status is TransactionStatus.settled  # unchanged: no silent mutation


def test_illegal_transition_refunded_to_pending_raises(session):
    tx = _persisted(session)
    _set_status(session, tx, TransactionStatus.refunded)

    with pytest.raises(IllegalTransitionError):
        tx.transition_to(TransactionStatus.pending)

    assert tx.status is TransactionStatus.refunded


def test_illegal_transition_cannot_skip_pending_to_settled(session):
    """`initiated -> settled` skips a hop and is not on the diagram."""
    tx = _persisted(session)
    assert tx.status is TransactionStatus.initiated  # DB default applied on flush

    with pytest.raises(IllegalTransitionError):
        tx.transition_to(TransactionStatus.settled)

    assert tx.status is TransactionStatus.initiated


def test_illegal_transition_approved_to_settled_raises(session):
    """`approved` only reaches `refunded` — settling an approved transaction is off-diagram."""
    tx = _persisted(session)
    _set_status(session, tx, TransactionStatus.approved)

    with pytest.raises(IllegalTransitionError):
        tx.transition_to(TransactionStatus.settled)

    assert tx.status is TransactionStatus.approved


@pytest.mark.parametrize(
    ("start", "target"),
    [
        (TransactionStatus.initiated, TransactionStatus.pending),
        (TransactionStatus.initiated, TransactionStatus.declined),
        (TransactionStatus.initiated, TransactionStatus.failed),
        (TransactionStatus.pending, TransactionStatus.settled),
        (TransactionStatus.pending, TransactionStatus.approved),
        (TransactionStatus.pending, TransactionStatus.expired),
        (TransactionStatus.approved, TransactionStatus.refunded),
    ],
)
def test_legal_transitions_are_allowed(session, start, target):
    """Every edge drawn in data-model.md must still work — the guard is not over-strict."""
    tx = _persisted(session)
    _set_status(session, tx, start)

    tx.transition_to(target)

    assert tx.status is target


def test_same_status_is_a_noop(session):
    """Idempotent callers (e.g. a retried scheduler sweep) must not trip the guard."""
    tx = _persisted(session)
    _set_status(session, tx, TransactionStatus.settled)

    tx.transition_to(TransactionStatus.settled)

    assert tx.status is TransactionStatus.settled


# --- numeric constraints reject bad input ------------------------------------


def test_amount_rial_negative_rejected(session):
    project = _project()
    session.add(project)
    adapter = AdapterConfig(
        id=uuid.uuid4(),
        project_id=project.id,
        provider=Provider.zarinpal,
        endpoint_path_prefix="/z",
    )
    session.add(adapter)
    session.flush()

    session.add(
        Transaction(
            id=uuid.uuid4(),
            project_id=project.id,
            adapter_id=adapter.id,
            amount_rial=-1,
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()


def test_amount_rial_zero_allowed(session):
    """`amount_rial >= 0` — zero is legal, so the guard must not be off-by-one."""
    _persisted(session, amount_rial=0)


@pytest.mark.parametrize("bad_cap", [0, -1])
def test_history_cap_below_one_rejected(session, bad_cap):
    session.add(_project(history_cap=bad_cap))
    with pytest.raises(IntegrityError):
        session.flush()


def test_history_cap_of_one_allowed(session):
    session.add(_project(history_cap=1))
    session.flush()  # must not raise


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("pending_settle_delay_s", -1),
        ("pending_settle_delay_s", 300),  # bound is exclusive
        ("timeout_delay_s", -1),
        ("timeout_delay_s", 300),
    ],
)
def test_delays_outside_zero_and_300_rejected(session, field, bad_value):
    session.add(_project(**{field: bad_value}))
    with pytest.raises(IntegrityError):
        session.flush()


@pytest.mark.parametrize("field", ["pending_settle_delay_s", "timeout_delay_s"])
def test_delay_upper_bound_is_exclusive(session, field):
    """299 is legal; 300 is not (covered above)."""
    session.add(_project(**{field: 299}))
    session.flush()


def test_webhook_retry_max_below_one_rejected(session):
    session.add(_project(webhook_retry_max=0))
    with pytest.raises(IntegrityError):
        session.flush()


def test_duplicate_authority_in_same_project_rejected(session):
    """Unique `(project_id, authority)` — data-model.md Uniqueness section."""
    _persisted(session, authority="A-1")

    project = session.query(Project).one()
    adapter = session.query(AdapterConfig).one()
    session.add(
        Transaction(
            id=uuid.uuid4(),
            project_id=project.id,
            adapter_id=adapter.id,
            amount_rial=50_000,
            authority="A-1",
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()


# --- Postgres-only schema details (asserted on compiled DDL) -----------------


def _index_for(name: str) -> str:
    for table in Transaction.metadata.tables.values():
        for index in table.indexes:
            if index.name == name:
                return str(CreateIndex(index).compile(dialect=postgresql.dialect()))
    raise AssertionError(f"index {name} not declared on any table")


def test_partial_unique_index_on_enabled_provider():
    """One *enabled* AdapterConfig per (project_id, provider).

    SQLite silently drops the partial predicate: it renders a plain UNIQUE over both columns,
    which would also forbid disabled duplicates, and CREATE UNIQUE INDEX ... WHERE is not an
    option there. The rule is therefore asserted against the compiled Postgres DDL.
    """
    ddl = _index_for("uq_adapter_configs_enabled_provider")

    assert "UNIQUE INDEX" in ddl
    assert "WHERE enabled" in ddl


def test_required_indexes_declared():
    """data-model.md indexes: (project_id, created_at DESC) and (status, due_at)."""
    assert "created_at DESC" in _index_for("ix_transactions_project_created_at")
    assert "(status, due_at)" in _index_for("ix_transactions_status_due_at")


def test_models_cover_only_the_four_t008_tables():
    """VisitorSession belongs to T052; webhook_deliveries landed in T037."""
    assert set(Transaction.metadata.tables) == {
        "projects",
        "adapter_configs",
        "transactions",
        "usage_meters",
        "webhook_deliveries",
        "visitor_sessions",
    }


def test_defaults_match_data_model(session):
    """Defaults land on the persisted row (they are applied at INSERT, not on construction)."""
    project = _project()
    session.add(project)
    adapter = AdapterConfig(
        id=uuid.uuid4(),
        project_id=project.id,
        provider=Provider.zarinpal,
        endpoint_path_prefix="/z",
    )
    session.add(adapter)
    session.flush()
    tx = _persisted(session)

    assert project.history_cap == 1000  # FR-006
    assert project.pending_settle_delay_s == 5  # clarification 5
    assert project.kind.value == "local"
    assert project.default_scenario.value == "approve"
    assert project.webhook_retry_backoff_s == [1, 2, 4]

    assert tx.status is TransactionStatus.initiated
    assert tx.currency == "IRR"
    assert tx.amount_rial == 50_000
    assert tx.effective_scenario.value == "approve"
