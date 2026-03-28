from __future__ import annotations

import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path


# The shell may still export DEBUG=release from another project.
os.environ.pop("DEBUG", None)
os.environ.pop("APP_DEBUG", None)

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.database import SessionLocal  # noqa: E402
from app.models.comment import Comment  # noqa: E402
from app.models.statushistory import StatusHistory  # noqa: E402
from app.models.ticket import Ticket, TicketPriority, TicketStatus  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.time_utils import utc_now  # noqa: E402
from app.utils.hashing import get_password_hash  # noqa: E402


RNG = random.Random(42)


@dataclass(frozen=True)
class SeedUser:
    username: str
    email: str
    role: UserRole
    password: str
    ticket_target: int


SEED_USERS: list[SeedUser] = [
    SeedUser("admin_oleg", "admin.oleg@example.com", UserRole.ADMIN, "AdminPass123", 25),
    SeedUser("admin_nika", "admin.nika@example.com", UserRole.ADMIN, "AdminPass123", 25),
    SeedUser("user_anna", "user.anna@example.com", UserRole.USER, "UserPass123", 5),
    SeedUser("user_igor", "user.igor@example.com", UserRole.USER, "UserPass123", 5),
    SeedUser("user_lena", "user.lena@example.com", UserRole.USER, "UserPass123", 5),
    SeedUser("user_timur", "user.timur@example.com", UserRole.USER, "UserPass123", 5),
]

TICKET_SUBJECTS = [
    "Cannot sign in to dashboard",
    "Need access to internal report",
    "Broken export to CSV",
    "Frontend form validation issue",
    "Mobile layout overflow",
    "Order status stuck in processing",
    "Password reset email not delivered",
    "Slow response from ticket list endpoint",
    "Need clarification on invoice data",
    "Permissions mismatch for support team",
]

TICKET_DETAILS = [
    "The problem is reproducible and should be visible in logs.",
    "User reports that the issue started after the last deployment.",
    "Please investigate both backend behavior and UI state.",
    "Temporary workaround does not help in all cases.",
    "This affects daily work and should be prioritized.",
]

COMMENT_TEXTS = [
    "Initial triage completed.",
    "Reproduced on local environment.",
    "Need additional details from the reporter.",
    "Assigned for investigation.",
    "Fix is prepared and waiting for verification.",
]


def get_or_create_user(db, seed_user: SeedUser) -> User:
    user = db.query(User).filter(User.username == seed_user.username).first()
    if not user:
        user = db.query(User).filter(User.email == seed_user.email).first()

    if user:
        user.email = seed_user.email
        user.username = seed_user.username
        user.role = seed_user.role
        user.is_active = True
        if not user.hashed_password:
            user.hashed_password = get_password_hash(seed_user.password)
        return user

    user = User(
        email=seed_user.email,
        username=seed_user.username,
        hashed_password=get_password_hash(seed_user.password),
        role=seed_user.role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def pick_status() -> TicketStatus:
    return RNG.choices(
        population=[
            TicketStatus.NEW,
            TicketStatus.IN_PROGRESS,
            TicketStatus.RESOLVED,
            TicketStatus.CLOSED,
        ],
        weights=[4, 3, 2, 1],
        k=1,
    )[0]


def build_ticket(author: User, admins: list[User], index: int) -> Ticket:
    status = pick_status()
    priority = RNG.choice(list(TicketPriority))
    assignee = None

    if status != TicketStatus.NEW and admins:
        possible_admins = [admin for admin in admins if admin.id != author.id] or admins
        assignee = RNG.choice(possible_admins)

    title = f"{TICKET_SUBJECTS[index % len(TICKET_SUBJECTS)]} #{index + 1}"
    description = (
        f"{TICKET_DETAILS[index % len(TICKET_DETAILS)]} "
        f"Seeded ticket for {author.username}. "
        f"Current priority is {priority.value}."
    )

    ticket = Ticket(
        title=title,
        description=description,
        status=status,
        priority=priority,
        author_id=author.id,
        assignee_id=assignee.id if assignee else None,
    )
    if status == TicketStatus.CLOSED:
        ticket.closed_at = utc_now()
    return ticket


def create_status_history(db, ticket: Ticket, admins: list[User]) -> None:
    if ticket.status == TicketStatus.NEW or not admins:
        return

    actor = ticket.assignees or admins[0]

    transitions: list[tuple[TicketStatus | None, TicketStatus]] = []
    if ticket.status == TicketStatus.IN_PROGRESS:
        transitions = [(TicketStatus.NEW, TicketStatus.IN_PROGRESS)]
    elif ticket.status == TicketStatus.RESOLVED:
        transitions = [
            (TicketStatus.NEW, TicketStatus.IN_PROGRESS),
            (TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED),
        ]
    elif ticket.status == TicketStatus.CLOSED:
        if ticket.priority == TicketPriority.HIGH:
            transitions = [
                (TicketStatus.NEW, TicketStatus.CLOSED),
            ]
        else:
            transitions = [
                (TicketStatus.NEW, TicketStatus.IN_PROGRESS),
                (TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED),
                (TicketStatus.RESOLVED, TicketStatus.CLOSED),
            ]

    for old_status, new_status in transitions:
        db.add(
            StatusHistory(
                ticket_id=ticket.id,
                changed_by=actor.id,
                old_status=old_status,
                new_status=new_status,
            )
        )


def create_comments(db, ticket: Ticket, author: User, admins: list[User], index: int) -> None:
    if index % 2 != 0:
        return

    db.add(
        Comment(
            ticket_id=ticket.id,
            author_id=author.id,
            content=COMMENT_TEXTS[index % len(COMMENT_TEXTS)],
        )
    )

    if ticket.assignee_id:
        db.add(
            Comment(
                ticket_id=ticket.id,
                author_id=ticket.assignee_id,
                content="Assignee reviewed the ticket and started work.",
            )
        )
    elif admins and author.role != UserRole.ADMIN:
        db.add(
            Comment(
                ticket_id=ticket.id,
                author_id=admins[0].id,
                content="Admin reviewed the request and left a note.",
            )
        )


def ensure_ticket_volume(db, author: User, admins: list[User], target_count: int) -> int:
    current_count = db.query(Ticket).filter(Ticket.author_id == author.id).count()
    created = 0

    for index in range(current_count, target_count):
        ticket = build_ticket(author, admins, index)
        db.add(ticket)
        db.flush()
        create_status_history(db, ticket, admins)
        create_comments(db, ticket, author, admins, index)
        created += 1

    return created


def main() -> None:
    db = SessionLocal()
    try:
        seeded_users: list[User] = []
        for seed_user in SEED_USERS:
            user = get_or_create_user(db, seed_user)
            seeded_users.append(user)

        db.commit()

        admins = [user for user in seeded_users if user.role == UserRole.ADMIN]
        created_tickets = 0

        for seed_user, db_user in zip(SEED_USERS, seeded_users, strict=True):
            created_tickets += ensure_ticket_volume(
                db, db_user, admins, seed_user.ticket_target
            )

        db.commit()

        print("Seed completed.")
        print(f"Demo users prepared: {len(seeded_users)}")
        print(f"New tickets created: {created_tickets}")
        print("")
        print("Credentials:")
        for seed_user in SEED_USERS:
            print(
                f"- {seed_user.username} | {seed_user.email} | "
                f"role={seed_user.role.value} | password={seed_user.password}"
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
