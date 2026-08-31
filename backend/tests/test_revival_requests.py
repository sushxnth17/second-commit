import pytest
from app.models.repository import Repository
from app.models.revival_request import RevivalRequest
from app.services.repository_service import create_repository
from app.services.user_service import create_user


def test_create_revival_request_lifecycle(client, db_session, test_user, auth_context):
    # 1. Create developer_b user
    developer_b = create_user(
        db=db_session,
        github_id=98765,
        username="devb",
        name="Developer B",
        avatar_url="https://avatar.url/b",
        access_token="token_b",
    )
    db_session.commit()

    # 2. Create repository owned by test_user
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 901,
            "name": "project-alpha",
            "full_name": "testuser/project-alpha",
            "html_url": "https://github.com/testuser/project-alpha",
            "default_branch": "main",
        },
    )
    # Publish repository
    repo.published = True
    db_session.commit()

    # 3. Request to revive as Developer B (Authenticated, Not Owner, Published)
    auth_context.user = developer_b
    response = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "I would love to help continue maintaining this project!"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["repository_id"] == repo.id
    assert data["requester_id"] == developer_b.id
    assert data["message"] == "I would love to help continue maintaining this project!"
    assert data["status"] == "pending"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

    # 4. Check if request is persisted in the database
    db_req = db_session.query(RevivalRequest).filter(RevivalRequest.id == data["id"]).first()
    assert db_req is not None
    assert db_req.repository_id == repo.id
    assert db_req.requester_id == developer_b.id
    assert db_req.message == "I would love to help continue maintaining this project!"
    assert db_req.status == "pending"

    # 5. Check GET my-pending endpoint
    response = client.get(f"/repositories/{repo.id}/revival-requests/my-pending")
    assert response.status_code == 200
    get_data = response.json()
    assert get_data is not None
    assert get_data["id"] == data["id"]
    assert get_data["status"] == "pending"


def test_revival_request_validation_rules(client, db_session, test_user, auth_context):
    # Setup Developer B
    developer_b = create_user(
        db=db_session,
        github_id=98765,
        username="devb",
        name="Developer B",
        avatar_url="https://avatar.url/b",
        access_token="token_b",
    )
    # Setup Developer C
    developer_c = create_user(
        db=db_session,
        github_id=98766,
        username="devc",
        name="Developer C",
        avatar_url="https://avatar.url/c",
        access_token="token_c",
    )
    
    # Create repository owned by test_user
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 902,
            "name": "project-beta",
            "full_name": "testuser/project-beta",
            "html_url": "https://github.com/testuser/project-beta",
            "default_branch": "main",
        },
    )
    db_session.commit()

    # Rule 5: Unauthenticated user cannot create a request
    auth_context.user = None
    response = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "Hack attempt"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    # Rule 6: Developer cannot request their own repository
    auth_context.user = test_user
    # Publish first to isolate the owner check
    repo.published = True
    db_session.commit()
    
    response = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "My own repo"},
    )
    assert response.status_code == 400
    assert "own repository" in response.json()["detail"]

    # Rule 7: Developer cannot request an unpublished repository
    # Unpublish it
    repo.published = False
    db_session.commit()

    auth_context.user = developer_b
    response = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "Unpublished project request"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"

    # Rule 8: Duplicate pending request is rejected
    # Publish it again
    repo.published = True
    db_session.commit()

    # Create first request
    response = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "First request"},
    )
    assert response.status_code == 201

    # Try creating second request
    response = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "Second duplicate request"},
    )
    assert response.status_code == 409
    assert "already have" in response.json()["detail"]

    # Rule 9: Different developers can each request the same published repository
    auth_context.user = developer_c
    response = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "Request from Dev C"},
    )
    assert response.status_code == 201
    assert response.json()["requester_id"] == developer_c.id

    # Rule 10: Missing repository returns appropriate error
    response = client.post(
        "/repositories/99999/revival-requests",
        json={"message": "Non-existent repo"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Repository not found"


def test_owner_view_revival_requests(client, db_session, test_user, auth_context):
    # Setup two developers who will request revival
    dev_b = create_user(
        db=db_session,
        github_id=98765,
        username="devb",
        name="Developer B",
        avatar_url="https://avatar.url/b",
        access_token="token_b",
    )
    dev_c = create_user(
        db=db_session,
        github_id=98766,
        username="devc",
        name="Developer C",
        avatar_url="https://avatar.url/c",
        access_token="token_c",
    )
    db_session.commit()

    # Create repo owned by test_user
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 903,
            "name": "project-gamma",
            "full_name": "testuser/project-gamma",
            "html_url": "https://github.com/testuser/project-gamma",
            "default_branch": "main",
        },
    )
    # Publish repository so developers can request
    repo.published = True
    db_session.commit()

    # Developer B submits a request
    auth_context.user = dev_b
    res_b = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "Dev B message"},
    )
    assert res_b.status_code == 201

    # Developer C submits a request (newer)
    auth_context.user = dev_c
    res_c = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "Dev C message"},
    )
    assert res_c.status_code == 201

    # Check 10. Unauthenticated user cannot view the request list.
    auth_context.user = None
    res = client.get(f"/repositories/{repo.id}/revival-requests")
    assert res.status_code == 401

    # Check 9. Another authenticated user (Dev B) cannot view the request list.
    auth_context.user = dev_b
    res = client.get(f"/repositories/{repo.id}/revival-requests")
    assert res.status_code == 404  # Returns 404 to avoid revealing ownership/existence

    # Check 1. Owner can retrieve requests for their repository
    auth_context.user = test_user
    res = client.get(f"/repositories/{repo.id}/revival-requests")
    assert res.status_code == 200
    requests_list = res.json()

    # Check 2. Owner receives multiple requests
    # Check 12. Requests from multiple developers are all returned
    assert len(requests_list) == 2

    # Check 3. Requests are ordered newest first (Dev C first)
    assert requests_list[0]["requester_id"] == dev_c.id
    assert requests_list[1]["requester_id"] == dev_b.id

    # Check 4. Requester information is included
    # Check 13. No sensitive requester fields (like access_token) are exposed
    req_c = requests_list[0]["requester"]
    assert req_c["username"] == "devc"
    assert req_c["name"] == "Developer C"
    assert req_c["avatar_url"] == "https://avatar.url/c"
    assert "access_token" not in req_c

    # Check 5. Request message is returned correctly
    assert requests_list[0]["message"] == "Dev C message"
    assert requests_list[1]["message"] == "Dev B message"

    # Check 6. Request status is returned as pending
    assert requests_list[0]["status"] == "pending"
    assert requests_list[1]["status"] == "pending"

    # Check 7. Owner can view requests when repository is published
    # Verified (currently published)

    # Check 8. Owner can view requests when repository is unpublished
    repo.published = False
    db_session.commit()

    res = client.get(f"/repositories/{repo.id}/revival-requests")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_decision_workflow_approval(client, db_session, test_user, auth_context):
    dev_b = create_user(
        db=db_session,
        github_id=98765,
        username="devb",
        name="Developer B",
        avatar_url="https://avatar.url/b",
        access_token="token_b",
    )
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 904,
            "name": "project-delta",
            "full_name": "testuser/project-delta",
            "html_url": "https://github.com/testuser/project-delta",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    # Developer B requests
    auth_context.user = dev_b
    res_b = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "Dev B message"},
    )
    assert res_b.status_code == 201
    request_id = res_b.json()["id"]

    # Check 7. Unauthenticated user cannot approve.
    auth_context.user = None
    res = client.post(f"/repositories/{repo.id}/revival-requests/{request_id}/approve")
    assert res.status_code == 401

    # Check 5. Other user (Dev B) cannot approve.
    # Check 6. Requester (Dev B) cannot approve their own request.
    auth_context.user = dev_b
    res = client.post(f"/repositories/{repo.id}/revival-requests/{request_id}/approve")
    assert res.status_code == 404  # Privacy: owner-only auth check returns 404

    # Check 8. Owner can approve even if repository is unpublished.
    repo.published = False
    db_session.commit()

    # Check 1. Owner can approve a pending request.
    auth_context.user = test_user
    res = client.post(f"/repositories/{repo.id}/revival-requests/{request_id}/approve")
    assert res.status_code == 200
    data = res.json()

    # Check 3. Response status becomes "approved".
    assert data["status"] == "approved"

    # Check 4. Requester information remains available.
    assert data["requester"]["username"] == "devb"

    # Check 2. Approval persists in the database.
    db_req = db_session.query(RevivalRequest).filter(RevivalRequest.id == request_id).first()
    assert db_req.status == "approved"

    # Check 16. Approved request cannot be approved again.
    res = client.post(f"/repositories/{repo.id}/revival-requests/{request_id}/approve")
    assert res.status_code == 409
    assert "already been decided" in res.json()["detail"]

    # Check 17. Approved request cannot be rejected.
    res = client.post(f"/repositories/{repo.id}/revival-requests/{request_id}/reject")
    assert res.status_code == 409

    # Check 20. Wrong repository/request combination returns 404.
    res = client.post(f"/repositories/99999/revival-requests/{request_id}/approve")
    assert res.status_code == 404


def test_decision_workflow_rejection(client, db_session, test_user, auth_context):
    dev_b = create_user(
        db=db_session,
        github_id=98765,
        username="devb",
        name="Developer B",
        avatar_url="https://avatar.url/b",
        access_token="token_b",
    )
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 905,
            "name": "project-epsilon",
            "full_name": "testuser/project-epsilon",
            "html_url": "https://github.com/testuser/project-epsilon",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    # Developer B requests
    auth_context.user = dev_b
    res_b = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "Dev B message"},
    )
    assert res_b.status_code == 201
    request_id = res_b.json()["id"]

    # Check 14. Unauthenticated user cannot reject.
    auth_context.user = None
    res = client.post(f"/repositories/{repo.id}/revival-requests/{request_id}/reject")
    assert res.status_code == 401

    # Check 12. Other user cannot reject.
    # Check 13. Requester cannot reject.
    auth_context.user = dev_b
    res = client.post(f"/repositories/{repo.id}/revival-requests/{request_id}/reject")
    assert res.status_code == 404

    # Check 15. Owner can reject even if repository is unpublished.
    repo.published = False
    db_session.commit()

    # Check 9. Owner can reject a pending request.
    auth_context.user = test_user
    res = client.post(f"/repositories/{repo.id}/revival-requests/{request_id}/reject")
    assert res.status_code == 200
    data = res.json()

    # Check 11. Response status becomes "rejected".
    assert data["status"] == "rejected"

    # Check 10. Rejection persists in the database.
    db_req = db_session.query(RevivalRequest).filter(RevivalRequest.id == request_id).first()
    assert db_req.status == "rejected"

    # Check 18. Rejected request cannot be approved.
    res = client.post(f"/repositories/{repo.id}/revival-requests/{request_id}/approve")
    assert res.status_code == 409

    # Check 19. Rejected request cannot be rejected again.
    res = client.post(f"/repositories/{repo.id}/revival-requests/{request_id}/reject")
    assert res.status_code == 409


def test_developer_request_status_retrieval(client, db_session, test_user, auth_context):
    dev_b = create_user(
        db=db_session,
        github_id=98765,
        username="devb",
        name="Developer B",
        avatar_url="https://avatar.url/b",
        access_token="token_b",
    )
    dev_c = create_user(
        db=db_session,
        github_id=98766,
        username="devc",
        name="Developer C",
        avatar_url="https://avatar.url/c",
        access_token="token_c",
    )
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 906,
            "name": "project-zeta",
            "full_name": "testuser/project-zeta",
            "html_url": "https://github.com/testuser/project-zeta",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    # Developer B requests
    auth_context.user = dev_b
    res_b = client.post(
        f"/repositories/{repo.id}/revival-requests",
        json={"message": "Dev B message"},
    )
    request_id = res_b.json()["id"]

    # Check 23. Developer can retrieve their own pending request.
    res = client.get(f"/repositories/{repo.id}/revival-requests/my")
    assert res.status_code == 200
    assert res.json()["status"] == "pending"

    # Check 24. Developer cannot retrieve another developer's request.
    auth_context.user = dev_c
    res = client.get(f"/repositories/{repo.id}/revival-requests/my")
    assert res.status_code == 200
    assert res.json() is None

    # Owner approves Dev B request
    auth_context.user = test_user
    client.post(f"/repositories/{repo.id}/revival-requests/{request_id}/approve")

    # Check 21. Developer can retrieve their own approved request.
    auth_context.user = dev_b
    res = client.get(f"/repositories/{repo.id}/revival-requests/my")
    assert res.status_code == 200
    assert res.json()["status"] == "approved"


def test_owner_request_list_all_statuses(client, db_session, test_user, auth_context):
    dev_b = create_user(
        db=db_session,
        github_id=98765,
        username="devb",
        name="Developer B",
        avatar_url="https://avatar.url/b",
        access_token="token_b",
    )
    dev_c = create_user(
        db=db_session,
        github_id=98766,
        username="devc",
        name="Developer C",
        avatar_url="https://avatar.url/c",
        access_token="token_c",
    )
    dev_d = create_user(
        db=db_session,
        github_id=98767,
        username="devd",
        name="Developer D",
        avatar_url="https://avatar.url/d",
        access_token="token_d",
    )
    repo = create_repository(
        db=db_session,
        owner_id=test_user.id,
        repo={
            "id": 907,
            "name": "project-eta",
            "full_name": "testuser/project-eta",
            "html_url": "https://github.com/testuser/project-eta",
            "default_branch": "main",
        },
    )
    repo.published = True
    db_session.commit()

    # Three requests
    auth_context.user = dev_b
    res_b = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "B"})
    req_b_id = res_b.json()["id"]

    auth_context.user = dev_c
    res_c = client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "C"})
    req_c_id = res_c.json()["id"]

    auth_context.user = dev_d
    client.post(f"/repositories/{repo.id}/revival-requests", json={"message": "D"})

    # Owner approves Dev B
    auth_context.user = test_user
    client.post(f"/repositories/{repo.id}/revival-requests/{req_b_id}/approve")

    # Owner rejects Dev C
    client.post(f"/repositories/{repo.id}/revival-requests/{req_c_id}/reject")

    # Owner retrieves requests list
    res = client.get(f"/repositories/{repo.id}/revival-requests")
    assert res.status_code == 200
    list_res = res.json()
    assert len(list_res) == 3

    # Check 25. Owner request list shows pending requests.
    # Check 26. Owner request list shows approved requests.
    # Check 27. Owner request list shows rejected requests.
    statuses = {item["status"] for item in list_res}
    assert "pending" in statuses
    assert "approved" in statuses
    assert "rejected" in statuses

    # Check 28. Other users cannot retrieve the owner request list.
    auth_context.user = dev_b
    res = client.get(f"/repositories/{repo.id}/revival-requests")
    assert res.status_code == 404
