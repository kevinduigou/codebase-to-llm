"""Step definitions for video key insights feature tests."""

import os
import requests
from behave import given, when, then
from dotenv import load_dotenv

# Load environment variables from .env-development
load_dotenv(".env-development")


@given("the FastAPI server is running")
def step_server_running(context):
    """Verify that the FastAPI server is accessible."""
    try:
        response = requests.get(f"{context.base_url}/docs")
        assert (
            response.status_code == 200
        ), f"Server not accessible: {response.status_code}"
    except requests.exceptions.ConnectionError:
        raise AssertionError("FastAPI server is not running or not accessible")


@given("I have a valid user account")
def step_have_user_account(context):
    """Use existing validated user account from environment variables."""
    # Use existing validated user credentials from environment variables
    context.test_user = {
        "user_name": os.getenv("TEST_USER_NAME"),
        "password": os.getenv("TEST_USER_PASSWORD"),
    }


@given("I am authenticated")
def step_authenticated(context):
    """Authenticate and get access token."""
    login_data = {
        "username": context.test_user["user_name"],
        "password": context.test_user["password"],
    }

    response = requests.post(
        f"{context.base_url}/auth/token",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert (
        response.status_code == 200
    ), f"Authentication failed: {response.status_code} - {response.text}"

    token_data = response.json()
    context.access_token = token_data["access_token"]
    context.auth_headers = {"Authorization": f"Bearer {context.access_token}"}


@given('I have video key insights data with title "{title}"')
def step_have_video_key_insights_data(context, title):
    """Prepare video key insights test data."""
    context.test_video_key_insights = {
        "title": title,
        "key_insights": [
            {
                "content": "This is a key insight about the video content",
                "video_url": "https://example.com/video.mp4",
                "begin_timestamp": "00:01:30",
                "end_timestamp": "00:02:45",
            },
            {
                "content": "Another important insight from the video",
                "video_url": "https://example.com/video.mp4",
                "begin_timestamp": "00:05:10",
                "end_timestamp": "00:06:20",
            },
        ],
    }


@when("I create the video key insights via POST request")
def step_create_video_key_insights(context):
    """Create video key insights via POST request."""
    response = requests.post(
        f"{context.base_url}/key-insights/video-key-insights",
        json=context.test_video_key_insights,
        headers=context.auth_headers,
    )

    context.create_response = response
    if response.status_code == 200:
        context.created_video_key_insights = response.json()


@then("the video key insights should be created successfully")
def step_video_key_insights_created_successfully(context):
    """Verify video key insights creation was successful."""
    assert (
        context.create_response.status_code == 200
    ), f"Expected 200, got {context.create_response.status_code}: {context.create_response.text}"


@then("I should receive a valid video key insights ID")
def step_receive_valid_id(context):
    """Verify that a valid ID was returned."""
    assert "id" in context.created_video_key_insights, "Response should contain an ID"
    assert context.created_video_key_insights["id"], "ID should not be empty"
    context.video_key_insights_id = context.created_video_key_insights["id"]


@when("I retrieve the video key insights by ID")
def step_retrieve_video_key_insights_by_id(context):
    """Retrieve video key insights by ID."""
    response = requests.get(
        f"{context.base_url}/key-insights/video-key-insights/{context.video_key_insights_id}",
        headers=context.auth_headers,
    )

    context.get_response = response
    if response.status_code == 200:
        context.retrieved_video_key_insights = response.json()


@then("I should get the same video key insights data")
def step_get_same_data(context):
    """Verify retrieved data matches created data."""
    assert (
        context.get_response.status_code == 200
    ), f"Expected 200, got {context.get_response.status_code}: {context.get_response.text}"

    retrieved = context.retrieved_video_key_insights
    original = context.test_video_key_insights

    # Verify key insights content
    assert len(retrieved["key_insights"]) == len(
        original["key_insights"]
    ), "Number of key insights should match"

    for i, insight in enumerate(retrieved["key_insights"]):
        original_insight = original["key_insights"][i]
        assert (
            insight["content"] == original_insight["content"]
        ), f"Content mismatch at index {i}"
        assert (
            insight["video_url"] == original_insight["video_url"]
        ), f"Video URL mismatch at index {i}"
        assert (
            insight["begin_timestamp"] == original_insight["begin_timestamp"]
        ), f"Begin timestamp mismatch at index {i}"
        assert (
            insight["end_timestamp"] == original_insight["end_timestamp"]
        ), f"End timestamp mismatch at index {i}"


@then('the title should be "{expected_title}"')
def step_verify_title(context, expected_title):
    """Verify the title matches expected value."""
    assert (
        context.retrieved_video_key_insights["title"] == expected_title
    ), f"Expected title '{expected_title}', got '{context.retrieved_video_key_insights['title']}'"


@when("I list all video key insights")
def step_list_all_video_key_insights(context):
    """List all video key insights."""
    response = requests.get(
        f"{context.base_url}/key-insights/all-video-key-insights",
        headers=context.auth_headers,
    )

    context.list_response = response
    if response.status_code == 200:
        context.all_video_key_insights = response.json()


@then("the created video key insights should be in the list")
def step_created_in_list(context):
    """Verify created video key insights appears in the list."""
    assert (
        context.list_response.status_code == 200
    ), f"Expected 200, got {context.list_response.status_code}: {context.list_response.text}"

    found = False
    for item in context.all_video_key_insights:
        if item["id"] == context.video_key_insights_id:
            found = True
            break

    assert (
        found
    ), f"Created video key insights with ID {context.video_key_insights_id} not found in list"


@when("I delete the video key insights by ID")
def step_delete_video_key_insights(context):
    """Delete video key insights by ID."""
    response = requests.delete(
        f"{context.base_url}/key-insights/video-key-insights/{context.video_key_insights_id}",
        headers=context.auth_headers,
    )

    context.delete_response = response


@then("the video key insights should be deleted successfully")
def step_video_key_insights_deleted_successfully(context):
    """Verify deletion was successful."""
    assert (
        context.delete_response.status_code == 200
    ), f"Expected 200, got {context.delete_response.status_code}: {context.delete_response.text}"

    response_data = context.delete_response.json()
    assert "message" in response_data, "Response should contain a message"
    assert (
        "deleted successfully" in response_data["message"]
    ), "Message should confirm deletion"


@when("I try to retrieve the deleted video key insights")
def step_try_retrieve_deleted(context):
    """Try to retrieve deleted video key insights."""
    response = requests.get(
        f"{context.base_url}/key-insights/video-key-insights/{context.video_key_insights_id}",
        headers=context.auth_headers,
    )

    context.get_deleted_response = response


@then("I should get a 404 error")
def step_get_404_error(context):
    """Verify that a 404 error is returned."""
    assert (
        context.get_deleted_response.status_code == 404
    ), f"Expected 404, got {context.get_deleted_response.status_code}: {context.get_deleted_response.text}"
