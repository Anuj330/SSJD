from fastapi import APIRouter
from app.api import users, auth
from . import members, member_profile, member_auth, ledger


router = APIRouter(prefix="/api/v1")

# Users
router.add_api_route(
    "/users/",
    users.create_user,
    methods=["POST"],
    response_model=None,
    tags=["Users"],
)

# Members
router.add_api_route(
    "/members/",
    members.create_member,
    methods=["POST"],
    tags=["Members"],
)

router.add_api_route(
    "/members/",
    members.list_members,
    methods=["GET"],
    tags=["Members"],
)

router.add_api_route(
    "/members/{member_id}",
    members.get_member,
    methods=["GET"],
    tags=["Members"],
)

router.add_api_route(
    "/members/{member_id}",
    members.update_member,
    methods=["PUT"],
    tags=["Members"],
)

router.add_api_route(
    "/members/{member_id}",
    members.deactivate_member,
    methods=["DELETE"],
    tags=["Members"],
)

# Member Profiles
router.add_api_route(
    "/member-profiles/",
    member_profile.create_member_profile,
    methods=["POST"],
    tags=["Member Profiles"],
)

router.add_api_route(
    "/member-profiles/",
    member_profile.list_member_profiles,
    methods=["GET"],
    tags=["Member Profiles"],
)

router.add_api_route(
    "/member-profiles/{profile_id}",
    member_profile.get_member_profile,
    methods=["GET"],
    tags=["Member Profiles"],
)

router.add_api_route(
    "/member-profiles/{profile_id}",
    member_profile.update_member_profile,
    methods=["PUT"],
    tags=["Member Profiles"],
)

# Member Auth
router.add_api_route(
    "/member/login",
    member_auth.member_login,
    methods=["POST"],
    tags=["Member Auth"],
)

# Ledger
router.add_api_route(
    "/ledger/accounts/",
    ledger.create_account,
    methods=["POST"],
    tags=["Ledger"],
)

router.add_api_route(
    "/ledger/journal/post",
    ledger.post_journal,
    methods=["POST"],
    tags=["Ledger"],
)

router.add_api_route(
    "/ledger/journal/{entry_id}/reverse",
    ledger.reverse_journal,
    methods=["POST"],
    tags=["Ledger"],
)

router.add_api_route(
    "/ledger/accounts/{account_id}/statement",
    ledger.account_statement,
    methods=["GET"],
    tags=["Ledger"],
)

router.add_api_route(
    "/ledger/trial-balance",
    ledger.trial_balance,
    methods=["GET"],
    tags=["Ledger"],
)

router.add_api_route(
    "/members/{member_id}/money-flow",
    ledger.member_money_flow,
    methods=["GET"],
    tags=["Ledger"],
)
