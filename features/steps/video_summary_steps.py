import requests
from behave import given, when, then


@given('I have video summary data with title "{title}"')
def step_have_video_summary_data(context, title):
    context.test_video_summary = {
        "title": title,
        "segments": [
            {
                "content": "This is a summary of the first part",
                "video_url": "https://example.com/video.mp4",
                "begin_timestamp": "00:01:30",
                "end_timestamp": "00:02:45",
            },
            {
                "content": "This summarizes another section",
                "video_url": "https://example.com/video.mp4",
                "begin_timestamp": "00:05:10",
                "end_timestamp": "00:06:20",
            },
        ],
    }


@when("I create the video summary via POST request")
def step_create_video_summary(context):
    response = requests.post(
        f"{context.base_url}/summaries/video-summaries",
        json=context.test_video_summary,
        headers=context.auth_headers,
    )
    context.create_response = response
    if response.status_code == 200:
        context.created_video_summary = response.json()


@then("the video summary should be created successfully")
def step_video_summary_created_successfully(context):
    assert (
        context.create_response.status_code == 200
    ), f"Expected 200, got {context.create_response.status_code}: {context.create_response.text}"


@then("I should receive a valid video summary ID")
def step_receive_valid_summary_id(context):
    assert "id" in context.created_video_summary
    assert context.created_video_summary["id"]
    context.video_summary_id = context.created_video_summary["id"]


@when("I retrieve the video summary by ID")
def step_retrieve_video_summary_by_id(context):
    response = requests.get(
        f"{context.base_url}/summaries/video-summaries/{context.video_summary_id}",
        headers=context.auth_headers,
    )
    context.get_response = response
    if response.status_code == 200:
        context.retrieved_video_summary = response.json()


@then("I should get the same video summary data")
def step_get_same_summary_data(context):
    assert (
        context.get_response.status_code == 200
    ), f"Expected 200, got {context.get_response.status_code}: {context.get_response.text}"
    retrieved = context.retrieved_video_summary
    original = context.test_video_summary
    assert len(retrieved["segments"]) == len(original["segments"])
    for i, seg in enumerate(retrieved["segments"]):
        orig = original["segments"][i]
        assert seg["content"] == orig["content"]
        assert seg["video_url"] == orig["video_url"]
        assert seg["begin_timestamp"] == orig["begin_timestamp"]
        assert seg["end_timestamp"] == orig["end_timestamp"]


@then('the summary title should be "{expected_title}"')
def step_verify_summary_title(context, expected_title):
    assert (
        context.retrieved_video_summary["title"] == expected_title
    ), f"Expected title '{expected_title}', got '{context.retrieved_video_summary['title']}'"


@when("I list all video summaries")
def step_list_all_video_summaries(context):
    response = requests.get(
        f"{context.base_url}/summaries/all-video-summaries",
        headers=context.auth_headers,
    )
    context.list_response = response
    if response.status_code == 200:
        context.all_video_summaries = response.json()


@then("the created video summary should be in the list")
def step_summary_created_in_list(context):
    assert (
        context.list_response.status_code == 200
    ), f"Expected 200, got {context.list_response.status_code}: {context.list_response.text}"
    found = any(
        item["id"] == context.video_summary_id for item in context.all_video_summaries
    )
    assert (
        found
    ), f"Created video summary with ID {context.video_summary_id} not found in list"


@when("I delete the video summary by ID")
def step_delete_video_summary(context):
    response = requests.delete(
        f"{context.base_url}/summaries/video-summaries/{context.video_summary_id}",
        headers=context.auth_headers,
    )
    context.delete_response = response


@then("the video summary should be deleted successfully")
def step_video_summary_deleted_successfully(context):
    assert (
        context.delete_response.status_code == 200
    ), f"Expected 200, got {context.delete_response.status_code}: {context.delete_response.text}"
    response_data = context.delete_response.json()
    assert "message" in response_data
    assert "deleted successfully" in response_data["message"]


@when("I try to retrieve the deleted video summary")
def step_try_retrieve_deleted_summary(context):
    response = requests.get(
        f"{context.base_url}/summaries/video-summaries/{context.video_summary_id}",
        headers=context.auth_headers,
    )
    context.get_deleted_response = response
