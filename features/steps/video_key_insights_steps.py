"""Step definitions for video key insights feature tests."""

import os
import time
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
                "begin_timestamp": {"hour": 0, "minute": 1, "second": 30},
                "end_timestamp": {"hour": 0, "minute": 2, "second": 45},
            },
            {
                "content": "Another important insight from the video",
                "video_url": "https://example.com/video.mp4",
                "begin_timestamp": {"hour": 0, "minute": 5, "second": 10},
                "end_timestamp": {"hour": 0, "minute": 6, "second": 20},
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


@given('I have a YouTube video URL "{video_url}"')
def step_have_youtube_video_url(context, video_url):
    context.youtube_video_url = video_url


@given('I have a target language "{target_language}"')
def step_have_target_language(context, target_language):
    context.target_language = target_language


@given("I want {count:d} key insights")
def step_want_key_insights(context, count):
    context.number_of_key_insights = count


@given('I have a model ID "{model_name}" for key insights processing')
def step_have_model_id_for_key_insights_processing(context, model_name):
    import os

    is_anthropic = model_name.startswith("claude-") or "claude" in model_name.lower()

    if is_anthropic:
        api_key_data = {
            "id_value": "test-anthropic-api-key",
            "url_provider": "https://api.anthropic.com/v1/",
            "api_key_value": os.getenv("ANTHROPIC_API_KEY", "test-key"),
        }
        api_key_id = "test-anthropic-api-key"
    else:
        api_key_data = {
            "id_value": "test-openai-api-key",
            "url_provider": "https://api.openai.com/v1/",
            "api_key_value": os.getenv("OPENAI_API_KEY", "test-key"),
        }
        api_key_id = "test-openai-api-key"

    api_key_response = requests.post(
        f"{context.base_url}/api-keys/",
        json=api_key_data,
        headers=context.auth_headers,
    )
    if api_key_response.status_code not in [200, 400]:
        raise AssertionError(
            f"Failed to create API key: {api_key_response.status_code} - {api_key_response.text}"
        )

    model_id = f"test-{model_name}"
    model_data = {"id_value": model_id, "name": model_name, "api_key_id": api_key_id}
    model_response = requests.post(
        f"{context.base_url}/models/",
        json=model_data,
        headers=context.auth_headers,
    )
    if model_response.status_code not in [200, 400]:
        raise AssertionError(
            f"Failed to create model: {model_response.status_code} - {model_response.text}"
        )
    context.key_insights_model_id = model_id
    context.test_api_key_id = api_key_id
    context.test_model_id = model_id


@when("I trigger key insights extraction for the YouTube URL")
def step_trigger_key_insights_extraction(context):
    request_data = {
        "model_id": context.key_insights_model_id,
        "video_url": context.youtube_video_url,
        "target_language": getattr(context, "target_language", "English"),
        "number_of_key_insights": getattr(context, "number_of_key_insights", 5),
    }
    response = requests.post(
        f"{context.base_url}/key-insights/",
        json=request_data,
        headers=context.auth_headers,
    )
    context.trigger_response = response
    if response.status_code == 200:
        context.task_data = response.json()


@then("I should receive a task ID for the key insights")
def step_receive_task_id_for_key_insights(context):
    assert (
        context.trigger_response.status_code == 200
    ), f"Expected 200, got {context.trigger_response.status_code}: {context.trigger_response.text}"
    assert "task_id" in context.task_data
    assert context.task_data["task_id"]
    context.key_insights_task_id = context.task_data["task_id"]


@when("I wait for the key insights task to complete")
def step_wait_for_key_insights_task_to_complete(context):
    max_wait_time = 300
    check_interval = 15
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        response = requests.get(
            f"{context.base_url}/key-insights/{context.key_insights_task_id}",
            headers=context.auth_headers,
        )
        if response.status_code == 200:
            task_status = response.json()
            context.task_status_response = task_status
            if task_status["status"] == "SUCCESS":
                context.completed_task_data = task_status
                return
            if task_status["status"] == "FAILURE":
                raise AssertionError(f"Key insights task failed: {task_status}")
        time.sleep(check_interval)

    raise AssertionError(
        f"Key insights task did not complete within {max_wait_time} seconds"
    )


@then("the key insights task should be completed successfully")
def step_key_insights_task_completed_successfully(context):
    assert (
        context.completed_task_data["status"] == "SUCCESS"
    ), f"Expected task status SUCCESS, got {context.completed_task_data['status']}"


@then("the extracted key insights should contain {expected_count:d} items")
def step_key_insights_should_contain_items(context, expected_count):
    assert "insights" in context.completed_task_data
    insights = context.completed_task_data["insights"]
    assert insights is not None, "Insights should not be None"
    assert (
        len(insights) == expected_count
    ), f"Expected {expected_count} insights, got {len(insights)}"
    context.task_insights = insights


@when("I create video key insights from the task result")
def step_create_video_key_insights_from_task_result(context):
    def _parse_timestamp(ts) -> dict[str, int]:
        # Handle both string and dictionary formats
        if isinstance(ts, dict):
            # If it's already a dictionary, return it as is (assuming it has the right structure)
            return {
                "hour": int(ts.get("hour", 0)),
                "minute": int(ts.get("minute", 0)),
                "second": int(ts.get("second", 0)),
            }
        elif isinstance(ts, str):
            # Parse string format like "0:1:30"
            parts = ts.split(":")
            if len(parts) == 3:
                hour, minute, second = parts
            elif len(parts) == 2:
                hour = "0"
                minute, second = parts
            else:
                hour = minute = second = "0"
            return {
                "hour": int(hour),
                "minute": int(minute),
                "second": int(second),
            }
        else:
            # Default fallback
            return {"hour": 0, "minute": 0, "second": 0}

    converted_insights = []
    for insight in context.task_insights:
        converted_insights.append(
            {
                "content": insight.get("content", ""),
                "video_url": insight.get("video_url", ""),
                "begin_timestamp": _parse_timestamp(
                    insight.get("begin_timestamp", "0:0:0")
                ),
                "end_timestamp": _parse_timestamp(
                    insight.get("end_timestamp", "0:0:0")
                ),
            }
        )

    title = context.completed_task_data.get(
        "title", f"YouTube Video Key Insights - {context.youtube_video_url}"
    )
    video_key_insights_data = {
        "title": title,
        "key_insights": converted_insights,
    }
    context.test_video_key_insights = video_key_insights_data
    response = requests.post(
        f"{context.base_url}/key-insights/video-key-insights",
        json=video_key_insights_data,
        headers=context.auth_headers,
    )
    context.create_response = response
    if response.status_code == 200:
        context.created_video_key_insights = response.json()
