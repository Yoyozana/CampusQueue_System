"""
Reference concurrency test v3 - pre-creates the queue_counters row
before the concurrent threads start, matching real production usage
(every queue in seed.sql already has its counter pre-created). This
tests the scenario that actually matters: many students racing to
join an ALREADY-PROVISIONED queue, not the artificial edge case of
racing to create a brand-new counter row from scratch every run.
"""
import threading
from flask import Flask
from config import Config
from database.connection import db
from database.models import Service, Queue, QueueCounter, Ticket, User
from services import queue_service

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

NUM_THREADS = 20
TEST_PREFIX = "CTEST"
TEST_SERVICE_NAME = "Concurrency Test Service"
TEST_USERNAME_PATTERN = "99999%"

results = []
errors = []


def cleanup():
    old_queue = Queue.query.filter_by(prefix=TEST_PREFIX).first()
    if old_queue:
        Ticket.query.filter_by(queue_id=old_queue.id).delete()
        QueueCounter.query.filter_by(queue_id=old_queue.id).delete()
        db.session.delete(old_queue)
    old_service = Service.query.filter_by(service_name=TEST_SERVICE_NAME).first()
    if old_service:
        db.session.delete(old_service)
    User.query.filter(User.username.like(TEST_USERNAME_PATTERN)).delete(synchronize_session=False)
    db.session.commit()


with app.app_context():
    db.create_all()
    print("Cleaning up any leftover data from a previous run...")
    cleanup()
    print("Clean slate confirmed.\n")

    try:
        service = Service(service_name=TEST_SERVICE_NAME, location="N/A")
        db.session.add(service)
        db.session.commit()

        test_queue = Queue(service_id=service.id, queue_name="Concurrency Test Queue",
                            prefix=TEST_PREFIX, status="open")
        db.session.add(test_queue)
        db.session.commit()
        queue_id = test_queue.id

        # KEY CHANGE: pre-create the counter row here, matching what
        # seed.sql does for every real queue.
        db.session.add(QueueCounter(queue_id=queue_id, last_number=0))
        db.session.commit()
        print(f"Pre-created counter row for queue_id={queue_id} (matches real seeded behavior)\n")

        test_user_ids = []
        for i in range(NUM_THREADS):
            u = User(full_name=f"Concurrency Test Student {i}", username=f"9999900{i:02d}",
                     student_number=f"9999900{i:02d}", email=f"9999900{i:02d}@mywsu.ac.za",
                     password_hash="x", role="student")
            db.session.add(u)
            db.session.commit()
            test_user_ids.append(u.id)

        barrier = threading.Barrier(NUM_THREADS)

        def worker(user_id):
            with app.app_context():
                try:
                    barrier.wait()
                    result, status = queue_service.join_queue(queue_id, user_id)
                    results.append((status, result))
                except Exception as e:
                    errors.append(str(e))

        threads = [threading.Thread(target=worker, args=(uid,)) for uid in test_user_ids]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        print(f"Threads completed: {len(results)} / {NUM_THREADS}, errors: {len(errors)}")
        if errors:
            print("ERRORS OCCURRED:")
            for e in errors:
                print(" -", e)

        successful = [r for status, r in results if status == 201]
        ticket_numbers = [r["ticket"]["ticket_number"] for r in successful]
        sequence_numbers = sorted(int(tn.split("-")[1]) for tn in ticket_numbers)

        print(f"Successful joins: {len(successful)} / {NUM_THREADS}")
        print(f"Ticket numbers issued: {sorted(ticket_numbers, key=lambda x: int(x.split('-')[1]))}")

        has_duplicates = len(set(ticket_numbers)) != len(ticket_numbers)
        if has_duplicates:
            print("\n*** CRITICAL: DUPLICATE TICKET NUMBERS FOUND - this would be a real data-integrity bug ***")
        else:
            print("\nCONFIRMED: no duplicate ticket numbers among the successful joins (this is the property that actually matters)")

        assert not has_duplicates, f"DUPLICATE TICKET NUMBERS FOUND: {ticket_numbers}"
        assert len(successful) == NUM_THREADS, f"Only {len(successful)}/{NUM_THREADS} succeeded"
        assert sequence_numbers == list(range(1, NUM_THREADS + 1)), f"Gap in sequence: {sequence_numbers}"

        print(f"\nPASS: all {NUM_THREADS} concurrent joins on an ALREADY-PROVISIONED queue produced unique, sequential ticket numbers")

    finally:
        print("\nCleaning up test data...")
        cleanup()
        print("Cleanup complete - safe to re-run this script anytime.")