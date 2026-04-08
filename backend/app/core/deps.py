from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models import OrgMembership, Organization, User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@dataclass(frozen=True)
class AuthedContext:
    user: User
    org: Organization
    role: str


def _get_or_create_dev_user_and_org(db: Session) -> AuthedContext:
    # Dev fallback: one user + one org.
    org = db.query(Organization).filter(Organization.slug == "dev").one_or_none()
    if org is None:
        org = Organization(slug="dev", name="Dev Org")
        db.add(org)
        db.flush()

    user = db.query(User).filter(User.external_sub == "dev-user").one_or_none()
    if user is None:
        user = User(external_sub="dev-user", email="dev@example.com", display_name="Dev User")
        db.add(user)
        db.flush()

    m = (
        db.query(OrgMembership)
        .filter(OrgMembership.org_id == org.id, OrgMembership.user_id == user.id)
        .one_or_none()
    )
    if m is None:
        m = OrgMembership(org_id=org.id, user_id=user.id, role="admin")
        db.add(m)
        db.flush()

    return AuthedContext(user=user, org=org, role=m.role)


def get_authed_context(
    db: Session = Depends(get_db),
    x_org_slug: Optional[str] = Header(default=None, alias="X-Org-Slug"),
):
    """
    Phase 2 baseline:
    - Real JWT verification will be enforced once AUTH0_* is configured.
    - Until then, we use a dev user/org so the app is usable locally.

    Multi-tenant note:
    - We scope requests by the selected org (X-Org-Slug). In production, this
      should be derived from the authenticated user's memberships (and ideally
      enforced via Postgres RLS).
    """

    ctx = _get_or_create_dev_user_and_org(db)

    if x_org_slug and x_org_slug != ctx.org.slug:
        org = db.query(Organization).filter(Organization.slug == x_org_slug).one_or_none()
        if org is None:
            raise HTTPException(status_code=404, detail="Organization not found.")
        membership = (
            db.query(OrgMembership)
            .filter(OrgMembership.org_id == org.id, OrgMembership.user_id == ctx.user.id)
            .one_or_none()
        )
        if membership is None:
            raise HTTPException(status_code=403, detail="Not a member of that organization.")
        return AuthedContext(user=ctx.user, org=org, role=membership.role)

    return ctx

